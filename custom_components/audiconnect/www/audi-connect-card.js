/*
 * Audi Connect card for Home Assistant.
 *
 * Shipped with the Audi Connect integration and loaded automatically, so there is
 * nothing to install and no YAML to write: add the card from the dashboard editor,
 * pick your vehicle, done. Every entity is found through the vehicle's device and the
 * entity's translation key, so it keeps working whatever language Home Assistant is in
 * and however the entities were renamed.
 */
const CARD_VERSION = "1.0.0";
const DOMAIN = "audiconnect";

const TEXT = {
  en: {
    locked: "Locked", unlocked: "Unlocked", lock_unknown: "Lock state unknown", not_secured: "Not secured",
    doors_closed: "Doors closed", windows_closed: "Windows closed",
    n_open: "{n} open", plugged: "Plugged in", unplugged: "Not plugged in",
    light_on: "Lights on", light_off: "Lights off", warning: "Warning",
    charge_target: "Charge target", range: "Range", charging_done: "done", power: "Power", charge_waiting: "Plugged in, waiting to start", charge_error: "Charging error", charge_reached: "Charge target reached", charge_conservation: "Conservation charging", rate: "Range per hour", in: "in {t}",
    last_trip: "Last trip", long_term: "Long term",
    distance: "Distance", speed: "Avg. speed", consumption: "Consumption", energy: "Energy",
    electric_range: "Electric range", inspection: "Inspection", inspection_days: "Inspection in", inspection_distance: "Inspection in (distance)", oil_change_days: "Oil change in", oil_change_distance: "Oil change in (distance)", parked: "Parked for",
    vehicle: "Vehicle", parking_brake: "Parking brake", brake_on: "Engaged", brake_off: "Released", warning_lights: "Warning lights", warning_active: "Active", warning_none: "None", security: "Security status", fuel_range: "Fuel range", tank: "Tank", outdoor: "Outside temperature", oil_change: "Oil change", oil_level: "Oil level", adblue: "AdBlue range", charge_type: "Charging type", max_current: "Max. charging current",
    climate: "Climate", climate_on: "Running", climate_off: "Off", mode: "Mode",
    heating: "Heating", cooling: "Cooling", ventilating: "Ventilating", running: "Running", remaining: "Time left",
    start: "Start", stop: "Stop",
    doors: "Doors", windows: "Windows", all_closed: "All closed and locked",
    all_closed_unlocked: "All closed, not locked", all_closed_unknown: "Lock state unknown", n_openings: "{n} openings open",
    one_opening: "1 opening open", open: "open", closed: "closed",
    closed_locked: "closed · locked", closed_unlocked: "closed · unlocked",
    lock: "Lock", unlock: "Unlock", close: "Close", temp_down: "Lower temperature", temp_up: "Raise temperature",
    hood: "Hood", trunk: "Trunk", fl: "Front left", fr: "Front right", rl: "Rear left", rr: "Rear right",
    confirm_lock: "Lock the vehicle?", confirm_unlock: "Unlock the vehicle?",
    no_vehicle: "No Audi Connect vehicle found. Pick one in the card settings.",
    stale: "Data is outdated", days: "days", ago: "{t} ago", now: "now",
    min: "min", h: "h", d: "d", refresh: "Refresh", refresh_data: "Refresh vehicle data", flash: "Flash lights",
    call_failed: "The action failed", failed: "{a} failed",
    a_start_climate: "Start climate", a_stop_climate: "Stop climate", a_temp: "Set temperature", a_target: "Set charge target", a_mode: "Set mode", a_toggle: "Switch",
    doors_unknown: "Doors: unknown", windows_unknown: "Windows: unknown",
    // editor
    e_device: "Vehicle", e_name: "Name", e_image: "Upload a photo (optional)", e_image_local: "…or pick one from the www folder", e_none: "none",
    e_icon: "Icon instead of the Audi logo (optional)", e_logo: "Show Audi logo", e_trips: "Show trips", e_climate: "Show climate", e_stats: "Show vehicle details", e_seats_front: "Show front seat/zone buttons", e_seats_rear: "Show rear seat/zone buttons",
  },
  de: {
    locked: "Verriegelt", unlocked: "Entriegelt", lock_unknown: "Schlosszustand unbekannt", not_secured: "Nicht gesichert",
    doors_closed: "Türen zu", windows_closed: "Fenster zu",
    n_open: "{n} offen", plugged: "Angesteckt", unplugged: "Nicht verbunden",
    light_on: "Licht an", light_off: "Licht aus", warning: "Warnung",
    charge_target: "Ladeziel", range: "Reichweite", charging_done: "fertig", power: "Leistung", charge_waiting: "Angesteckt, wartet auf Freigabe", charge_error: "Ladefehler", charge_reached: "Ladeziel erreicht", charge_conservation: "Erhaltungsladen", rate: "Reichweite je Std.", in: "in {t}",
    last_trip: "Letzte Fahrt", long_term: "Langzeit",
    distance: "Strecke", speed: "Ø Tempo", consumption: "Verbrauch", energy: "Energie",
    electric_range: "Elektrische Reichweite", inspection: "Inspektion", inspection_days: "Inspektion in", inspection_distance: "Inspektion in (Strecke)", oil_change_days: "Ölwechsel in", oil_change_distance: "Ölwechsel in (Strecke)", parked: "Geparkt seit",
    vehicle: "Fahrzeug", parking_brake: "Parkbremse", brake_on: "Angezogen", brake_off: "Gelöst", warning_lights: "Warnleuchten", warning_active: "Aktiv", warning_none: "Keine", security: "Sicherheitsstatus", fuel_range: "Reichweite Kraftstoff", tank: "Tank", outdoor: "Außentemperatur", oil_change: "Ölwechsel", oil_level: "Ölstand", adblue: "AdBlue-Reichweite", charge_type: "Ladeart", max_current: "Max. Ladestrom",
    climate: "Klimatisierung", climate_on: "Läuft", climate_off: "Aus", mode: "Modus",
    heating: "Heizt", cooling: "Kühlt", ventilating: "Lüftet", running: "Läuft", remaining: "Restlaufzeit",
    start: "Starten", stop: "Stoppen",
    doors: "Türen", windows: "Fenster", all_closed: "Alles zu und verriegelt",
    all_closed_unlocked: "Alles zu, nicht verriegelt", all_closed_unknown: "Schlosszustand unbekannt", n_openings: "{n} Öffnungen offen",
    one_opening: "1 Öffnung offen", open: "offen", closed: "zu",
    closed_locked: "zu · verriegelt", closed_unlocked: "zu · entriegelt",
    lock: "Verriegeln", unlock: "Entriegeln", close: "Schließen", temp_down: "Temperatur senken", temp_up: "Temperatur erhöhen",
    hood: "Motorhaube", trunk: "Heckklappe", fl: "Vorne links", fr: "Vorne rechts", rl: "Hinten links", rr: "Hinten rechts",
    confirm_lock: "Fahrzeug verriegeln?", confirm_unlock: "Fahrzeug entriegeln?",
    no_vehicle: "Kein Audi-Connect-Fahrzeug gefunden. Wähle eines in den Karteneinstellungen.",
    stale: "Daten sind veraltet", days: "Tage", ago: "vor {t}", now: "gerade eben",
    min: "Min.", h: "Std.", d: "T.", refresh: "Aktualisieren", refresh_data: "Fahrzeugdaten aktualisieren", flash: "Lichthupe",
    call_failed: "Aktion fehlgeschlagen", failed: "{a} fehlgeschlagen",
    a_start_climate: "Klima starten", a_stop_climate: "Klima stoppen", a_temp: "Temperatur setzen", a_target: "Ladeziel setzen", a_mode: "Modus setzen", a_toggle: "Umschalten",
    doors_unknown: "Türen: unbekannt", windows_unknown: "Fenster: unbekannt",
    e_device: "Fahrzeug", e_name: "Name", e_image: "Foto hochladen (optional)", e_image_local: "…oder eines aus dem www-Ordner wählen", e_none: "keines",
    e_icon: "Icon statt Audi-Logo (optional)", e_logo: "Audi-Logo anzeigen", e_trips: "Fahrten anzeigen", e_climate: "Klimatisierung anzeigen", e_stats: "Fahrzeugdetails anzeigen", e_seats_front: "Vordere Sitz-/Zonen-Tasten anzeigen", e_seats_rear: "Hintere Sitz-/Zonen-Tasten anzeigen",
  },
};

// What a failed call is called in the error note.
const ACTION_TEXT = {
  "climate.turn_on": "a_start_climate", "climate.turn_off": "a_stop_climate", "climate.set_temperature": "a_temp",
  "lock.lock": "lock", "lock.unlock": "unlock", "button.press": "refresh_data",
  "number.set_value": "a_target", "select.select_option": "a_mode", "homeassistant.toggle": "a_toggle",
};

// What an entity says when it has nothing to say.
const NO_VALUE = new Set(["unavailable", "unknown", "invalid", "unsupported", ""]);

const DOOR_KEYS = {
  hood: "hood_open", fl: "left_front_door_open", fr: "right_front_door_open",
  rl: "left_rear_door_open", rr: "right_rear_door_open", trunk: "trunk_open",
};
const WINDOW_KEYS = {
  fl: "left_front_window_open", fr: "right_front_window_open",
  rl: "left_rear_window_open", rr: "right_rear_window_open",
};
const WINDOW_PCT = {
  fl: "window_open_pct_front_left", fr: "window_open_pct_front_right",
  rl: "window_open_pct_rear_left", rr: "window_open_pct_rear_right",
};

const NATIVE = "button,a,input,select,summary,textarea";
const FOCUSABLE = 'button,[role="button"],input,select,summary,[tabindex="0"]';

const STYLE = `
:host{display:block}
ha-card{overflow:hidden;position:relative;border-radius:24px}
*{box-sizing:border-box}
.title{display:flex;align-items:center;justify-content:center;gap:10px;padding:16px 16px 0;font-size:22px;font-weight:600;color:var(--secondary-text-color)}
.title svg{width:42px;height:auto}
.title ha-icon{--mdc-icon-size:38px}
.tap{cursor:pointer}
.busy{opacity:.45;transition:opacity .2s}
.photo{display:block;width:100%;max-height:220px;object-fit:contain;padding:6px 16px 0}
.row{display:flex;align-items:center;justify-content:space-between;padding:8px 18px;font-size:14px;color:var(--primary-text-color);gap:8px}
.row .item{display:flex;align-items:center;gap:6px;min-width:0}
.row .item ha-icon{--mdc-icon-size:20px;color:var(--secondary-text-color)}
.row .mid{font-size:12px;color:var(--secondary-text-color);display:flex;align-items:center;gap:4px}
.row .mid.warn{color:var(--warning-color)}
.icons{display:flex;padding:0 6px 10px}
.ic{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;padding:6px 2px;border-radius:12px;cursor:pointer;font-size:11px;color:var(--secondary-text-color);text-align:center;background:none;border:0;font-family:inherit}
.ic:hover{background:var(--secondary-background-color)}
.ic ha-icon{--mdc-icon-size:30px}
.ic.ok ha-icon{color:var(--success-color)}.ic.warn ha-icon{color:var(--warning-color)}.ic.bad ha-icon{color:var(--error-color)}
.sep{border-top:1px solid var(--divider-color)}
.energy{padding:14px 18px 12px}
.barwrap{position:relative;height:26px;background:var(--secondary-background-color);border:1px solid var(--divider-color);border-radius:999px;overflow:hidden}
.bar{position:relative;height:100%;border-radius:999px;display:flex;align-items:center;justify-content:flex-end;padding-right:10px;font-size:13px;font-weight:600;color:#1b2a10;overflow:hidden;min-width:48px;transition:width .6s ease;background-image:linear-gradient(90deg,#e24b4a 0%,#f0b429 50%,#4caf50 100%);background-repeat:no-repeat}
.bar span{position:relative;z-index:1}
.bar.charging::before{content:"";position:absolute;top:0;bottom:0;left:-30px;right:0;background:repeating-linear-gradient(45deg,rgba(255,255,255,.3) 0 8px,transparent 8px 16px);animation:mv 1s linear infinite}
@keyframes mv{to{transform:translateX(22.63px)}}
@keyframes pu{0%,100%{opacity:1}50%{opacity:.35}}
.mark{position:absolute;top:0;bottom:0;width:2px;background:var(--primary-text-color);opacity:.7;z-index:2}
.eline{display:flex;justify-content:space-between;font-size:14px;margin-top:8px;color:var(--secondary-text-color)}
.eline b{font-weight:500;color:var(--primary-text-color)}
.eline span[data-more],.barwrap[data-more]{cursor:pointer}
input[type=range]{width:100%;margin:2px 0 0;accent-color:var(--primary-color)}
.band{display:flex;align-items:stretch;margin-top:12px;padding:12px 4px;border-radius:16px;background:linear-gradient(135deg,color-mix(in srgb,var(--primary-color) 18%,transparent),color-mix(in srgb,var(--primary-color) 8%,transparent));box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--primary-color) 22%,transparent);color:var(--primary-text-color)}
.cell{flex:1;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;gap:2px;min-width:0;padding:0 6px;cursor:pointer;text-align:center}
.cell+.cell::before{content:"";position:absolute;left:0;top:14%;bottom:14%;width:1px;background:color-mix(in srgb,var(--primary-color) 30%,transparent)}
.cell .ci{--mdc-icon-size:20px;margin-bottom:2px;color:var(--primary-color)}
.band{container-type:inline-size}
.cell .v{font-size:18px;font-size:clamp(14px,5.4cqi,18px);font-weight:600;line-height:1.2;white-space:nowrap;font-variant-numeric:tabular-nums}
@container (max-width:300px){.cell .v{white-space:normal;overflow-wrap:anywhere}}
.cell .k,.cell .s{font-size:11px;color:var(--primary-text-color);opacity:.78}
.cell .k{letter-spacing:.02em}
.note{display:flex;align-items:center;gap:10px;margin-top:10px;padding:10px 14px;border-radius:12px;font-size:14px;cursor:pointer;background:var(--secondary-background-color);color:var(--primary-text-color)}
.note ha-icon{--mdc-icon-size:22px;color:var(--secondary-text-color)}
.note.bad{background:color-mix(in srgb,var(--error-color) 14%,transparent)}
.note.bad ha-icon{color:var(--error-color)}
.note.err{cursor:default;margin:10px 14px 0}
.note .sub{display:block;margin-top:2px;font-size:12px;color:var(--primary-text-color);opacity:.8}
.note .nd{margin-left:auto;font-size:12px;color:var(--secondary-text-color)}
.pulse{animation:pu 1.4s ease-in-out infinite}
details{border-top:1px solid var(--divider-color)}
summary{list-style:none;display:flex;align-items:center;gap:10px;padding:12px 18px;cursor:pointer;font-size:14px;color:var(--primary-text-color)}
summary::-webkit-details-marker{display:none}
@media (hover:hover){summary:hover{background:var(--secondary-background-color)}}
summary:active{background:var(--secondary-background-color)}
summary .t{font-weight:500;min-width:112px}
summary .sm{flex:1;color:var(--secondary-text-color);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
summary ha-icon{--mdc-icon-size:20px;color:var(--secondary-text-color)}
summary .ch{transition:transform .15s}
details[open] summary .ch{transform:rotate(180deg)}
.trip{display:flex;padding:2px 12px 14px}
.trip div{flex:1;display:flex;flex-direction:column;align-items:center;gap:1px;min-width:0}
.trip ha-icon{--mdc-icon-size:22px;color:var(--secondary-text-color)}
.trip .v{font-size:16px;font-weight:500}.trip .u{font-size:11px;color:var(--secondary-text-color)}.trip .k{font-size:11px;color:var(--secondary-text-color);margin-top:2px}
.facts{padding:0 18px 12px}
.fact{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--divider-color);font-size:14px;color:var(--primary-text-color);cursor:pointer}
.fact:last-child{border:0}
.fact ha-icon{--mdc-icon-size:20px;color:var(--secondary-text-color)}
.fact .fl{flex:1;color:var(--secondary-text-color)}
.fact .fv{font-weight:500;text-align:right}
.cbody{padding:6px 16px 16px}
.mrow{display:flex;justify-content:space-between;align-items:center;font-size:14px;color:var(--secondary-text-color);margin-bottom:2px}
.cstatus{display:flex;align-items:center;gap:10px;margin-top:12px;padding:10px 14px;border-radius:12px;background:color-mix(in srgb,var(--primary-color) 14%,transparent);color:var(--primary-text-color);font-size:14px}
.cstatus ha-icon{--mdc-icon-size:22px;color:var(--primary-color);animation:spin 2s linear infinite}
.cstatus b{font-weight:600}
.cstatus span{margin-left:auto;color:var(--secondary-text-color)}
.cstatus span b{color:var(--primary-text-color);font-weight:600}
@keyframes spin{to{transform:rotate(360deg)}}
select{background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);border-radius:999px;padding:8px 12px;font-size:13px;font-family:inherit}
.step{display:flex;align-items:center;justify-content:center;gap:20px;margin-top:14px}
.step b{font-size:22px;font-weight:500;min-width:84px;text-align:center}
.stp{width:40px;height:40px;border-radius:50%;background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;transition:transform .12s,background .2s}
.stp:active{transform:scale(.92);background:color-mix(in srgb,var(--primary-color) 28%,transparent)}
.trow{display:flex;align-items:center;gap:10px;margin-top:12px;font-size:13px;color:var(--primary-text-color)}
.trow ha-icon{--mdc-icon-size:18px}.trow input{flex:1;accent-color:var(--primary-color);cursor:pointer}.trow b{min-width:48px;text-align:right;font-weight:500}
.pills{display:grid;gap:8px;margin-top:10px}
.pill{background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);border-radius:999px;padding:10px 0;font-size:13px;display:flex;align-items:center;justify-content:center;gap:6px;cursor:pointer;font-family:inherit;transition:transform .12s,background .2s,border-color .2s,opacity .2s}
@media (hover:hover){.pill:hover{border-color:var(--primary-color)}}
.pill:active{transform:scale(.95);background:color-mix(in srgb,var(--primary-color) 28%,transparent)}
.pill.wait{pointer-events:none;opacity:.7}
.pill.wait ha-icon{animation:spin 1s linear infinite}
.pill.go{background:var(--primary-color);border-color:var(--primary-color);color:var(--text-primary-color,#fff);font-weight:500}
.pill.go:active{filter:brightness(.9);background:var(--primary-color)}
.pill.on{background:color-mix(in srgb,var(--primary-color) 18%,transparent);color:var(--primary-color);border-color:var(--primary-color)}
.pill ha-icon{--mdc-icon-size:18px}
.ov{position:absolute;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:flex-start;justify-content:center;padding:14px;z-index:5;overflow:auto}
.dlg{background:var(--card-background-color);border-radius:16px;padding:14px;width:100%;max-width:340px}
.dh{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}
.dh b{font-size:15px;font-weight:500;display:block}.dh span{font-size:12px}
.x{cursor:pointer;color:var(--secondary-text-color);background:none;border:0;padding:0}
.tabs{display:flex;gap:4px;background:var(--secondary-background-color);border-radius:8px;padding:3px;margin-bottom:6px}
.tab{flex:1;padding:7px 0;text-align:center;font-size:13px;border-radius:6px;cursor:pointer;color:var(--secondary-text-color);background:none;border:0;font-family:inherit}
.tab.on{background:var(--card-background-color);color:var(--primary-text-color);font-weight:500;box-shadow:0 0 0 1px var(--divider-color)}
.car{width:100%;max-width:290px;display:block;margin:6px auto 4px;
--c-edge:color-mix(in srgb,var(--primary-text-color) 22%,var(--secondary-background-color));
--c-mid:color-mix(in srgb,var(--card-background-color) 55%,var(--secondary-background-color));
--c-line:color-mix(in srgb,var(--primary-text-color) 34%,transparent);
--c-bodyline:color-mix(in srgb,var(--primary-text-color) 28%,transparent);
--c-trim:color-mix(in srgb,var(--primary-text-color) 78%,var(--card-background-color));
--c-cavity:color-mix(in srgb,var(--primary-text-color) 70%,var(--card-background-color));
--c-engine:color-mix(in srgb,var(--primary-text-color) 16%,var(--c-cavity));
--c-gl-a:color-mix(in srgb,#4f8fc4 30%,color-mix(in srgb,var(--primary-text-color) 42%,var(--card-background-color)));
--c-gl-b:color-mix(in srgb,#4f8fc4 20%,color-mix(in srgb,var(--primary-text-color) 58%,var(--card-background-color)));
--c-gl-c:color-mix(in srgb,#4f8fc4 14%,color-mix(in srgb,var(--primary-text-color) 70%,var(--card-background-color)));
--c-tail:color-mix(in srgb,var(--error-color) 55%,var(--secondary-background-color));
--c-head:color-mix(in srgb,var(--primary-text-color) 10%,var(--card-background-color));
--c-drl:color-mix(in srgb,#8cc8f0 80%,var(--card-background-color));
--c-ul:color-mix(in srgb,var(--warning-color) 14%,var(--secondary-background-color));
--c-open:color-mix(in srgb,var(--error-color) 40%,var(--secondary-background-color));
--c-win:color-mix(in srgb,var(--warning-color) 45%,var(--c-cavity))}
.car .pn{stroke-width:1.1}
.car .pn.lk,.car .pn.unk{stroke:var(--c-line);stroke-width:.8}
.car .pn.ul{fill:var(--c-ul);stroke:var(--warning-color)}
.car .pn.open{fill:var(--c-open);stroke:var(--error-color)}
.car .wn.open{fill:var(--c-win);stroke:var(--warning-color)}
.car .hit{cursor:pointer}
.car .bd{fill:var(--secondary-text-color)}
.car .bd.lk{fill:color-mix(in srgb,var(--success-color) 65%,#000)}
.car .bd.ul,.car .bd.win{fill:color-mix(in srgb,var(--warning-color) 65%,#000)}
.car .bd.open{fill:color-mix(in srgb,var(--error-color) 72%,#000)}
.li{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--divider-color);font-size:13px;color:var(--primary-text-color);cursor:pointer}
.li:last-of-type{border:0}
.c-ok{color:var(--success-color)}.c-warn{color:var(--warning-color)}.c-bad{color:var(--error-color)}.c-mute{color:var(--secondary-text-color)}
.big{width:100%;margin-top:10px}
.pills .big{margin-top:0}
.empty{padding:24px;text-align:center;color:var(--secondary-text-color)}
[role="button"]:focus-visible,button:focus-visible,summary:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--primary-color);outline-offset:2px}
[role="button"]{cursor:pointer}
@supports not (color:color-mix(in srgb,red,blue)){
.band,.cstatus,.pill.on,.stp:active,.pill:active,.note.bad{background:var(--secondary-background-color)}
.cell+.cell::before{background:var(--divider-color)}
.note.bad{background:var(--secondary-background-color);border-left:3px solid var(--error-color)}
.car .bd.lk{fill:var(--success-color)}.car .bd.ul,.car .bd.win{fill:var(--warning-color)}.car .bd.open{fill:var(--error-color)}
.car{--c-edge:var(--divider-color);--c-mid:var(--card-background-color);--c-line:var(--divider-color);--c-bodyline:var(--divider-color);--c-trim:var(--secondary-text-color);--c-cavity:var(--secondary-text-color);--c-engine:var(--secondary-text-color);--c-gl-a:var(--secondary-text-color);--c-gl-b:var(--secondary-text-color);--c-gl-c:var(--secondary-text-color);--c-tail:var(--error-color);--c-head:var(--secondary-background-color);--c-drl:#8cc8f0;--c-ul:var(--secondary-background-color);--c-open:var(--secondary-background-color);--c-win:var(--secondary-background-color)}
}
@media (prefers-reduced-motion:reduce){.bar.charging::before,.pulse,.cstatus ha-icon,.pill.wait ha-icon{animation:none}}
`;

// Top view of the car, 300 x 342. The right side is drawn once; the left is its mirror.
const CAR = {
 "BODY": "M150 12C182 12 203 14 208 26C212 36 213 50 213 64C213 96 210 120 210 160C210 200 214 222 214 250C214 282 211 302 203 312C193 320 172 322 150 322C128 322 107 320 97 312C89 302 86 282 86 250C86 222 90 200 90 160C90 120 87 96 87 64C87 50 88 36 92 26C97 14 118 12 150 12Z",
 "HOOD": "M150 25C170 25 186 26 194 31C198 50 200.5 72 201 93C190 89.5 172 88 150 88C128 88 110 89.5 99 93C99.5 72 102 50 106 31C114 26 130 25 150 25Z",
 "GREEN": "M150 92C176 92 194 94 201.5 99C200 120 199 145 199 171C199 200 198.5 234 195 267C184 274 166 276 150 276C134 276 116 274 105 267C101.5 234 101 200 101 171C101 145 100 120 98.5 99C106 94 124 92 150 92Z",
 "WIND": "M150 96.5C174 96.5 190 98.5 197.5 102.5L190 140.5C181 138.5 166 137.5 150 137.5C134 137.5 119 138.5 110 140.5L102.5 102.5C110 98.5 126 96.5 150 96.5Z",
 "ROOF": "M150 138C168 138 182 139 190.5 142C191.5 170 191.5 195 190 222C178 226 164 227 150 227C136 227 122 226 110 222C108.5 195 108.5 170 109.5 142C118 139 132 138 150 138Z",
 "PANO": "M150 147C166 147 178 147.5 184 150C185.5 172 185.5 196 184 214C176 217.5 164 218 150 218C136 218 124 217.5 116 214C114.5 196 114.5 172 116 150C122 147.5 134 147 150 147Z",
 "REARW": "M150 228.5C166 228.5 179 227.5 189 224.5L193.2 264C182 270.5 166 272.5 150 272.5C134 272.5 118 270.5 106.80000000000001 264L111 224.5C121 227.5 134 228.5 150 228.5Z",
 "TAILG": "M150 272.5C166 272.5 183 270.5 194 264.5C198 280 199 294 197 304C184 311 168 313 150 313C132 313 116 311 103 304C101 294 102 280 106 264.5C117 270.5 134 272.5 150 272.5Z",
 "TAILL": "M150 305.5C170 305.5 189 303 200.5 298L201.5 301.5C190 307.5 170 309.5 150 309.5C130 309.5 110 307.5 98.5 301.5L99.5 298C111 303 130 305.5 150 305.5Z",
 "BUMPF": "M163 14.2C180 14.6 195 16.5 203 20.5M137 14.2C120 14.6 105 16.5 97 20.5",
 "BUMPR": "M170 318.5C185 317.5 196 314.5 202 309M130 318.5C115 317.5 104 314.5 98 309",
 "WIN": {
  "f": "M191 143L198.6 107C199.2 128 199.3 150 199.1 168.5L191.4 168.5C191.6 160 191.5 150 191 143Z",
  "r": "M191.4 174L199 174C199 196 198.6 212 197.3 226L190.4 222C191 205 191.4 190 191.4 174Z"
 },
 "DOOR": {
  "f": "M201.5 99L212.4 99C211 125 210 150 210 171L199 171C199 145 200 120 201.5 99Z",
  "r": "M199 173L210 173C210.3 196 211.5 216 212.6 234C206 235 199.5 238 195.6 243C198 222 199 198 199 173Z"
 },
 "HINGE": {
  "f": [
   212,
   100
  ],
  "r": [
   210.3,
   174
  ]
 },
 "DOOR_CY": {
  "f": 135,
  "r": 207
 },
 "HANDLE": {
  "f": [
   208.2,
   150
  ],
  "r": [
   208.6,
   214
  ]
 },
 "MIRROR": "M202 103C209 100.5 219 101 223 106C224 110 220 113.5 213 112.5L203 110.5Z",
 "HEAD": "M172 20C186 20.3 198 22 205.5 27L205 30.5C197 26.5 186 24.6 172 24Z",
 "DRL": "M173 21.6C186 21.9 197 23.6 204.6 28.2",
 "TIRES": [
  [
   205,
   46,
   12,
   40
  ],
  [
   206,
   230,
   12,
   42
  ]
 ],
 "FENDER": "M206.5 236C208.5 258 208 284 204 300",
 "ICON": {
  "help": "M10,19H13V22H10V19M12,2C17.35,2.22 19.68,7.62 16.5,11.67C15.67,12.67 14.33,13.33 13.67,14.17C13,15 13,16 13,17H10C10,15.33 10,13.92 10.67,12.92C11.33,11.92 12.67,11.33 13.5,10.67C15.92,8.43 15.32,5.26 12,5A3,3 0 0,0 9,8H6A6,6 0 0,1 12,2Z",
  "lock": "M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z",
  "unlock": "M18,1C15.24,1 13,3.24 13,6V8H4A2,2 0 0,0 2,10V20A2,2 0 0,0 4,22H16A2,2 0 0,0 18,20V10A2,2 0 0,0 16,8H15V6A3,3 0 0,1 18,3A3,3 0 0,1 21,6V8H23V6C23,3.24 20.76,1 18,1M10,13A2,2 0 0,1 12,15C12,16.11 11.11,17 10,17A2,2 0 0,1 8,15A2,2 0 0,1 10,13Z",
  "open": "M11 3H13V15H11ZM11 18H13V21H11Z",
  "down": "M11 3H13V15.2L17.6 10.6L19 12L12 19L5 12L6.4 10.6L11 15.2Z",
  "check": "M9 16.2L4.8 12L3.4 13.4L9 19L21 7L19.6 5.6Z"
 }
};
const RINGS =
  '<svg viewBox="0 0 100 32" fill="none" stroke="currentColor" stroke-width="3"><circle cx="20" cy="16" r="12"/><circle cx="40" cy="16" r="12"/><circle cx="60" cy="16" r="12"/><circle cx="80" cy="16" r="12"/></svg>';

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class AudiConnectCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._ui = { popup: null, tab: "doors", open: {} };
    this._sig = "";
    this._byDevice = null;
    this._entRef = null;
    this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card><div id="root"></div></ha-card>`;
    this._root = this.shadowRoot.getElementById("root");
    this._root.addEventListener("click", (e) => this._onClick(e));
    this._root.addEventListener("change", (e) => this._onChange(e));
    this._root.addEventListener("input", (e) => this._onInput(e));
    this._root.addEventListener("pointerdown", (e) => this._pressStart(e));
    this._root.addEventListener("pointermove", (e) => this._pressMove(e));
    for (const type of ["pointerup", "pointercancel"]) {
      this._root.addEventListener(type, () => this._pressEnd());
    }
    // A long press on a phone would otherwise open the browser's own menu.
    this._root.addEventListener("contextmenu", (e) => {
      if (e.target.closest?.("[data-press]")) e.preventDefault();
    });
    this._root.addEventListener("keydown", (e) => this._onKey(e));
    this._root.addEventListener("toggle", (e) => {
      const d = e.target.closest?.("details[data-id]");
      if (d) this._ui.open[d.dataset.id] = d.open;
    }, true);
  }

  static getConfigElement() {
    return document.createElement("audi-connect-card-editor");
  }

  static getStubConfig(hass) {
    const dev = AudiConnectCard._firstDevice(hass);
    return dev ? { device_id: dev } : {};
  }

  static _firstDevice(hass) {
    for (const e of Object.values(hass?.entities || {})) {
      if (e.platform === DOMAIN && e.device_id) return e.device_id;
    }
    return undefined;
  }

  setConfig(config) {
    this._config = { show_logo: true, show_trips: true, show_climate: true, show_stats: true, ...config };
    this._sig = "";
    this._update();
  }

  set hass(hass) {
    this._hass = hass;
    this._settleDraft();
    this._update();
  }

  // The sent temperature is no longer a draft once the car reports it.
  _settleDraft() {
    const draft = this._ui.tempDraft;
    if (draft === null || draft === undefined) return;
    const reported = Number(this._s("climatisation")?.attributes?.temperature);
    if (reported === draft) {
      clearTimeout(this._draftTimer);
      this._ui.tempDraft = null;
    }
  }

  disconnectedCallback() {
    for (const t of [this._pressTimer, this._errTimer, this._tempTimer, this._draftTimer, ...Object.values(this._waitTimers || {})]) clearTimeout(t);
    this._pressTimer = null;
    this._waitTimers = {};
  }

  getCardSize() {
    return 12;
  }

  // ---------------------------------------------------------------- entity lookup
  _t(key, vars) {
    const lang = (this._hass?.language || "en").slice(0, 2);
    let s = (TEXT[lang] || TEXT.en)[key] ?? TEXT.en[key] ?? key;
    for (const [k, v] of Object.entries(vars || {})) s = s.replace(`{${k}}`, v);
    return s;
  }

  _deviceId() {
    return this._config?.device_id || AudiConnectCard._firstDevice(this._hass);
  }

  _index() {
    const ents = this._hass?.entities;
    if (!ents) return {};
    if (this._entRef !== ents) {
      this._entRef = ents;
      this._byDevice = {};
      for (const e of Object.values(ents)) {
        if (e.platform !== DOMAIN || !e.device_id || !e.translation_key) continue;
        const m = (this._byDevice[e.device_id] ||= {});
        const domain = e.entity_id.split(".")[0];
        // A select and a sensor can share a translation key, so each one is also
        // stored as "<domain>.<key>". The first one wins; a hidden duplicate must
        // not shadow a visible one.
        for (const key of [e.translation_key, `${domain}.${e.translation_key}`]) {
          if (!m[key] || (m[key].hidden && !e.hidden)) m[key] = e;
        }
      }
    }
    return this._byDevice[this._deviceId()] || {};
  }

  _id(tk) {
    return this._index()[tk]?.entity_id;
  }

  _s(tk) {
    const id = this._id(tk);
    return id ? this._hass.states[id] : undefined;
  }

  _on(tk) {
    return this._s(tk)?.state === "on";
  }

  _has(tk) {
    const s = this._s(tk);
    return !!s;
  }

  _known(tk) {
    const s = this._s(tk);
    return !!s && !NO_VALUE.has(s.state);
  }

  _num(tk) {
    const s = this._s(tk);
    if (!s) return undefined;
    const n = parseFloat(s.state);
    return Number.isFinite(n) ? n : undefined;
  }

  _fmt(tk, fallbackUnit) {
    const s = this._s(tk);
    if (!s || s.state === "unavailable" || s.state === "unknown") return "–";
    if (this._hass.formatEntityState) {
      try {
        return this._hass.formatEntityState(s);
      } catch (_) {
        /* fall through */
      }
    }
    const unit = s.attributes.unit_of_measurement || fallbackUnit || "";
    return unit ? `${s.state} ${unit}` : s.state;
  }

  _ago(iso) {
    const t = Date.parse(iso);
    if (!Number.isFinite(t)) return "";
    const m = Math.max(0, Math.round((Date.now() - t) / 60000));
    if (m < 1) return this._t("now");
    let str;
    if (m < 60) str = `${m} ${this._t("min")}`;
    else if (m < 1440) str = `${Math.round(m / 60)} ${this._t("h")}`;
    else str = `${Math.round(m / 1440)} ${this._t("d")}`;
    return this._t("ago", { t: str });
  }

  _since(iso) {
    const t = Date.parse(iso);
    if (!Number.isFinite(t)) return "–";
    const m = Math.max(0, Math.round((Date.now() - t) / 60000));
    if (m < 60) return `${m} ${this._t("min")}`;
    if (m < 1440) return `${Math.round(m / 60)} ${this._t("h")}`;
    return `${Math.round(m / 1440)} ${this._t("d")}`;
  }

  // ---------------------------------------------------------------- derived state
  _doorState(k) {
    // "closed" is only trusted when the sensor says so; unavailable counts as closed-unknown.
    const open = this._on(DOOR_KEYS[k]);
    let locked = true;
    let unk = false;
    if (k === "trunk" && this._has("trunk_unlocked")) {
      unk = !this._known("trunk_unlocked");
      locked = !this._on("trunk_unlocked");
    } else if (k !== "hood") {
      const ls = this._lockState();
      unk = ls === "unknown";
      locked = ls === "locked";
    }
    return { open, locked, unk };
  }

  _lockState() {
    const s = this._s("door_lock");
    if (s && (s.state === "locked" || s.state === "unlocked")) return s.state;
    // unavailable/unknown is not "locked": claiming it would show a possibly open car as secure.
    if (this._known("any_door_unlocked")) return this._on("any_door_unlocked") ? "unlocked" : "locked";
    return "unknown";
  }

  _openLists() {
    const doors = Object.keys(DOOR_KEYS).filter((k) => this._on(DOOR_KEYS[k]));
    const wins = Object.keys(WINDOW_KEYS).filter((k) => this._on(WINDOW_KEYS[k]));
    if (!doors.length && this._on("any_door_open")) doors.push("fl");
    if (!wins.length && this._on("any_window_open")) wins.push("fl");
    return { doors, wins };
  }

  _isCharging() {
    const st = (this._s("charging_state")?.state || "").toLowerCase();
    return st === "charging" || (this._num("charging_power") || 0) > 0;
  }

  // ---------------------------------------------------------------- rendering
  _watched() {
    const idx = this._index();
    return Object.values(idx).map((e) => e.entity_id);
  }

  _update() {
    if (!this._hass || !this._config) return;
    const idx = this._index();
    const sig =
      JSON.stringify(this._ui) + this._hass.language + this._deviceId() +
      Object.values(idx).map((e) => {
        const s = this._hass.states[e.entity_id];
        return s ? s.state + "|" + s.last_updated : "-";
      }).join(",") + JSON.stringify(this._config) + Math.floor(Date.now() / 60000);
    if (sig === this._sig) return;
    // Do not replace the DOM under a slider being dragged or a dropdown being
    // used: that would cancel the gesture. The next update renders instead.
    const focused = this.shadowRoot.activeElement;
    if (focused && (focused.tagName === "INPUT" || focused.tagName === "SELECT")) return;
    // Keep keyboard focus on the same control across the re-render.
    const popup = !!this._ui.popup;
    const sameMode = popup === !!this._lastPopup;
    const index = focused && sameMode ? [...this._root.querySelectorAll(FOCUSABLE)].indexOf(focused) : -1;
    this._sig = sig;
    this._root.innerHTML = this._render();
    this._a11y();
    this._lastPopup = popup;
    if (popup && !sameMode) this._root.querySelector(".x")?.focus();
    else if (!popup && !sameMode && focused) {
      // Closing the dialog returns focus to the button that opened it.
      this._root.querySelector(`[data-act="popup"][data-tab="${this._ui.tab}"]`)?.focus();
    } else if (index >= 0) this._root.querySelectorAll(FOCUSABLE)[index]?.focus();
  }

  // Clickable divs, spans and SVG shapes become buttons for keyboards and screen readers.
  _a11y() {
    for (const el of this._root.querySelectorAll("[data-more],[data-act],[data-toggle]")) {
      if (el.matches(NATIVE) || el.dataset.act === "close-bg") continue;
      // A zone or row for an entity the car does not have: nothing to open, so not a button.
      if (el.hasAttribute("data-more") && !el.dataset.more && !el.dataset.act && !el.dataset.toggle) continue;
      el.setAttribute("role", "button");
      el.setAttribute("tabindex", "0");
      if (!el.hasAttribute("aria-label") && !(el.textContent || "").trim()) {
        const st = this._hass?.states[el.dataset.more];
        const name = st?.attributes?.friendly_name;
        if (name) el.setAttribute("aria-label", name);
      }
    }
    const dlg = this._root.querySelector(".dlg");
    if (dlg) {
      dlg.setAttribute("role", "dialog");
      dlg.setAttribute("aria-modal", "true");
      dlg.setAttribute("aria-label", this._t("doors") + " / " + this._t("windows"));
    }
  }

  _onKey(e) {
    if (e.key === "Escape" && this._ui.popup) {
      e.preventDefault();
      this._ui.popup = null; this._sig = ""; this._update();
      return;
    }
    if ((e.key === "Enter" || e.key === " ") && e.target.getAttribute?.("role") === "button" && !e.target.matches(NATIVE)) {
      e.preventDefault();
      e.target.dispatchEvent(new MouseEvent("click", { bubbles: true, composed: true }));
      return;
    }
    if (e.key === "Tab" && this._ui.popup) {
      const items = [...(this._root.querySelector(".dlg")?.querySelectorAll(FOCUSABLE) || [])];
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      const active = this.shadowRoot.activeElement;
      if (e.shiftKey && (active === first || !items.includes(active))) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && (active === last || !items.includes(active))) { e.preventDefault(); first.focus(); }
    }
  }

  _render() {
    const dev = this._deviceId();
    if (!dev || !Object.keys(this._index()).length) {
      return `<div class="empty">${esc(this._t("no_vehicle"))}</div>`;
    }
    const c = this._config;
    const name = c.name || this._hass.devices?.[dev]?.name_by_user || this._hass.devices?.[dev]?.name || "Audi";
    const parts = [];

    const canRefresh = !!this._id("refresh_vehicle_data");
    const busy = this._ui.refreshing ? " busy" : "";
    // A tap opens the integration; holding it refreshes the vehicle data.
    const act = ` data-act="open-integration"${canRefresh ? " data-press" : ""}`;
    parts.push(`<div class="title tap${busy}"${act}>${c.icon ? `<ha-icon icon="${esc(c.icon)}"></ha-icon>` : c.show_logo ? RINGS : ""}<span>${esc(name)}</span></div>`);
    const photo = c.image_local || c.image;
    if (photo) parts.push(`<img class="photo tap${busy}"${act} src="${esc(photo)}" alt="">`);
    if (!this._ui.popup) parts.push(this._renderError());
    parts.push(this._renderInfoRow());
    parts.push(this._renderIcons());
    parts.push(this._renderEnergy());
    if (c.show_trips) parts.push(this._renderTrips());
    if (c.show_stats) parts.push(this._renderStats());
    if (c.show_climate && this._has("climatisation")) parts.push(this._renderClimate());
    if (this._ui.popup) parts.push(this._renderPopup());
    return parts.join("");
  }

  // A rejected action (Audi did not answer, the car is out of reach) shows here for a few seconds.
  _renderError() {
    const e = this._ui.error;
    if (!e) return "";
    const title = e.action ? this._t("failed", { a: e.action }) : this._t("call_failed");
    return `<div class="note bad err" role="alert"><ha-icon icon="mdi:alert-circle-outline"></ha-icon><span>${esc(title)}${e.text ? `<span class="sub">${esc(e.text)}</span>` : ""}</span></div>`;
  }

  _renderInfoRow() {
    const tracker = this._s("position");
    const loc = tracker ? (this._hass.formatEntityState ? this._hass.formatEntityState(tracker) : tracker.state) : "";
    const upd = this._s("last_update_time");
    const fresh = this._s("vehicle_data_freshness")?.state;
    const stale = fresh === "stale" || fresh === "delayed";
    const mid = upd && upd.state !== "unavailable" && upd.state !== "unknown"
      ? `<span class="mid ${stale ? "warn" : ""}" data-more="${esc(upd.entity_id)}" ${stale ? `title="${esc(this._t("stale"))}"` : ""}>${stale ? '<ha-icon icon="mdi:alert-outline"></ha-icon>' : ""}${esc(this._ago(upd.state))}</span>`
      : "";
    return `<div class="row">
      <span class="item" ${tracker ? `data-more="${esc(tracker.entity_id)}"` : ""}><ha-icon icon="mdi:map-marker"></ha-icon>${esc(loc)}</span>
      ${mid}
      <span class="item" ${this._id("mileage") ? `data-more="${esc(this._id("mileage"))}"` : ""}><ha-icon icon="mdi:counter"></ha-icon>${esc(this._fmt("mileage", "km"))}</span>
    </div>`;
  }

  _renderIcons() {
    const { doors, wins } = this._openLists();
    const lock = this._lockState();
    const unlockedIdle = lock === "unlocked" && !doors.length;
    let lockCls, lockIcon, lockTxt;
    if (doors.length) { lockCls = ""; lockIcon = "mdi:lock-open-variant"; lockTxt = this._t("not_secured"); }
    else if (unlockedIdle) { lockCls = "warn"; lockIcon = "mdi:lock-open-variant"; lockTxt = this._t("unlocked"); }
    else if (lock === "unknown") { lockCls = ""; lockIcon = "mdi:lock-question"; lockTxt = this._t("lock_unknown"); }
    else { lockCls = "ok"; lockIcon = "mdi:lock"; lockTxt = this._t("locked"); }

    // No sensor reporting at all (a cloud outage, a car without them) must not read as "closed".
    const doorsKnown = Object.values(DOOR_KEYS).some((k) => this._known(k)) || this._known("any_door_open");
    const winsKnown = Object.values(WINDOW_KEYS).some((k) => this._known(k)) || this._known("any_window_open");
    const items = [];
    if (this._has("door_lock") || this._has("any_door_unlocked")) {
      items.push(`<button class="ic ${lockCls}" data-more="${esc(this._id("door_lock") || this._id("any_door_unlocked"))}"><ha-icon icon="${lockIcon}"></ha-icon>${esc(lockTxt)}</button>`);
    }
    items.push(`<button class="ic ${doors.length ? "bad" : doorsKnown ? "ok" : ""}" data-act="popup" data-tab="doors"><ha-icon icon="mdi:car-door"></ha-icon>${esc(doors.length ? this._t("n_open", { n: doors.length }) : doorsKnown ? this._t("doors_closed") : this._t("doors_unknown"))}</button>`);
    items.push(`<button class="ic ${wins.length ? "warn" : winsKnown ? "ok" : ""}" data-act="popup" data-tab="windows"><ha-icon icon="mdi:car-windshield-outline"></ha-icon>${esc(wins.length ? this._t("n_open", { n: wins.length }) : winsKnown ? this._t("windows_closed") : this._t("windows_unknown"))}</button>`);
    if (this._has("plug_state")) {
      const p = this._on("plug_state");
      items.push(`<button class="ic ${p ? "ok" : ""}" data-more="${esc(this._id("plug_state"))}"><ha-icon icon="mdi:power-plug"></ha-icon>${esc(p ? this._t("plugged") : this._t("unplugged"))}</button>`);
    }
    if (this._has("parking_light")) {
      const l = this._on("parking_light");
      items.push(`<button class="ic ${l ? "warn" : ""}" data-more="${esc(this._id("parking_light"))}"><ha-icon icon="mdi:lightbulb-on-outline"></ha-icon>${esc(l ? this._t("light_on") : this._t("light_off"))}</button>`);
    }
    const warnCount = this._num("warning_light_count") || 0;
    if (this._on("warning_lights") || warnCount > 0) {
      items.push(`<button class="ic warn" data-more="${esc(this._id("warning_light_count") || this._id("warning_lights"))}"><ha-icon icon="mdi:alert-outline"></ha-icon>${esc(this._t("warning"))}${warnCount ? " · " + warnCount : ""}</button>`);
    }
    return `<div class="icons">${items.join("")}</div>`;
  }

  _renderEnergy() {
    const useTank = !this._known("state_of_charge") && this._known("tank_level");
    const key = useTank ? "tank_level" : "state_of_charge";
    const soc = this._num(key);
    const rangeKey = this._known("range") ? "range" : "primary_engine_range";
    const target = this._num("target_state_of_charge");
    const tState = this._s("target_state_of_charge");
    const charging = this._isCharging();
    const pct = soc === undefined ? 0 : Math.max(0, Math.min(100, soc));
    // Charging is what the car says it is doing; the target is only where the mark sits.
    const active = charging;

    let slider = "";
    if (tState && target !== undefined && !useTank) {
      const n = (v, d) => (Number.isFinite(Number(v)) ? Number(v) : d);
      const min = n(tState.attributes.min, 20), max = n(tState.attributes.max, 100), step = n(tState.attributes.step, 5);
      slider = `<input type="range" data-slider="target" min="${min}" max="${max}" step="${step}" value="${target}" aria-label="${esc(this._t("charge_target"))}">`;
    }
    const band = active ? this._renderChargeBand() : this._renderChargeNotice();
    return `<div class="sep"></div><div class="energy">
      <div class="barwrap" ${this._id(key) ? `data-more="${esc(this._id(key))}"` : ""}>
        <div class="bar ${active ? "charging" : ""}" style="width:${pct}%;background-size:${(10000 / Math.max(pct, 1)).toFixed(1)}% 100%"><span>${soc === undefined ? "–" : Math.round(soc) + " %"}</span></div>
        ${target !== undefined && !useTank ? `<div class="mark" data-live="mark" style="left:calc(${target}% - 1px)"></div>` : ""}
      </div>
      ${band}
      <div class="eline">
        <span ${tState && !useTank ? `data-more="${esc(tState.entity_id)}"` : ""}>${target !== undefined && !useTank ? `${esc(this._t("charge_target"))} <b data-live="target">${Math.round(target)} %</b>` : ""}</span>
        <span ${this._id(rangeKey) ? `data-more="${esc(this._id(rangeKey))}"` : ""}>${esc(this._t("range"))} <b>${esc(this._fmt(rangeKey, "km"))}</b></span>
      </div>
      ${slider}
    </div>`;
  }

  _temp(v) {
    const n = Number(v);
    if (!Number.isFinite(n)) return String(v);
    return `${n.toLocaleString(this._hass?.language || undefined, { minimumFractionDigits: n % 1 ? 1 : 0, maximumFractionDigits: 1 })} ${this._hass?.config?.unit_system?.temperature || "°C"}`;
  }

  // Power, range gained per hour and when it is done: only while charging, and only what the car reports.
  _renderChargeBand() {
    const cells = [];
    if (this._known("charging_power")) {
      cells.push(`<div class="cell" data-more="${esc(this._id("charging_power"))}"><ha-icon class="ci pulse" icon="mdi:flash"></ha-icon><span class="v">${esc(this._fmt("charging_power", "kW"))}</span><span class="k">${esc(this._t("power"))}</span></div>`);
    }
    const rate = this._num("actual_charge_rate");
    if (this._known("actual_charge_rate") && rate !== undefined && rate > 0) {
      const unit = this._s("actual_charge_rate").attributes.unit_of_measurement || "km/h";
      const shown = rate.toLocaleString(this._hass.language || undefined, { maximumFractionDigits: 0 });
      cells.push(`<div class="cell" data-more="${esc(this._id("actual_charge_rate"))}"><ha-icon class="ci" icon="mdi:map-marker-distance"></ha-icon><span class="v">+${esc(shown)} ${esc(unit)}</span><span class="k">${esc(this._t("rate"))}</span></div>`);
    }
    const done = this._known("charging_complete_time") ? this._timeOf(this._s("charging_complete_time").state) : "";
    const day = done ? this._dayOf(this._s("charging_complete_time").state) : "";
    const mins = this._known("remaining_charging_time") ? this._num("remaining_charging_time") : undefined;
    const left = mins !== undefined && mins > 0 ? this._t("in", { t: this._dur(mins) }) : "";
    if (done || left) {
      const id = this._id(done ? "charging_complete_time" : "remaining_charging_time");
      cells.push(`<div class="cell" data-more="${esc(id)}"><ha-icon class="ci" icon="mdi:clock-check-outline"></ha-icon><span class="v">${esc(done || left)}</span><span class="k">${esc(this._t("charging_done") + (day ? " " + day : ""))}</span>${done && left ? `<span class="s">${esc(left)}</span>` : ""}</div>`);
    }
    return cells.length ? `<div class="band">${cells.join("")}</div>` : "";
  }

  // The car's own words for what the charging is doing, shown only when it is not plain charging
  // or plain "not plugged in", which the plug icon already says.
  _renderChargeNotice() {
    const s = this._s("charging_state");
    if (!s || NO_VALUE.has(s.state)) return "";
    const state = s.state.toLowerCase();
    const plugged = this._on("plug_state");
    let tone = "", icon = "mdi:ev-plug-type2", text = "";
    if (state === "charging" || state === "notreadyforcharging" || state === "off") return "";
    if (state === "readyforcharging") {
      if (!plugged) return "";
      text = this._t("charge_waiting");
    } else if (/error|fault|fail/.test(state)) {
      tone = "bad"; icon = "mdi:alert-circle-outline"; text = this._t("charge_error");
    } else if (state.startsWith("chargepurposereached")) {
      if (!plugged) return "";
      icon = "mdi:battery-check"; text = this._t("charge_reached");
    } else if (state.includes("conservation")) {
      icon = "mdi:battery-heart-variant"; text = this._t("charge_conservation");
    } else {
      // A value this card does not know: say it plainly rather than hide it.
      const words = s.state.replace(/([a-z])([A-Z])/g, "$1 $2");
      text = words.charAt(0).toUpperCase() + words.slice(1);
    }
    const spoken = s.state.replace(/([a-z])([A-Z])/g, "$1 $2");
    const detail = tone === "bad" && !/^error$/i.test(s.state) ? `<span class="nd">${esc(spoken.charAt(0).toUpperCase() + spoken.slice(1))}</span>` : "";
    return `<div class="note ${tone}" data-more="${esc(s.entity_id)}"><ha-icon icon="${icon}"></ha-icon><span>${esc(text)}</span>${detail}</div>`;
  }

  _dur(minutes) {
    minutes = Math.round(minutes);
    const h = Math.floor(minutes / 60), m = minutes % 60;
    return h ? (m ? `${h} ${this._t("h")} ${m} ${this._t("min")}` : `${h} ${this._t("h")}`) : `${m} ${this._t("min")}`;
  }

  _now() {
    return new Date();
  }

  // The language for dates and times: Home Assistant's own, unless the card has no texts for it,
  // so a label never reads "done demain".
  _locale() {
    const lang = this._hass?.language;
    return lang && TEXT[lang.slice(0, 2)] ? lang : "en";
  }

  // "" for today, otherwise "tomorrow" or the weekday, so a finish time after midnight is not ambiguous.
  _dayOf(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return "";
    const lang = this._locale();
    const start = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
    const diff = Math.round((start(d) - start(this._now())) / 86400000);
    if (diff <= 0) return "";
    if (diff === 1) return new Intl.RelativeTimeFormat(lang, { numeric: "auto" }).format(1, "day");
    return d.toLocaleDateString(lang, { weekday: "short" });
  }

  _timeOf(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return "";
    return d.toLocaleTimeString(this._locale(), { hour: "2-digit", minute: "2-digit" });
  }

  _renderTrips() {
    const block = (id, title, icon, prefix) => {
      if (!this._has(`${prefix}_distance`)) return "";
      const f = (k, u) => this._fmt(`${prefix}_${k}`, u);
      const num = (k) => this._known(`${prefix}_${k}`) ? this._s(`${prefix}_${k}`).state : "–";
      const unit = (k, d) => this._s(`${prefix}_${k}`)?.attributes.unit_of_measurement || d;
      const sum = `${f("distance", "km")} · ${f("consumption", "kWh/100 km")}`;
      const cell = (ic, k, label, d) => `<div class="tap" data-more="${esc(this._id(`${prefix}_${k}`))}"><ha-icon icon="${ic}"></ha-icon><span class="v">${esc(this._known(`${prefix}_${k}`) ? this._rounded(`${prefix}_${k}`) : "–")}</span><span class="u">${esc(unit(k, d))}</span><span class="k">${esc(this._t(label))}</span></div>`;
      return `<details data-id="${id}" ${this._ui.open[id] ? "open" : ""}>
        <summary><ha-icon icon="${icon}"></ha-icon><span class="t">${esc(title)}</span><span class="sm">${esc(sum)}</span><ha-icon class="ch" icon="mdi:chevron-down"></ha-icon></summary>
        <div class="trip">
          ${cell("mdi:map-marker-distance", "distance", "distance", "km")}
          ${cell("mdi:speedometer", "speed", "speed", "km/h")}
          ${cell("mdi:ev-station", "consumption", "consumption", "kWh/100 km")}
          ${cell("mdi:lightning-bolt", "energy", "energy", "kWh")}
        </div></details>`;
    };
    return block("trip-last", this._t("last_trip"), "mdi:history", "last_trip") +
           block("trip-long", this._t("long_term"), "mdi:infinity", "trip_totals");
  }

  _rounded(tk) {
    const n = this._num(tk);
    if (n === undefined) return this._s(tk).state;
    const digits = Math.abs(n) >= 100 ? 0 : 1;
    return n.toLocaleString(this._hass.language || undefined, { maximumFractionDigits: digits });
  }

  _renderStats() {
    const rows = [];
    const add = (icon, label, value, tk) => {
      if (value) rows.push({ icon, label, value, id: this._id(tk) });
    };
    const known = (tk) => this._known(tk);
    const withDays = (tk) => {
      const n = this._num(tk);
      const unit = this._s(tk).attributes.unit_of_measurement;
      return n !== undefined && (!unit || unit === "d") ? `${n} ${this._t("days")}` : this._fmt(tk);
    };

    if (known("secondary_engine_range")) add("mdi:gas-station", this._t("fuel_range"), this._fmt("secondary_engine_range", "km"), "secondary_engine_range");
    if (known("tank_level") && known("state_of_charge")) add("mdi:gauge", this._t("tank"), this._fmt("tank_level"), "tank_level");
    if (known("park_time")) add("mdi:parking", this._t("parked"), this._since(this._s("park_time").state), "park_time");
    if (this._has("parking_brake") && this._known("parking_brake")) add("mdi:car-brake-parking", this._t("parking_brake"), this._on("parking_brake") ? this._t("brake_on") : this._t("brake_off"), "parking_brake");
    if (this._has("warning_lights") && this._known("warning_lights")) {
      const count = this._num("warning_light_count");
      add("mdi:car-light-alert", this._t("warning_lights"), this._on("warning_lights") ? this._t("warning_active") + (count ? ` · ${count}` : "") : this._t("warning_none"), "warning_lights");
    }
    if (known("access_overall_status")) {
      const raw = this._fmt("access_overall_status");
      add("mdi:shield-car", this._t("security"), raw.charAt(0).toUpperCase() + raw.slice(1), "access_overall_status");
    }
    if (known("outdoor_temperature")) add("mdi:thermometer", this._t("outdoor"), this._fmt("outdoor_temperature"), "outdoor_temperature");
    if (known("service_inspection_time")) add("mdi:wrench-clock", this._t("inspection_days"), withDays("service_inspection_time"), "service_inspection_time");
    if (known("service_inspection_distance")) add("mdi:wrench", this._t("inspection_distance"), this._fmt("service_inspection_distance", "km"), "service_inspection_distance");
    if (known("oil_change_time")) add("mdi:oil", this._t("oil_change_days"), withDays("oil_change_time"), "oil_change_time");
    if (known("oil_change_distance")) add("mdi:oil", this._t("oil_change_distance"), this._fmt("oil_change_distance", "km"), "oil_change_distance");
    if (known("oil_level")) add("mdi:oil-level", this._t("oil_level"), this._fmt("oil_level"), "oil_level");
    if (known("service_adblue_distance")) add("mdi:water-outline", this._t("adblue"), this._fmt("service_adblue_distance", "km"), "service_adblue_distance");
    if (known("charging_type")) add("mdi:ev-plug-type2", this._t("charge_type"), this._fmt("charging_type"), "charging_type");
    if (known("max_charge_current")) add("mdi:current-ac", this._t("max_current"), this._fmt("max_charge_current"), "max_charge_current");
    const canRefresh = !!this._id("refresh_vehicle_data");
    if (!rows.length && !canRefresh) return "";

    const sum = known("park_time") ? `${this._t("parked")} ${this._since(this._s("park_time").state)}` : "";
    const refresh = canRefresh
      ? `<button class="pill big${this._ui.refreshing ? " busy" : ""}" data-act="refresh"><ha-icon icon="mdi:refresh"></ha-icon>${esc(this._t("refresh_data"))}</button>`
      : "";
    return `<details data-id="vehicle" ${this._ui.open.vehicle ? "open" : ""}>
      <summary><ha-icon icon="mdi:car-info"></ha-icon><span class="t">${esc(this._t("vehicle"))}</span><span class="sm">${esc(sum)}</span><ha-icon class="ch" icon="mdi:chevron-down"></ha-icon></summary>
      <div class="facts">${rows.map((r) => `<div class="fact" ${r.id ? `data-more="${esc(r.id)}"` : ""}><ha-icon icon="${r.icon}"></ha-icon><span class="fl">${esc(r.label)}</span><span class="fv">${esc(r.value)}</span></div>`).join("")}</div>
      ${refresh ? `<div class="facts">${refresh}</div>` : ""}
    </details>`;
  }

  _renderClimate() {
    const cl = this._s("climatisation");
    const on = cl.state !== "off" && cl.state !== "unavailable" && cl.state !== "unknown";
    const a = cl.attributes;
    const temp = a.temperature;
    const mode = this._s("select.climatisation_mode");
    const modeOptions = mode?.attributes.options || [];
    const outdoor = this._known("outdoor_temperature") ? ` · ${this._fmt("outdoor_temperature")}` : "";
    // What the car is doing, and how long it keeps doing it.
    const action = { heating: "heating", cooling: "cooling", fan: "ventilating" }[a.hvac_action] || "running";
    let left = "";
    if (on) {
      const n = this._known("remaining_climatisation_time") ? this._num("remaining_climatisation_time") : Number(a.remaining_climatisation_time);
      if (Number.isFinite(n)) left = this._known("remaining_climatisation_time") ? this._fmt("remaining_climatisation_time", "min") : `${n} ${this._t("min")}`;
    }
    const status = on
      ? `<div class="cstatus"><ha-icon icon="mdi:fan"></ha-icon><b>${esc(this._t(action))}</b>${left ? `<span>${esc(this._t("remaining"))} <b>${esc(left)}</b></span>` : ""}</div>`
      : "";
    const seatBtn = (tk, label) => this._has(tk)
      ? `<button class="pill ${this._on(tk) ? "on" : ""}${this._waiting(this._id(tk)) ? " wait" : ""}" data-toggle="${esc(this._id(tk))}"><ha-icon icon="${this._waiting(this._id(tk)) ? "mdi:loading" : "mdi:car-seat-heater"}"></ha-icon>${esc(label)}</button>` : "";
    // Off by default. The single option of earlier versions, show_seats, meant the front zones.
    const cfg = this._config;
    const frontOn = cfg.show_seats_front ?? cfg.show_seats ?? false;
    const rearOn = cfg.show_seats_rear ?? false;
    const frontSeats = frontOn ? seatBtn("climatisation_zone_front_left", this._t("fl")) + seatBtn("climatisation_zone_front_right", this._t("fr")) : "";
    const rearSeats = rearOn ? seatBtn("climatisation_zone_rear_left", this._t("rl")) + seatBtn("climatisation_zone_rear_right", this._t("rr")) : "";
    const seats = [frontSeats, rearSeats].filter(Boolean).map((row) => `<div class="pills" style="grid-template-columns:repeat(2,1fr)">${row}</div>`).join("");
    const id = esc(cl.entity_id);
    const sub = on ? `${this._t(action)}${left ? " · " + this._t("remaining") + " " + left : ""}` : this._t("climate_off") + outdoor;
    const modeRow = mode && modeOptions.length
      ? `<div class="mrow"><span>${esc(this._t("mode"))}</span><select data-select="${esc(mode.entity_id)}" aria-label="${esc(this._t("mode"))}">${modeOptions.map((o) => `<option value="${esc(o)}" ${o === mode.state ? "selected" : ""}>${esc(this._hass.formatEntityState ? this._hass.formatEntityState(mode, o) : o)}</option>`).join("")}</select></div>`
      : "";
    return `<details class="climate" data-id="climate" ${this._ui.open.climate ? "open" : ""}>
      <summary><ha-icon icon="mdi:air-conditioner"></ha-icon><span class="t">${esc(this._t("climate"))}</span><span class="sm">${esc(sub)}</span><ha-icon class="ch" icon="mdi:chevron-down"></ha-icon></summary>
      <div class="cbody">
        ${modeRow}
        ${temp !== undefined && temp !== null ? `<div class="step"><button class="stp" data-step="-1" aria-label="${esc(this._t("temp_down"))}"><ha-icon icon="mdi:minus"></ha-icon></button><b data-live="temp">${esc(this._temp(this._ui.tempDraft ?? temp))}</b><button class="stp" data-step="1" aria-label="${esc(this._t("temp_up"))}"><ha-icon icon="mdi:plus"></ha-icon></button></div>` : ""}
        ${seats}
        <div class="pills">
          ${on
            ? `<button class="pill big${this._waiting("climate-off") ? " wait" : ""}" data-act="climate-off"><ha-icon icon="${this._waiting("climate-off") ? "mdi:loading" : "mdi:stop"}"></ha-icon>${esc(this._t("stop"))}</button>`
            : `<button class="pill big go${this._waiting("climate-on") ? " wait" : ""}" data-act="climate-on"><ha-icon icon="${this._waiting("climate-on") ? "mdi:loading" : "mdi:play"}"></ha-icon>${esc(this._t("start"))}</button>`}
        </div>
        ${status}
      </div>
    </details>`;
  }

  // The car seen from above. Colours come from the theme variables set on .car,
  // so it follows light and dark. The click zones are separate, transparent
  // shapes on top of the drawing.
  _carSvg(tab) {
    const C = CAR;
    const doorsTab = tab === "doors";
    const kindOf = (k) => {
      const st = this._doorState(k);
      return st.open ? "open" : st.unk ? "unk" : st.locked ? "lk" : "ul";
    };
    const COL = {
      open: "var(--error-color)", ul: "var(--warning-color)", lk: "var(--success-color)",
      unk: "var(--secondary-text-color)", win: "var(--warning-color)",
    };
    const MIR = ' transform="matrix(-1 0 0 1 300 0)"';
    const mx = (x) => 300 - x;
    const dim = doorsTab ? "" : ' opacity=".45"';
    const pn = (d, kind) => `<path d="${d}" class="pn ${kind}"${kind === "lk" || kind === "unk" ? ' fill="url(#acbody)"' : ""}/>`;
    const badge = (x, y, kind, icon) =>
      `<g transform="translate(${x} ${y})" style="pointer-events:none">` +
      `<circle r="12.5" cy="1.2" fill="var(--primary-text-color)" opacity=".2" filter="url(#acsoft)"/>` +
      `<circle class="bd ${kind}" r="12" stroke="var(--card-background-color)" stroke-width="1.6"/>` +
      `<path transform="translate(-8.4 -8.4) scale(.7)" fill="#fff" d="${C.ICON[icon]}"/></g>`;
    // thin line from the car's flank to the badge, so it is clear what it belongs to
    const lead = (y, side) => `<path d="M${side === "r" ? 203 : mx(203)} ${y}H${side === "r" ? 217 : mx(217)}" stroke="var(--c-line)" stroke-width="1.2" stroke-linecap="round"/>`;
    const mirror = `<path d="${C.MIRROR}" fill="url(#acbody)" stroke="var(--c-bodyline)" stroke-width=".8"/>`;
    const hood = this._doorState("hood");
    const trunk = this._doorState("trunk");
    const trunkOpen = trunk.open;
    const trunkKind = kindOf("trunk");

    let s = `<svg class="car" viewBox="0 0 300 352"><defs>` +
      `<linearGradient id="acbody" x1="0" x2="1"><stop offset="0" style="stop-color:var(--c-edge)"/><stop offset=".2" style="stop-color:var(--secondary-background-color)"/>` +
      `<stop offset=".5" style="stop-color:var(--c-mid)"/><stop offset=".8" style="stop-color:var(--secondary-background-color)"/><stop offset="1" style="stop-color:var(--c-edge)"/></linearGradient>` +
      `<linearGradient id="acglass" x1="0" y1="0" x2=".35" y2="1"><stop offset="0" style="stop-color:var(--c-gl-a)"/><stop offset=".45" style="stop-color:var(--c-gl-b)"/><stop offset="1" style="stop-color:var(--c-gl-c)"/></linearGradient>` +
      `<linearGradient id="acsheen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--card-background-color);stop-opacity:.55"/><stop offset="1" style="stop-color:var(--card-background-color);stop-opacity:0"/></linearGradient>` +
      `<filter id="acblur" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="5"/></filter>` +
      `<filter id="acsoft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.6"/></filter></defs>`;
    s += '<g transform="translate(150 0) scale(.92 1) translate(-150 0)">';
    s += `<path d="${C.BODY}" transform="translate(150 170) scale(1.04 1.01) translate(-150 -167)" fill="var(--primary-text-color)" opacity=".16" filter="url(#acblur)"/>`;
    const tires = C.TIRES.map(([x, y, w, h]) =>
      `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="4.5" fill="var(--c-cavity)"/>` +
      `<rect x="${x + w - 4}" y="${y + 3}" width="2" height="${h - 6}" rx="1" fill="var(--card-background-color)" opacity=".18"/>`).join("");
    s += `<g>${tires}</g><g${MIR}>${tires}</g>`;
    s += `<path d="${C.BODY}" fill="url(#acbody)" stroke="var(--c-bodyline)" stroke-width="1"/>`;
    s += `<path d="M136 26C135 46 135.5 70 137 86M164 26C165 46 164.5 70 163 86" fill="none" stroke="var(--c-line)" stroke-width=".6"/>`;
    // hood
    if (hood.open) {
      s += `<g${dim}><path d="${C.HOOD}" fill="var(--c-cavity)"/><rect x="128" y="34" width="44" height="22" rx="5" fill="var(--c-engine)"/>` +
        `<g transform="translate(0 90) scale(1 .42) translate(0 -90)">${pn(C.HOOD, "open")}</g></g>`;
    } else {
      s += `<g${dim}><path d="${C.HOOD}" fill="url(#acbody)" stroke="var(--c-line)" stroke-width=".8"/></g>`;
    }
    for (const tf of ["", MIR]) {
      s += `<g${tf}><path d="${C.HEAD}" fill="var(--c-head)" stroke="var(--c-line)" stroke-width=".6"/>` +
        `<path d="${C.DRL}" fill="none" stroke="var(--c-drl)" stroke-width="1.1" stroke-linecap="round"/>` +
        `<path d="${C.FENDER}" fill="none" stroke="var(--c-line)" stroke-width=".8"/></g>`;
    }
    s += `<path d="${C.BUMPF} ${C.BUMPR}" fill="none" stroke="var(--c-line)" stroke-width=".8"/>`;
    // greenhouse
    s += `<path d="${C.GREEN}" fill="var(--c-trim)"/><path d="${C.WIND}" fill="url(#acglass)"/>`;
    if (!trunkOpen) s += `<path d="${C.REARW}" fill="url(#acglass)"/>`;
    s += `<path d="${C.ROOF}" fill="url(#acbody)" stroke="var(--c-line)" stroke-width=".8"/><path d="${C.PANO}" fill="url(#acglass)"/>`;
    s += `<path d="M126 154C140 152 160 152 174 154L171 176C157 174 143 174 129 176Z" fill="url(#acsheen)" opacity=".5"/>` +
      `<path d="M116 99C134 98 166 98 184 99L180 112C161 110 139 110 120 112Z" fill="url(#acsheen)" opacity=".55"/>`;
    if (!trunkOpen) s += `<path d="M108 282C125 285.5 175 285.5 192 282" fill="none" stroke="var(--c-line)" stroke-width=".8"/>`;
    // tailgate
    if (trunkOpen) {
      s += `<g${dim}><path d="${C.REARW}" fill="var(--c-cavity)"/><path d="${C.TAILG}" fill="var(--c-cavity)" stroke="var(--c-cavity)" stroke-width="2"/>` +
        `<rect x="124" y="250" width="52" height="46" rx="6" fill="var(--c-engine)"/>` +
        `<g transform="translate(0 226) scale(1 .3) translate(0 -226)"><path d="${C.REARW}" fill="url(#acglass)"/>${pn(C.TAILG, "open")}</g></g>`;
    } else {
      s += `<g${dim}>${pn(C.TAILG, trunkKind)}<path d="${C.TAILL}" fill="var(--c-tail)"/></g>`;
    }
    // doors and windows, right side drawn once and mirrored for the left
    let opened = "";
    let badges = "";
    for (const side of ["r", "l"]) {
      const tf = side === "l" ? MIR : "";
      let closed = "";
      let swung = "";
      for (const pos of ["f", "r"]) {
        const key = pos + side;
        const kind = kindOf(key);
        const wopen = this._on(WINDOW_KEYS[key]);
        const [hx, hy] = C.HINGE[pos];
        const handle = C.HANDLE[pos];
        const panel = `<g${dim}>${pn(C.DOOR[pos], kind)}<rect x="${handle[0]}" y="${handle[1]}" width="1.6" height="9" rx=".8" fill="var(--c-line)"/></g>`;
        if (kind === "open") {
          closed += `<path d="${C.DOOR[pos]}" fill="var(--c-cavity)"/><path d="${C.WIN[pos]}" fill="var(--c-cavity)"/>`;
          swung += `<g transform="rotate(-38 ${hx} ${hy})"${doorsTab ? "" : ' opacity=".4"'}>` +
            `<path d="${C.DOOR[pos]}" transform="translate(2 2.5)" fill="var(--primary-text-color)" opacity=".25" filter="url(#acsoft)"/>` +
            `<path d="${C.WIN[pos]}" fill="var(--c-trim)"/>${panel}${pos === "f" ? mirror : ""}</g>`;
        } else {
          closed += wopen
            ? `<path d="${C.WIN[pos]}" class="wn open" stroke-width="${doorsTab ? ".9" : "1.2"}"/>`
            : `<path d="${C.WIN[pos]}" fill="url(#acglass)"/>`;
          closed += panel;
          if (pos === "f") closed += mirror;
        }
        if (doorsTab) {
          if (kind === "open") badges += badge(side === "r" ? 268 : mx(268), C.DOOR_CY[pos] + 8, "open", "open");
          else badges += lead(C.DOOR_CY[pos], side) + badge(side === "r" ? 229 : mx(229), C.DOOR_CY[pos], kind, kind === "lk" ? "lock" : kind === "unk" ? "help" : "unlock");
        } else {
          badges += lead(C.DOOR_CY[pos], side) + badge(side === "r" ? 229 : mx(229), C.DOOR_CY[pos], wopen ? "win" : "lk", wopen ? "down" : "check");
        }
      }
      s += `<g${tf}>${closed}</g>`;
      opened += `<g${tf}>${swung}</g>`;
    }
    s += opened;
    // click zones: transparent shapes carrying the entity to open
    const zone = (cls, id, d, tf = "") => `<path class="hit ${cls}" data-more="${esc(id)}" d="${d}"${tf}/>`;
    const DZ = { f: "M199 97H250V171H199Z", r: "M196 173H250V244H196Z" };
    const WZ = { f: "M189 102H201V170H189Z", r: "M189 172H201V234H189Z" };
    let hits = "";
    for (const pos of ["f", "r"]) {
      hits += zone("seg", this._id(DOOR_KEYS[pos + "r"]), DZ[pos]) + zone("seg", this._id(DOOR_KEYS[pos + "l"]), DZ[pos], MIR);
      hits += zone("gl", this._id(WINDOW_KEYS[pos + "r"]), WZ[pos]) + zone("gl", this._id(WINDOW_KEYS[pos + "l"]), WZ[pos], MIR);
    }
    hits += zone("seg", this._id(DOOR_KEYS.hood), "M96 8H204V92H96Z") + zone("seg", this._id(DOOR_KEYS.trunk), "M96 236H204V342H96Z");
    s += `<g fill="transparent">${hits}</g></g>`;
    if (doorsTab) {
      s += trunkOpen ? badge(150, 337, "open", "open") : badge(150, 337, trunkKind, trunkKind === "lk" ? "lock" : trunkKind === "unk" ? "help" : "unlock");
      if (hood.open) s += badge(150, 52, "open", "open");
    }
    return s + badges + "</svg>";
  }

  _renderPopup() {
    const tab = this._ui.tab;
    const { doors, wins } = this._openLists();
    const lock = this._lockState();
    const n = doors.length + wins.length;
    let sum, cls;
    if (n) { sum = n === 1 ? this._t("one_opening") : this._t("n_openings", { n }); cls = "c-bad"; }
    else if (lock === "unlocked") { sum = this._t("all_closed_unlocked"); cls = "c-warn"; }
    else if (lock === "unknown") { sum = this._t("all_closed_unknown"); cls = "c-mute"; }
    else { sum = this._t("all_closed"); cls = "c-ok"; }

    const svg = this._carSvg(tab);

    let list = "";
    if (tab === "doors") {
      for (const k of ["fl", "fr", "rl", "rr", "hood", "trunk"]) {
        const st = this._doorState(k);
        const txt = st.open ? this._t("open") : k === "hood" || st.unk ? this._t("closed") : st.locked ? this._t("closed_locked") : this._t("closed_unlocked");
        const c = st.open ? "c-bad" : k === "hood" || st.unk || st.locked ? "c-mute" : "c-warn";
        list += `<div class="li" data-more="${esc(this._id(DOOR_KEYS[k]))}"><span>${esc(this._t(k))}</span><span class="${c}">${esc(txt)}</span></div>`;
      }
    } else {
      for (const k of ["fl", "fr", "rl", "rr"]) {
        const open = this._on(WINDOW_KEYS[k]);
        const pct = this._num(WINDOW_PCT[k]);
        const txt = open ? this._t("open") + (pct !== undefined && pct > 0 ? ` · ${Math.round(pct)} %` : "") : this._t("closed");
        list += `<div class="li" data-more="${esc(this._id(WINDOW_KEYS[k]))}"><span>${esc(this._t(k))}</span><span class="${open ? "c-warn" : "c-mute"}">${esc(txt)}</span></div>`;
      }
    }
    const lockBtn = tab === "doors" && lock !== "unknown" && this._has("door_lock")
      ? `<button class="pill big" data-act="lock"><ha-icon icon="${lock === "locked" ? "mdi:lock-open-variant" : "mdi:lock"}"></ha-icon>${esc(lock === "locked" ? this._t("unlock") : this._t("lock"))}</button>` : "";
    return `<div class="ov" data-act="close-bg"><div class="dlg">
      <div class="dh"><div><b>${esc(this._t("doors"))} / ${esc(this._t("windows"))}</b><span class="${cls}">${esc(sum)}</span></div>
      <button class="x" data-act="close" aria-label="${esc(this._t("close"))}"><ha-icon icon="mdi:close"></ha-icon></button></div>
      ${this._renderError()}
      <div class="tabs"><button class="tab ${tab === "doors" ? "on" : ""}" data-tab-set="doors">${esc(this._t("doors"))}</button><button class="tab ${tab === "windows" ? "on" : ""}" data-tab-set="windows">${esc(this._t("windows"))}</button></div>
      ${svg}${list}${lockBtn}
    </div></div>`;
  }

  // ---------------------------------------------------------------- actions
  _moreInfo(entityId) {
    if (!entityId) return;
    this.dispatchEvent(new CustomEvent("hass-more-info", { bubbles: true, composed: true, detail: { entityId } }));
  }

  _pressStart(e) {
    if (!e.target.closest?.("[data-press]")) return;
    this._pressAt = { x: e.clientX, y: e.clientY };
    clearTimeout(this._pressTimer);
    this._pressTimer = setTimeout(() => {
      this._pressTimer = null;
      this._longPressed = true;
      if (navigator.vibrate) navigator.vibrate(30);
      this._refresh();
    }, 600);
  }

  _pressMove(e) {
    // Scrolling or dragging is not a press.
    if (this._pressTimer && this._pressAt && Math.hypot(e.clientX - this._pressAt.x, e.clientY - this._pressAt.y) > 10) {
      this._pressEnd();
    }
  }

  _pressEnd() {
    clearTimeout(this._pressTimer);
    this._pressTimer = null;
    // The click that ends a long press must not also count as a tap.
    if (this._longPressed) setTimeout(() => { this._longPressed = false; }, 350);
  }

  _openIntegration() {
    // The device page is an admin page; anyone else would land on a refusal.
    if (this._hass?.user && this._hass.user.is_admin === false) return;
    const dev = this._deviceId();
    history.pushState(null, "", dev ? `/config/devices/device/${dev}` : `/config/integrations/integration/${DOMAIN}`);
    window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: false } }));
  }

  _onClick(e) {
    if (this._longPressed) { this._longPressed = false; return; }
    const t = e.target;
    const bg = t.closest?.('[data-act="close-bg"]');
    if (bg && t === bg) { this._ui.popup = null; this._sig = ""; this._update(); return; }
    const el = t.closest?.("[data-act],[data-more],[data-toggle],[data-tab-set],[data-step]");
    if (!el || !this._hass) return;
    if (el.dataset.more && t.closest("summary")) e.preventDefault();
    if (el.dataset.step) { this._stepTemp(Number(el.dataset.step)); return; }
    if (el.dataset.tabSet) { this._ui.tab = el.dataset.tabSet; this._sig = ""; this._update(); return; }
    if (el.dataset.toggle) { this._call("homeassistant", "toggle", { entity_id: el.dataset.toggle }, el.dataset.toggle); this._wait(el.dataset.toggle); return; }
    switch (el.dataset.act) {
      case "popup": this._ui.popup = true; this._ui.tab = el.dataset.tab; this._sig = ""; this._update(); return;
      case "close": this._ui.popup = null; this._sig = ""; this._update(); return;
      case "lock": this._toggleLock(); return;
      case "refresh": this._refresh(); return;
      case "open-integration": this._openIntegration(); return;
      case "climate-on": this._call("climate", "turn_on", { entity_id: this._id("climatisation") }, "climate-on"); this._wait("climate-on"); return;
      case "climate-off": this._call("climate", "turn_off", { entity_id: this._id("climatisation") }, "climate-off"); this._wait("climate-off"); return;
      default: break;
    }
    if (el.dataset.more) this._moreInfo(el.dataset.more);
  }

  // Plus/minus change a draft shown at once; the value is sent once the taps stop.
  _stepTemp(dir) {
    const a = this._s("climatisation").attributes;
    const step = Number(a.target_temp_step ?? 0.5);
    const cur = Number(this._ui.tempDraft ?? a.temperature);
    const v = Math.min(Number(a.max_temp ?? 28), Math.max(Number(a.min_temp ?? 16), cur + dir * step));
    this._ui.tempDraft = v;
    const el = this._root.querySelector('[data-live="temp"]');
    if (el) el.textContent = this._temp(v);
    clearTimeout(this._tempTimer);
    this._tempTimer = setTimeout(() => {
      this._call("climate", "set_temperature", { entity_id: this._id("climatisation"), temperature: v });
      // Audi takes minutes to report the new value. Keep showing the sent one until the car's value
      // matches it (_settleDraft) or ninety seconds have passed, so the next tap starts from it.
      clearTimeout(this._draftTimer);
      this._draftTimer = setTimeout(() => { this._ui.tempDraft = null; this._sig = ""; this._update(); }, 90000);
    }, 700);
  }

  // Shows a button as "working" until the car answers (or a few seconds pass).
  _waiting(key) { return !!this._ui.wait?.[key]; }

  _wait(key) {
    (this._ui.wait ||= {})[key] = true;
    this._sig = "";
    this._update();
    // One timer per button, so an earlier click cannot end the wait of a later one.
    this._waitTimers ||= {};
    clearTimeout(this._waitTimers[key]);
    this._waitTimers[key] = setTimeout(() => {
      delete this._waitTimers[key];
      if (this._ui.wait) delete this._ui.wait[key];
      this._sig = "";
      this._update();
    }, 5000);
  }

  // Every action goes through here. A call Home Assistant rejects is shown on the card instead of
  // vanishing after the spinner, and only the state that belongs to that action is reset.
  _call(domain, service, data, waitKey) {
    const kind = `${domain}.${service}`;
    let result;
    try {
      // The fifth argument keeps Home Assistant from also showing its own toast: the card shows the failure.
      result = this._hass.callService(domain, service, data, undefined, false);
    } catch (err) {
      result = Promise.reject(err);
    }
    Promise.resolve(result).catch((err) => this._fail(err, { waitKey, kind }));
  }

  _fail(err, { waitKey, kind } = {}) {
    if (waitKey) {
      clearTimeout(this._waitTimers?.[waitKey]);
      if (this._ui.wait) delete this._ui.wait[waitKey];
    }
    if (kind === "button.press") this._ui.refreshing = false;
    if (kind === "climate.set_temperature") this._ui.tempDraft = null;
    const raw = String((typeof err === "string" ? err : err?.message) ?? "");
    const text = raw.length > 140 ? raw.slice(0, 139) + "…" : raw;
    const named = ACTION_TEXT[kind];
    this._ui.error = { action: named ? this._t(named) : "", text };
    clearTimeout(this._errTimer);
    this._errTimer = setTimeout(() => {
      this._ui.error = null;
      this._sig = "";
      this._update();
    }, 8000);
    // A slider or dropdown that still has focus would keep the card from drawing the note.
    const focused = this.shadowRoot.activeElement;
    if (focused && (focused.tagName === "INPUT" || focused.tagName === "SELECT")) focused.blur();
    this._sig = "";
    this._update();
  }

  _refresh() {
    const id = this._id("refresh_vehicle_data");
    if (!id || this._ui.refreshing) return;
    this._call("button", "press", { entity_id: id });
    // The car takes a while to answer; this only shows that the request went out.
    this._ui.refreshing = true;
    this._sig = "";
    this._update();
    setTimeout(() => {
      this._ui.refreshing = false;
      this._sig = "";
      this._update();
    }, 4000);
  }

  _toggleLock() {
    const id = this._id("door_lock");
    if (!id) { this._moreInfo(this._id("any_door_unlocked")); return; }
    const state = this._lockState();
    if (state === "unknown") return;
    const locked = state === "locked";
    if (!window.confirm(this._t(locked ? "confirm_unlock" : "confirm_lock"))) return;
    this._call("lock", locked ? "unlock" : "lock", { entity_id: id });
  }

  // While a slider is dragged only its readout moves; the value is sent on release.
  _onInput(e) {
    const t = e.target;
    const live = (name) => this._root.querySelector(`[data-live="${name}"]`);
    if (t.dataset.slider === "temp") {
      const el = live("temp");
      if (el) el.textContent = this._temp(t.value);
    } else if (t.dataset.slider === "target") {
      const el = live("target");
      if (el) el.textContent = `${Math.round(Number(t.value))} %`;
      const mark = live("mark");
      if (mark) mark.style.left = `calc(${Number(t.value)}% - 1px)`;
    }
  }

  _onChange(e) {
    const t = e.target;
    if (t.dataset.slider === "target") {
      this._call("number", "set_value", { entity_id: this._id("target_state_of_charge"), value: Number(t.value) });
    } else if (t.dataset.slider === "temp") {
      this._call("climate", "set_temperature", { entity_id: this._id("climatisation"), temperature: Number(t.value) });
    } else if (t.dataset.select) {
      this._call("select", "select_option", { entity_id: t.dataset.select, option: t.value });
    }
  }
}

class AudiConnectCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    for (const form of this._forms || []) form.hass = hass;
    if (first) this._loadImages();
    this._render();
  }

  _t(key) {
    const lang = (this._hass?.language || "en").slice(0, 2);
    return (TEXT[lang] || TEXT.en)[key] ?? key;
  }

  // The pictures in /config/www, offered by the integration (admins only).
  async _loadImages() {
    try {
      this._images = await this._hass.callWS({ type: `${DOMAIN}/list_images` });
    } catch (_) {
      this._images = [];
    }
    this._render();
  }

  // Whether the chosen vehicle (or any Audi Connect vehicle, before one is chosen) has the zone switches
  // of one end of the car. The car announces each zone itself, and a zone it says it lacks gets no switch.
  _hasZones(part) {
    const device = this._config?.device_id;
    const re = new RegExp(`^climatisation_zone_${part}_(left|right)$`);
    return Object.values(this._hass?.entities || {}).some(
      (e) => e.platform === DOMAIN && (!device || e.device_id === device) && re.test(e.translation_key || ""),
    );
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      const make = () => {
        const form = document.createElement("ha-form");
        form.addEventListener("value-changed", (ev) => {
          // An empty choice means "not set", so it is left out of the config.
          const config = Object.fromEntries(Object.entries(ev.detail.value).filter(([, v]) => v !== "" && v !== undefined));
          // Replaced by show_seats_front; the card still reads it, but a saved config does not keep it.
          delete config.show_seats;
          this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
        });
        return form;
      };
      // Three forms in a row, so the seat option can sit indented under "show climate" as its sub-item.
      // Each one is given the whole config, and ha-form returns the whole config with its own change.
      this._form = make();
      this._seatForm = make();
      this._restForm = make();
      this._seatBox = document.createElement("div");
      this._seatBox.style.cssText = "margin-left:28px;padding-left:12px;border-left:2px solid var(--divider-color)";
      this._seatBox.appendChild(this._seatForm);
      this._forms = [this._form, this._seatForm, this._restForm];
      this.append(this._form, this._seatBox, this._restForm);
      for (const form of this._forms) form.hass = this._hass;
    }
    const data = {
      show_logo: true, show_trips: true, show_climate: true, show_stats: true,
      show_seats_front: this._config.show_seats ?? false, show_seats_rear: false, image_local: "", ...this._config,
    };
    for (const form of this._forms) form.data = data;
    const options = [{ value: "", label: this._t("e_none") }, ...(this._images || []).map((i) => ({ value: i.path, label: i.name }))];
    // A picture that is no longer in the folder must stay selectable, or the editor would drop it.
    const current = this._config.image_local;
    if (current && !options.some((o) => o.value === current)) options.push({ value: current, label: current });
    this._form.schema = [
      { name: "device_id", required: true, selector: { device: { integration: DOMAIN } } },
      { name: "name", selector: { text: {} } },
      { name: "image", selector: { image: {} } },
      { name: "image_local", selector: { select: { options, mode: "dropdown" } } },
      { name: "icon", selector: { icon: {} } },
      { name: "show_logo", selector: { boolean: {} } },
      { name: "show_trips", selector: { boolean: {} } },
      { name: "show_climate", selector: { boolean: {} } },
    ];
    // A sub-item of the climate option: only offered when the car has such zones, and switched off with it.
    // Hidden by default on the card because what the zones heat is not confirmed.
    this._seatForm.schema = [
      ...(this._hasZones("front") ? [{ name: "show_seats_front", selector: { boolean: {} } }] : []),
      ...(this._hasZones("rear") ? [{ name: "show_seats_rear", selector: { boolean: {} } }] : []),
    ];
    this._seatBox.hidden = !this._seatForm.schema.length;
    this._seatForm.disabled = data.show_climate === false;
    this._restForm.schema = [{ name: "show_stats", selector: { boolean: {} } }];
    const labels = {
      device_id: "e_device", name: "e_name", image: "e_image", image_local: "e_image_local",
      icon: "e_icon", show_logo: "e_logo", show_trips: "e_trips", show_climate: "e_climate", show_stats: "e_stats", show_seats_front: "e_seats_front", show_seats_rear: "e_seats_rear",
    };
    for (const form of this._forms) form.computeLabel = (sc) => this._t(labels[sc.name]);
  }
}

if (!customElements.get("audi-connect-card")) {
  customElements.define("audi-connect-card", AudiConnectCard);
  customElements.define("audi-connect-card-editor", AudiConnectCardEditor);
}
window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "audi-connect-card")) {
  window.customCards.push({
    type: "audi-connect-card",
    name: "Audi Connect",
    description: "Status, charging, trips and climate of your Audi, found automatically from the integration.",
    preview: false,
    documentationURL: "https://github.com/bertel2020/HA-audi_connect",
  });
}
console.info(`%c AUDI-CONNECT-CARD %c ${CARD_VERSION} `, "color:#fff;background:#bb0a30;font-weight:700", "color:#bb0a30");
