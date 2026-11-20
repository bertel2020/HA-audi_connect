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
    driver: "Driver", passenger: "Passenger", start: "Start", stop: "Stop",
    doors: "Doors", windows: "Windows", all_closed: "All closed and locked",
    all_closed_unlocked: "All closed, not locked", all_closed_unknown: "Lock state unknown", n_openings: "{n} openings open",
    one_opening: "1 opening open", open: "open", closed: "closed",
    closed_locked: "closed · locked", closed_unlocked: "closed · unlocked",
    lock: "Lock", unlock: "Unlock", close: "Close",
    hood: "Hood", trunk: "Trunk", fl: "Front left", fr: "Front right", rl: "Rear left", rr: "Rear right",
    confirm_lock: "Lock the vehicle?", confirm_unlock: "Unlock the vehicle?",
    no_vehicle: "No Audi Connect vehicle found. Pick one in the card settings.",
    stale: "Data is outdated", days: "days", ago: "{t} ago", now: "now",
    min: "min", h: "h", d: "d", refresh: "Refresh", refresh_data: "Refresh vehicle data", flash: "Flash lights",
    // editor
    e_device: "Vehicle", e_name: "Name", e_image: "Upload a photo (optional)", e_image_local: "…or pick one from the www folder", e_none: "none",
    e_icon: "Icon instead of the Audi logo (optional)", e_logo: "Show Audi logo", e_trips: "Show trips", e_climate: "Show climate", e_stats: "Show vehicle details",
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
    driver: "Fahrer", passenger: "Beifahrer", start: "Starten", stop: "Stoppen",
    doors: "Türen", windows: "Fenster", all_closed: "Alles zu und verriegelt",
    all_closed_unlocked: "Alles zu, nicht verriegelt", all_closed_unknown: "Schlosszustand unbekannt", n_openings: "{n} Öffnungen offen",
    one_opening: "1 Öffnung offen", open: "offen", closed: "zu",
    closed_locked: "zu · verriegelt", closed_unlocked: "zu · entriegelt",
    lock: "Verriegeln", unlock: "Entriegeln", close: "Schließen",
    hood: "Motorhaube", trunk: "Heckklappe", fl: "Vorne links", fr: "Vorne rechts", rl: "Hinten links", rr: "Hinten rechts",
    confirm_lock: "Fahrzeug verriegeln?", confirm_unlock: "Fahrzeug entriegeln?",
    no_vehicle: "Kein Audi-Connect-Fahrzeug gefunden. Wähle eines in den Karteneinstellungen.",
    stale: "Daten sind veraltet", days: "Tage", ago: "vor {t}", now: "gerade eben",
    min: "Min.", h: "Std.", d: "T.", refresh: "Aktualisieren", refresh_data: "Fahrzeugdaten aktualisieren", flash: "Lichthupe",
    e_device: "Fahrzeug", e_name: "Name", e_image: "Foto hochladen (optional)", e_image_local: "…oder eines aus dem www-Ordner wählen", e_none: "keines",
    e_icon: "Icon statt Audi-Logo (optional)", e_logo: "Audi-Logo anzeigen", e_trips: "Fahrten anzeigen", e_climate: "Klimatisierung anzeigen", e_stats: "Fahrzeugdetails anzeigen",
  },
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
.band{display:flex;align-items:stretch;margin-top:10px;padding:10px 6px;border-radius:12px;background:color-mix(in srgb,var(--primary-color) 14%,transparent);color:var(--primary-text-color)}
.cell{flex:1;display:flex;flex-direction:column;align-items:center;gap:1px;min-width:0;padding:0 4px;cursor:pointer;text-align:center}
.cell+.cell{border-left:1px solid color-mix(in srgb,var(--primary-color) 35%,transparent)}
.cell .v{font-size:17px;font-weight:500;line-height:1.2;white-space:nowrap}
.cell .k,.cell .s{font-size:11px;color:var(--secondary-text-color)}
.cell ha-icon{--mdc-icon-size:18px;vertical-align:-4px;color:var(--primary-color)}
.note{display:flex;align-items:center;gap:10px;margin-top:10px;padding:10px 14px;border-radius:12px;font-size:14px;cursor:pointer;background:var(--secondary-background-color);color:var(--primary-text-color)}
.note ha-icon{--mdc-icon-size:22px;color:var(--secondary-text-color)}
.note.bad{background:color-mix(in srgb,var(--error-color) 14%,transparent)}
.note.bad ha-icon{color:var(--error-color)}
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
.car{width:100%;max-height:210px;display:block;margin:0 auto}
.seg{cursor:pointer;stroke-width:1.5}
.seg.open{fill:color-mix(in srgb,var(--error-color) 28%,transparent);stroke:var(--error-color)}
.seg.lk{fill:color-mix(in srgb,var(--success-color) 22%,transparent);stroke:var(--success-color)}
.seg.ul{fill:color-mix(in srgb,var(--warning-color) 28%,transparent);stroke:var(--warning-color)}
.gl{cursor:pointer;stroke-width:1.5;fill:color-mix(in srgb,var(--secondary-text-color) 18%,transparent);stroke:var(--secondary-text-color)}
.gl.open{fill:color-mix(in srgb,var(--warning-color) 35%,transparent);stroke:var(--warning-color)}
.li{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--divider-color);font-size:13px;color:var(--primary-text-color);cursor:pointer}
.li:last-of-type{border:0}
.c-ok{color:var(--success-color)}.c-warn{color:var(--warning-color)}.c-bad{color:var(--error-color)}.c-mute{color:var(--secondary-text-color)}
.big{width:100%;margin-top:10px}
.pills .big{margin-top:0}
.empty{padding:24px;text-align:center;color:var(--secondary-text-color)}
@media (prefers-reduced-motion:reduce){.bar.charging::before,.pulse,.cstatus ha-icon,.pill.wait ha-icon{animation:none}}
`;

// Positions inside the 200 x 300 top view.
const SEG = {
  hood: [62, 18, 76, 46, 16], fl: [44, 72, 52, 68, 10], fr: [104, 72, 52, 68, 10],
  rl: [44, 146, 52, 68, 10], rr: [104, 146, 52, 68, 10], trunk: [62, 222, 76, 60, 18],
};
const GLASS = { fl: [33, 80, 11, 52], fr: [156, 80, 11, 52], rl: [33, 154, 11, 52], rr: [156, 154, 11, 52] };
const ICON_AT = { hood: [100, 41], fl: [70, 106], fr: [130, 106], rl: [70, 180], rr: [130, 180], trunk: [100, 252] };
const BODY =
  "M100 6 C132 6 152 20 156 50 C158 68 160 90 160 118 L160 190 C160 222 158 246 154 266 C150 288 130 296 100 296 C70 296 50 288 46 266 C42 246 40 222 40 190 L40 118 C40 90 42 68 44 50 C48 20 68 6 100 6 Z";
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
    this._update();
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
    this._sig = sig;
    this._root.innerHTML = this._render();
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
    parts.push(this._renderInfoRow());
    parts.push(this._renderIcons());
    parts.push(this._renderEnergy());
    if (c.show_trips) parts.push(this._renderTrips());
    if (c.show_stats) parts.push(this._renderStats());
    if (c.show_climate && this._has("climatisation")) parts.push(this._renderClimate());
    if (this._ui.popup) parts.push(this._renderPopup());
    return parts.join("");
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

    const items = [];
    if (this._has("door_lock") || this._has("any_door_unlocked")) {
      items.push(`<button class="ic ${lockCls}" data-more="${esc(this._id("door_lock") || this._id("any_door_unlocked"))}"><ha-icon icon="${lockIcon}"></ha-icon>${esc(lockTxt)}</button>`);
    }
    items.push(`<button class="ic ${doors.length ? "bad" : "ok"}" data-act="popup" data-tab="doors"><ha-icon icon="mdi:car-door"></ha-icon>${esc(doors.length ? this._t("n_open", { n: doors.length }) : this._t("doors_closed"))}</button>`);
    items.push(`<button class="ic ${wins.length ? "warn" : "ok"}" data-act="popup" data-tab="windows"><ha-icon icon="mdi:car-windshield-outline"></ha-icon>${esc(wins.length ? this._t("n_open", { n: wins.length }) : this._t("windows_closed"))}</button>`);
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
    const active = charging && target !== undefined && pct < target;

    let slider = "";
    if (tState && target !== undefined && !useTank) {
      const min = tState.attributes.min ?? 20, max = tState.attributes.max ?? 100, step = tState.attributes.step ?? 5;
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
    return `${n.toLocaleString(this._hass?.language || undefined, { minimumFractionDigits: n % 1 ? 1 : 0, maximumFractionDigits: 1 })} °C`;
  }

  // Power, range gained per hour and when it is done: only while charging, and only what the car reports.
  _renderChargeBand() {
    const cells = [];
    if (this._known("charging_power")) {
      cells.push(`<div class="cell" data-more="${esc(this._id("charging_power"))}"><span class="v"><ha-icon class="pulse" icon="mdi:flash"></ha-icon> ${esc(this._fmt("charging_power", "kW"))}</span><span class="k">${esc(this._t("power"))}</span></div>`);
    }
    const rate = this._num("actual_charge_rate");
    if (this._known("actual_charge_rate") && rate !== undefined && rate >= 0) {
      const unit = this._s("actual_charge_rate").attributes.unit_of_measurement || "km/h";
      const shown = rate.toLocaleString(this._hass.language || undefined, { maximumFractionDigits: 0 });
      cells.push(`<div class="cell" data-more="${esc(this._id("actual_charge_rate"))}"><span class="v">+${esc(shown)} ${esc(unit)}</span><span class="k">${esc(this._t("rate"))}</span></div>`);
    }
    const done = this._known("charging_complete_time") ? this._timeOf(this._s("charging_complete_time").state) : "";
    const mins = this._known("remaining_charging_time") ? this._num("remaining_charging_time") : undefined;
    const left = mins !== undefined && mins > 0 ? this._t("in", { t: this._dur(mins) }) : "";
    if (done || left) {
      const id = this._id(done ? "charging_complete_time" : "remaining_charging_time");
      cells.push(`<div class="cell" data-more="${esc(id)}"><span class="v">${esc(done || left)}</span><span class="k">${esc(this._t("charging_done"))}</span>${done && left ? `<span class="s">${esc(left)}</span>` : ""}</div>`);
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
    const h = Math.floor(minutes / 60), m = Math.round(minutes % 60);
    return h ? (m ? `${h} ${this._t("h")} ${m} ${this._t("min")}` : `${h} ${this._t("h")}`) : `${m} ${this._t("min")}`;
  }

  _timeOf(iso) {
    const d = new Date(iso);
    if (isNaN(d)) return "";
    return d.toLocaleTimeString(this._hass.language || undefined, { hour: "2-digit", minute: "2-digit" });
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
    const seats = seatBtn("climatisation_zone_front_left", this._t("driver")) + seatBtn("climatisation_zone_front_right", this._t("passenger"));
    const id = esc(cl.entity_id);
    const sub = on ? `${this._t(action)}${left ? " · " + this._t("remaining") + " " + left : ""}` : this._t("climate_off") + outdoor;
    const modeRow = mode && modeOptions.length
      ? `<div class="mrow"><span>${esc(this._t("mode"))}</span><select data-select="${esc(mode.entity_id)}" aria-label="${esc(this._t("mode"))}">${modeOptions.map((o) => `<option value="${esc(o)}" ${o === mode.state ? "selected" : ""}>${esc(this._hass.formatEntityState ? this._hass.formatEntityState(mode, o) : o)}</option>`).join("")}</select></div>`
      : "";
    return `<details class="climate" data-id="climate" ${this._ui.open.climate ? "open" : ""}>
      <summary><ha-icon icon="mdi:air-conditioner"></ha-icon><span class="t">${esc(this._t("climate"))}</span><span class="sm">${esc(sub)}</span><ha-icon class="ch" icon="mdi:chevron-down"></ha-icon></summary>
      <div class="cbody">
        ${modeRow}
        ${temp !== undefined && temp !== null ? `<div class="step"><button class="stp" data-step="-1" aria-label="-"><ha-icon icon="mdi:minus"></ha-icon></button><b data-live="temp">${esc(this._temp(this._ui.tempDraft ?? temp))}</b><button class="stp" data-step="1" aria-label="+"><ha-icon icon="mdi:plus"></ha-icon></button></div>` : ""}
        ${seats ? `<div class="pills" style="grid-template-columns:repeat(2,1fr)">${seats}</div>` : ""}
        <div class="pills">
          ${on
            ? `<button class="pill big${this._waiting("climate-off") ? " wait" : ""}" data-act="climate-off"><ha-icon icon="${this._waiting("climate-off") ? "mdi:loading" : "mdi:stop"}"></ha-icon>${esc(this._t("stop"))}</button>`
            : `<button class="pill big go${this._waiting("climate-on") ? " wait" : ""}" data-act="climate-on"><ha-icon icon="${this._waiting("climate-on") ? "mdi:loading" : "mdi:play"}"></ha-icon>${esc(this._t("start"))}</button>`}
        </div>
        ${status}
      </div>
    </details>`;
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

    const dim = (isDoor) => (isDoor === (tab === "doors") ? 1 : 0.35);
    let svg = `<svg class="car" viewBox="0 0 200 300" role="img"><path d="${BODY}" fill="var(--secondary-background-color)" stroke="var(--divider-color)" stroke-width="1.5"/>`;
    for (const [k, [x, y, w, h, r]] of Object.entries(SEG)) {
      const st = this._doorState(k);
      const cls2 = st.open ? "open" : st.unk ? "lk" : st.locked ? "lk" : "ul";
      svg += `<rect class="seg ${cls2}" data-more="${esc(this._id(DOOR_KEYS[k]))}" x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" style="opacity:${dim(true)}"/>`;
    }
    for (const [k, [x, y, w, h]] of Object.entries(GLASS)) {
      const open = this._on(WINDOW_KEYS[k]);
      svg += `<rect class="gl ${open ? "open" : ""}" data-more="${esc(this._id(WINDOW_KEYS[k]))}" x="${x}" y="${y}" width="${w}" height="${h}" rx="3" style="opacity:${dim(false)}"/>`;
    }
    if (tab === "doors") {
      for (const [k, [x, y]] of Object.entries(ICON_AT)) {
        const st = this._doorState(k);
        if (st.open) continue;
        svg += `<g transform="translate(${x - 10} ${y - 10}) scale(.83)" style="pointer-events:none"><path fill="${st.unk ? "var(--secondary-text-color)" : st.locked ? "var(--success-color)" : "var(--warning-color)"}" d="${st.locked ? "M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z" : "M18,1C15.24,1 13,3.24 13,6V8H4A2,2 0 0,0 2,10V20A2,2 0 0,0 4,22H16A2,2 0 0,0 18,20V10A2,2 0 0,0 16,8H15V6A3,3 0 0,1 18,3A3,3 0 0,1 21,6V8H23V6C23,3.24 20.76,1 18,1M10,13A2,2 0 0,1 12,15C12,16.11 11.11,17 10,17A2,2 0 0,1 8,15A2,2 0 0,1 10,13Z"}"/></g>`;
      }
    }
    svg += "</svg>";

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
    const lockBtn = tab === "doors" && lock !== "unknown" && (this._has("door_lock") || this._has("any_door_unlocked"))
      ? `<button class="pill big" data-act="lock"><ha-icon icon="${lock === "locked" ? "mdi:lock-open-variant" : "mdi:lock"}"></ha-icon>${esc(lock === "locked" ? this._t("unlock") : this._t("lock"))}</button>` : "";
    return `<div class="ov" data-act="close-bg"><div class="dlg">
      <div class="dh"><div><b>${esc(this._t("doors"))} / ${esc(this._t("windows"))}</b><span class="${cls}">${esc(sum)}</span></div>
      <button class="x" data-act="close" aria-label="${esc(this._t("close"))}"><ha-icon icon="mdi:close"></ha-icon></button></div>
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
    if (el.dataset.toggle) { this._hass.callService("homeassistant", "toggle", { entity_id: el.dataset.toggle }); this._wait(el.dataset.toggle); return; }
    switch (el.dataset.act) {
      case "popup": this._ui.popup = true; this._ui.tab = el.dataset.tab; this._sig = ""; this._update(); return;
      case "close": this._ui.popup = null; this._sig = ""; this._update(); return;
      case "lock": this._toggleLock(); return;
      case "refresh": this._refresh(); return;
      case "open-integration": this._openIntegration(); return;
      case "climate-on": this._hass.callService("climate", "turn_on", { entity_id: this._id("climatisation") }); this._wait("climate-on"); return;
      case "climate-off": this._hass.callService("climate", "turn_off", { entity_id: this._id("climatisation") }); this._wait("climate-off"); return;
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
      this._hass.callService("climate", "set_temperature", { entity_id: this._id("climatisation"), temperature: v });
      setTimeout(() => { this._ui.tempDraft = null; this._sig = ""; this._update(); }, 3000);
    }, 700);
  }

  // Shows a button as "working" until the car answers (or a few seconds pass).
  _waiting(key) { return !!this._ui.wait?.[key]; }

  _wait(key) {
    (this._ui.wait ||= {})[key] = true;
    this._sig = "";
    this._update();
    setTimeout(() => {
      delete this._ui.wait[key];
      this._sig = "";
      this._update();
    }, 5000);
  }

  _refresh() {
    const id = this._id("refresh_vehicle_data");
    if (!id || this._ui.refreshing) return;
    this._hass.callService("button", "press", { entity_id: id });
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
    this._hass.callService("lock", locked ? "unlock" : "lock", { entity_id: id });
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
      this._hass.callService("number", "set_value", { entity_id: this._id("target_state_of_charge"), value: Number(t.value) });
    } else if (t.dataset.slider === "temp") {
      this._hass.callService("climate", "set_temperature", { entity_id: this._id("climatisation"), temperature: Number(t.value) });
    } else if (t.dataset.select) {
      this._hass.callService("select", "select_option", { entity_id: t.dataset.select, option: t.value });
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
    if (this._form) this._form.hass = hass;
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

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => {
        // An empty choice means "not set", so it is left out of the config.
        const config = Object.fromEntries(Object.entries(ev.detail.value).filter(([, v]) => v !== "" && v !== undefined));
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.data = { show_logo: true, show_trips: true, show_climate: true, show_stats: true, image_local: "", ...this._config };
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
      { name: "show_stats", selector: { boolean: {} } },
    ];
    const labels = {
      device_id: "e_device", name: "e_name", image: "e_image", image_local: "e_image_local",
      icon: "e_icon", show_logo: "e_logo", show_trips: "e_trips", show_climate: "e_climate", show_stats: "e_stats",
    };
    this._form.computeLabel = (s) => this._t(labels[s.name]);
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
    documentationURL: "https://github.com/audiconnect/audi_connect_ha",
  });
}
console.info(`%c AUDI-CONNECT-CARD %c ${CARD_VERSION} `, "color:#fff;background:#bb0a30;font-weight:700", "color:#bb0a30");
