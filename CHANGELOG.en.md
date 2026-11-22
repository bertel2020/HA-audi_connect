# Changelog

*[🇩🇪 Deutsche Version](CHANGELOG.md)*

Versions up to `v2.5.3b1` are on the [releases page](https://github.com/bertel2020/HA-audi_connect/releases). This file starts with what came after.

## 2.6.0 – 2026-11-22

**New**
- **Card:** The integration ships its own dashboard card (`audi-connect-card`): photo or icon, status, charging band, trips, vehicle details and a fold-away climatisation panel. Tap the title to open the integration, hold it to refresh the vehicle data.
- **Card – doors and windows:** A realistic top view of the car in the dialog, with a status badge for each door and window.
- **Card – editor:** The Audi logo, trips, climate and vehicle details can be switched on and off. The front and rear seat and zone buttons are separate options (off by default). The last trip and the long-term trip can be chosen one by one (`show_trip_last`, `show_trip_long`), and the rows of the vehicle details can be selected (`stats_rows`); only what the car reports is offered.
- **Card – display:** Failed actions, the day a charge finishes, keyboard and screen-reader access, and an unknown lock state instead of "locked". The last trip says when it ended ("10 h ago").
- **Trips:** Sensors for the last trip and the long-term totals, with state classes so the totals keep long-term statistics. Plus the timestamp sensor "Last trip ended", which only gives a value when the car sends a real time with a time zone.
- **More sensors:** How far each window is open in percent, warning lights, parking brake, battery care mode, climatisation mode (also as a select), charging scenario, the car's security status and when the online services end.
- **Charging:** The charge target limits the car reports, a select for the charging current of the profile the car stands in, and the switch for the charging plug's auto-unlock (experimental). Long-term statistics for charge level, range, tank level, charging power and outdoor temperature.
- **Controls:** A horn button (off by default, apart from the silent flash). Services to create, delete and switch climatisation timers on or off.
- **Translations:** Entity names in English and German, plus complete fi, fr, nl, nb, pt and pt-BR translations. Entity IDs come from the English names, whatever language Home Assistant uses.
- **Troubleshooting:** Two options, both off by default: write the car's raw replies to the debug log (VIN, positions, user ID, PINs and tokens masked), and optionally leave the VIN and the position in. Sign-in and token routes are never logged.
- **Repair hints:** When the car reports online services as ended, or one ends within 30 days, a hint under **Repairs** names the services and the date. It goes away by itself.
- **Error messages:** The messages for failed commands, service calls and the sign-in are translated (8 languages).
- **Diagnostics:** They list every capability ID and the car's supports flags, name the climatisation, charging, wake-up, honk and timer routes, and say which trip figures are held. `probe_api` and read-only probes of known routes (BFF, GraphQL, `bs/`, trips).

**Changed**
- **Parking light and braking status:** Both show plain On/Off instead of "Safe/Unsafe".
- **Wake-up:** The button is off by default. A wake-up the car does not carry out is a warning, not an error.
- **Options:** The scan interval is explained. Entities are filed by use, with connection details in diagnostics and the odometer in the main view. The car type is part of the device model and no longer a sensor.
- **Sensors only when needed:** Connectivity, activity, the AC current limit and a further engine are only created for cars that report them. The dealer and service sensors only appear when there is something to show.
- **Commands:** Commands to the car (switches, buttons, lock, climate, numbers, selects) now run one after the other instead of at once, because Audi limits the requests.
- **Reauthentication:** It refuses a different myAudi account than the one the entry was set up with.

**Fixed**
- **Diagnostics:** A trip end that arrives as a real time counts as readable.
- **Sign-in:** A rotated refresh token is kept when a later login or refresh step fails. No second cloud poll follows a command that already refreshed.
- **Inputs:** Numbers and selects show the value just written until the car reports another one. The target temperature of a stopped car is written to the car in half-degree steps.
- **Values:** The remaining charge time is unknown, not 0, while charging without an estimate. Departure timers and the charge target limits are read the way the A6 reports them. The device tracker no longer stores the VIN as an attribute. Secrets are redacted in logs.
- **Card:** Glass and daytime running lights keep their colour whatever the theme's primary colour is. The focus stays inside the open dialog.

**Removed**
- The start and stop charging buttons, which the car never carried out.
- The navigation charge target sensor, the duplicate target state of charge sensor and the local dealer and service data.
- The "Cloud Update at Startup" option: skipping the first poll left no entities.
- The unused legacy charger poll and the unreachable device-code step.
