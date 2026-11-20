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
];

let dom, window, card, calls, infos, pushes;

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
const openDoors = () => root().querySelector('button[data-act="popup"][data-tab="doors"]').click();

beforeEach(() => {
  dom = new JSDOM("<!doctype html><body></body>", { runScripts: "outside-only", pretendToBeVisual: true, url: "http://localhost/" });
  window = dom.window;
  window.confirm = () => true;
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
  const shape = root().querySelector('rect[data-more="binary_sensor.wfr"]');
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
