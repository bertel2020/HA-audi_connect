# Audi Connect – API notes

*[🇩🇪 Deutsche Version](api-notes.md)*

Background on what the Audi API and the cars actually do: which features are proven, which are only accepted, and why entities sometimes disappear. For everyday use the [user guide](user-guide.en.md) is enough.

## Feature status and API compatibility

Audi vehicles and regions do not all expose the same features. The integration
distinguishes between an Audi API request being accepted and the vehicle
actually performing an action. Check the vehicle and its subsequent reported
state before relying on remote commands in automations.

| Status                               | Control or capability                                               | Notes                                                                                                                                   |
| ------------------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Standard, capability-dependent       | Door lock/unlock and flash lights                                   | Require the corresponding vehicle permission; verify the actual vehicle state                                                           |
| Standard on supported Auth0 vehicles | **Climatisation ON/OFF** switch                                     | Uses the climate settings already stored in the car and reads the car's reported state; does not replace the climate temperature entity |
| Legacy / model-dependent             | **Preheater** and the original **Climatisation** climate entity     | Retained for compatibility; older routes may be unavailable or rejected on newer Auth0-backed accounts                                  |
| Experimental, opt-in                 | Window heating and **start/stop charging** buttons, charging plug release switch | Off by default; enable under Configure as _experimental vehicle controls_. Start/stop charging is accepted by Audi, an A6 e-tron does not carry it out |
| Capability-dependent                 | **Wake vehicle** and **Honk and flash** buttons                     | Wake vehicle needs a reported wake-up capability; Wake vehicle and Honk and flash are disabled in the entity registry by default      |
| Model-dependent                      | Charge mode and target SOC changes                                  | Audi may accept an HTTP request while rejecting or not applying the setting                                                             |

_Legacy_ describes an older interface; it does not announce removal.
The integration keeps existing unique IDs and service calls where possible.
Availability and feature support must be checked per vehicle, not inferred from
one successful command or a capability list alone. A partial cloud response
may leave an entity **unavailable** instead of removing it.

**Lock/unlock:** Both directions now use one post-command refresh and
expose a `last_command_status` attribute: `request_failed`,
`accepted_unconfirmed`, `confirmed_by_readback`, or
`already_reported_in_requested_state`. An Audi gateway acknowledgement or
a delayed cloud state is not a confirmed physical door action, and neither
direction issues a blind retry.

**Remote engine:** Older non-Auth0 combustion vehicles without a capability
inventory retain the previous engine-button fallback. Explicit capability
denial, impaired support, known hybrid/electric types, and Q8 model vetoes
still apply. Auth0 vehicles require an explicitly reported permission.

**Charging settings:** On Auth0 vehicles a global target-SOC update refuses
to submit a potentially destructive `charging/settings` PUT if Audi returns
unknown settings. Known writable settings are preserved; timestamp metadata
is excluded. Additional writable keys require vehicle-specific evidence.

**Q8 climate:** On the tested Audi Q8 PHEV, climate ON/OFF works through the
separate modern Auth0/CARIAD command path using the car's stored settings.
Passing a temperature to the legacy climate interface has not worked on that
vehicle. This does not establish support across other Audi types or regions.
A future capability model should combine reported features with vehicle type,
API generation and verified model-specific behavior, without assuming that a
model name grants permission or that a missing capability is definitive proof
of absence.

**Wake / sleeping vehicle:** The `Wake vehicle` button is created when the car reports a wake-up capability. It is disabled in the entity registry by default and can be enabled by hand. It uses the Auth0/CARIAD `vehiclewakeuptrigger` route. On an A6 e-tron it answers 204, and the car then reports a fresh timestamp. That shows the car reacting, not that every car and region answers the same way; above all, a 2xx answer alone never replaces checking the state reported afterwards. A wake-up the car does not carry out counts as a warning, not an error.

Waking a parked vehicle can cost energy from the 12 V and/or traction battery. For that reason automatic polling **never** wakes the vehicle on each cycle, and that is meant to stay: passive cloud refresh and active wake-up stay separate, the trigger is explicit user intent, and freshness is confirmed after a bounded, delayed readback before wake-up or charging status counts as current. There are no measurements of the effect on the parked vehicle's battery.

`Refresh vehicle data` uses a separate route (`vehiclewakeup`) and waits up to 100 seconds for the car to answer. A car that does not answer in time is logged as a warning, not an error: it may be asleep or out of coverage.

## Why an entity sometimes disappears

Entities are created when the integration sets up, and until now that decision asked whether the value was present in the poll it happened to be holding. A partial or rate-limited poll therefore removed controls: on one vehicle a `429 Too Many Requests` took sixteen entities away, including a parking-position sensor for a car that plainly has parking position. They returned only after a reload.

The car reports what it can do, separately from what any one poll contains, and the integration now asks that list instead where a capability maps cleanly onto an entity. A missing value leaves the entity unavailable rather than deleting it.

Vehicles that do not report a capability list are unaffected and keep the previous behaviour.
