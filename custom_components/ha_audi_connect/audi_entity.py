from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AudiDataUpdateCoordinator


@cache
def _english_entity_names() -> dict[str, dict[str, str]]:
    """{domain: {translation_key: English name}} from the shipped en.json."""
    path = Path(__file__).parent / "translations" / "en.json"
    try:
        entities = json.loads(path.read_text(encoding="utf-8")).get("entity", {})
    except (OSError, ValueError):
        return {}
    return {
        domain: {
            key: value["name"]
            for key, value in keys.items()
            if isinstance(value, dict) and isinstance(value.get("name"), str)
        }
        for domain, keys in entities.items()
        if isinstance(keys, dict)
    }


def english_object_name(
    domain: str | None, key: str | None, placeholders: dict[str, str] | None
) -> str | None:
    """The English name an entity id is built from, or None when there is none."""
    if not key:
        return None
    names = _english_entity_names()
    if domain is not None:
        name = names.get(domain, {}).get(key)
    else:
        found = {n[key] for n in names.values() if key in n}
        name = found.pop() if len(found) == 1 else None
    if name is None:
        return None
    try:
        return name.format(**(placeholders or {}))
    except (KeyError, IndexError, ValueError):
        return None


# How long a written value is shown before the car's own reading counts again.
# Longer than the default poll interval, so a car that never confirms the write
# (it was refused, or changed back) does not leave a stale guess on screen.
ASSUMED_VALUE_TTL = 20 * 60


class AssumedValueMixin:
    """Show what was just written until the car reports something else.

    The car acknowledges a write before it reports the new value, so the refresh
    that follows usually reads the old one and the entity would snap back for up
    to a poll interval, which looks like the command failed. The guess is dropped
    as soon as the car reports anything other than what it said at the time of
    the write (even if that differs from what was asked: another client may have
    changed it), and after ASSUMED_VALUE_TTL.

    Put it before the entity base in the class list and implement
    ``_reported_value``.
    """

    _assumed_active = False
    _assumed_value: Any = None
    _reported_at_write: Any = None
    _assumed_at = 0.0

    def _reported_value(self) -> Any:
        raise NotImplementedError

    def _shown_value(self) -> Any:
        if self._assumed_active:
            if time.monotonic() - self._assumed_at < ASSUMED_VALUE_TTL:
                return self._assumed_value
            self._drop_assumption()
        return self._reported_value()

    def _assume(self, value: Any) -> None:
        self._reported_at_write = self._reported_value()
        self._assumed_value = value
        self._assumed_at = time.monotonic()
        self._assumed_active = True
        self.async_write_ha_state()

    def _drop_assumption(self) -> None:
        self._assumed_active = False
        self._assumed_value = None
        self._reported_at_write = None

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._assumed_active and self._reported_value() != self._reported_at_write:
            self._drop_assumption()
        super()._handle_coordinator_update()


def entity_unique_id(vehicle: Any, platform: str, key: str) -> str:
    """The unique_id every platform builds, in one place.

    The registry lookup below only finds an existing entity if it asks for the
    exact string that entity was created with, so the format cannot be spelled
    out twice.
    """
    return f"{vehicle.vin.lower()}_{platform}_{key}"


def _capability_verdict(vehicle: Any, capability: str | None) -> bool | None:
    """What the car says about a capability: yes, no, or nothing at all."""
    if capability is None:
        return None
    if not hasattr(vehicle, "has_capability"):
        return None
    return vehicle.has_capability(capability)


def _present_in_this_poll(vehicle: Any, attr_key: str) -> bool:
    """The legacy Instrument.is_supported logic, unchanged.

    1. If a ``{attr_key}_supported`` property exists, return its truthiness.
    2. Otherwise, if the vehicle object has an ``attr_key`` attribute, True.
    3. Otherwise, False.
    """
    supported_attr = f"{attr_key}_supported"
    if hasattr(vehicle, supported_attr):
        return bool(getattr(vehicle, supported_attr))
    return hasattr(vehicle, attr_key)


def is_entity_supported(
    vehicle: Any, attr_key: str, capability: str | None = None
) -> bool:
    """Check if a vehicle supports a given entity attribute.

    Asks the car's capability list where one is named and the car reports it,
    and otherwise falls back to whether the value is in the poll we happen to
    be holding.

    That fallback asks the wrong question: a rate-limited or partial poll makes
    a car look like it lost a feature. On one vehicle a 429 removed sixteen
    entities, including a parking-position sensor for a car that plainly has
    parking position.

    The fallback survives anyway, because a car that reports no capability list
    must keep exactly the old behaviour: treating "did not say" as "not
    capable" would strip every entity from those vehicles. ``should_create_entity``
    is what covers the remaining gap, and is what the platforms call.
    """
    capable = _capability_verdict(vehicle, capability)
    if capable is not None:
        return capable
    return _present_in_this_poll(vehicle, attr_key)


def should_create_entity(
    hass: HomeAssistant,
    platform: str,
    key: str,
    vehicle: Any,
    attr_key: str,
    capability: str | None = None,
    *,
    configured: bool = True,
) -> bool:
    """Whether a platform should create this entity for this vehicle.

    The capability list is job-level: it answers "does this car do
    climatisation", never "does it report isMirrorHeatingActive". So an entity
    backed by a single field, inside a capability the car has, is still dropped
    when a poll arrives without that field, and a car with no capability list
    at all gets no protection from it whatsoever.

    An entity already in the registry is one this integration created for this
    car on an earlier, better poll. Recreating it costs nothing, and it reports
    unavailable while its value is missing (see AudiEntity.available), which is
    the truthful state. Losing it deletes the user's history, their dashboard
    card and any automation referring to it.

    The car's own "no" still wins. A capability the car explicitly does not
    list is a statement about the vehicle rather than about this poll, so a
    stale registry entry does not resurrect an entity for a feature the car
    says it does not have. That only bites where a description names a
    capability, which today is the parking-position family; everywhere else the
    rescue rests on the registry alone.

    ``configured`` is the other kind of "no", and it is not about this poll
    either. A control gated on something the user set, an S-PIN above all, must
    disappear when they unset it, so a registry entry cannot bring it back.
    Pass it wherever the gate is a configuration fact rather than vehicle data.
    """
    if not configured:
        return False
    if _capability_verdict(vehicle, capability) is False:
        return False
    if is_entity_supported(vehicle, attr_key, capability):
        return True
    registry = er.async_get(hass)
    unique_id = entity_unique_id(vehicle, platform, key)
    return registry.async_get_entity_id(platform, DOMAIN, unique_id) is not None


class AudiEntity(CoordinatorEntity[AudiDataUpdateCoordinator]):
    """Base class for all Audi entities."""

    _attr_has_entity_name = True

    # The vehicle attribute this entity reads. Set by platforms whose entity
    # has no entity_description to carry it.
    _backing_attr: str | None = None

    @staticmethod
    def _command_started() -> datetime:
        """Take before sending a command; see ``_refresh_after_command``."""
        return datetime.now(UTC)

    async def _refresh_after_command(self, started: datetime) -> None:
        """Refresh the cloud data, unless the command already did.

        Most commands schedule their own refresh once the car has had time to
        take them (the account's notify step). A second request here would be
        held back by the coordinator's cooldown and run as another full poll
        right after the first. A poll that began after the command started is
        that refresh, so nothing more is asked for.
        """
        attempt = getattr(self.coordinator, "last_cloud_poll_attempt", None)
        if isinstance(attempt, datetime) and attempt >= started:
            return
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Unavailable when the car is not reporting this entity's value.

        Without this, an entity kept across a thin poll reports a value it does
        not have: a switch reads off, a lock reads unlocked, a sensor reads
        unknown. For a stored setting that may well be on, "off" is not a
        gentler version of "no data", it is a wrong answer that an automation
        will act on.

        This is deliberately not limited to entities the registry rescued. An
        entity whose backing value is absent is in the same state however it
        came to exist, and Home Assistant already has a word for it.
        """
        if not super().available:
            return False
        attr = self._backing_attr or getattr(
            getattr(self, "entity_description", None), "attr_key", None
        )
        if attr is None:
            return True
        return getattr(self._vehicle, attr, None) is not None

    def __init__(
        self,
        coordinator: AudiDataUpdateCoordinator,
        vehicle: Any,
    ) -> None:
        super().__init__(coordinator)
        self._vehicle = vehicle

    @property
    def suggested_object_id(self) -> str | None:
        """Entity ids are English, whatever language Home Assistant runs in.

        The names shown follow the user's language; the id is what automations
        and dashboards refer to, so it must not change with it.
        """
        platform_data = getattr(self, "platform_data", None)
        english = english_object_name(
            getattr(platform_data, "domain", None),
            self.translation_key,
            getattr(self, "translation_placeholders", None),
        )
        return english if english is not None else super().suggested_object_id

    @property
    def device_info(self) -> DeviceInfo:
        model_info = (self._vehicle.model or self._vehicle.title or "Unknown").strip()
        if model_info.startswith("Audi "):
            model_info = model_info[5:]
        model_year = getattr(self._vehicle, "model_year", "") or ""
        # What kind of drive the car has belongs to the car, not to a sensor.
        car_type = getattr(self._vehicle, "car_type", None)
        details = [str(model_year)] if model_year else []
        if isinstance(car_type, str) and car_type.strip():
            details.append(car_type.strip().capitalize())
        display_model = (
            f"{model_info} ({', '.join(details)})" if details else model_info
        )
        return DeviceInfo(
            identifiers={(DOMAIN, self._vehicle.vin.lower())},
            manufacturer="Audi",
            name=self._vehicle.title or "Audi vehicle",
            model=display_model,
        )


__all__ = [
    "AudiEntity",
    "entity_unique_id",
    "is_entity_supported",
    "should_create_entity",
]
