"""Privacy and status tests for Audi Connect diagnostics."""

import importlib.util
from pathlib import Path
import unittest

MODULE = (
    Path(__file__).resolve().parents[1]
    / "custom_components/ha_audi_connect/diagnostic_events.py"
)
spec = importlib.util.spec_from_file_location("audi_diagnostic_events", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestDiagnostics(unittest.TestCase):
    def test_legacy_401_contains_no_vin_or_token(self):
        url = "https://msg.volkswagen.de/fs-car/bs/climatisation/v1/Audi/DE/vehicles/EXAMPLEVIN0000001/climater/actions?token=SECRET"
        event = module.build_http_event("POST", url, 401)
        self.assertEqual(event["route"], "legacy_climatisation")
        self.assertEqual(event["outcome"], "http_rejected")
        self.assertNotIn("EXAMPLEVIN0000001", str(event))
        self.assertNotIn("SECRET", str(event))

    def test_accepted_command_not_marked_success(self):
        event = module.build_http_event(
            "POST",
            "https://emea.bff.cariad.digital/vehicle/v1/vehicles/SECRET/climatisation/start",
            200,
        )
        self.assertEqual(event["outcome"], "http_accepted_not_vehicle_confirmed")

    def test_auth0_token_exchange_is_not_vehicle_command(self):
        event = module.build_http_event(
            "POST",
            "https://group.identity.vwgroup.io/oauth/token?secret=PRIVATE",
            200,
        )
        self.assertEqual(event["route"], "authentication")
        self.assertEqual(event["outcome"], "authentication_http_success")
        self.assertNotIn("PRIVATE", str(event))

    def test_other_post_is_not_assumed_authentication(self):
        event = module.build_http_event("POST", "https://example.org/oauth/token", 200)
        self.assertEqual(event["route"], "other")
        self.assertEqual(event["outcome"], "http_accepted_not_vehicle_confirmed")

    def test_auth0_failed_token_exchange(self):
        event = module.build_http_event(
            "POST", "https://group.identity.vwgroup.io/oauth/token", 401
        )
        self.assertEqual(event["route"], "authentication")
        self.assertEqual(event["outcome"], "http_rejected")

    def test_successful_read_ignored(self):
        self.assertIsNone(
            module.build_http_event(
                "GET", "https://example.test/vehicle/v1/status", 200
            )
        )

    def test_legacy_unlock(self):
        url = "https://example.test/api/rolesrights/authorization/v2/vehicles/EXAMPLEVIN0000001/services/rlu_v1/operations/UNLOCK/security-pin-auth-requested"
        self.assertEqual(
            module.build_http_event("POST", url, 401)["route"],
            "remote_lock_authorization",
        )

    def test_http_error_is_recorded_even_for_read(self):
        self.assertEqual(
            module.build_http_event("GET", "https://example.test/selectivestatus", 502)[
                "outcome"
            ],
            "http_rejected",
        )


if __name__ == "__main__":
    unittest.main()


class TestRouteNames(unittest.TestCase):
    """The names the diagnostics show instead of one "other" bucket."""

    BFF = "https://emea.bff.cariad.digital/vehicle/v1/vehicles/SECRETVIN"

    def route(self, url, method="POST", status=502):
        return module.build_http_event(method, url, status)["route"]

    def test_climatisation_settings_start_and_stop_are_told_apart(self):
        self.assertEqual(
            self.route(self.BFF + "/climatisation/settings", "PUT"),
            "climatisation_settings",
        )
        self.assertEqual(
            self.route(self.BFF + "/climatisation/start"), "climatisation_start"
        )
        self.assertEqual(
            self.route(self.BFF + "/climatisation/stop"), "climatisation_stop"
        )

    def test_charging_settings_are_told_apart_from_start_and_stop(self):
        self.assertEqual(
            self.route(self.BFF + "/charging/settings", "PUT"), "charging_settings"
        )
        self.assertEqual(self.route(self.BFF + "/charging/start"), "charging")

    def test_timers_are_departure_timers_not_climatisation_or_charging(self):
        base = "https://emea.bff.cariad.digital/vehicle/v2/departure/SECRETVIN"
        self.assertEqual(
            self.route(base + "/climatisation/timers", "PUT"), "departure_timers"
        )
        self.assertEqual(
            self.route(base + "/charging/timers", "POST"), "departure_timers"
        )

    def test_wakeup_honk_graphql_and_capabilities_have_names(self):
        self.assertEqual(self.route(self.BFF + "/vehiclewakeup"), "vehicle_wakeup")
        self.assertEqual(
            self.route(self.BFF + "/vehiclewakeuptrigger"), "vehicle_wakeup"
        )
        self.assertEqual(self.route(self.BFF + "/honkandflash"), "honk_and_flash")
        self.assertEqual(
            self.route("https://app-api.live-my.audi.com/vgql/v1/graphql"), "graphql"
        )
        self.assertEqual(self.route(self.BFF + "/capabilities", "GET"), "capabilities")

    def test_unknown_routes_stay_other_and_no_vin_leaks(self):
        event = module.build_http_event("POST", self.BFF + "/somethingnew", 502)
        self.assertEqual(event["route"], "other")
        self.assertNotIn("SECRETVIN", str(event))
