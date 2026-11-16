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
        "chargingCareSettings": {
            "value": {"carCapturedTimestamp": T, "batteryCareMode": "deactivated"}
        },
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
