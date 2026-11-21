"""Sign-in, token refresh and session setup for the Audi service."""

from __future__ import annotations

import base64
import hmac
import json
import logging
import os
import re
import uuid
from datetime import datetime, UTC
from hashlib import sha256, sha512
from typing import Any, NoReturn
from urllib.parse import parse_qs, urlencode, urlparse

from bs4 import BeautifulSoup

from .audi_api import AudiAPI
from .const import AUTH0_REDIRECT_URI, AUTH0_REFRESH_TOKEN_PREFIX
from .util import to_byte_array

_LOGGER = logging.getLogger(__name__)

# Scope requested for the Device Authorization Grant. "mbb" is required for the
# legacy MBB / fs-car endpoints (lock/unlock, trip statistics, climater); the
# other scopes cover account identity and the CARIAD BFF vehicle data.
DEVICE_CODE_SCOPE = "openid mbb profile badge cars dealers vin"

# Auth0 tokens target CARIAD directly and cannot use the legacy IDK endpoint.
_AUTH0_AUTHORIZATION_ENDPOINT = "https://group.identity.vwgroup.io/authorize"
_AUTH0_TOKEN_ENDPOINT = "https://group.identity.vwgroup.io/oauth/token"
_AUTH0_AUDIENCE = "https://api.cariad.com"
_AUTH0_SCOPE = "openid profile offline_access"


class AudiAuthError(Exception):
    """Raised when authorization is missing or a token has been rejected."""


class AudiTokenRefreshError(Exception):
    """Raised when a token refresh is rejected for a reason re-authenticating
    cannot fix — e.g. ``invalid_client`` (the client_id is fixed in code, so a
    reauth reuses the same client), or a transient / malformed response. It is
    treated as a retryable update failure rather than escalated to reauth.
    """


# OAuth errors on a refresh exchange that genuinely need the user to sign in
# again: the refresh token itself is rejected, and only a fresh grant can fix
# it. Everything else — invalid_client, a transient blip, a malformed body — is
# retried instead of raising an un-actionable reauth prompt. Listing the hard
# failures (rather than the transient ones) means an unknown code degrades to a
# retry, which is the harmless direction.
_REFRESH_REAUTH_ERRORS = frozenset({"invalid_grant", "invalid assertion headers"})


def _raise_refresh_rejected(context: str, parsed: dict, raw: str) -> NoReturn:
    """Raise for a refresh-token exchange that returned no access token.

    ``invalid_grant`` → AudiAuthError (reauth genuinely needed); anything else →
    AudiTokenRefreshError (retryable, no reauth prompt). Used for both the IDK
    refresh and the mbboauth refresh, so it prefers ``error_description`` (which
    mbboauth returns) for the message while classifying on ``error``.
    """
    detail = str(parsed.get("error_description") or parsed.get("error") or raw[:200])
    if parsed.get("error") in _REFRESH_REAUTH_ERRORS:
        raise AudiAuthError(f"{context}: {detail}")
    raise AudiTokenRefreshError(f"{context}: {detail}")


def _to_absolute(absolute_url: str, relative_url: str) -> str:
    """Convert a relative url to an absolute url."""
    url_parts = urlparse(absolute_url)
    return url_parts.scheme + "://" + url_parts.netloc + relative_url


class AudiAuthMixin:
    """Authentication half of AudiService; relies on its connection state."""

    def get_hidden_html_input_form_data(
        self, response: str, form_data: dict[str, str]
    ) -> dict[str, str]:
        # Now parse the html body and extract the target url, csrf token and other required parameters
        html = BeautifulSoup(response, "html.parser")
        form_inputs = html.find_all("input", attrs={"type": "hidden"})
        for form_input in form_inputs:
            name = form_input.get("name")
            form_data[name] = form_input.get("value")

        return form_data

    def get_post_url(self, response: str, url: str) -> str:
        # Now parse the html body and extract the target url, csrf token and other required parameters
        html = BeautifulSoup(response, "html.parser")
        form_tag = html.find("form")

        # Extract the target url
        action = form_tag.get("action")
        if action.startswith("http"):
            # Absolute url
            username_post_url = action
        elif action.startswith("/"):
            # Relative to domain
            username_post_url = _to_absolute(url, action)
        else:
            raise ValueError("Unknown form action: " + action)
        return username_post_url

    # TR/2022-12-20: New secret for X_QMAuth
    def _calculate_X_QMAuth(self) -> str:
        # Calculate X-QMAuth value
        gmtime_100sec = int(
            (datetime.now(UTC) - datetime(1970, 1, 1, tzinfo=UTC)).total_seconds() / 100
        )
        xqmauth_secret = bytes(
            [
                26,
                256 - 74,
                256 - 103,
                37,
                256 - 84,
                23,
                256 - 102,
                256 - 86,
                78,
                256 - 125,
                256 - 85,
                256 - 26,
                113,
                256 - 87,
                71,
                109,
                23,
                100,
                24,
                256 - 72,
                91,
                256 - 41,
                6,
                256 - 15,
                67,
                108,
                256 - 95,
                91,
                256 - 26,
                71,
                256 - 104,
                256 - 100,
            ]
        )
        xqmauth_val = hmac.new(
            xqmauth_secret,
            str(gmtime_100sec).encode("ascii", "ignore"),
            digestmod="sha256",
        ).hexdigest()

        # v1:01da27b0:fbdb6e4ba3109bc68040cb83f380796f4d3bb178a626c4cc7e166815b806e4b5
        return "v1:01da27b0:" + xqmauth_val

    async def _request_auth0_token(
        self, data: dict[str, str], context: str
    ) -> dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        encoded = urlencode(data, encoding="utf-8").replace("+", "%20")
        _rsp, rsptxt = await self._api.request(
            "POST",
            _AUTH0_TOKEN_ENDPOINT,
            encoded,
            headers=headers,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        result = json.loads(rsptxt)
        if "access_token" not in result:
            _raise_refresh_rejected(context, result, rsptxt)
        return result

    def _set_auth0_session(self, result: dict[str, Any]) -> None:
        self._uses_auth0 = True
        self._bearer_token_json = result
        self.audiToken = result
        self.vwToken = result
        self.mbboauthToken = None
        self.xclientId = None
        self._api.set_xclient_id(None)

    async def get_auth0_authorization_url(self, code_challenge: str, state: str) -> str:
        """Return the interactive myAudi Auth0 authorization URL."""
        await self._discover_endpoints()
        params = {
            "client_id": self._client_id,
            "audience": _AUTH0_AUDIENCE,
            "redirect_uri": AUTH0_REDIRECT_URI,
            "response_type": "code",
            "scope": _AUTH0_SCOPE,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state,
            "ui_locales": f"{self._language}-{self._country.upper()}",
        }
        return f"{_AUTH0_AUTHORIZATION_ENDPOINT}?{urlencode(params)}"

    async def login_with_auth0_code(self, code: str, code_verifier: str) -> str:
        """Exchange an interactive Auth0 authorization code."""
        if not self._client_id:
            await self._discover_endpoints()
        result = await self._request_auth0_token(
            {
                "client_id": self._client_id,
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": code_verifier,
                "redirect_uri": AUTH0_REDIRECT_URI,
            },
            "Auth0 code exchange rejected",
        )
        if "refresh_token" not in result:
            raise AudiAuthError("Auth0 did not issue a refresh token")
        self._set_auth0_session(result)
        return AUTH0_REFRESH_TOKEN_PREFIX + result["refresh_token"]

    async def _refresh_auth0_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh a token issued by the myAudi Auth0 public client."""
        result = await self._request_auth0_token(
            {
                "client_id": self._client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "audience": _AUTH0_AUDIENCE,
                "scope": _AUTH0_SCOPE,
            },
            "Auth0 refresh rejected",
        )
        result.setdefault("refresh_token", refresh_token)
        self._set_auth0_session(result)
        return result

    # TR/2021-12-01: Refresh token before it expires
    # returns True when refresh was required and successful, otherwise False
    async def refresh_token_if_necessary(self, elapsed_sec: int) -> bool:
        # The IDK bearer token drives the CARIAD BFF session and carries its own
        # refresh token, independent of the mbboauth token. Base the timing on it
        # and always refresh it: a login whose mbboauth response carried no
        # refresh_token (see _finalize_session) must still keep the IDK session —
        # and therefore every entity — alive past the ~1h access-token lifetime.
        if self._bearer_token_json is None:
            return False
        if "refresh_token" not in self._bearer_token_json:
            return False
        if "expires_in" not in self._bearer_token_json:
            return False

        if (elapsed_sec + 5 * 60) < self._bearer_token_json["expires_in"]:
            # refresh not needed now
            return False

        try:
            if self._uses_auth0:
                await self._refresh_auth0_token(
                    self._bearer_token_json["refresh_token"]
                )
                return True

            # mbboauth refresh — only when a refresh_token is available. The auth
            # response no longer always includes one; when it doesn't, vwToken
            # keeps its current value instead of blocking the IDK refresh below.
            if self.mbboauthToken and "refresh_token" in self.mbboauthToken:
                headers = {
                    "Accept": "application/json",
                    "Accept-Charset": "utf-8",
                    "User-Agent": AudiAPI.HDR_USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Client-ID": self.xclientId,
                }
                mbboauth_refresh_data = {
                    "grant_type": "refresh_token",
                    "token": self.mbboauthToken["refresh_token"],
                    "scope": "sc2:fal",
                }
                encoded_mbboauth_refresh_data = urlencode(
                    mbboauth_refresh_data, encoding="utf-8"
                ).replace("+", "%20")
                mbboauth_refresh_rsp, mbboauth_refresh_rsptxt = await self._api.request(
                    "POST",
                    self.mbbOAuthBaseURL + "/mobile/oauth2/v1/token",
                    encoded_mbboauth_refresh_data,
                    headers=headers,
                    allow_redirects=False,
                    rsp_wtxt=True,
                )
                # this code is the old "vwToken"
                refreshed = json.loads(mbboauth_refresh_rsptxt)
                if "access_token" not in refreshed:
                    _raise_refresh_rejected(
                        "mbboauth refresh rejected",
                        refreshed,
                        mbboauth_refresh_rsptxt,
                    )
                self.vwToken = refreshed
                # If a new refresh_token is provided, save it for further refreshes
                if "refresh_token" in self.vwToken:
                    self.mbboauthToken["refresh_token"] = self.vwToken["refresh_token"]

            # IDK refresh — always, using the IDK token's own refresh token.
            headers = {
                "Accept": "application/json",
                "Accept-Charset": "utf-8",
                "User-Agent": AudiAPI.HDR_USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            # IDK token request data
            tokenreq_data = {
                "client_id": self._client_id,
                "grant_type": "refresh_token",
                "refresh_token": self._bearer_token_json.get("refresh_token"),
                "response_type": "token id_token",
            }
            # IDK token request
            encoded_tokenreq_data = urlencode(tokenreq_data, encoding="utf-8").replace(
                "+", "%20"
            )
            bearer_token_rsp, bearer_token_rsptxt = await self._api.request(
                "POST",
                self._tokenEndpoint,
                encoded_tokenreq_data,
                headers=headers,
                allow_redirects=False,
                rsp_wtxt=True,
            )
            refreshed = json.loads(bearer_token_rsptxt)
            if "access_token" not in refreshed:
                _raise_refresh_rejected(
                    "IDK refresh rejected", refreshed, bearer_token_rsptxt
                )
            # A reply without a new refresh token means "keep using the old one".
            refreshed.setdefault(
                "refresh_token", self._bearer_token_json.get("refresh_token")
            )
            self._bearer_token_json = refreshed

            # AZS token
            headers = {
                "Accept": "application/json",
                "Accept-Charset": "utf-8",
                "X-App-Version": AudiAPI.HDR_XAPP_VERSION,
                "X-App-Name": "myAudi",
                "User-Agent": AudiAPI.HDR_USER_AGENT,
                "Content-Type": "application/json; charset=utf-8",
            }
            asz_req_data = {
                "token": self._bearer_token_json["access_token"],
                "grant_type": "id_token",
                "stage": "live",
                "config": "myaudi",
            }
            azs_token_rsp, azs_token_rsptxt = await self._api.request(
                "POST",
                self._authorizationServerBaseURLLive + "/token",
                json.dumps(asz_req_data),
                headers=headers,
                allow_redirects=False,
                rsp_wtxt=True,
            )
            azs_token_json = json.loads(azs_token_rsptxt)
            self.audiToken = azs_token_json

            return True

        except AudiAuthError:
            raise
        except Exception:
            _LOGGER.exception("Refresh token failed")
            return False

    async def _discover_endpoints(self) -> None:
        """Resolve the dynamic client id and OIDC endpoints.

        Fetches the market configuration and the IDK openid-configuration and
        stores the client id, token endpoint, AZS/mbboauth base URLs and the
        device-authorization endpoint on the instance.
        """
        self._api.use_token(None)
        self._api.set_xclient_id(None)
        self.xclientId = None

        # get markets
        markets_json = await self._api.request(
            "GET",
            "https://content.app.my.audi.com/service/mobileapp/configurations/markets",
            None,
        )
        if (
            self._country.upper()
            not in markets_json["countries"]["countrySpecifications"]
        ):
            raise Exception("Country not found")
        self._language = markets_json["countries"]["countrySpecifications"][
            self._country.upper()
        ]["defaultLanguage"]

        # Dynamic configuration URLs
        marketcfg_url = f"https://content.app.my.audi.com/service/mobileapp/configurations/market/{self._country}/{self._language}?v=4.23.1"
        openidcfg_url = self._get_cariad_url("/auth/v1/idk/oidc/openid-configuration")

        # get market config
        marketcfg_json = await self._api.request("GET", marketcfg_url, None)

        # use dynamic config from marketcfg
        self._client_id = "09b6cbec-cd19-4589-82fd-363dfa8c24da@apps_vw-dilab_com"
        if "idkClientIDAndroidLive" in marketcfg_json:
            self._client_id = marketcfg_json["idkClientIDAndroidLive"]

        self._authorizationServerBaseURLLive = self._get_cariad_url("/login/v1/audi")

        if "myAudiAuthorizationServerProxyServiceURLProduction" in marketcfg_json:
            self._authorizationServerBaseURLLive = marketcfg_json[
                "myAudiAuthorizationServerProxyServiceURLProduction"
            ]
        self.mbbOAuthBaseURL = "https://mbboauth-1d.prd.ece.vwg-connect.com/mbbcoauth"
        if "mbbOAuthBaseURLLive" in marketcfg_json:
            self.mbbOAuthBaseURL = marketcfg_json["mbbOAuthBaseURLLive"]

        if "idkLoginServiceConfigurationURLProduction" in marketcfg_json:
            openidcfg_url = marketcfg_json["idkLoginServiceConfigurationURLProduction"]

        # get openId config
        openidcfg_json = await self._api.request("GET", openidcfg_url, None)

        self._tokenEndpoint = self._get_cariad_url("/auth/v1/idk/oidc/token")
        if "token_endpoint" in openidcfg_json:
            self._tokenEndpoint = openidcfg_json["token_endpoint"]

        # Authorization endpoint, used by the password (authorization-code) login
        # that non-European regions still rely on.
        self._authorizationEndpoint = "https://identity.vwgroup.io/oidc/v1/authorize"
        if "authorization_endpoint" in openidcfg_json:
            self._authorizationEndpoint = openidcfg_json["authorization_endpoint"]

        # Device Authorization Grant (RFC 8628) endpoint. Discovery advertises it;
        # fall back to the well-known global identity endpoint.
        self._deviceAuthorizationEndpoint = (
            "https://identity.vwgroup.io/oidc/v1/device_authorization"
        )
        if "device_authorization_endpoint" in openidcfg_json:
            self._deviceAuthorizationEndpoint = openidcfg_json[
                "device_authorization_endpoint"
            ]

    async def login(self, user: str, password: str) -> None:
        """Username/password login (authorization-code flow).

        Retained for the regions where Audi has not (yet) enforced Play Integrity
        attestation on the token exchange. European accounts must use the Device
        Authorization Grant instead; see `request_device_code`.
        """
        _LOGGER.debug("LOGIN: Starting password login to the Audi service...")
        await self.login_request(user, password)

    async def login_request(self, user: str, password: str) -> None:
        await self._discover_endpoints()

        # generate code_challenge
        code_verifier = str(base64.urlsafe_b64encode(os.urandom(32)), "utf-8").strip(
            "="
        )
        code_challenge = str(
            base64.urlsafe_b64encode(
                sha256(code_verifier.encode("ascii", "ignore")).digest()
            ),
            "utf-8",
        ).strip("=")
        code_challenge_method = "S256"

        state = str(uuid.uuid4())
        nonce = str(uuid.uuid4())

        # login page
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "X-App-Version": AudiAPI.HDR_XAPP_VERSION,
            "X-App-Name": "myAudi",
            "User-Agent": AudiAPI.HDR_USER_AGENT,
        }
        idk_data = {
            "response_type": "code",
            "client_id": self._client_id,
            "redirect_uri": "myaudi:///",
            "scope": "address profile badge birthdate birthplace nationalIdentifier nationality profession email vin phone nickname name picture mbb gallery openid",
            "state": state,
            "nonce": nonce,
            "prompt": "login",
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "ui_locales": "de-de de",
        }
        idk_rsp, idk_rsptxt = await self._api.request(
            "GET",
            self._authorizationEndpoint,
            None,
            headers=headers,
            params=idk_data,
            rsp_wtxt=True,
        )

        # form_data with email
        submit_data = self.get_hidden_html_input_form_data(idk_rsptxt, {"email": user})
        submit_url = self.get_post_url(idk_rsptxt, self._authorizationEndpoint)
        # send email
        email_rsp, email_rsptxt = await self._api.request(
            "POST",
            submit_url,
            submit_data,
            headers=headers,
            cookies=idk_rsp.cookies,
            allow_redirects=True,
            rsp_wtxt=True,
        )

        # form_data with password
        # 2022-01-29: new HTML response uses js to build the html form data + button.
        #             Therefore it's not possible to extract hmac and other form data.
        #             --> extract hmac from embedded js snippet.
        regex_res = re.findall('"hmac"\\s*:\\s*"[0-9a-fA-F]+"', email_rsptxt)
        if regex_res:
            submit_url = submit_url.replace("identifier", "authenticate")
            submit_data["hmac"] = regex_res[0].split(":")[1].strip('"')
            submit_data["password"] = password
        else:
            submit_data = self.get_hidden_html_input_form_data(
                email_rsptxt, {"password": password}
            )
            submit_url = self.get_post_url(email_rsptxt, submit_url)

        # send password
        pw_rsp, _pw_rsptxt = await self._api.request(
            "POST",
            submit_url,
            submit_data,
            headers=headers,
            cookies=idk_rsp.cookies,
            allow_redirects=False,
            rsp_wtxt=True,
        )

        # forward1 after pwd
        if "Location" not in pw_rsp.headers:
            raise AudiAuthError(
                f"Login redirect missing after password submission "
                f"(HTTP {pw_rsp.status}). "
                "Audi may be showing a consent or terms-of-service prompt. "
                "Please log in to myAudi via a browser or the myAudi app and "
                "accept any pending agreements, then restart the integration."
            )
        fwd1_rsp, _fwd1_rsptxt = await self._api.request(
            "GET",
            pw_rsp.headers["Location"],
            None,
            headers=headers,
            cookies=idk_rsp.cookies,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        # forward2 after pwd
        fwd2_rsp, _fwd2_rsptxt = await self._api.request(
            "GET",
            fwd1_rsp.headers["Location"],
            None,
            headers=headers,
            cookies=idk_rsp.cookies,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        # get tokens
        codeauth_rsp, _codeauth_rsptxt = await self._api.request(
            "GET",
            fwd2_rsp.headers["Location"],
            None,
            headers=headers,
            cookies=fwd2_rsp.cookies,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        authcode_parsed = urlparse(
            codeauth_rsp.headers["Location"][len("myaudi:///?") :]
        )
        authcode_strings = parse_qs(authcode_parsed.path)

        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "X-QMAuth": self._calculate_X_QMAuth(),
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        tokenreq_data = {
            "client_id": self._client_id,
            "grant_type": "authorization_code",
            "code": authcode_strings["code"][0],
            "redirect_uri": "myaudi:///",
            "response_type": "token id_token",
            "code_verifier": code_verifier,
        }
        encoded_tokenreq_data = urlencode(tokenreq_data, encoding="utf-8").replace(
            "+", "%20"
        )
        _bearer_token_rsp, bearer_token_rsptxt = await self._api.request(
            "POST",
            self._tokenEndpoint,
            encoded_tokenreq_data,
            headers=headers,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        bearer_token_json = json.loads(bearer_token_rsptxt)
        if "access_token" not in bearer_token_json:
            # In Europe this is where Play Integrity attestation rejects the
            # exchange ("invalid assertion headers"); surface it clearly rather
            # than failing later with a KeyError.
            raise AudiAuthError(
                "Password login rejected at the token exchange: "
                + str(bearer_token_json.get("error", bearer_token_rsptxt[:200]))
            )
        self._bearer_token_json = bearer_token_json

        await self._finalize_session()

    async def request_device_code(self) -> dict[str, Any]:
        """Start the OAuth Device Authorization Grant (RFC 8628).

        Returns the response containing ``user_code``, ``verification_uri`` /
        ``verification_uri_complete``, ``device_code``, ``interval`` and
        ``expires_in``. The user approves the ``user_code`` in a browser. This
        grant does not require a Play Integrity attestation header.
        """
        await self._discover_endpoints()
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "X-App-Version": AudiAPI.HDR_XAPP_VERSION,
            "X-App-Name": "myAudi",
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"client_id": self._client_id, "scope": DEVICE_CODE_SCOPE}
        encoded = urlencode(data, encoding="utf-8").replace("+", "%20")
        _rsp, rsptxt = await self._api.request(
            "POST",
            self._deviceAuthorizationEndpoint,
            encoded,
            headers=headers,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        result = json.loads(rsptxt)
        if "device_code" not in result:
            raise Exception(
                "Device authorization request failed: "
                + str(result.get("error", rsptxt[:200]))
            )
        return result

    async def poll_device_token(self, device_code: str) -> str:
        """Poll the token endpoint once for a device_code grant.

        Returns one of ``"ok"``, ``"authorization_pending"``, ``"slow_down"``,
        ``"expired"``, ``"denied"`` or ``"error"``. On ``"ok"`` the IDK bearer
        token is stored and the AZS + mbboauth session tokens are derived. No
        attestation header is sent.
        """
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": self._client_id,
            "device_code": device_code,
        }
        encoded = urlencode(data, encoding="utf-8").replace("+", "%20")
        _rsp, rsptxt = await self._api.request(
            "POST",
            self._tokenEndpoint,
            encoded,
            headers=headers,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        result = json.loads(rsptxt)
        if "access_token" in result:
            self._bearer_token_json = result
            await self._finalize_session()
            return "ok"
        error = result.get("error")
        mapping = {
            "authorization_pending": "authorization_pending",
            "slow_down": "slow_down",
            "expired_token": "expired",
            "access_denied": "denied",
        }
        if error in mapping:
            return mapping[error]
        _LOGGER.debug("Unexpected device token response: %s", rsptxt[:200])
        return "error"

    async def login_with_refresh_token(self, refresh_token: str) -> str:
        """Obtain a session from a stored IDK or Auth0 refresh token.

        Auth0 refresh tokens are persisted with a provider prefix so they use
        the direct Auth0 issuer instead of the attestation-gated IDK BFF.
        """
        await self._discover_endpoints()

        if refresh_token.startswith(AUTH0_REFRESH_TOKEN_PREFIX):
            raw_refresh_token = refresh_token[len(AUTH0_REFRESH_TOKEN_PREFIX) :]
            result = await self._refresh_auth0_token(raw_refresh_token)
            return AUTH0_REFRESH_TOKEN_PREFIX + result["refresh_token"]

        self._uses_auth0 = False
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "client_id": self._client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "response_type": "token id_token",
        }
        encoded = urlencode(data, encoding="utf-8").replace("+", "%20")
        _rsp, rsptxt = await self._api.request(
            "POST",
            self._tokenEndpoint,
            encoded,
            headers=headers,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        result = json.loads(rsptxt)
        if "access_token" not in result:
            _raise_refresh_rejected("Token refresh rejected", result, rsptxt)
        result.setdefault("refresh_token", refresh_token)
        self._bearer_token_json = result
        await self._finalize_session()
        return self._bearer_token_json.get("refresh_token", refresh_token)

    def current_refresh_token(self) -> str | None:
        """Return the current provider-tagged refresh token."""
        if self._bearer_token_json is None:
            return None
        refresh_token = self._bearer_token_json.get("refresh_token")
        if refresh_token and self._uses_auth0:
            return AUTH0_REFRESH_TOKEN_PREFIX + refresh_token
        return refresh_token

    @property
    def uses_auth0(self) -> bool:
        """Return whether this session uses the modern CARIAD Auth0 API."""
        return self._uses_auth0

    def get_id_token_subject(self) -> str | None:
        """Return a stable account identifier (email or sub) from the id token."""
        if self._bearer_token_json is None:
            return None
        id_token = self._bearer_token_json.get("id_token")
        if not id_token:
            return None
        try:
            segment = id_token.split(".")[1]
            segment += "=" * (-len(segment) % 4)
            payload = json.loads(base64.urlsafe_b64decode(segment))
        except (ValueError, IndexError, json.JSONDecodeError):
            return None
        return payload.get("email") or payload.get("sub")

    async def _finalize_session(self) -> None:
        """Derive the AZS and mbboauth tokens from the current IDK bearer token."""

        # AZS token
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "X-App-Version": AudiAPI.HDR_XAPP_VERSION,
            "X-App-Name": "myAudi",
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/json; charset=utf-8",
        }
        asz_req_data = {
            "token": self._bearer_token_json["access_token"],
            "grant_type": "id_token",
            "stage": "live",
            "config": "myaudi",
        }
        azs_token_rsp, azs_token_rsptxt = await self._api.request(
            "POST",
            self._authorizationServerBaseURLLive + "/token",
            json.dumps(asz_req_data),
            headers=headers,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        azs_token_json = json.loads(azs_token_rsptxt)
        self.audiToken = azs_token_json

        # mbboauth client register
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/json; charset=utf-8",
        }
        mbboauth_reg_data = {
            "client_name": "SM-A405FN",
            "platform": "google",
            "client_brand": "Audi",
            "appName": "myAudi",
            "appVersion": AudiAPI.HDR_XAPP_VERSION,
            "appId": "de.myaudi.mobile.assistant",
        }
        mbboauth_client_reg_rsp, mbboauth_client_reg_rsptxt = await self._api.request(
            "POST",
            self.mbbOAuthBaseURL + "/mobile/register/v1",
            json.dumps(mbboauth_reg_data),
            headers=headers,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        mbboauth_client_reg_json = json.loads(mbboauth_client_reg_rsptxt)
        self.xclientId = mbboauth_client_reg_json["client_id"]
        self._api.set_xclient_id(self.xclientId)

        # mbboauth auth
        headers = {
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "User-Agent": AudiAPI.HDR_USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Client-ID": self.xclientId,
        }
        mbboauth_auth_data = {
            "grant_type": "id_token",
            "token": self._bearer_token_json["id_token"],
            "scope": "sc2:fal",
        }
        encoded_mbboauth_auth_data = urlencode(
            mbboauth_auth_data, encoding="utf-8"
        ).replace("+", "%20")
        mbboauth_auth_rsp, mbboauth_auth_rsptxt = await self._api.request(
            "POST",
            self.mbbOAuthBaseURL + "/mobile/oauth2/v1/token",
            encoded_mbboauth_auth_data,
            headers=headers,
            allow_redirects=False,
            rsp_wtxt=True,
        )
        mbboauth_auth_json = json.loads(mbboauth_auth_rsptxt)
        if "access_token" not in mbboauth_auth_json:
            # Fail here rather than storing the error body as a token: otherwise
            # vwToken silently becomes {"error": ...} and only surfaces much later
            # as KeyError('access_token') in get_tripdata() or a TypeError in
            # get_climater(), far from the real cause.
            error_description = mbboauth_auth_json.get(
                "error_description",
                mbboauth_auth_rsptxt[:200],
            )

            raise AudiAuthError(f"mbboauth token exchange failed: {error_description}")
        # store token and expiration time
        self.mbboauthToken = mbboauth_auth_json

        # mbboauth refresh (app immediately refreshes the token)
        # The MBB OAuth auth response no longer always includes a refresh_token.
        # Skip the immediate refresh if absent and use the auth token directly.
        if "refresh_token" in mbboauth_auth_json:
            headers = {
                "Accept": "application/json",
                "Accept-Charset": "utf-8",
                "User-Agent": AudiAPI.HDR_USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Client-ID": self.xclientId,
            }
            mbboauth_refresh_data = {
                "grant_type": "refresh_token",
                "token": mbboauth_auth_json["refresh_token"],
                "scope": "sc2:fal",
                # "vin": vin,  << App uses a dedicated VIN here, but it works without, don't know
            }
            encoded_mbboauth_refresh_data = urlencode(
                mbboauth_refresh_data, encoding="utf-8"
            ).replace("+", "%20")
            mbboauth_refresh_rsp, mbboauth_refresh_rsptxt = await self._api.request(
                "POST",
                self.mbbOAuthBaseURL + "/mobile/oauth2/v1/token",
                encoded_mbboauth_refresh_data,
                headers=headers,
                allow_redirects=False,
                cookies=mbboauth_client_reg_rsp.cookies,
                rsp_wtxt=True,
            )
            # this code is the old "vwToken"
            refreshed = json.loads(mbboauth_refresh_rsptxt)
            if "access_token" not in refreshed:
                _raise_refresh_rejected(
                    "mbboauth refresh rejected", refreshed, mbboauth_refresh_rsptxt
                )
            self.vwToken = refreshed
        else:
            _LOGGER.debug(
                "mbboauth: no refresh_token in auth response, using auth token directly as vwToken"
            )
            self.vwToken = mbboauth_auth_json

    def _generate_security_pin_hash(self, challenge: str) -> str:
        if not self._spin:
            raise Exception("sPin is required to perform this action")

        pin = to_byte_array(self._spin)
        byteChallenge = to_byte_array(challenge)
        b = bytes(pin + byteChallenge)
        return sha512(b).hexdigest().upper()
