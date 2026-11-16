"""A single Audi vehicle: collects its data from the cloud."""

from __future__ import annotations

import asyncio
import builtins
import logging
import re
from datetime import datetime, UTC

from aiohttp import ClientResponseError

from .audi_services import AudiService
from .audi_vehicle_properties import AudiVehicleProperties
from .util import get_attr, log_exception, parse_datetime

_LOGGER = logging.getLogger(__name__)

MAX_RESPONSE_ATTEMPTS = 10
REQUEST_STATUS_SLEEP = 5


class AudiConnectVehicle(AudiVehicleProperties):
    def __init__(self, audi_service: AudiService, vehicle) -> None:
        self._audi_service = audi_service
        self._vehicle = vehicle
        self._vin = vehicle.vin.lower()
        self._vehicle.state = {}
        self._vehicle.fields = {}
        self._logged_errors = set()
        self._no_error = False

        self.support_status_report = True
        self.support_position = True

        # Auth0 uses selectivestatus; the legacy fs-car polls reject its token.
        uses_auth0 = getattr(self._audi_service, "uses_auth0", False)
        self.support_climater = not uses_auth0
        self.support_preheater = not uses_auth0
        self.support_charger = not uses_auth0
        self.support_trip_data = not uses_auth0

        self.charging_complete_time_frozen = None
        # Last selectivestatus payload as received; only read by diagnostics.

    @property
    def vin(self):
        return self._vin

    @property
    def _redacted_vin(self) -> str:
        """The last four characters only. A VIN identifies a specific car and
        its owner, and these messages end up in logs people paste into issues;
        the reporter of #862 had to redact it by hand."""
        vin = self._vehicle.vin
        return "*" * (len(vin) - 4) + vin[-4:]

    @property
    def csid(self):
        return self._vehicle.csid

    @property
    def title(self):
        return self._vehicle.title

    @property
    def model(self):
        return self._vehicle.model

    @property
    def model_source(self):
        return getattr(self._vehicle, "model_source", "unavailable")

    @property
    def model_year(self):
        return self._vehicle.model_year

    @property
    def model_family(self):
        return self._vehicle.model_family

    async def call_update(self, func, ntries: int):
        try:
            await func()
        except builtins.TimeoutError:
            if ntries > 1:
                await asyncio.sleep(2)
                await self.call_update(func, ntries - 1)
            else:
                raise

    async def update(self):
        info = ""
        try:
            self._no_error = True
            info = "statusreport"
            await self.call_update(self.update_vehicle_statusreport, 3)
            info = "shortterm"
            await self.call_update(self.update_vehicle_shortterm, 3)
            info = "longterm"
            await self.call_update(self.update_vehicle_longterm, 3)
            info = "position"
            await self.call_update(self.update_vehicle_position, 3)
            info = "climater"
            await self.call_update(self.update_vehicle_climater, 3)
            info = "preheater"
            await self.call_update(self.update_vehicle_preheater, 3)
            # Return True on success, False on error
            return self._no_error
        except Exception as exception:
            log_exception(
                exception,
                f"Unable to update vehicle data {info} of {self._redacted_vin}",
            )
            return False

    def log_exception_once(self, exception, message):
        self._no_error = False
        err = message + ": " + str(exception).rstrip("\n")
        if err not in self._logged_errors:
            self._logged_errors.add(err)
            _LOGGER.error(err, exc_info=True)

    async def update_vehicle_statusreport(self):
        if not self.support_status_report:
            return

        try:
            status = await self._audi_service.get_stored_vehicle_data(self._vehicle.vin)
            # #793: on a CARIAD outage this comes back 200, but every job is an
            # error object instead of a value, so it parses to nothing. Assigning
            # that would wipe every field and the entities quietly disappear, while
            # the update still reports success. Same handling as the 403/502 case
            # below: keep the last known values, mark the update failed so it
            # surfaces, and skip the overwrite.
            if status.all_jobs_errored:
                self._no_error = False
                _LOGGER.warning(
                    "Vehicle status report for %s came back with only errors "
                    "(transient CARIAD outage); keeping the last known values.",
                    self._vehicle.vin,
                )
                return
            if not status.data_fields and not status.states:
                # HTTP 200/207 may still carry no usable vehicle measurement.
                # Never discard cached fields or claim a fully refreshed car.
                self._no_error = False
                _LOGGER.debug(
                    "Vehicle status response contained no usable data; "
                    "keeping previous state and fields."
                )
                return
            new_fields = {field.name: field.value for field in status.data_fields}
            if status.error_count or getattr(status, "partial_response", False):
                # Some CARIAD jobs may fail while other ones succeed with HTTP 200.
                # Preserve unaffected fields rather than removing sensors after
                # every partial response. A cached value is NOT freshly measured.
                self._vehicle.fields.update(new_fields)
            else:
                self._vehicle.fields = new_fields

            # The newest source measurement can remain old while an HTTP request
            # succeeds. A partial/untimestamped response must never reset the
            # vehicle to the 1970 sentinel or claim a fresh car reading.
            prior = self._vehicle.state.get("last_update_time")
            last_observed = (
                prior
                if isinstance(prior, datetime) and prior.tzinfo and prior.year >= 2020
                else datetime(1970, 1, 1, tzinfo=UTC)
            )
            for field in status.data_fields:
                if not field.measure_time:
                    continue
                new_time = parse_datetime(field.measure_time)
                if new_time and new_time.tzinfo and new_time.year >= 2020:
                    last_observed = max(last_observed, new_time)
            # A state can carry no timestamp: userCapabilities is a statement
            # about the vehicle rather than a reading from it.
            for state in status.states:
                timestamp = state.get("measure_time")
                if not timestamp:
                    continue
                new_time = parse_datetime(timestamp)
                if new_time and new_time.tzinfo and new_time.year >= 2020:
                    last_observed = max(last_observed, new_time)
            self._vehicle.state["last_update_time"] = last_observed

            # Keep previous per-feature readings when CARIAD reports only a
            # partial response; the global latest timestamp is not their age.
            for state in status.states:
                self._vehicle.state[state["name"]] = state["value"]

        except builtins.TimeoutError:
            raise
        except ClientResponseError as resp_exception:
            if resp_exception.status == 404:
                self.support_status_report = False
            elif resp_exception.status in (403, 502):
                # Transient CARIAD gateway error; the cached state is kept and the
                # next poll normally recovers. Logged at debug like the other
                # endpoints, not as an error, to avoid noise.
                _LOGGER.debug(
                    "Received status 502 while obtaining the vehicle status report "
                    "of %s. This is typically transient and may resolve on its own.",
                    self._vehicle.vin,
                )
            else:
                self.log_exception_once(
                    resp_exception,
                    f"Unable to obtain the vehicle status report of {self._redacted_vin}",
                )
        except Exception as exception:
            self.log_exception_once(
                exception,
                f"Unable to obtain the vehicle status report of {self._redacted_vin}",
            )

    async def update_vehicle_position(self):
        # Redact all but the last 4 characters of the VIN
        redacted_vin = self._redacted_vin
        _LOGGER.debug(
            "POSITION: Starting update_vehicle_position for VIN: %s", redacted_vin
        )

        if not self.support_position:
            _LOGGER.debug(
                "POSITION: Vehicle position support is disabled for VIN: %s. Exiting update process.",
                redacted_vin,
            )
            return

        try:
            _LOGGER.debug(
                "POSITION: Attempting to retrieve stored vehicle position for VIN: %s",
                redacted_vin,
            )
            resp = await self._audi_service.get_stored_position(self._vehicle.vin)
            # To enable detailed logging of raw vehicle position data for debugging purposes:
            # 1. Remove the '#' from the start of the _LOGGER.debug line below.
            # 2. Save the file.
            # 3. Restart Home Assistant to apply the changes.
            # Note: This will log sensitive data. To stop logging this data:
            # 1. Add the '#' back at the start of the _LOGGER.debug line.
            # 2. Save the file and restart Home Assistant again.
            # _LOGGER.debug("POSITION - UNREDACTED SENSITIVE DATA: Raw vehicle position data: %s", resp)
            if resp is not None:
                redacted_lat = re.sub(r"\d", "#", str(resp["data"]["lat"]))
                redacted_lon = re.sub(r"\d", "#", str(resp["data"]["lon"]))

                # Check if 'carCapturedTimestamp' is available in the data
                if "carCapturedTimestamp" in resp["data"]:
                    timestamp = parse_datetime(resp["data"]["carCapturedTimestamp"])
                    parktime = parse_datetime(resp["data"]["carCapturedTimestamp"])
                else:
                    # Log and use None timestamp and parktime
                    timestamp = None
                    parktime = None
                    _LOGGER.debug(
                        "POSITION: Timestamp not available for vehicle position data of VIN: %s.",
                        redacted_vin,
                    )
                _LOGGER.debug(
                    "POSITION: Vehicle position data received for VIN: %s, lat: %s, lon: %s, timestamp: %s, parktime: %s",
                    redacted_vin,
                    redacted_lat,
                    redacted_lon,
                    timestamp,
                    parktime,
                )

                self._vehicle.state["position"] = {
                    "latitude": resp["data"]["lat"],
                    "longitude": resp["data"]["lon"],
                    "timestamp": timestamp,
                    "parktime": parktime,
                }

                self._vehicle.state["is_moving"] = False

                _LOGGER.debug(
                    "POSITION: Vehicle position updated successfully for VIN: %s",
                    redacted_vin,
                )
            else:
                _LOGGER.warning(
                    "POSITION: No vehicle position data received for VIN: %s. Response was None.",
                    redacted_vin,
                )

        except builtins.TimeoutError:
            _LOGGER.warning(
                "POSITION: TimeoutError encountered while updating vehicle position for VIN: %s.",
                redacted_vin,
            )
            raise
        except ClientResponseError as cre:
            if cre.status == 404:
                _LOGGER.debug(
                    "POSITION: ClientResponseError with status %s for VIN: %s. Vehicle does not support position — disabling.",
                    cre.status,
                    redacted_vin,
                )
                self.support_position = False
            elif cre.status in (403, 502):
                _LOGGER.debug(
                    "POSITION: Received status %s while updating vehicle position for VIN: %s. This is typically transient and may resolve on its own.",
                    cre.status,
                    redacted_vin,
                )
            elif cre.status != 204:
                _LOGGER.warning(
                    "POSITION: ClientResponseError with status %s for VIN: %s. Error: %s",
                    cre.status,
                    redacted_vin,
                    cre,
                )
            else:
                _LOGGER.debug(
                    "POSITION: Vehicle position currently not available for VIN: %s (Is moving?!). Received 204 status.",
                    redacted_vin,
                )
                # we receive a 204 when the vehicle is moving.
                self._vehicle.state["is_moving"] = True

        except Exception as e:
            _LOGGER.error(
                "POSITION: An unexpected error occurred while updating vehicle position for VIN: %s. Error: %s",
                redacted_vin,
                e,
            )

    async def update_vehicle_climater(self):
        redacted_vin = self._redacted_vin
        if not self.support_climater:
            return

        try:
            result = await self._audi_service.get_climater(self._vehicle.vin)
            if result:
                self._vehicle.state["climatisationState"] = get_attr(
                    result,
                    "climater.status.climatisationStatusData.climatisationState.content",
                )
                tmp = get_attr(
                    result,
                    "climater.status.temperatureStatusData.outdoorTemperature.content",
                )
                if tmp is not None:
                    self._vehicle.state["outdoorTemperature"] = round(
                        float(tmp) / 10 - 273, 1
                    )
                else:
                    self._vehicle.state["outdoorTemperature"] = None

                remainingClimatisationTime = get_attr(
                    result,
                    "climater.status.climatisationStatusData.remainingClimatisationTime.content",
                )
                self._vehicle.state["remainingClimatisationTime"] = (
                    remainingClimatisationTime
                )
                _LOGGER.debug(
                    "CLIMATER: remainingClimatisationTime: %s",
                    remainingClimatisationTime,
                )

                vehicleParkingClock = get_attr(
                    result,
                    "climater.status.vehicleParkingClockStatusData.vehicleParkingClock.content",
                )
                self._vehicle.state["vehicleParkingClock"] = parse_datetime(
                    vehicleParkingClock
                )
                _LOGGER.debug("CLIMATER: vehicleParkingClock: %s", vehicleParkingClock)

                isMirrorHeatingActive = get_attr(
                    result,
                    "climater.status.climatisationStatusData.climatisationElementStates.isMirrorHeatingActive.content",
                )
                self._vehicle.state["isMirrorHeatingActive"] = isMirrorHeatingActive
                _LOGGER.debug(
                    "CLIMATER: isMirrorHeatingActive: %s", isMirrorHeatingActive
                )

            else:
                _LOGGER.debug(
                    "No climater data received for VIN: %s. Response was None.",
                    redacted_vin,
                )

        except builtins.TimeoutError:
            _LOGGER.debug(
                "TimeoutError encountered while updating climater for VIN: %s.",
                redacted_vin,
            )
            raise
        except ClientResponseError as cre:
            if cre.status == 404:
                _LOGGER.debug(
                    "CLIMATER: ClientResponseError with status %s for VIN: %s. Vehicle does not support climater — disabling.",
                    cre.status,
                    redacted_vin,
                )
                self.support_climater = False
            elif cre.status in (403, 502):
                _LOGGER.debug(
                    "CLIMATER: Received status %s while updating climater for VIN: %s. This is typically transient and may resolve on its own.",
                    cre.status,
                    redacted_vin,
                )
            elif cre.status != 204:
                _LOGGER.debug(
                    "ClientResponseError with status %s while updating climater for VIN: %s. Error: %s",
                    cre.status,
                    redacted_vin,
                    cre,
                )
            else:
                _LOGGER.debug(
                    "Climater currently not available for VIN: %s. Received 204 status.",
                    redacted_vin,
                )

        except Exception as e:
            _LOGGER.error(
                "An unexpected error occurred while updating climater for VIN: %s. Error: %s",
                redacted_vin,
                e,
            )

    async def update_vehicle_preheater(self):
        redacted_vin = self._redacted_vin
        if not self.support_preheater:
            return

        try:
            result = await self._audi_service.get_preheater(self._vehicle.vin)
            if result:
                self._vehicle.state["preheaterState"] = get_attr(
                    result,
                    "statusResponse",
                )

        except builtins.TimeoutError:
            raise
        except ClientResponseError as cre:
            if cre.status == 404:
                _LOGGER.debug(
                    "PREHEATER: ClientResponseError with status %s for VIN: %s. Preheater not available — disabling.",
                    cre.status,
                    redacted_vin,
                )
                self.support_preheater = False
            elif cre.status in (401, 403, 502):
                # Gateway or account-side refusal that may not be permanent (a
                # temporary API ban answers 401 too), so keep the feature enabled
                # and let the next poll recover. Left as an error, a 401 logged a
                # traceback on every restart with nothing to switch off (#862).
                _LOGGER.debug(
                    "PREHEATER: Received status %s while updating preheater for VIN: %s. This is typically transient and may resolve on its own.",
                    cre.status,
                    redacted_vin,
                )
            else:
                self.log_exception_once(
                    cre,
                    f"Unable to obtain the vehicle preheater state for {self._redacted_vin}",
                )
        except Exception as exception:
            self.log_exception_once(
                exception,
                f"Unable to obtain the vehicle preheater state for {self._redacted_vin}",
            )

    async def update_vehicle_charger(self):
        redacted_vin = self._redacted_vin
        if not self.support_charger:
            return

        try:
            result = await self._audi_service.get_charger(self._vehicle.vin)
            if result:
                self._vehicle.state["maxChargeCurrent"] = get_attr(
                    result, "charger.settings.maxChargeCurrent.content"
                )

                self._vehicle.state["chargingState"] = get_attr(
                    result, "charger.status.chargingStatusData.chargingState.content"
                )
                self._vehicle.state["actualChargeRate"] = get_attr(
                    result, "charger.status.chargingStatusData.actualChargeRate.content"
                )
                if self._vehicle.state["actualChargeRate"] is not None:
                    self._vehicle.state["actualChargeRate"] = float(
                        self._vehicle.state["actualChargeRate"]
                    )
                self._vehicle.state["actualChargeRateUnit"] = get_attr(
                    result, "charger.status.chargingStatusData.chargeRateUnit.content"
                )
                self._vehicle.state["chargingPower"] = get_attr(
                    result, "charger.status.chargingStatusData.chargingPower.content"
                )
                self._vehicle.state["chargingMode"] = get_attr(
                    result, "charger.status.chargingStatusData.chargingMode.content"
                )

                self._vehicle.state["energyFlow"] = get_attr(
                    result, "charger.status.chargingStatusData.energyFlow.content"
                )

                self._vehicle.state["engineTypeFirstEngine"] = get_attr(
                    result,
                    "charger.status.cruisingRangeStatusData.engineTypeFirstEngine.content",
                )
                self._vehicle.state["engineTypeSecondEngine"] = get_attr(
                    result,
                    "charger.status.cruisingRangeStatusData.engineTypeSecondEngine.content",
                )
                self._vehicle.state["hybridRange"] = get_attr(
                    result, "charger.status.cruisingRangeStatusData.hybridRange.content"
                )
                self._vehicle.state["primaryEngineRange"] = get_attr(
                    result,
                    "charger.status.cruisingRangeStatusData.primaryEngineRange.content",
                )
                self._vehicle.state["secondaryEngineRange"] = get_attr(
                    result,
                    "charger.status.cruisingRangeStatusData.secondaryEngineRange.content",
                )

                self._vehicle.state["stateOfCharge"] = get_attr(
                    result, "charger.status.batteryStatusData.stateOfCharge.content"
                )
                self._vehicle.state["remainingChargingTime"] = get_attr(
                    result,
                    "charger.status.batteryStatusData.remainingChargingTime.content",
                )
                self._vehicle.state["plugState"] = get_attr(
                    result, "charger.status.plugStatusData.plugState.content"
                )
                self._vehicle.state["plugLockState"] = get_attr(
                    result, "charger.status.plugStatusData.plugLockState.content"
                )
                self._vehicle.state["externalPower"] = get_attr(
                    result, "charger.status.plugStatusData.externalPower.content"
                )
                self._vehicle.state["plugledColor"] = get_attr(
                    result, "charger.status.plugStatusData.plugledColor.content"
                )

        except builtins.TimeoutError:
            raise
        except ClientResponseError as cre:
            if cre.status == 404:
                _LOGGER.debug(
                    "CHARGER: ClientResponseError with status %s for VIN: %s. Vehicle does not support charger — disabling.",
                    cre.status,
                    redacted_vin,
                )
                self.support_charger = False
            elif cre.status in (403, 502):
                _LOGGER.debug(
                    "CHARGER: Received status %s while updating charger for VIN: %s. This is typically transient and may resolve on its own.",
                    cre.status,
                    redacted_vin,
                )
            else:
                self.log_exception_once(
                    cre,
                    f"Unable to obtain the vehicle charger state for {self._redacted_vin}",
                )
        except Exception as exception:
            self.log_exception_once(
                exception,
                f"Unable to obtain the vehicle charger state for {self._redacted_vin}",
            )

    async def update_vehicle_longterm(self):
        await self.update_vehicle_tripdata("longTerm")

    async def update_vehicle_shortterm(self):
        await self.update_vehicle_tripdata("shortTerm")

    async def update_vehicle_tripdata(self, kind: str):
        redacted_vin = self._redacted_vin
        if not self.support_trip_data:
            _LOGGER.debug(
                "TRIP DATA: Trip data support is disabled for VIN: %s. Exiting update process.",
                redacted_vin,
            )
            return
        try:
            td_cur, td_rst = await self._audi_service.get_tripdata(
                self._vehicle.vin, kind
            )
            self._vehicle.state[kind.lower() + "_current"] = {
                "tripID": td_cur.tripID,
                "averageElectricEngineConsumption": td_cur.averageElectricEngineConsumption,
                "averageFuelConsumption": td_cur.averageFuelConsumption,
                "averageSpeed": td_cur.averageSpeed,
                "mileage": td_cur.mileage,
                "startMileage": td_cur.startMileage,
                "traveltime": td_cur.traveltime,
                "timestamp": td_cur.timestamp,
                "overallMileage": td_cur.overallMileage,
                "zeroEmissionDistance": td_cur.zeroEmissionDistance,
            }
            self._vehicle.state[kind.lower() + "_reset"] = {
                "tripID": td_rst.tripID,
                "averageElectricEngineConsumption": td_rst.averageElectricEngineConsumption,
                "averageFuelConsumption": td_rst.averageFuelConsumption,
                "averageSpeed": td_rst.averageSpeed,
                "mileage": td_rst.mileage,
                "startMileage": td_rst.startMileage,
                "traveltime": td_rst.traveltime,
                "timestamp": td_rst.timestamp,
                "overallMileage": td_rst.overallMileage,
                "zeroEmissionDistance": td_rst.zeroEmissionDistance,
            }

        except builtins.TimeoutError:
            _LOGGER.debug(
                "TRIP DATA: TimeoutError encountered while updating trip data for VIN: %s.",
                redacted_vin,
            )
            raise
        except ClientResponseError as cre:
            if cre.status == 404:
                _LOGGER.debug(
                    "TRIP DATA: ClientResponseError with status %s for VIN: %s. Vehicle does not support trip data — disabling.",
                    cre.status,
                    redacted_vin,
                )
                self.support_trip_data = False
            elif cre.status in (403, 502):
                _LOGGER.debug(
                    "TRIP DATA: Received status %s while updating trip data for VIN: %s. This is typically transient and may resolve on its own.",
                    cre.status,
                    redacted_vin,
                )
            elif cre.status != 204:
                _LOGGER.debug(
                    "TRIP DATA: ClientResponseError with status %s while updating trip data for VIN: %s. Error: %s",
                    cre.status,
                    redacted_vin,
                    cre,
                )
            else:
                _LOGGER.debug(
                    "TRIP DATA: Trip data currently not available for VIN: %s. Received 204 status.",
                    redacted_vin,
                )

        except Exception as e:
            _LOGGER.error(
                "TRIP DATA: An unexpected error occurred while updating trip data for VIN: %s. Error: %s",
                redacted_vin,
                e,
            )
