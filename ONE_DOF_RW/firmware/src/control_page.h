#pragma once

static const char CONTROL_PAGE[] PROGMEM = R"HTML(<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reaction wheel control</title><style>
body{font:18px system-ui;background:#101a26;color:#eef4ff;margin:auto;padding:24px;max-width:480px}
section{background:#1b2b3d;padding:22px;border-radius:16px;margin:20px 0}
h1{font-size:26px}button,input,select{font:inherit;padding:14px;border-radius:10px;border:0;box-sizing:border-box}
button{cursor:pointer;background:#5cb9ff;color:#071421;margin:8px 0;min-height:52px}
button:disabled{opacity:.5;cursor:default}#stop,#manual-stop{background:#ff7b7b;width:100%}#start{width:100%}
.directions{display:flex;gap:12px}.directions button{flex:1}
input,select{width:100%;margin:10px 0}small{color:#c6d4e5}#message{min-height:48px}
dl{display:grid;grid-template-columns:1fr 1fr;gap:12px}dd{margin:0;text-align:right}
</style></head><body><h1>Reaction wheel</h1>
<section><strong id="state">Connecting...</strong>
<dl><dt>Y rotation</dt><dd id="rate">-- deg/s</dd><dt>Motor PWM</dt><dd id="pwm">-- / 255</dd>
<dt>Active Kp</dt><dd id="gain">--</dd><dt>Active Ki</dt><dd id="ki-value">--</dd>
<dt>Integral correction</dt><dd id="integral">-- PWM</dd></dl>
<button id="start" disabled>Enable automatic control</button><button id="stop">Disable control</button>
<small>Keep this page open. Losing contact for 2 seconds disables control.
Zero PWM lets the motor coast; the flywheel may still move.</small></section>
<section><h2>Motor direction</h2>
<button id="invert-direction" disabled>Motor direction: connecting...</button><br>
<small>Tap to invert automatic and manual motor direction. This turns control OFF;
enable again to test. Reboot restores INVERTED.</small></section>
<section><h2>Manual wheel</h2>
<label for="throttle">Throttle: <output id="throttle-value">0% PWM</output></label>
<input id="throttle" type="range" min="0" max="100" step="1" value="0">
<div class="directions"><button id="left" disabled>Turn left</button><button id="right" disabled>Turn right</button></div>
<div class="directions"><button id="ramp-left" disabled>Ramp left</button><button id="ramp-right" disabled>Ramp right</button></div>
<small>Ramp test: 0 to the selected throttle in 5 seconds, hold 2 seconds, then PWM OFF.
Keep this page open. Stop wheel cancels the test; the wheel then coasts.</small>
<button id="apply-throttle" disabled>Apply throttle</button><button id="manual-stop">Stop wheel</button>
<p>Manual throttle limit: <strong id="applied-throttle">0% PWM</strong></p>
<small>Choose throttle, then a direction. The wheel runs until Stop wheel or a lost connection.
Manual mode turns automatic control OFF. Apply throttle updates the running manual command.
PWM is not measured wheel speed. Left/right depend on wheel mounting and motor wiring.</small></section>
<section><label for="kp">Kp (PWM per deg/s)</label>
<input id="kp" type="number" min="0" max="20" step="any" value="2" inputmode="decimal">
<button id="apply" disabled>Apply Kp</button><br>
<small>Range 0 to 20. Changes apply immediately. Reboot restores Kp = 2 and control OFF.</small>
</section><section><label for="ki">Ki (PWM per degree of accumulated rate error)</label>
<input id="ki" type="number" min="0" max="20" step="any" value="0" inputmode="decimal">
<button id="apply-ki" disabled>Apply Ki</button><br>
<small>Ki = 0 disables integral control. Range 0 to 20. Accumulation uses elapsed time,
ignores the +/-2 deg/s deadband, and stops growing into PWM saturation.
The integral can keep a correction at zero rate. Changing either gain clears it;
Stop, mode changes, calibration, faults and disconnects clear it too.
Reboot restores Ki = 0.</small>
</section><section><label for="gyro-range">MPU6050 gyro range</label>
<select id="gyro-range"><option value="250">+/-250 deg/s (finer resolution)</option>
<option value="500" selected>+/-500 deg/s</option><option value="1000">+/-1000 deg/s</option>
<option value="2000">+/-2000 deg/s (fastest rotation)</option></select>
<button id="apply-range" disabled>Apply range &amp; calibrate</button>
<dl><dt>Active range</dt><dd id="range-value">--</dd><dt>Sensitivity</dt><dd id="sensitivity">--</dd>
<dt>Filter</dt><dd id="filter">--</dd></dl>
<small>Changing range turns control OFF. Keep the sensor still for calibration,
then explicitly enable again. Lower ranges resolve smaller changes but clip sooner.
Reboot restores +/-500 deg/s. Terminal CSV contains readings and these settings.</small>
</section><p id="message" role="status" aria-live="polite"></p>
<script>
const $ = id => document.getElementById(id);
// A new page gets a new heartbeat owner; reopening cannot silently keep control on.
const owner = String(Math.floor(Math.random() * 4294967294) + 1);
let ownsControl = false, ready = false, editing = false, busy = false;
let requestQueue = Promise.resolve(), commandVersion = 0, commandsPending = 0;
let rangeEditing = false;
let manualDirection = 0;
let motorInverted = true;
let kiEditing = false;
$('ki').addEventListener('input', () => kiEditing = true);
$('kp').addEventListener('input', () => editing = true);
$('gyro-range').addEventListener('change', () => rangeEditing = true);
$('throttle').addEventListener('input', () => $('throttle-value').textContent = $('throttle').value + '% PWM');
async function request(path, data) {
  const send = async () => {
    const response = await fetch(path, {method: data ? 'POST' : 'GET', cache:'no-store',
      headers: data ? {'Content-Type':'application/x-www-form-urlencoded','X-RW-Control':'1'} : {},
      body: data ? new URLSearchParams(data) : undefined,
      signal: AbortSignal.timeout(1200)});
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  };
  // Preserve click order: Disable must follow an outstanding Enable.
  const pending = requestQueue.then(send);
  requestQueue = pending.catch(() => {});
  return pending;
}
function render(s) {
  ready = true;
  $('state').textContent = s.fault ? 'FAULT: reset ESP32 to recalibrate' : s.calibrating ? 'Calibrating: keep sensor still' : s.manual ? (s.ramp ? 'Ramp ' : 'Manual ') + (s.direction < 0 ? 'LEFT' : 'RIGHT') + ': ' + s.throttle + '% PWM limit' : s.enabled ? 'Control ON' : 'Control OFF';
  $('rate').textContent = s.rate.toFixed(1) + ' deg/s';
  $('pwm').textContent = s.pwm + ' / 255';
  $('gain').textContent = String(s.kp);
  $('ki-value').textContent = String(s.ki);
  $('integral').textContent = s.integral.toFixed(1) + ' PWM';
  if (!kiEditing) $('ki').value = s.ki;
  if (!editing) $('kp').value = s.kp;
  $('start').disabled = s.fault || s.calibrating || s.enabled;
  $('apply').disabled = s.fault;
  $('apply-ki').disabled = s.fault;
  $('apply-range').disabled = s.fault || s.calibrating;
  motorInverted = s.inverted;
  $('invert-direction').textContent = 'Motor direction: ' + (motorInverted ? 'INVERTED' : 'NORMAL') + ' (tap to flip)';
  $('invert-direction').disabled = s.fault || s.calibrating;
  $('left').disabled = s.fault || s.calibrating;
  $('right').disabled = s.fault || s.calibrating;
  $('ramp-left').disabled = s.fault || s.calibrating;
  $('ramp-right').disabled = s.fault || s.calibrating;
  $('apply-throttle').disabled = s.fault || s.calibrating || s.ramp || !s.manual || !ownsControl;
  $('applied-throttle').textContent = (s.manual ? s.throttle : 0) + '% PWM';
  manualDirection = s.manual ? s.direction : 0;
  $('range-value').textContent = '+/-' + s.range + ' deg/s';
  $('sensitivity').textContent = s.lsb_per_dps + ' LSB/(deg/s)';
  $('filter').textContent = s.filter_hz + ' Hz';
  if (!rangeEditing && !s.calibrating) $('gyro-range').value = String(s.range);
  if (!s.enabled && !s.manual) ownsControl = false;
}
function lost(error) {
  ownsControl = false; ready = false;
  $('start').disabled = true; $('apply').disabled = true;
  $('apply-ki').disabled = true;
  $('apply-range').disabled = true;
  $('invert-direction').disabled = true;
  $('left').disabled = true; $('right').disabled = true; $('apply-throttle').disabled = true;
  $('ramp-left').disabled = true; $('ramp-right').disabled = true;
  $('state').textContent = 'Connection lost';
  $('message').textContent = 'Control times out within 2 seconds. Reconnect and explicitly enable again. ' + error.message;
}
$('start').onclick = async () => {
  if (!ready || commandsPending) return;
  const version = ++commandVersion;
  commandsPending++; $('start').disabled = true;
  try { const s = await request('/control', {enabled:'1',owner});
    if (version !== commandVersion) return;
    ownsControl = s.enabled;
    render(s); $('message').textContent = 'Control enabled.';
  } catch (e) { if (version === commandVersion) lost(e); }
  finally { commandsPending--; }
};
$('stop').onclick = async () => {
  const version = ++commandVersion;
  commandsPending++;
  ownsControl = false;
  try { const s = await request('/control', {enabled:'0'});
    if (version !== commandVersion) return;
    render(s); $('message').textContent = 'Control disabled.';
  } catch (e) { if (version === commandVersion) lost(e); }
  finally { commandsPending--; }
};
$('manual-stop').onclick = $('stop').onclick;
$('invert-direction').onclick = async () => {
  if (!ready || commandsPending || $('invert-direction').disabled) return;
  const version = ++commandVersion;
  commandsPending++; ownsControl = false;
  $('invert-direction').disabled = true; $('start').disabled = true;
  try { const s = await request('/motor-direction', {inverted:motorInverted ? '0' : '1'});
    if (version !== commandVersion) return;
    render(s); $('message').textContent = 'Motor direction changed. Control OFF; enable again to test.';
  } catch (e) { if (version === commandVersion) lost(e); }
  finally { commandsPending--; }
};
async function manualCommand(direction, update = false, ramp = false) {
  if (!ready || commandsPending || ![-1,1].includes(direction)) return;
  const text = $('throttle').value;
  const throttle = Number(text);
  if (!text.trim() || !Number.isInteger(throttle) || throttle < 0 || throttle > 100) {
    $('message').textContent = 'Choose a whole throttle percentage from 0 to 100.'; return;
  }
  if (ramp && throttle === 0) {
    $('message').textContent = 'Choose a throttle limit from 1 to 100% for the ramp test.'; return;
  }
  const version = ++commandVersion;
  commandsPending++;
  try { const s = await request('/manual', {direction:direction < 0 ? 'left' : 'right',
      throttle:text,owner,action:ramp ? 'ramp' : update ? 'update' : 'start'});
    if (version !== commandVersion) return;
    ownsControl = s.manual;
    render(s); $('message').textContent = ramp ? 'Ramp test started: 5 seconds up, 2 seconds hold, then PWM OFF. Stop wheel cancels.' : 'Manual wheel command applied. Use Stop wheel to stop PWM.';
  } catch (e) { if (version === commandVersion) lost(e); }
  finally { commandsPending--; }
}
$('left').onclick = () => manualCommand(-1);
$('right').onclick = () => manualCommand(1);
$('ramp-left').onclick = () => manualCommand(-1, false, true);
$('ramp-right').onclick = () => manualCommand(1, false, true);
$('apply-throttle').onclick = () => manualCommand(manualDirection, true);
$('apply').onclick = async () => {
  const value = Number($('kp').value);
  if (!$('kp').value.trim() || !Number.isFinite(value) || value < 0 || value > 20) {
    $('message').textContent = 'Enter a Kp from 0 to 20.'; return;
  }
  const version = commandVersion;
  try { const s = await request('/kp', {kp:$('kp').value});
    if (version !== commandVersion) return;
    editing = false;
    render(s); $('message').textContent = 'Kp updated.';
  } catch (e) { $('message').textContent = e.message; }
};
$('apply-ki').onclick = async () => {
  if (!ready || commandsPending) return;
  const text = $('ki').value;
  const value = Number(text);
  if (!text.trim() || !Number.isFinite(value) || value < 0 || value > 20) {
    $('message').textContent = 'Enter a Ki from 0 to 20.'; return;
  }
  const version = ++commandVersion;
  commandsPending++; $('apply-ki').disabled = true;
  try { const s = await request('/ki', {ki:text});
    if (version !== commandVersion) return;
    kiEditing = false; render(s);
    $('message').textContent = 'Ki updated; accumulated integral cleared.';
  } catch (e) { if (version === commandVersion) lost(e); }
  finally { commandsPending--; }
};
$('apply-range').onclick = async () => {
  const range = $('gyro-range').value;
  if (!['250','500','1000','2000'].includes(range) || commandsPending) return;
  const version = ++commandVersion;
  commandsPending++; ownsControl = false;
  $('start').disabled = true; $('apply-range').disabled = true;
  try { const s = await request('/gyro-range', {range});
    if (version !== commandVersion) return;
    rangeEditing = false; render(s);
    $('message').textContent = 'Keep sensor still during calibration. Enable control when ready.';
  } catch (e) { if (version === commandVersion) lost(e); }
  finally { commandsPending--; }
};
async function poll() {
  if (busy || commandsPending) return;
  const version = commandVersion;
  busy = true;
  try { const s = await request(ownsControl ? '/heartbeat' : '/status', ownsControl ? {owner} : undefined);
    if (version === commandVersion) render(s);
  } catch (e) { if (version === commandVersion) lost(e); }
  finally { busy = false; }
}
poll(); setInterval(poll, 500);
</script></body></html>)HTML";
