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
  ["number.target", "target_state_of_charge", "80", { min: 20, max: 100, step: 5 }],
  ["climate.car", "climatisation", "off", { temperature: 21, min_temp: 15, max_temp: 30, target_temp_step: 0.5 }],
  ["select.mode", "climatisation_mode", "comfort", { options: ["comfort", "economy"] }],
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

test("the editor is labelled in the user's language", async () => {
  const el = editor({ language: "de" });
  await settle();
  assert.equal(el._form.computeLabel({ name: "show_trips" }), "Fahrten anzeigen");
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
