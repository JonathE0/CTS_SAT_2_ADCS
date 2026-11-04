const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const script = fs.readFileSync('src/control_page.h', 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
const flush = async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); };
const state = enabled => ({enabled, manual:false, direction:0, throttle:0, fault:false, calibrating:false, range:500,
  lsb_per_dps:65.5, filter_hz:21, kp:2, ki:0, integral:0, rate:12, inverted:true, ramp:false, pwm:enabled ? 20 : 0});

function page() {
  const elements = Object.fromEntries(['kp','state','rate','pwm','gain','start','stop','apply','message',
    'gyro-range','range-value','sensitivity','filter','apply-range',
    'left','right','manual-stop','throttle','throttle-value','apply-throttle','applied-throttle','invert-direction','ramp-left','ramp-right','ki','apply-ki','integral','ki-value']
    .map(id => [id, {value:'2', disabled:false, textContent:'', addEventListener(){}}]));
  const calls = [];
  let poll;
  const context = vm.createContext({document:{getElementById:id => elements[id]},
    URLSearchParams, AbortSignal, Math,
    fetch:(path, options) => new Promise(resolve => calls.push({path, options,
      respond:s => resolve({ok:true,json:async()=>s})})),
    setInterval:fn => poll = fn});
  vm.runInContext(script, context);
  return {elements, calls, poll:()=>poll()};
}

(async () => {
  // A Stop while Start is pending must be sent after Start, and must not
  // leave this page heartbeating a stale enabled state.
  const p = page(); await flush();
  p.calls[0].respond(state(false)); await flush();
  const start = p.elements.start.onclick(); await flush();
  assert.equal(p.calls[1].options.body.get('enabled'), '1');
  const stop = p.elements.stop.onclick(); await flush();
  assert.equal(p.calls.length, 2, 'Stop must wait for pending Start');
  p.calls[1].respond(state(true)); await flush();
  assert.equal(p.calls[2].options.body.get('enabled'), '0');
  p.calls[2].respond(state(false)); await Promise.all([start,stop]);
  assert.equal(p.elements.state.textContent, 'Control OFF');
  const polling = p.poll(); await flush();
  assert.equal(p.calls[3].path, '/status', 'Stopped page must not heartbeat');
  p.calls[3].respond(state(false)); await polling;

  // An earlier status poll must not discard a newly requested Enable.
  const q = page(); await flush();
  q.calls[0].respond(state(false)); await flush();
  const oldPoll = q.poll(); await flush();
  const enable = q.elements.start.onclick(); await flush();
  q.calls[1].respond(state(false)); await flush();
  q.calls[2].respond(state(true)); await Promise.all([oldPoll, enable]);
  const heartbeat = q.poll(); await flush();
  assert.equal(q.calls[3].path, '/heartbeat');
  q.calls[3].respond(state(true)); await heartbeat;
  assert.equal(q.elements.state.textContent, 'Control ON');
  q.elements.kp.value = '-1';
  await q.elements.apply.onclick();
  assert.equal(q.calls.length, 4, 'Invalid gain must not be sent');

  const r = page(); await flush();
  r.calls[0].respond(state(false)); await flush();
  assert.equal(String(r.elements['gyro-range'].value), '500');
  assert.equal(r.elements.sensitivity.textContent, '65.5 LSB/(deg/s)');
  r.elements['gyro-range'].value = '250';
  const changing = r.elements['apply-range'].onclick(); await flush();
  assert.equal(r.calls[1].path, '/gyro-range');
  assert.equal(r.calls[1].options.body.get('range'), '250');
  const calibrating = {...state(false), calibrating:true};
  r.calls[1].respond(calibrating); await changing;
  assert.equal(r.elements.start.disabled, true);
  assert.equal(r.elements['apply-range'].disabled, true);
  assert.match(r.elements.state.textContent, /[Cc]alibrat/);
  const finished = r.poll(); await flush();
  assert.equal(r.calls[2].path, '/status');
  r.calls[2].respond({...state(false), range:250, lsb_per_dps:131}); await finished;
  assert.equal(r.elements.start.disabled, false);
  assert.equal(r.elements['range-value'].textContent, '+/-250 deg/s');
  assert.equal(r.elements.state.textContent, 'Control OFF');

  const m = page(); await flush();
  m.calls[0].respond(state(false)); await flush();
  m.elements.throttle.value = '50';
  const left = m.elements.left.onclick(); await flush();
  assert.equal(m.calls[1].path, '/manual');
  assert.equal(m.calls[1].options.body.get('direction'), 'left');
  assert.equal(m.calls[1].options.body.get('throttle'), '50');
  assert.equal(m.calls[1].options.body.get('action'), 'start');
  const manual = {...state(false), manual:true, direction:-1, throttle:50, pwm:-128};
  m.calls[1].respond(manual); await left;
  assert.match(m.elements.state.textContent, /Manual LEFT/);
  const manualPoll = m.poll(); await flush();
  assert.equal(m.calls[2].path, '/heartbeat', 'Manual mode needs heartbeat despite auto enabled=false');
  m.calls[2].respond(manual); await manualPoll;
  m.elements.throttle.value = '75';
  const throttle = m.elements['apply-throttle'].onclick(); await flush();
  assert.equal(m.calls[3].options.body.get('direction'), 'left');
  assert.equal(m.calls[3].options.body.get('throttle'), '75');
  assert.equal(m.calls[3].options.body.get('action'), 'update');
  m.calls[3].respond({...manual, throttle:75}); await throttle;
  const right = m.elements.right.onclick(); await flush();
  const manualStop = m.elements['manual-stop'].onclick(); await flush();
  assert.equal(m.calls.length, 5, 'Stop must wait for pending direction command');
  m.calls[4].respond({...manual, direction:1}); await flush();
  assert.equal(m.calls[5].path, '/control');
  assert.equal(m.calls[5].options.body.get('enabled'), '0');
  m.calls[5].respond(state(false)); await Promise.all([right,manualStop]);
  assert.equal(m.elements.state.textContent, 'Control OFF');
  const stoppedPoll = m.poll(); await flush();
  assert.equal(m.calls[6].path, '/status');
  m.calls[6].respond({...state(false), calibrating:true}); await stoppedPoll;
  assert.equal(m.elements.left.disabled, true);
  assert.equal(m.elements.right.disabled, true);
  assert.equal(m.elements['apply-throttle'].disabled, true);
  // Direction changes are explicit, stop ownership, and do not re-enable control.
  const d = page(); await flush();
  d.calls[0].respond(state(false)); await flush();
  assert.match(d.elements['invert-direction'].textContent, /INVERTED/);
  const invert = d.elements['invert-direction'].onclick(); await flush();
  assert.equal(d.calls[1].path, '/motor-direction');
  assert.equal(d.calls[1].options.body.get('inverted'), '0');
  const duplicate = d.elements['invert-direction'].onclick(); await flush();
  assert.equal(d.calls.length, 2, 'Ignore a second click while inversion is pending');
  d.calls[1].respond({...state(false), inverted:false}); await Promise.all([invert,duplicate]);
  assert.match(d.elements['invert-direction'].textContent, /NORMAL/);
  const directionPoll = d.poll(); await flush();
  assert.equal(d.calls[2].path, '/status');
  d.calls[2].respond({...state(false), inverted:false, calibrating:true}); await directionPoll;
  assert.equal(d.elements['invert-direction'].disabled, true);
  { const r = page(); await flush();
  r.calls[0].respond(state(false)); await flush();
  r.elements.throttle.value = '50';
  const ramp = r.elements['ramp-right'].onclick(); await flush();
  assert.equal(r.calls[1].path, '/manual');
  assert.equal(r.calls[1].options.body.get('action'), 'ramp');
  assert.equal(r.calls[1].options.body.get('direction'), 'right');
  assert.equal(r.calls[1].options.body.get('throttle'), '50');
  const rampState = {...state(false), manual:true, ramp:true, direction:1, throttle:50, pwm:64};
  r.calls[1].respond(rampState); await ramp;
  assert.match(r.elements.state.textContent, /Ramp RIGHT/);
  assert.equal(r.elements['apply-throttle'].disabled, true);
  const rampPoll = r.poll(); await flush();
  assert.equal(r.calls[2].path, '/heartbeat');
  r.calls[2].respond(state(false)); await rampPoll;
  const finishedPoll = r.poll(); await flush();
  assert.equal(r.calls[3].path, '/status', 'Finished ramp must not heartbeat or restart');
  r.calls[3].respond({...state(false), fault:true}); await finishedPoll;
  assert.equal(r.elements['ramp-left'].disabled, true);
  assert.equal(r.elements['ramp-right'].disabled, true);
  }
  { const pi = page(); await flush();
    pi.calls[0].respond(state(false)); await flush();
    pi.elements.ki.value = '0.5';
    const gain = pi.elements['apply-ki'].onclick(); await flush();
    assert.equal(pi.calls[1].path, '/ki');
    assert.equal(pi.calls[1].options.body.get('ki'), '0.5');
    pi.calls[1].respond({...state(false), ki:0.5, integral:2.25}); await gain;
    assert.equal(pi.elements['ki-value'].textContent, '0.5');
    assert.equal(pi.elements.integral.textContent, '2.3 PWM');
    pi.elements.ki.value = '-1';
    await pi.elements['apply-ki'].onclick(); await flush();
    assert.equal(pi.calls.length, 2, 'Invalid Ki must not be sent');
  }
  console.log('PASS: page ordering, heartbeats, throttle, calibration, direction, ramp and integral controls');
})().catch(error => { console.error(error); process.exitCode = 1; });
