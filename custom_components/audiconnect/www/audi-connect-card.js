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
    locked: "Locked", unlocked: "Unlocked", not_secured: "Not secured",
    doors_closed: "Doors closed", windows_closed: "Windows closed",
    n_open: "{n} open", plugged: "Plugged in", unplugged: "Not plugged in",
    light_on: "Lights on", light_off: "Lights off", warning: "Warning",
    charge_target: "Charge target", range: "Range", charging_done: "done",
    last_trip: "Last trip", long_term: "Long term",
    distance: "Distance", speed: "Avg. speed", consumption: "Consumption", energy: "Energy",
    electric_range: "electric", inspection: "inspection", parked: "parked",
    climate: "Climate", climate_on: "Running", climate_off: "Off", mode: "Mode",
    driver: "Driver", passenger: "Passenger", start: "Start", stop: "Stop",
    doors: "Doors", windows: "Windows", all_closed: "All closed and locked",
    all_closed_unlocked: "All closed, not locked", n_openings: "{n} openings open",
    one_opening: "1 opening open", open: "open", closed: "closed",
    closed_locked: "closed · locked", closed_unlocked: "closed · unlocked",
    lock: "Lock", unlock: "Unlock", close: "Close",
    hood: "Hood", trunk: "Trunk", fl: "Front left", fr: "Front right", rl: "Rear left", rr: "Rear right",
    confirm_lock: "Lock the vehicle?", confirm_unlock: "Unlock the vehicle?",
    no_vehicle: "No Audi Connect vehicle found. Pick one in the card settings.",
    stale: "Data is outdated", days: "days", ago: "{t} ago", now: "now",
    min: "min", h: "h", d: "d", refresh: "Refresh", flash: "Flash lights",
    // editor
    e_device: "Vehicle", e_name: "Name", e_image: "Photo (optional)",
    e_logo: "Show Audi logo", e_trips: "Show trips", e_climate: "Show climate", e_stats: "Show key figures",
  },
  de: {
    locked: "Verriegelt", unlocked: "Entriegelt", not_secured: "Nicht gesichert",
    doors_closed: "Türen zu", windows_closed: "Fenster zu",
    n_open: "{n} offen", plugged: "Angesteckt", unplugged: "Nicht verbunden",
    light_on: "Licht an", light_off: "Licht aus", warning: "Warnung",
    charge_target: "Ladeziel", range: "Reichweite", charging_done: "fertig",
    last_trip: "Letzte Fahrt", long_term: "Langzeit",
    distance: "Strecke", speed: "Ø Tempo", consumption: "Verbrauch", energy: "Energie",
    electric_range: "elektrisch", inspection: "Inspektion", parked: "geparkt",
    climate: "Klimatisierung", climate_on: "Läuft", climate_off: "Aus", mode: "Modus",
    driver: "Fahrer", passenger: "Beifahrer", start: "Starten", stop: "Stoppen",
    doors: "Türen", windows: "Fenster", all_closed: "Alles zu und verriegelt",
    all_closed_unlocked: "Alles zu, nicht verriegelt", n_openings: "{n} Öffnungen offen",
    one_opening: "1 Öffnung offen", open: "offen", closed: "zu",
    closed_locked: "zu · verriegelt", closed_unlocked: "zu · entriegelt",
    lock: "Verriegeln", unlock: "Entriegeln", close: "Schließen",
    hood: "Motorhaube", trunk: "Heckklappe", fl: "Vorne links", fr: "Vorne rechts", rl: "Hinten links", rr: "Hinten rechts",
    confirm_lock: "Fahrzeug verriegeln?", confirm_unlock: "Fahrzeug entriegeln?",
    no_vehicle: "Kein Audi-Connect-Fahrzeug gefunden. Wähle eines in den Karteneinstellungen.",
    stale: "Daten sind veraltet", days: "Tage", ago: "vor {t}", now: "gerade eben",
    min: "Min.", h: "Std.", d: "T.", refresh: "Aktualisieren", flash: "Lichthupe",
    e_device: "Fahrzeug", e_name: "Name", e_image: "Foto (optional)",
    e_logo: "Audi-Logo anzeigen", e_trips: "Fahrten anzeigen", e_climate: "Klimatisierung anzeigen", e_stats: "Kennzahlen anzeigen",
  },
};

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
input[type=range]{width:100%;margin:2px 0 0;accent-color:var(--primary-color)}
.chg{display:flex;justify-content:center;gap:28px;font-size:14px;margin-top:6px;color:var(--primary-text-color)}
.chg ha-icon{--mdc-icon-size:18px;vertical-align:-4px}
.chg .pulse ha-icon{color:var(--primary-color);animation:pu 1.4s ease-in-out infinite}
details{border-top:1px solid var(--divider-color)}
summary{list-style:none;display:flex;align-items:center;gap:10px;padding:12px 18px;cursor:pointer;font-size:14px;color:var(--primary-text-color)}
summary::-webkit-details-marker{display:none}
summary:hover{background:var(--secondary-background-color)}
summary .t{font-weight:500;min-width:92px}
summary .sm{flex:1;color:var(--secondary-text-color);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
summary ha-icon{--mdc-icon-size:20px;color:var(--secondary-text-color)}
summary .ch{transition:transform .15s}
details[open] summary .ch{transform:rotate(180deg)}
.trip{display:flex;padding:2px 12px 14px}
.trip div{flex:1;display:flex;flex-direction:column;align-items:center;gap:1px;min-width:0}
.trip ha-icon{--mdc-icon-size:22px;color:var(--secondary-text-color)}
.trip .v{font-size:16px;font-weight:500}.trip .u{font-size:11px;color:var(--secondary-text-color)}.trip .k{font-size:11px;color:var(--secondary-text-color);margin-top:2px}
.stats{display:flex;padding:14px 8px;border-top:1px solid var(--divider-color)}
.stats .s{flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;font-size:14px;color:var(--primary-text-color);cursor:pointer}
.stats ha-icon{--mdc-icon-size:22px;color:var(--secondary-text-color)}
.stats small{font-size:11px;color:var(--secondary-text-color)}
.climate{border-top:1px solid var(--divider-color);padding:14px 16px 16px}
.chead{display:flex;align-items:center;gap:12px}
.cicon{width:44px;height:44px;border-radius:50%;background:var(--secondary-background-color);display:flex;align-items:center;justify-content:center;flex:none}
.cicon.on ha-icon{color:var(--primary-color)}
.ctitle{flex:1}.ctitle b{display:block;font-size:16px;font-weight:500}.ctitle span{font-size:13px;color:var(--secondary-text-color)}
select{background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);border-radius:999px;padding:8px 12px;font-size:13px;font-family:inherit}
.trow{display:flex;align-items:center;gap:10px;margin-top:12px;font-size:13px;color:var(--primary-text-color)}
.trow ha-icon{--mdc-icon-size:18px}.trow input{flex:1}.trow b{min-width:48px;text-align:right;font-weight:500}
.pills{display:grid;gap:8px;margin-top:10px}
.pill{background:var(--secondary-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);border-radius:999px;padding:10px 0;font-size:13px;display:flex;align-items:center;justify-content:center;gap:6px;cursor:pointer;font-family:inherit}
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
.empty{padding:24px;text-align:center;color:var(--secondary-text-color)}
@media (prefers-reduced-motion:reduce){.bar.charging::before,.chg .pulse ha-icon{animation:none}}
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
        // The first one wins; a hidden duplicate must not shadow a visible one.
        if (!m[e.translation_key] || (m[e.translation_key].hidden && !e.hidden)) {
          m[e.translation_key] = e;
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
    return !!s && s.state !== "unavailable" && s.state !== "unknown";
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
    if (k === "trunk" && this._has("trunk_unlocked")) locked = !this._on("trunk_unlocked");
    else if (k !== "hood") locked = this._lockState() !== "unlocked";
    return { open, locked };
  }

  _lockState() {
    const s = this._s("door_lock");
    if (s && (s.state === "locked" || s.state === "unlocked")) return s.state;
    if (this._has("any_door_unlocked")) return this._on("any_door_unlocked") ? "unlocked" : "locked";
    return "locked";
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

    parts.push(`<div class="title">${c.show_logo ? RINGS : ""}<span>${esc(name)}</span></div>`);
    if (c.image) parts.push(`<img class="photo" src="${esc(c.image)}" alt="">`);
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
      ? `<span class="mid ${stale ? "warn" : ""}" data-more="${esc(upd.entity_id)}" title="${esc(this._t("stale"))}">${stale ? '<ha-icon icon="mdi:alert-outline"></ha-icon>' : ""}${esc(this._ago(upd.state))}</span>`
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
    else { lockCls = "ok"; lockIcon = "mdi:lock"; lockTxt = this._t("locked"); }

    const items = [];
    if (this._has("door_lock") || this._has("any_door_unlocked")) {
      items.push(`<button class="ic ${lockCls}" data-act="lock"><ha-icon icon="${lockIcon}"></ha-icon>${esc(lockTxt)}</button>`);
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
    const chargeLine = active
      ? `<div class="chg"><span class="pulse"><ha-icon icon="mdi:flash"></ha-icon> ${esc(this._fmt("charging_power"))}</span>${this._known("charging_complete_time") ? `<span><ha-icon icon="mdi:clock-outline"></ha-icon> ${esc(this._t("charging_done"))} ${esc(this._timeOf(this._s("charging_complete_time").state))}</span>` : ""}</div>`
      : "";
    return `<div class="sep"></div><div class="energy">
      <div class="barwrap">
        <div class="bar ${active ? "charging" : ""}" style="width:${pct}%;background-size:${(10000 / Math.max(pct, 1)).toFixed(1)}% 100%"><span>${soc === undefined ? "–" : Math.round(soc) + " %"}</span></div>
        ${target !== undefined && !useTank ? `<div class="mark" style="left:calc(${target}% - 1px)"></div>` : ""}
      </div>
      <div class="eline">
        <span>${target !== undefined && !useTank ? `${esc(this._t("charge_target"))} <b>${Math.round(target)} %</b>` : ""}</span>
        <span>${esc(this._t("range"))} <b>${esc(this._fmt(rangeKey, "km"))}</b></span>
      </div>
      ${slider}${chargeLine}
    </div>`;
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
      const cell = (ic, k, label, d) => `<div><ha-icon icon="${ic}"></ha-icon><span class="v">${esc(this._known(`${prefix}_${k}`) ? this._rounded(`${prefix}_${k}`) : "–")}</span><span class="u">${esc(unit(k, d))}</span><span class="k">${esc(this._t(label))}</span></div>`;
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
    const cells = [];
    const rk = this._known("primary_engine_range") ? "primary_engine_range" : (this._known("range") ? "range" : null);
    if (rk) cells.push(["mdi:battery-charging", this._fmt(rk, "km"), this._t("electric_range"), this._id(rk)]);
    if (this._known("service_inspection_time")) {
      const s = this._s("service_inspection_time");
      const n = this._num("service_inspection_time");
      const v = n !== undefined && !s.attributes.unit_of_measurement ? `${n} ${this._t("days")}` : this._fmt("service_inspection_time");
      cells.push(["mdi:wrench-clock", v, this._t("inspection"), s.entity_id]);
    }
    if (this._known("park_time")) {
      cells.push(["mdi:parking", this._since(this._s("park_time").state), this._t("parked"), this._id("park_time")]);
    }
    if (!cells.length) return "";
    return `<div class="stats">${cells.map(([ic, v, l, id]) => `<div class="s" ${id ? `data-more="${esc(id)}"` : ""}><ha-icon icon="${ic}"></ha-icon>${esc(v)}<small>${esc(l)}</small></div>`).join("")}</div>`;
  }

  _renderClimate() {
    const cl = this._s("climatisation");
    const on = cl.state !== "off" && cl.state !== "unavailable" && cl.state !== "unknown";
    const a = cl.attributes;
    const temp = a.temperature;
    const mode = this._s("climatisation_mode");
    const modeOptions = mode?.attributes.options || [];
    const remaining = this._known("remaining_climatisation_time") && on ? ` · ${this._fmt("remaining_climatisation_time")}` : "";
    const outdoor = this._known("outdoor_temperature") ? ` · ${this._fmt("outdoor_temperature")}` : "";
    const seatBtn = (tk, label) => this._has(tk)
      ? `<button class="pill ${this._on(tk) ? "on" : ""}" data-toggle="${esc(this._id(tk))}"><ha-icon icon="mdi:car-seat-heater"></ha-icon>${esc(label)}</button>` : "";
    const seats = seatBtn("climatisation_zone_front_left", this._t("driver")) + seatBtn("climatisation_zone_front_right", this._t("passenger"));
    return `<div class="climate">
      <div class="chead">
        <div class="cicon ${on ? "on" : ""}"><ha-icon icon="mdi:air-conditioner"></ha-icon></div>
        <div class="ctitle"><b>${esc(this._t("climate"))}</b><span>${esc((on ? this._t("climate_on") : this._t("climate_off")) + remaining + outdoor)}</span></div>
        ${mode && modeOptions.length ? `<select data-select="${esc(mode.entity_id)}" aria-label="${esc(this._t("mode"))}">${modeOptions.map((o) => `<option value="${esc(o)}" ${o === mode.state ? "selected" : ""}>${esc(this._hass.formatEntityState ? this._hass.formatEntityState(mode, o) : o)}</option>`).join("")}</select>` : ""}
      </div>
      ${temp !== undefined && temp !== null ? `<div class="trow"><ha-icon icon="mdi:thermometer"></ha-icon><input type="range" data-slider="temp" min="${a.min_temp ?? 16}" max="${a.max_temp ?? 28}" step="${a.target_temp_step ?? 0.5}" value="${temp}" aria-label="${esc(this._t("climate"))}"><b id="tv">${esc(temp)} °C</b></div>` : ""}
      ${seats ? `<div class="pills" style="grid-template-columns:repeat(2,1fr)">${seats}</div>` : ""}
      <div class="pills" style="grid-template-columns:repeat(2,1fr)">
        <button class="pill" data-act="climate-on">${esc(this._t("start"))}</button>
        <button class="pill" data-act="climate-off">${esc(this._t("stop"))}</button>
      </div>
    </div>`;
  }

  _renderPopup() {
    const tab = this._ui.tab;
    const { doors, wins } = this._openLists();
    const lock = this._lockState();
    const n = doors.length + wins.length;
    let sum, cls;
    if (n) { sum = n === 1 ? this._t("one_opening") : this._t("n_openings", { n }); cls = "c-bad"; }
    else if (lock === "unlocked") { sum = this._t("all_closed_unlocked"); cls = "c-warn"; }
    else { sum = this._t("all_closed"); cls = "c-ok"; }

    const dim = (isDoor) => (isDoor === (tab === "doors") ? 1 : 0.35);
    let svg = `<svg class="car" viewBox="0 0 200 300" role="img"><path d="${BODY}" fill="var(--secondary-background-color)" stroke="var(--divider-color)" stroke-width="1.5"/>`;
    for (const [k, [x, y, w, h, r]] of Object.entries(SEG)) {
      const st = this._doorState(k);
      const cls2 = st.open ? "open" : st.locked ? "lk" : "ul";
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
        svg += `<g transform="translate(${x - 10} ${y - 10}) scale(.83)" style="pointer-events:none"><path fill="${st.locked ? "var(--success-color)" : "var(--warning-color)"}" d="${st.locked ? "M12,17A2,2 0 0,0 14,15C14,13.89 13.1,13 12,13A2,2 0 0,0 10,15A2,2 0 0,0 12,17M18,8A2,2 0 0,1 20,10V20A2,2 0 0,1 18,22H6A2,2 0 0,1 4,20V10C4,8.89 4.9,8 6,8H7V6A5,5 0 0,1 12,1A5,5 0 0,1 17,6V8H18M12,3A3,3 0 0,0 9,6V8H15V6A3,3 0 0,0 12,3Z" : "M18,1C15.24,1 13,3.24 13,6V8H4A2,2 0 0,0 2,10V20A2,2 0 0,0 4,22H16A2,2 0 0,0 18,20V10A2,2 0 0,0 16,8H15V6A3,3 0 0,1 18,3A3,3 0 0,1 21,6V8H23V6C23,3.24 20.76,1 18,1M10,13A2,2 0 0,1 12,15C12,16.11 11.11,17 10,17A2,2 0 0,1 8,15A2,2 0 0,1 10,13Z"}"/></g>`;
      }
    }
    svg += "</svg>";

    let list = "";
    if (tab === "doors") {
      for (const k of ["fl", "fr", "rl", "rr", "hood", "trunk"]) {
        const st = this._doorState(k);
        const txt = st.open ? this._t("open") : k === "hood" ? this._t("closed") : st.locked ? this._t("closed_locked") : this._t("closed_unlocked");
        const c = st.open ? "c-bad" : k === "hood" || st.locked ? "c-mute" : "c-warn";
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
    const lockBtn = tab === "doors" && (this._has("door_lock") || this._has("any_door_unlocked"))
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

  _onClick(e) {
    const t = e.target;
    const bg = t.closest?.('[data-act="close-bg"]');
    if (bg && t === bg) { this._ui.popup = null; this._sig = ""; this._update(); return; }
    const el = t.closest?.("[data-act],[data-more],[data-toggle],[data-tab-set]");
    if (!el || !this._hass) return;
    if (el.dataset.tabSet) { this._ui.tab = el.dataset.tabSet; this._sig = ""; this._update(); return; }
    if (el.dataset.toggle) { this._hass.callService("homeassistant", "toggle", { entity_id: el.dataset.toggle }); return; }
    switch (el.dataset.act) {
      case "popup": this._ui.popup = true; this._ui.tab = el.dataset.tab; this._sig = ""; this._update(); return;
      case "close": this._ui.popup = null; this._sig = ""; this._update(); return;
      case "lock": this._toggleLock(); return;
      case "climate-on": this._hass.callService("climate", "turn_on", { entity_id: this._id("climatisation") }); return;
      case "climate-off": this._hass.callService("climate", "turn_off", { entity_id: this._id("climatisation") }); return;
      default: break;
    }
    if (el.dataset.more) this._moreInfo(el.dataset.more);
  }

  _toggleLock() {
    const id = this._id("door_lock");
    if (!id) { this._moreInfo(this._id("any_door_unlocked")); return; }
    const locked = this._lockState() === "locked";
    if (!window.confirm(this._t(locked ? "confirm_unlock" : "confirm_lock"))) return;
    this._hass.callService("lock", locked ? "unlock" : "lock", { entity_id: id });
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
    this._hass = hass;
    if (this._form) this._form.hass = hass;
    this._render();
  }

  _t(key) {
    const lang = (this._hass?.language || "en").slice(0, 2);
    return (TEXT[lang] || TEXT.en)[key] ?? key;
  }

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => {
        this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: ev.detail.value }, bubbles: true, composed: true }));
      });
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.data = { show_logo: true, show_trips: true, show_climate: true, show_stats: true, ...this._config };
    this._form.schema = [
      { name: "device_id", required: true, selector: { device: { integration: DOMAIN } } },
      { name: "name", selector: { text: {} } },
      { name: "image", selector: { image: {} } },
      { name: "show_logo", selector: { boolean: {} } },
      { name: "show_trips", selector: { boolean: {} } },
      { name: "show_climate", selector: { boolean: {} } },
      { name: "show_stats", selector: { boolean: {} } },
    ];
    const labels = {
      device_id: "e_device", name: "e_name", image: "e_image",
      show_logo: "e_logo", show_trips: "e_trips", show_climate: "e_climate", show_stats: "e_stats",
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
