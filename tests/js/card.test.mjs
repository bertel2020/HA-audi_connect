// Tests for the dashboard card, run in jsdom with a fake `hass`.
//   cd tests/js && npm install && npm test
import { test, beforeEach } from "node:test";
import assert from "node:assert";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { JSDOM } from "jsdom";

const here = dirname(fileURLToPath(import.meta.url));
const CARD = readFileSync(
  join(here, "../../custom_components/audiconnect/www/audi-connect-card.js"),
  "utf8",
);

const DEFS = [
  ["lock.car", "door_lock", "locked"],
  ["binary_sensor.fl", "left_front_door_open", "off"],
  ["binary_sensor.fr", "right_front_door_open", "off"],
  ["binary_sensor.rl", "left_rear_door_open", "off"],
  ["binary_sensor.rr", "right_rear_door_open", "off"],
  ["binary_sensor.hood", "hood_open", "off"],
  ["binary_sensor.trunk", "trunk_open", "off"],
  ["binary_sensor.wfl", "left_front_window_open", "off"],
  ["binary_sensor.wfr", "right_front_window_open", "on"],
  ["binary_sensor.wrl", "left_rear_window_open", "off"],
  ["binary_sensor.wrr", "right_rear_window_open", "off"],
  ["sensor.soc", "state_of_charge", "64", { unit_of_measurement: "%" }],
  ["sensor.range", "range", "310", { unit_of_measurement: "km" }],
  ["sensor.cs", "charging_state", "charging"],
  ["sensor.cp", "charging_power", "11", { unit_of_measurement: "kW" }],
  ["sensor.rate", "actual_charge_rate", "20", { unit_of_measurement: "km/h" }],
  ["sensor.done", "charging_complete_time", new Date(Date.now() + 30 * 60e3).toISOString()],
  ["number.target", "target_state_of_charge", "80", { min: 20, max: 100, step: 5 }],
  ["climate.car", "climatisation", "off", { temperature: 21, min_temp: 15, max_temp: 30, target_temp_step: 0.5 }],
  ["select.mode", "climatisation_mode", "comfort", { options: ["comfort", "economy"] }],
  ["switch.zfl", "climatisation_zone_front_left", "off"],
  ["switch.zfr", "climatisation_zone_front_right", "on"],
  ["switch.zrl", "climatisation_zone_rear_left", "off"],
  ["switch.zrr", "climatisation_zone_rear_right", "off"],
  ["button.refresh", "refresh_vehicle_data", "unknown"],
];

let dom, window, card, calls, infos, pushes, timers, now;

function build(over = {}, { unit = "°C", admin = true, skip = [] } = {}) {
  const entities = {};
  const states = {};
  for (const [id, tk, state, attrs = {}] of DEFS) {
    if (skip.includes(id)) continue;
    entities[id] = { entity_id: id, platform: "audiconnect", device_id: "dev1", translation_key: tk };
    states[id] = {
      entity_id: id,
      state: over[id] ?? state,
      attributes: { friendly_name: tk, ...attrs },
      last_updated: "2026-11-20T10:00:00+00:00",
    };
  }
  return {
    language: "en",
    entities,
    states,
    config: { unit_system: { temperature: unit } },
    user: { is_admin: admin },
    callService: (d, s, x) => calls.push([d, s, x]),
  };
}

function setHass(over, opts) {
  card.hass = build(over, opts);
}

const root = () => card.shadowRoot.getElementById("root");
const active = () => card.shadowRoot.activeElement;
const key = (target, k, extra = {}) =>
  target.dispatchEvent(new window.KeyboardEvent("keydown", { key: k, bubbles: true, composed: true, cancelable: true, ...extra }));
const tick = (ms) => {
  const end = now + ms;
  for (;;) {
    const due = timers.filter((t) => t.at <= end).sort((a, b) => a.at - b.at)[0];
    if (!due) break;
    timers = timers.filter((t) => t !== due);
    now = due.at;
    due.fn();
  }
  now = end;
};
const pointer = (target, type, x = 0, y = 0) =>
  target.dispatchEvent(new window.MouseEvent(type, { bubbles: true, composed: true, clientX: x, clientY: y }));
const title = () => root().querySelector('[data-act="open-integration"]');
const openDoors = () => root().querySelector('button[data-act="popup"][data-tab="doors"]').click();

beforeEach(() => {
  dom = new JSDOM("<!doctype html><body></body>", { runScripts: "outside-only", pretendToBeVisual: true, url: "http://localhost/" });
  window = dom.window;
  window.confirm = () => true;
  // Timers the test advances by hand, so debounces and long presses are exact.
  timers = [];
  now = 0;
  let nextId = 1;
  window.setTimeout = (fn, ms = 0) => {
    const id = nextId++;
    timers.push({ id, fn, at: now + ms });
    return id;
  };
  window.clearTimeout = (id) => {
    timers = timers.filter((t) => t.id !== id);
  };
  window.eval(CARD);
  calls = [];
  infos = [];
  pushes = [];
  window.document.addEventListener("hass-more-info", (e) => infos.push(e.detail.entityId));
  window.addEventListener("location-changed", () => pushes.push(window.location.pathname));
  card = window.document.createElement("audi-connect-card");
  window.document.body.appendChild(card);
  card.setConfig({ device_id: "dev1" });
  setHass({});
});

test("clickable divs, spans and SVG shapes become keyboard buttons", () => {
  const faux = [...root().querySelectorAll("[data-more],[data-act]")].filter(
    (e) => !e.matches("button,a,input,select,summary") && e.dataset.act !== "close-bg",
  );
  assert.ok(faux.length > 0);
  for (const el of faux) {
    assert.equal(el.getAttribute("role"), "button");
    assert.equal(el.getAttribute("tabindex"), "0");
  }
});

test("Enter on the title opens the integration for an admin", () => {
  const title = root().querySelector('[data-act="open-integration"]');
  title.focus();
  key(title, "Enter");
  assert.deepEqual(pushes, ["/config/devices/device/dev1"]);
});

test("a non-admin does not navigate to the device page", () => {
  setHass({}, { admin: false });
  root().querySelector('[data-act="open-integration"]').click();
  assert.deepEqual(pushes, []);
});

test("the dialog gets its role, the focus and an Escape that returns it", () => {
  openDoors();
  const dlg = root().querySelector(".dlg");
  assert.equal(dlg.getAttribute("role"), "dialog");
  assert.equal(dlg.getAttribute("aria-modal"), "true");
  assert.equal(active().className, "x");
  key(active(), "Escape");
  assert.equal(root().querySelector(".dlg"), null);
  assert.equal(active().dataset.act, "popup");
  assert.equal(active().dataset.tab, "doors");
});

test("Tab wraps inside the dialog in both directions", () => {
  openDoors();
  const items = [...root().querySelector(".dlg").querySelectorAll('button,[role="button"],input,select,summary,[tabindex="0"]')];
  const first = items[0];
  const last = items.at(-1);
  last.focus();
  key(last, "Tab");
  assert.equal(active(), first);
  key(first, "Tab", { shiftKey: true });
  assert.equal(active(), last);
});

test("Space on a window shape opens that window's entity", () => {
  openDoors();
  const shape = root().querySelector('path.gl[data-more="binary_sensor.wfr"]');
  shape.focus();
  key(shape, " ");
  assert.deepEqual(infos, ["binary_sensor.wfr"]);
});

test("keyboard focus stays on the same control across a state update", () => {
  const btn = root().querySelector('button[data-act="popup"][data-tab="doors"]');
  btn.focus();
  setHass({ "binary_sensor.fl": "on" });
  assert.equal(active().dataset.act, "popup");
  assert.equal(active().dataset.tab, "doors");
});

test("a focused slider is not replaced; the update lands after it loses focus", () => {
  const slider = root().querySelector('input[type="range"]');
  slider.focus();
  setHass({ "sensor.soc": "65" });
  assert.equal(root().querySelector('input[type="range"]'), slider);
  assert.ok(root().textContent.includes("64 %"));
  slider.blur();
  setHass({ "sensor.soc": "66" });
  assert.ok(root().textContent.includes("66 %"));
});

test("an unavailable lock reads as unknown, never as locked", () => {
  setHass({ "lock.car": "unavailable" });
  const lockButton = root().querySelector("button.ic");
  assert.ok(lockButton.textContent.includes("Lock state unknown"));
  assert.ok(!lockButton.classList.contains("ok"));
  openDoors();
  assert.equal(root().querySelector('.dlg [data-act="lock"]'), null);
});

test("a known lock still offers to unlock and asks the lock service", () => {
  openDoors();
  root().querySelector('[data-act="lock"]').click();
  assert.deepEqual(calls, [["lock", "unlock", { entity_id: "lock.car" }]]);
});

test("the temperature unit follows Home Assistant", () => {
  assert.equal(card._temp(21.5), "21.5 °C");
  setHass({}, { unit: "°F" });
  assert.equal(card._temp(70.7), "70.7 °F");
});

test("charging shows the band even when the car reports no charge target", () => {
  setHass({}, { skip: ["number.target"] });
  assert.ok(root().querySelector(".band"));
});

test("every cell of the charging band has an icon, a value and a label", () => {
  setHass({
    "sensor.rate": "20",
    "sensor.done": "2026-11-20T22:51:00+00:00",
  });
  const cells = [...root().querySelectorAll(".band .cell")];
  assert.ok(cells.length >= 1);
  for (const cell of cells) {
    assert.ok(cell.querySelector("ha-icon.ci"), "icon");
    assert.ok(cell.querySelector(".v").textContent.trim(), "value");
    assert.ok(cell.querySelector(".k").textContent.trim(), "label");
  }
});

// Local-time dates and a pinned clock, so the result does not depend on when or where the tests run.
const at = (day, h, m = 0) => new Date(2026, 10, day, h, m);
const pin = (d) => { card._now = () => d; };

test("a finish time today carries no day", () => {
  pin(at(21, 10));
  assert.equal(card._dayOf(at(21, 11, 30).toISOString()), "");
});

test("a finish time tomorrow says tomorrow, and a later one the weekday", () => {
  pin(at(21, 22));
  assert.equal(card._dayOf(at(22, 4, 10).toISOString()).toLowerCase(), "tomorrow");
  const later = card._dayOf(at(24, 10).toISOString());
  assert.ok(later && later.toLowerCase() !== "tomorrow", later);
});

test("the band says tomorrow next to the finish label when it ends after midnight", () => {
  pin(at(21, 22));
  setHass({ "sensor.done": at(22, 4, 10).toISOString() });
  const label = root().querySelector(".band .cell:last-child .k").textContent;
  assert.match(label, /^done tomorrow$/i);
});

test("a language the card has no texts for does not mix in foreign dates", () => {
  card.hass = { ...build(), language: "fr" };
  assert.equal(card._locale(), "en");
  pin(at(21, 22));
  assert.equal(card._dayOf(at(22, 4).toISOString()).toLowerCase(), "tomorrow");
});

test("an invalid finish time has no day", () => {
  assert.equal(card._dayOf("not a date"), "");
});

const zones = () => [...root().querySelectorAll("button[data-toggle]")].map((b) => b.dataset.toggle).filter((id) => /^switch\.z/.test(id));

test("the seat and zone buttons are hidden unless a card option is on", () => {
  assert.deepEqual(zones(), []);
});

test("the front option shows the two front zones, labelled by position", () => {
  card.setConfig({ device_id: "dev1", show_seats_front: true });
  setHass({});
  assert.deepEqual(zones(), ["switch.zfl", "switch.zfr"]);
  const labels = [...root().querySelectorAll("button[data-toggle]")].map((b) => b.textContent.trim());
  assert.ok(labels.includes("Front left") && labels.includes("Front right"), labels.join("|"));
});

test("the rear option shows the two rear zones only", () => {
  card.setConfig({ device_id: "dev1", show_seats_rear: true });
  setHass({});
  assert.deepEqual(zones(), ["switch.zrl", "switch.zrr"]);
});

test("front and rear are separate rows", () => {
  card.setConfig({ device_id: "dev1", show_seats_front: true, show_seats_rear: true });
  setHass({});
  const rows = [...root().querySelectorAll(".pills")].filter((r) => r.querySelector('button[data-toggle^="switch.z"]'));
  assert.equal(rows.length, 2);
  assert.deepEqual([...rows[0].querySelectorAll("button")].map((b) => b.dataset.toggle), ["switch.zfl", "switch.zfr"]);
  assert.deepEqual([...rows[1].querySelectorAll("button")].map((b) => b.dataset.toggle), ["switch.zrl", "switch.zrr"]);
});

test("the single option of earlier versions still means the front zones", () => {
  card.setConfig({ device_id: "dev1", show_seats: true });
  setHass({});
  assert.deepEqual(zones(), ["switch.zfl", "switch.zfr"]);
});

test("a car without rear zones shows no rear row even when the option is on", () => {
  card.setConfig({ device_id: "dev1", show_seats_rear: true });
  setHass({}, { skip: ["switch.zrl", "switch.zrr"] });
  assert.deepEqual(zones(), []);
});

test("the temperature stepper has real labels", () => {
  card._ui.tempDraft = undefined;
  setHass({ "climate.car": "heat" });
  const labels = [...root().querySelectorAll("button.stp")].map((b) => b.getAttribute("aria-label"));
  assert.deepEqual(labels, ["Lower temperature", "Raise temperature"]);
});

// --- climate panel ------------------------------------------------------------------

const running = { "climate.car": "heat" };

test("a running climatisation shows what it does and offers to stop it", () => {
  setHass(running);
  const stop = root().querySelector('[data-act="climate-off"]');
  assert.ok(stop);
  assert.equal(root().querySelector('[data-act="climate-on"]'), null);
  assert.ok(root().querySelector(".cstatus"));
  stop.click();
  assert.deepEqual(calls, [["climate", "turn_off", { entity_id: "climate.car" }]]);
});

test("a pressed climate button shows it is waiting, then settles", () => {
  root().querySelector('[data-act="climate-on"]').click();
  assert.ok(root().querySelector('[data-act="climate-on"]').classList.contains("wait"));
  tick(5000);
  assert.ok(!root().querySelector('[data-act="climate-on"]').classList.contains("wait"));
});

const rejecting = (message) => ({
  ...build(),
  callService: (d, s, x) => {
    calls.push([d, s, x]);
    return Promise.reject(new Error(message));
  },
});

test("a rejected action is shown on the card and the button stops waiting", async () => {
  card.hass = rejecting("Audi wake_vehicle_modern request failed; check the logs");
  root().querySelector('[data-act="climate-on"]').click();
  assert.ok(root().querySelector('[data-act="climate-on"]').classList.contains("wait"));
  await settle();
  const note = root().querySelector(".note.err");
  assert.ok(note, "an error note");
  assert.equal(note.getAttribute("role"), "alert");
  assert.match(note.textContent, /Start climate failed/);
  assert.match(note.textContent, /request failed; check the logs/);
  assert.ok(!root().querySelector('[data-act="climate-on"]').classList.contains("wait"));
});

test("the error note goes away by itself", async () => {
  card.hass = rejecting("nope");
  root().querySelector('[data-act="climate-on"]').click();
  await settle();
  assert.ok(root().querySelector(".note.err"));
  tick(8000);
  assert.equal(root().querySelector(".note.err"), null);
});

test("a call that throws instead of rejecting is shown the same way", async () => {
  card.hass = { ...build(), callService: () => { throw new Error("boom"); } };
  root().querySelector('[data-act="climate-on"]').click();
  await settle();
  assert.match(root().querySelector(".note.err").textContent, /boom/);
});

test("a refresh that fails stops the busy state and says so", async () => {
  card.hass = rejecting("Audi did not answer");
  card._refresh();
  assert.ok(card._ui.refreshing);
  await settle();
  assert.equal(card._ui.refreshing, false);
  assert.ok(root().querySelector(".note.err"));
});

test("a successful action shows no error", async () => {
  root().querySelector('[data-act="climate-on"]').click();
  await settle();
  assert.equal(root().querySelector(".note.err"), null);
});

test("a failure while the target slider has focus is still drawn", async () => {
  const slider = root().querySelector('input[data-slider="target"]');
  slider.focus();
  assert.equal(card.shadowRoot.activeElement, slider);
  card.hass = rejecting("Audi did not answer");
  card._call("number", "set_value", { entity_id: "number.target", value: 90 });
  await settle();
  assert.ok(root().querySelector(".note.err"), "the note is drawn");
  assert.notEqual(card.shadowRoot.activeElement?.tagName, "INPUT");
});

test("a failed lock command is shown inside the open popup, not behind it", async () => {
  openDoors();
  card.hass = rejecting("Audi rejected the command");
  root().querySelector('[data-act="lock"]').click();
  await settle();
  assert.ok(root().querySelector(".dlg .note.err"), "inside the dialog");
  assert.match(root().querySelector(".dlg .note.err").textContent, /Unlock failed/);
  assert.equal(root().querySelectorAll(".note.err").length, 1, "once, not also behind it");
});

test("the error text is shown as text, never as markup", async () => {
  card.hass = rejecting('<img src=x onerror="window.pwned=1"><b>bold</b>');
  root().querySelector('[data-act="climate-on"]').click();
  await settle();
  const note = root().querySelector(".note.err");
  assert.equal(note.querySelector("img, b"), null);
  assert.match(note.textContent, /<img src=x/);
});

test("a long message is cut with an ellipsis", async () => {
  card.hass = rejecting("x".repeat(300));
  root().querySelector('[data-act="climate-on"]').click();
  await settle();
  const sub = root().querySelector(".note.err .sub").textContent;
  assert.equal(sub.length, 140);
  assert.ok(sub.endsWith("…"));
});

test("a failure resets only the state of its own action", async () => {
  card._ui.tempDraft = 25;
  card.hass = rejecting("no");
  card._call("lock", "unlock", { entity_id: "lock.car" });
  await settle();
  assert.equal(card._ui.tempDraft, 25, "a lock failure keeps the temperature draft");
  card._call("climate", "set_temperature", { entity_id: "climate.car", temperature: 22 });
  await settle();
  assert.equal(card._ui.tempDraft, null, "a temperature failure drops it");
});

test("Home Assistant is told not to show its own toast", () => {
  const seen = [];
  card.hass = { ...build(), callService: (...args) => { seen.push(args); } };
  card._call("climate", "turn_on", { entity_id: "climate.car" });
  assert.equal(seen[0][4], false);
});

test("the sent temperature stays shown until the car reports it", () => {
  const plus = () => root().querySelector('button[data-step="1"]');
  plus().click(); plus().click(); plus().click();
  tick(700);
  tick(3000);
  assert.ok(root().querySelector('[data-live="temp"]').textContent.includes("22.5"), "still the sent value after 3 s");
  const base = build();
  card.hass = { ...base, states: { ...base.states, "climate.car": { ...base.states["climate.car"], attributes: { ...base.states["climate.car"].attributes, temperature: 22.5 } } } };
  assert.equal(card._ui.tempDraft, null, "settled once the car reports it");
});

test("a second click restarts the wait instead of ending with the first timer", () => {
  const on = () => root().querySelector('[data-act="climate-on"]');
  on().click();
  tick(3000);
  on().click();
  tick(2500);
  assert.ok(on().classList.contains("wait"), "5.5 s after the first click, 2.5 s after the second");
  tick(2600);
  assert.ok(!on().classList.contains("wait"));
});

test("removing the card cancels a pending temperature change", () => {
  const plus = root().querySelector('button[data-step="1"]');
  plus.click();
  card.remove();
  tick(700);
  assert.deepEqual(calls, []);
});

test("the stepper sends one temperature after the taps stop", () => {
  const plus = () => root().querySelector('button[data-step="1"]');
  plus().click();
  plus().click();
  plus().click();
  assert.ok(root().querySelector('[data-live="temp"]').textContent.includes("22.5"));
  assert.deepEqual(calls, []);
  tick(700);
  assert.deepEqual(calls, [["climate", "set_temperature", { entity_id: "climate.car", temperature: 22.5 }]]);
});

test("the stepper stops at the car's limits", () => {
  const plus = () => root().querySelector('button[data-step="1"]');
  for (let i = 0; i < 40; i++) plus().click();
  tick(700);
  assert.equal(calls[0][2].temperature, 30);
});

test("choosing a climatisation mode calls the select service", () => {
  const select = root().querySelector("select[data-select]");
  select.value = "economy";
  select.dispatchEvent(new window.Event("change", { bubbles: true, composed: true }));
  assert.deepEqual(calls, [["select", "select_option", { entity_id: "select.mode", option: "economy" }]]);
});

// --- long press refresh ---------------------------------------------------------------

test("holding the title asks the car for fresh data", () => {
  pointer(title(), "pointerdown");
  tick(599);
  assert.deepEqual(calls, []);
  tick(1);
  assert.deepEqual(calls, [["button", "press", { entity_id: "button.refresh" }]]);
});

test("the click that ends a long press does not also open the device page", () => {
  pointer(title(), "pointerdown");
  tick(600);
  pointer(title(), "pointerup");
  title().click();
  assert.deepEqual(pushes, []);
});

test("releasing early or dragging away cancels the press", () => {
  pointer(title(), "pointerdown");
  tick(300);
  pointer(title(), "pointerup");
  tick(600);
  assert.deepEqual(calls, []);
  pointer(title(), "pointerdown", 0, 0);
  pointer(title(), "pointermove", 40, 0);
  tick(600);
  assert.deepEqual(calls, []);
});

test("a second refresh is ignored while the first is still showing", () => {
  pointer(title(), "pointerdown");
  tick(600);
  pointer(title(), "pointerup");
  pointer(title(), "pointerdown");
  tick(600);
  assert.equal(calls.length, 1);
  tick(4000);
  assert.equal(root().querySelector(".busy"), null);
});

// --- editor ---------------------------------------------------------------------------

function editor({ config = { device_id: "dev1" }, ws, language = "en" } = {}) {
  const el = window.document.createElement("audi-connect-card-editor");
  window.document.body.appendChild(el);
  el.setConfig(config);
  el.hass = { ...build(), language, callWS: ws ?? (async () => []) };
  return el;
}
const settle = () => new Promise((r) => setImmediate(r));

test("the editor offers the pictures the integration lists", async () => {
  const el = editor({ ws: async (msg) => (msg.type === "audiconnect/list_images" ? [{ path: "/local/a.png", name: "a.png" }] : []) });
  await settle();
  const field = el._form.schema.find((f) => f.name === "image_local");
  assert.deepEqual(field.selector.select.options.map((o) => o.value), ["", "/local/a.png"]);
});

test("a picture that is gone from the folder stays selectable", async () => {
  const el = editor({ config: { device_id: "dev1", image_local: "/local/old.png" } });
  await settle();
  const field = el._form.schema.find((f) => f.name === "image_local");
  assert.ok(field.selector.select.options.some((o) => o.value === "/local/old.png"));
});

test("a failing image list costs only the list", async () => {
  const el = editor({ ws: async () => { throw new Error("not an admin"); } });
  await settle();
  const field = el._form.schema.find((f) => f.name === "image_local");
  assert.deepEqual(field.selector.select.options.map((o) => o.value), [""]);
});

test("empty choices are left out of the saved config", async () => {
  const el = editor();
  await settle();
  let saved;
  el.addEventListener("config-changed", (e) => { saved = e.detail.config; });
  el._form.dispatchEvent(new window.CustomEvent("value-changed", { detail: { value: { device_id: "dev1", name: "", image_local: "", show_logo: false } } }));
  assert.deepEqual(saved, { device_id: "dev1", show_logo: false });
});

test("the seat options are indented sub-items under 'show climate', front and rear", async () => {
  const el = editor();
  await settle();
  assert.deepEqual(el._seatForm.schema.map((f) => f.name), ["show_seats_front", "show_seats_rear"]);
  assert.equal(el._seatBox.hidden, false);
  assert.equal(el._form.data.show_seats_front, false);
  assert.equal(el._form.data.show_seats_rear, false);
  assert.match(el._seatForm.computeLabel({ name: "show_seats_front" }), /front seat\/zone/);
  assert.match(el._seatForm.computeLabel({ name: "show_seats_rear" }), /rear seat\/zone/);
  // Order: the main form (ending with show climate), then the indented box, then the rest.
  assert.deepEqual([...el.children], [el._form, el._seatBox, el._restForm, el._rowsBox]);
  assert.equal(el._form.schema.at(-1).name, "show_climate");
  assert.equal(el._restForm.schema[0].name, "show_stats");
  assert.match(el._seatBox.style.marginLeft, /28px/);
  assert.ok(el._seatBox.contains(el._seatForm));
});

test("each seat option is offered only when the car has that end's zones", async () => {
  const make = (skip) => {
    const e = window.document.createElement("audi-connect-card-editor");
    window.document.body.appendChild(e);
    e.setConfig({ device_id: "dev1" });
    e.hass = { ...build({}, { skip }), callWS: async () => [] };
    return e;
  };
  const noRear = make(["switch.zrl", "switch.zrr"]);
  const noFront = make(["switch.zfl", "switch.zfr"]);
  const none = make(["switch.zfl", "switch.zfr", "switch.zrl", "switch.zrr"]);
  await settle();
  assert.deepEqual(noRear._seatForm.schema.map((f) => f.name), ["show_seats_front"]);
  assert.deepEqual(noFront._seatForm.schema.map((f) => f.name), ["show_seats_rear"]);
  assert.equal(none._seatBox.hidden, true);
});

test("the seat options are switched off together with the climate option", async () => {
  const el = editor({ config: { device_id: "dev1", show_climate: false } });
  await settle();
  assert.equal(el._seatForm.disabled, true);
  const on = editor({ config: { device_id: "dev1", show_climate: true } });
  await settle();
  assert.equal(on._seatForm.disabled, false);
});

test("a config with the old option opens with the front option on, and saves without it", async () => {
  const el = editor({ config: { device_id: "dev1", show_seats: true } });
  await settle();
  assert.equal(el._form.data.show_seats_front, true);
  let saved;
  el.addEventListener("config-changed", (e) => { saved = e.detail.config; });
  el._seatForm.dispatchEvent(new window.CustomEvent("value-changed", { detail: { value: { ...el._seatForm.data, show_seats_rear: true } } }));
  assert.equal(saved.show_seats_front, true);
  assert.equal(saved.show_seats_rear, true);
  assert.ok(!("show_seats" in saved), "the old key is gone");
});

test("a change in the seat form keeps the rest of the config", async () => {
  const el = editor({ config: { device_id: "dev1", name: "Mine" } });
  await settle();
  let saved;
  el.addEventListener("config-changed", (e) => { saved = e.detail.config; });
  el._seatForm.dispatchEvent(new window.CustomEvent("value-changed", { detail: { value: { ...el._seatForm.data, show_seats_front: true } } }));
  assert.equal(saved.show_seats_front, true);
  assert.equal(saved.device_id, "dev1");
  assert.equal(saved.name, "Mine");
});

test("the editor is labelled in the user's language", async () => {
  const el = editor({ language: "de" });
  await settle();
  assert.equal(el._form.computeLabel({ name: "show_trip_last" }), "Letzte Fahrt anzeigen");
  assert.equal(el._form.computeLabel({ name: "show_trip_long" }), "Langzeit anzeigen");
  assert.equal(el._rowsForm.computeLabel({ name: "stats_rows" }), "Angezeigte Fahrzeugdetails");
});

// ---- the car drawing in the doors and windows popup ----------------------------

const car = () => root().querySelector("svg.car");

test("the car has a click zone for every door, the hood, the tailgate and each window", () => {
  openDoors();
  const zones = [...car().querySelectorAll("path.hit")].map((e) => e.dataset.more).sort();
  assert.deepEqual(zones, [
    "binary_sensor.fl", "binary_sensor.fr", "binary_sensor.hood", "binary_sensor.rl",
    "binary_sensor.rr", "binary_sensor.trunk", "binary_sensor.wfl", "binary_sensor.wfr",
    "binary_sensor.wrl", "binary_sensor.wrr",
  ]);
});

test("a click on a door zone opens that door's entity", () => {
  openDoors();
  car().querySelector('path.seg[data-more="binary_sensor.fr"]').dispatchEvent(
    new window.MouseEvent("click", { bubbles: true, composed: true }),
  );
  assert.deepEqual(infos, ["binary_sensor.fr"]);
});

test("a locked closed car shows only lock badges, an open door swings out", () => {
  openDoors();
  assert.equal(car().querySelectorAll(".pn.open").length, 0);
  assert.equal(car().querySelectorAll('g[transform^="rotate("]').length, 0);
  setHass({ "binary_sensor.fr": "on" });
  openDoors();
  assert.equal(car().querySelectorAll(".pn.open").length, 1);
  assert.equal(car().querySelectorAll('g[transform^="rotate("]').length, 1);
});

test("an unlocked car marks its doors as unlocked, an unknown lock state does not claim locked", () => {
  setHass({ "lock.car": "unlocked" });
  openDoors();
  assert.equal(car().querySelectorAll(".pn.ul").length, 4 + 1);
  setHass({ "lock.car": "unknown" });
  assert.equal(car().querySelectorAll(".pn.ul").length, 0);
  assert.equal(car().querySelectorAll(".pn.unk").length, 4 + 1);
});

test("an open window is drawn amber on the doors tab and on the windows tab", () => {
  openDoors();
  assert.equal(car().querySelectorAll(".wn.open").length, 1);
  root().querySelector('[data-tab-set="windows"]').click();
  assert.equal(car().querySelectorAll(".wn.open").length, 1);
});

test("the open hood and tailgate are drawn folded up, the click zones stay", () => {
  setHass({ "binary_sensor.hood": "on", "binary_sensor.trunk": "on" });
  openDoors();
  assert.equal(car().querySelectorAll(".pn.open").length, 2);
  assert.ok(car().querySelector('path.seg[data-more="binary_sensor.hood"]'));
  assert.ok(car().querySelector('path.seg[data-more="binary_sensor.trunk"]'));
});

test("each status badge is a filled circle in the colour of its state", () => {
  openDoors();
  assert.equal(car().querySelectorAll("circle.bd.lk").length, 5);
  setHass({ "lock.car": "unlocked", "binary_sensor.fr": "on" });
  assert.equal(car().querySelectorAll("circle.bd.ul").length, 3 + 1);
  assert.equal(car().querySelectorAll("circle.bd.open").length, 1);
  setHass({ "lock.car": "unknown" });
  assert.equal(car().querySelectorAll("circle.bd.unk").length, 5);
});

test("the badges stay inside the drawing", () => {
  openDoors();
  const [, , w, h] = car().getAttribute("viewBox").split(" ").map(Number);
  for (const g of car().querySelectorAll('g[style*="pointer-events"]')) {
    const m = /translate\(([\d.]+) ([\d.]+)\)/.exec(g.getAttribute("transform"));
    const [x, y] = [Number(m[1]), Number(m[2])];
    assert.ok(x - 13 >= 0 && x + 13 <= w && y - 13 >= 0 && y + 13 <= h, `${x},${y}`);
  }
});

// ---- choosing what the trips and the vehicle details show -----------------------------

// The fixture has no trip or detail entities, so these tests add the ones they need.
function withEntities(list, config) {
  const hass = build();
  for (const [id, tk, state, attrs = {}] of list) {
    hass.entities[id] = { entity_id: id, platform: "audiconnect", device_id: "dev1", translation_key: tk };
    hass.states[id] = { entity_id: id, state, attributes: { friendly_name: tk, ...attrs }, last_updated: "2026-11-20T10:00:00+00:00" };
  }
  card.setConfig({ device_id: "dev1", ...config });
  card.hass = hass;
}
const TRIPS = [
  ["sensor.lt", "last_trip_distance", "12", { unit_of_measurement: "km" }],
  ["sensor.tt", "trip_totals_distance", "3400", { unit_of_measurement: "km" }],
];
const DETAILS = [
  ["sensor.pt", "park_time", "2026-11-20T08:00:00+00:00"],
  ["sensor.oc", "outdoor_temperature", "9", { unit_of_measurement: "°C" }],
  ["sensor.ins", "service_inspection_time", "304", { unit_of_measurement: "d" }],
];
const tripIds = () => [...root().querySelectorAll("details")].map((d) => d.dataset.id).filter((i) => i.startsWith("trip-"));
const factLabels = () => [...root().querySelectorAll(".fact .fl")].map((e) => e.textContent);

test("the last trip and the long-term trip are shown by default", () => {
  withEntities(TRIPS, {});
  assert.deepEqual(tripIds(), ["trip-last", "trip-long"]);
});

test("the last trip and the long-term trip can be switched off one by one", () => {
  withEntities(TRIPS, { show_trip_long: false });
  assert.deepEqual(tripIds(), ["trip-last"]);
  withEntities(TRIPS, { show_trip_last: false });
  assert.deepEqual(tripIds(), ["trip-long"]);
});

test("the older show_trips option still switches both trips", () => {
  withEntities(TRIPS, { show_trips: false });
  assert.deepEqual(tripIds(), []);
  withEntities(TRIPS, { show_trips: false, show_trip_long: true });
  assert.deepEqual(tripIds(), ["trip-long"]);
});

test("the vehicle details show every row the car reports unless some are chosen", () => {
  withEntities(DETAILS, {});
  assert.deepEqual(factLabels(), ["Parked for", "Outside temperature", "Inspection in"]);
  withEntities(DETAILS, { stats_rows: ["parked", "inspection_days"] });
  assert.deepEqual(factLabels(), ["Parked for", "Inspection in"]);
});

test("the editor offers only the detail rows the car reports, all ticked", async () => {
  const el = editor();
  el._hass = { ...el._hass, entities: withRows(el._hass.entities, DETAILS) };
  el._render();
  const field = el._rowsForm.schema[0];
  assert.deepEqual(field.selector.select.options.map((o) => o.value), ["parked", "outdoor", "inspection_days"]);
  assert.equal(field.selector.select.multiple, true);
  assert.deepEqual(el._rowsForm.data.stats_rows, ["parked", "outdoor", "inspection_days"]);
  assert.equal(el._rowsBox.hidden, false);
});

test("ticking every detail row is saved as not choosing, so new rows still show", async () => {
  const el = editor();
  el._hass = { ...el._hass, entities: withRows(el._hass.entities, DETAILS) };
  el._render();
  let saved;
  el.addEventListener("config-changed", (e) => { saved = e.detail.config; });
  el._rowsForm.dispatchEvent(new window.CustomEvent("value-changed", { detail: { value: { device_id: "dev1", stats_rows: ["parked", "outdoor", "inspection_days"] } } }));
  assert.equal("stats_rows" in saved, false);
  el._rowsForm.dispatchEvent(new window.CustomEvent("value-changed", { detail: { value: { device_id: "dev1", stats_rows: ["parked"] } } }));
  assert.deepEqual(saved.stats_rows, ["parked"]);
});

test("the editor saves the two trip options and drops show_trips", async () => {
  const el = editor({ config: { device_id: "dev1", show_trips: false } });
  await settle();
  assert.equal(el._form.data.show_trip_last, false);
  assert.equal(el._form.data.show_trip_long, false);
  let saved;
  el.addEventListener("config-changed", (e) => { saved = e.detail.config; });
  el._form.dispatchEvent(new window.CustomEvent("value-changed", { detail: { value: { ...el._form.data, show_trip_last: true } } }));
  assert.equal(saved.show_trip_last, true);
  assert.equal("show_trips" in saved, false);
});

function withRows(entities, list) {
  const out = { ...entities };
  for (const [id, tk] of list) out[id] = { entity_id: id, platform: "audiconnect", device_id: "dev1", translation_key: tk };
  return out;
}

// ---- the hood lock ---------------------------------------------------------------------

const hoodBadges = () => [...root().querySelectorAll("svg.car .bd")].length;

test("an unlocked hood is drawn as unlocked and gets a badge on the doors tab", () => {
  withEntities([["binary_sensor.hl", "hood_unlocked", "on"]], {});
  openDoors();
  assert.ok(root().querySelector("svg.car .pn.ul"), "the hood panel is marked unlocked");
  const before = hoodBadges();
  withEntities([["binary_sensor.hl", "hood_unlocked", "off"]], {});
  openDoors();
  assert.equal(root().querySelector("svg.car .pn.ul"), null);
  assert.equal(hoodBadges(), before, "locked or not, the hood has its badge");
});

test("without a hood lock sensor the hood has no lock badge", () => {
  withEntities([], {});
  openDoors();
  const without = hoodBadges();
  withEntities([["binary_sensor.hl", "hood_unlocked", "off"]], {});
  openDoors();
  assert.equal(hoodBadges(), without + 1);
});
