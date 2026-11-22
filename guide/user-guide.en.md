# Audi Connect – User guide

*[🇩🇪 Deutsche Version](user-guide.md)*

This guide describes what the integration offers once it is set up: controls, charging, climatisation, service actions, diagnostics and repair hints. Installation, configuration and options are in the [README](../README.en.md), as is the dashboard card. Background on feature status and the API is in the [API notes](api-notes.en.md).

## Controls

Each vehicle's device page exposes its actions directly, so the common ones no longer need a service call. Availability depends on what the vehicle reports and, for the lock and engine controls, on an S-PIN being configured. Entities are grouped on the device page; the full list of sensors and binary sensors (range, mileage, charging, doors and windows, trips, service intervals, data freshness and more) follows what the car reports.

| Control                        | Type    | Replaces                                              |
| ------------------------------ | ------- | ----------------------------------------------------- |
| `Door lock`                    | Lock    | `execute_vehicle_action` with `lock` / `unlock`       |
| `Climatisation`                | Climate | `start_climate_control` / `stop_climatisation`        |
| `Preheater`                    | Switch  | `execute_vehicle_action` with `start_/stop_preheater` |
| `Global charge target`         | Number  | `set_target_soc`                                      |
| `Current location target`      | Number  | `set_location_charge_target` (no `profile_id`)        |
| `<Profile> charge target`      | Number  | `set_location_charge_target` with `profile_id`        |
| `Start engine` / `Stop engine` | Button  | `start_engine` / `stop_engine`                        |
| `Flash lights`                 | Button  | n/a, new                                              |
| `Charge mode`                  | Select  | `set_charge_mode`                                     |
| `Start/Stop charging (experimental)` | Button | `execute_vehicle_action` with `start_/stop_charger`; see below |
| Charging current of the location profile | Select | –, new; only when the car reports the setting |
| `Refresh vehicle data`         | Button  | `refresh_vehicle_data`                                |
| `Wake vehicle`                 | Button  | n/a, new; needs a reported wake-up capability         |
| `Honk and flash`               | Button  | n/a, new; disabled by default                         |
| `Climatisation ON/OFF`         | Switch  | n/a, Auth0 vehicles                                   |
| `Window heating`, `Climatisation at unlock`, seat zones | Switch | n/a, the car's stored climatisation settings |
| `Climatisation mode`           | Select  | `start_climate_control` with `climatisation_mode`     |
| `Start/Stop window heating (experimental)` | Button | `execute_vehicle_action` with `start_/stop_window_heating` |
| `Release plug after charging (experimental)` | Switch | n/a                                       |

### Charge targets

There are three kinds, because the car has three places to put the number:

- **Global charge target** writes `charging/settings`. It does not govern where a charge stops at a location (upstream #722), so it is the least useful of the three and is kept only because it is a real, separately-stored setting.
- **Current location charge target** writes whichever profile the car is parked in, resolved by the integration from `vehiclePositionedInProfileID`. Use it in automations that should apply wherever the car happens to be.
- **One number per location profile**, named after the profile ("Home charge target", "Work charge target"). These are enumerated from what the car reports, so a profile added or removed in the car appears or disappears after the next refresh. A profile deleted in the car leaves its control unavailable rather than showing a stale target.

`sensor.<vehicle>_active_charging_profile_name` says which profile is in force, so a dashboard can show the governing location beside the sliders. The per-profile controls are keyed on the profile id, not its name, so renaming a location in the myAudi app renames the control without breaking automations that reference it.

The service actions below still work and remain the way to reach the parameterised commands: `start_climate_control` (temperature, seat and glass heating, climatisation mode) and `start_auxiliary_heating` (duration) both take settings the vehicle does not report back, so they have no on-page control.

### Starting and stopping a charge

The `Start charging (experimental)` and `Stop charging (experimental)` buttons exist, but are guarded twice: they only appear with the _Enable experimental vehicle controls_ option, only for cars that report a charging capability, and are disabled in the entity registry by default. The car reports no flag for "remote start charging", so the integration cannot tell whether it carries the command out. Both are also reachable through `execute_vehicle_action` (`start_charger`, `stop_charger`, `start_timed_charger`).

Check the effect on your own car before relying on them in an automation. On an A6 e-tron the API accepts the command but the car does not carry it out: stop, sent twice from a settled state, left the car drawing 6.5 kW. Start is unproven. It appeared to work once, but the car had a target well above its state of charge at that moment and would have charged anyway; repeated later with the target below the state of charge, the command was accepted and nothing happened. Timed charging goes through the same command and is therefore equally unreliable.

`Target state of charge` is more reliable: raising it above the current level starts a charge and lowering it below stops one, which is the lever that behaved consistently in every direction under testing. The car's departure timers are the other reliable route, and are reported here but not yet writable.

Number and select entities (charge targets, `Charge mode`, `Climatisation mode`) show the value that was just sent until the car reports a different one, for at most 20 minutes. The car often confirms such values only after several minutes; without this assumption the control would jump straight back to the old value.

After a command the integration polls the cloud once. If the command itself already triggered a poll, no second one follows.

### Flash and honk

`Flash` flashes the vehicle's lights for ten seconds. The car must have reported a position, because the API requires one; the control refuses rather than sending a request that would be rejected.

`Honk and flash` also sounds the horn. It is a separate button and disabled in the entity registry by default because it is loud. Both use the same endpoint, but `Flash` sends only the flash mode, so it can never sound the horn.

## Climatisation

The climate entity turns climatisation on and off and sets the target temperature. The car reports whether climatisation is running and in which mode (heating, cooling, ventilation), so the entity reflects the vehicle rather than what Home Assistant last asked for.

Two things it deliberately does not do. It has no current temperature, because the car reports the outdoor reading and not the cabin, and showing the outside temperature as a climate entity's current temperature would misstate what it measures. And it does not expose seat or glass heating, climatisation-at-unlock, or the comfort/economy mode: the vehicle never reports those back, so a control for them would only ever show what you last set. Use the `start_climate_control` service action for those.

The target temperature comes from the car, which reports it in its climatisation settings. Home Assistant only holds a value as a fallback for a vehicle that reports none, and for the moment between asking for a change and the car confirming it. The car stores half degrees and the control steps in half degrees too. With climatisation off, a new target is written to the car's settings without starting it; the car can take several minutes to report the new value, and until it does the control shows the value the car still holds.

The rest of the climatisation settings the car reports (window heating, climatisation at unlock, and the seat zones it has) appear as switches under configuration. They are written through the car's settings endpoint without starting climatisation, which the myAudi app does not offer: there, a heated seat can only be enabled while starting the air conditioning.

Each toggle sends the whole settings object back with one field changed, because the endpoint replaces rather than merges. Changing a seat therefore cannot clear the target temperature.

`start_auxiliary_heating` (duration) stays service-only for the same reason.

On Auth0 vehicles the **Climatisation ON/OFF** switch starts and stops climatisation with the settings stored in the car and follows the car's reported state. The option _Quick start climate using car-stored settings_ makes the climate entity do the same instead of sending the temperature shown in Home Assistant. The `Climatisation mode` select (comfort or economy) appears where the car reports a mode.

Which of these switches exist is up to the car: when it answers a setting with an explicit "not supported" (for example `supportsWindowHeatingEnabled: false` on the A6 e-tron), the integration does not create the switch. A missing answer keeps it. What your car reports is in the integration's diagnostics download under `capability_inventory`: `capability_ids` (every capability) and `supports_flags` (the answers for climatisation and charging profiles). The flags are read once when the integration starts; after a reload they show up in the diagnostics.

Climatisation timers in the car are reported by sensors (number of enabled timers, next timer in local time). They are created, switched and deleted with the timer service actions below.

## Service Actions

### Audi Connect: Refresh Vehicle Data

`ha_audi_connect.refresh_vehicle_data`

Normal updates retrieve data from the Audi Connect cloud service, and don't interact directly with the vehicle. _This_ service action triggers an update request from the vehicle itself. When data is retrieved successfully, Home Assistant is automatically updated. The service action requires the vehicle (device) as a parameter.

#### Parameters

- **`device_id`**: The Audi vehicle (device) to perform the action on.

> [!CAUTION]
> **This service action counts against your daily API rate limit.** Repeated use may exhaust your limit. Use sparingly and monitor your remaining API calls via the **"API Requests Remaining"** diagnostic sensor or **Settings → System → Repairs & System Information**.

> [!NOTE]
> The **"API Requests Remaining"** diagnostic sensor restores its last known value after a Home Assistant restart. Its `last_observed` attribute records when Audi last returned a `Vcf-Remaining-Calls` value. If `value_restored` is `true`, the displayed value was restored from the previous Home Assistant runtime and may no longer represent the current remaining allowance.

### Audi Connect: Refresh Cloud Data

`ha_audi_connect.refresh_cloud_data`

_This_ service action triggers an update request from the cloud.

- Functionality: Updates data for all vehicles from the online source, mirroring the action performed at integration startup or during scheduled refresh intervals.
- Behavior: Does not force a vehicle-side data refresh. Consequently, if vehicles haven't recently pushed updates, retrieved data might be outdated.
- Note: This service action replicates the function of active polling without scheduling, offering a more granular control over data refresh moments.
- **IMPORTANT:** This service action has no built in usage limits. Excessive use may result in a temporary suspension of your account.

#### Parameters

- `none`

### Audi Connect: Execute Vehicle Action

`ha_audi_connect.execute_vehicle_action`

This service action allows you to perform actions on your Audi vehicle, specified by the vehicle and the desired action.

#### Service Parameters

- **`device_id`**: The Audi vehicle (device) to perform the action on.
- **`action`**: The specific action to perform on the vehicle. Available actions include:
  - **`lock`**: Lock the vehicle.
  - **`unlock`**: Unlock the vehicle.
  - **`start_climatisation`**: Start the vehicle's climatisation system. (Legacy) -- Deprecated
  - **`stop_climatisation`**: Stop the vehicle's climatisation system.
  - **`start_charger`**: Start charging the vehicle.
  - **`start_timed_charger`**: Start the vehicle's charger with a timer.
  - **`stop_charger`**: Stop charging the vehicle.
  - **`start_preheater`**: Start the vehicle's preheater system. (Legacy) -- Deprecated
  - **`stop_preheater`**: Stop the vehicle's preheater system.
  - **`start_window_heating`**: Start heating the vehicle's windows.
  - **`stop_window_heating`**: Stop heating the vehicle's windows.

#### Usage Example

To lock a vehicle, use the following service call:

```yaml
service: ha_audi_connect.execute_vehicle_action
data:
  device_id: 034986de941a1f824b3f06c0a1d9333f
  action: "lock"
```

#### Notes

- Certain service actions require the S-PIN to be set in the configuration.
- After a successful action, the integration waits for the configured **Cloud Refresh Delay** and then performs a cloud data refresh. If **Refresh Vehicle Data After Action** is enabled, a vehicle refresh is also sent before the delay.

### Audi Connect: Start Climate Control

`ha_audi_connect.start_climate_control`

This service action allows you to start the climate control with options for temperature, glass surface heating, and auto seat comfort.

#### Parameters

- **`device_id`**: The Audi vehicle (device) to perform the action on.
- **`temp_f`** (_optional_): Desired temperature in Fahrenheit. Default is `70`.
- **`temp_c`** (_optional_): Desired temperature in Celsius. Default is `21`.
- **`glass_heating`** (_optional_): Enable (`True`) or disable (`False`) glass heating. Default is `False`.
- **`seat_fl`** (_optional_): Enable (`True`) or disable (`False`) the front-left seat heater. Default is `False`.
- **`seat_fr`** (_optional_): Enable (`True`) or disable (`False`) the front-right seat heater. Default is `False`.
- **`seat_rl`** (_optional_): Enable (`True`) or disable (`False`) the rear-left seat heater. Default is `False`.
- **`seat_rr`** (_optional_): Enable (`True`) or disable (`False`) the rear-right seat heater. Default is `False`.
- **`climatisation_at_unlock`** (_optional_): Let climatisation continue when the vehicle is unlocked.
- **`climatisation_mode`** (_optional_): `comfort` (default) or `economy`.

#### Usage Example

To start the climate control with a temperature of 72°F, enable glass heating, and activate both front seat heaters, use the following service call:

```yaml
service: ha_audi_connect.start_climate_control
data:
  device_id: 034986de941a1f824b3f06c0a1d9333f
  temp_f: 72
  glass_heating: True
  seat_fl: True
  seat_fr: True
```

#### Notes

- The `temp_f` and `temp_c` parameters are mutually exclusive. If both are provided, `temp_f` takes precedence.
- If neither `temp_f` nor `temp_c` is provided, the system defaults to 70°F or 21°C.
- After a successful action, the integration waits for the configured **Cloud Refresh Delay** and then performs a cloud data refresh. If **Refresh Vehicle Data After Action** is enabled, a vehicle refresh is also sent before the delay.

### Audi Connect: Start Auxiliary Heating

`ha_audi_connect.start_auxiliary_heating`

This service action allows you to start auxiliary heating the vehicle, with option for duration.

#### Parameters

- **`device_id`**: The Audi vehicle (device) to perform the action on.
- **`duration`** (_optional_): The number of minutes the auxiliary heater should run before turning off. Default is `20` minutes if not provided.

#### Usage Example

To start the auxiliary heater for 40 minutes, use the following service call action:

```yaml
service: ha_audi_connect.start_auxiliary_heating
data:
  device_id: 034986de941a1f824b3f06c0a1d9333f
  duration: 40
```

#### Notes

- Requires the S-PIN to be set in the configuration.
- After a successful action, the integration waits for the configured **Cloud Refresh Delay** and then performs a cloud data refresh. If **Refresh Vehicle Data After Action** is enabled, a vehicle refresh is also sent before the delay.

### Audi Connect: Set Target State of Charge

`ha_audi_connect.set_target_soc`

Sets the global target state of charge (20-100 %, steps of 5). See [Charge targets](#charge-targets) for what this value does and does not govern.

- **`device_id`**: The Audi vehicle.
- **`target_soc`**: Target charge level in percent.

### Audi Connect: Set Location Charge Target

`ha_audi_connect.set_location_charge_target`

Sets the target state of charge of a location profile (20-100 %, steps of 5). This persistent setting is what governs where a charge stops at that location.

- **`device_id`**: The Audi vehicle.
- **`profile_id`** (_optional_): The profile to change. Leave empty to change the profile the car is currently parked in.
- **`target_soc`**: Target charge level for this location.

### Audi Connect: Set Charge Mode

`ha_audi_connect.set_charge_mode`

Sets the charge mode preference. It does not start or stop a charge in progress.

- **`device_id`**: The Audi vehicle.
- **`charge_mode`**: `manual` charges whenever plugged in; `timer` charges only during the car's scheduled times.

### Audi Connect: Start Engine / Stop Engine

`ha_audi_connect.start_engine`, `ha_audi_connect.stop_engine`

Remotely start or stop the engine. Starting requires the S-PIN. Subject to the capability rules under **Feature status and API compatibility** in the [API notes](api-notes.en.md).

- **`device_id`**: The Audi vehicle.

### Audi Connect: Climatisation timers

`ha_audi_connect.create_climatisation_timer`, `ha_audi_connect.set_climatisation_timer_enabled`, `ha_audi_connect.delete_climatisation_timer`

Manage the car's climatisation timers. Times are in the car's local time. The timer number is shown in the attributes of the climate timer sensors.

- **`device_id`**: The Audi vehicle.
- Create: **`time`** (for example `07:30`), **`days`** (a single timer takes exactly one day), **`repeat`** (every week, default on), **`enabled`** (default on).
- Switch: **`timer_id`**, **`enabled`**.
- Delete: **`timer_id`**.

### Diagnostics

The following service actions are for troubleshooting. Use them only when investigating missing data, because they count against the API limit.

- `ha_audi_connect.probe_api` sends a read-only request (selectivestatus `jobs`, a `path` below the vehicle URL, or a fixed `graphql` query) and returns the redacted answer.
- `ha_audi_connect.probe_api_paths` checks eight known read-only endpoints (`extended` adds four experimental ones). The result appears in the next **Download diagnostics** export. Running it again with a different mode within 15 minutes is rejected.
- `ha_audi_connect.test_climatisation_write` is experimental. It writes one climatisation setting with a chosen request body variant (`app_dto` is the default; `app_full` sends all twelve fields of the app's request) and **changes the setting stored in the car**.

To see what Audi really sends, switch on `Log raw API responses (debug)` in the **options**, enable **debug logging** under **Settings ➤ Devices & Services ➤ Audi Connect**, trigger **Refresh vehicle data** and read the log (lines `Raw API response from …`). Then switch both off again. The VIN, coordinates, user ID, PINs and tokens are masked; with `Also log VIN and position unredacted` the VIN, the position and the user ID stay in. Sign-in and token replies never reach the log, unlike the `DEBUG_VERBOSE` switch in the code, which also prints tokens.

The diagnostic sensors `Vehicle data freshness`, `Vehicle data age`, `Cloud last successful poll` and `API Requests Remaining` show how current the data is. For detailed logs set `custom_components.ha_audi_connect: debug` under `logger:` in `configuration.yaml`.

### Repair hints

After every successful poll the integration checks the end dates of the online services the car lists. When one has ended, or one ends within 30 days, a hint appears under **Settings ➤ System ➤ Repairs** with the services concerned and the date (at most one per car, "ended" wins over "ends soon"). The hint goes away by itself once the dates are far off again, and with the entry when you remove the integration. Data and controls that depend on an ended service can stop working; renew it in the myAudi app or at your Audi dealer. The VIN is in neither the hint nor its identifier.
