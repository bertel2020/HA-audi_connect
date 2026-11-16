"""Trimmed selectivestatus payload from an A6 Avant e-tron, 2026-11-16.

Captured through the probe_api service. Only the jobs the tests read are kept;
nothing identifying is in it. The car was parked and not plugged in, which is
why every plug value is the literal "invalid".
"""

import datetime

T = datetime.datetime(2026, 11, 16, 12, 39, 15, tzinfo=datetime.UTC)

PAYLOAD = {
    "charging": {
        "batteryStatus": {"value": {"carCapturedTimestamp": T, "currentSOC_pct": 66}},
        "chargingStatus": {
            "value": {
                "carCapturedTimestamp": T,
                "chargingState": "notReadyForCharging",
                "chargeMode": "manual",
                "chargePower_kW": 0,
                "chargeType": "ac",
                "chargingScenario": "off",
            }
        },
        "chargingSettings": {
            "value": {
                "carCapturedTimestamp": T,
                "maxChargeCurrentAC": "invalid",
                "autoUnlockPlugWhenChargedAC": "off",
                "targetSOC_pct": 100,
            }
        },
        "plugStatus": {
            "value": {
                "carCapturedTimestamp": T,
                "plugConnectionState": "invalid",
                "plugLockState": "invalid",
                "externalPower": "invalid",
                "ledColor": "invalid",
            }
        },
        # No carCapturedTimestamp here: the car really sends it bare.
        "chargingCareSettings": {"value": {"batteryCareMode": "deactivated"}},
        "chargingBidirectionalSettings": {
            "error": {"message": "Bad Gateway", "code": 4104, "retry": False}
        },
    },
    "climatisation": {
        "climatisationSettings": {
            "value": {
                "carCapturedTimestamp": T,
                "targetTemperature_C": 22.5,
                "climatisationMode": "economy",
            }
        },
        "climatisationStatus": {
            "value": {"carCapturedTimestamp": T, "climatisationState": "off"}
        },
    },
    "parkingBrake": {
        "parkingBrakeStatus": {"value": {"carCapturedTimestamp": T, "value": True}}
    },
}

# Capability list as the car sends it: most services run to 2035, six end on
# 2028-03-10, and "permanent" ones carry a date a century out. One has no date.
CAPABILITIES = {
    "userCapabilities": {
        "capabilitiesStatus": {
            "value": [
                {"id": "access", "expirationDate": "2035-03-10T00:00:00+00:00"},
                {"id": "trafficLights", "expirationDate": "2028-03-10T00:00:00+00:00"},
                {"id": "eRoutePlanner", "expirationDate": "2028-03-10T00:00:00+00:00"},
                {"id": "bluetoothIdent", "expirationDate": "2124-03-10T00:00:00+00:00"},
                {"id": "batteryChargingCare"},
            ]
        }
    }
}
