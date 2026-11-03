'use strict';

const PHASES = {
  a: 'Slow the tumble', b: 'Magnetometer', c: 'Wheel and nadir lock', d: 'Sun, nadir and star sensors', e: 'Three-axis control', f: 'GPS',
};
const $ = (s, r) => (r || document).querySelector(s);
const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
const reduceMotion = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

const st = { scene: null, P: {}, sim: null, t: 0, playing: false, speed: '1', wa: [0, 0, 0], activeIdx: -1, cmds: [] };
const stage = $('#stage'), sctx = stage.getContext('2d');

/* ------------------------------------------------------------- simulation */
function simulate(sc, P) {
  const b = sc.build(P), T = b.T || sc.T, N = b.N || sc.N || 500, dt = T / (N - 1);
  const S = [];
  for (let i = 0; i < N; i++) { const t = i * dt; S.push({ t, ...b.f(t, i) }); }
  let wmax = 0, driven = false;
  S.forEach(s => { if (s.w && !s.euler && !s.q) { driven = true; wmax = Math.max(wmax, V.len(s.w)); } });
  const k = driven ? Math.min(1, 220 / (wmax * T / sc.dur + 1e-9)) : 1;
  let q = b.q0 || Q.id(), qv = q; const ang = [0, 0, 0], ex = sc.exag || 1;
  S.forEach((s, i) => {
    if (s.q) { q = s.q; qv = s.q; s.eul = Q.toEuler(q); }
    else if (s.euler) { q = Q.euler(...s.euler); qv = ex !== 1 ? Q.euler(s.euler[0] * ex, s.euler[1] * ex, s.euler[2] * ex) : q; s.eul = s.euler; }
    else if (s.w && i > 0) { q = Q.step(q, s.w, dt); qv = Q.step(qv, V.mul(s.w, k), dt); s.eul = Q.toEuler(q); }
    else s.eul = Q.toEuler(q);
    if (s.w && i > 0) for (let j = 0; j < 3; j++) ang[j] += s.w[j] * dt;
    s.q = q; s.qv = qv; s.ang = ang.slice();
    if (i > 0) { const d = Q.mul(Q.conj(S[i - 1].q), q), sg = d[0] < 0 ? -1 : 1, sh = Math.hypot(d[1], d[2], d[3]), th = 2 * Math.atan2(sh, Math.abs(d[0])) * R2D / dt; s.rate = sh > 1e-12 ? [sg * d[1] / sh * th, sg * d[2] / sh * th, sg * d[3] / sh * th] : [0, 0, 0]; } else s.rate = [0, 0, 0];
    s.slew = V.len(s.rate);
    if (s.B) s.bBody = Q.rot(Q.conj(q), s.B);
    if (b.derive) b.derive(s, i, s.t, S);
  });
  return { S, T, N, dt, k, wmax, q0: b.q0 };
}

function getRate() { return st.speed === 'fit' ? st.sim.T / st.scene.dur : +st.speed; }

/* -------------------------------------------------------------- stage draw */
function modeAt(sc, P, t) {
  const m = typeof sc.modes === 'function' ? sc.modes(P) : sc.modes;
  let cur = m[0]; m.forEach(x => { if (t >= x.t) cur = x; });
  return cur;
}

function drawDefault(ctx, W, H, s, t, sc, P) {
  const show = sc.show || {};
  drawStars(ctx, W, H);
  let limb = null;
  if (show.nadir || show.orbit) limb = drawEarth(ctx, W, H, !!s.ecl);
  const cx = W * 0.5, cy = H * (limb != null ? 0.38 : 0.46), scale = Math.min(W * 0.1, H * 0.17);
  const cam = makeCam(cx, cy, scale, -38, 20);
  if (limb != null) { drawArrow(ctx, cam, [0, 0, 0], [0, 0, 5.2], 'rgba(214,228,240,0.5)', 'nadir', { dash: [4, 4], w: 1.2, head: 5 }); }
  if (show.sun && s.sun) {
    const col = s.ecl ? 'rgba(244,187,69,0.25)' : C.sun;
    drawArrow(ctx, cam, [0, 0, 0], V.mul(s.sun, 5.6), col, s.ecl ? '' : 'Sun', { w: 2.2, head: 8 });
    const tip = cam.p(V.mul(s.sun, 6.3)); ctx.fillStyle = col; ctx.beginPath(); ctx.arc(tip[0], tip[1], s.ecl ? 6 : 8, 0, TAU); ctx.fill();
    if (s.ecl) { ctx.fillStyle = C.dim; ctx.font = '600 12px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'left'; ctx.fillText('In eclipse: Sun hidden by the Earth', 16, H - 52); }
  }
  if (show.b && s.B) { const bn = V.mul(V.norm(s.B), 3.3); drawArrow(ctx, cam, [0, 0, 0], bn, C.field, 'B', { w: 2, head: 7, alpha: 0.9 }); }
  const hi = sc.hi ? sc.hi(s, t, P) : [];
  drawSat(ctx, cam, s.qv, { hi, boom: s.boom });
  /* wheels */
  if (show.wheels) {
    show.wheels.forEach((a, k) => dial(ctx, 36 + k * 74, H - 64, 22, st.wa[a], s.wheel ? s.wheel[a] : 0, 'XYZ'[a] + ' wheel', AX[a]));
  }
  if (show.mtq && s.mtq) {
    const bx = show.wheels ? 36 + show.wheels.length * 74 + 14 : 20, by = H - 56;
    ctx.fillStyle = C.text; ctx.font = '600 11.5px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'left'; ctx.fillText('Magnetorquers', bx, by - 20);
    for (let a = 0; a < 3; a++) {
      const x = bx + a * 26, v = clamp(s.mtq[a], -1, 1);
      ctx.fillStyle = 'rgba(214,228,240,0.15)'; ctx.fillRect(x, by - 14, 16, 36);
      ctx.fillStyle = AX[a]; ctx.fillRect(x, by + 4 - (v > 0 ? v * 18 : 0), 16, Math.abs(v) * 18);
      ctx.fillStyle = C.dim; ctx.font = '10.5px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.fillText('XYZ'[a], x + 8, by + 36);
    }
  }
}

function drawStage() {
  const sc = st.scene, sim = st.sim; if (!sc || !sim) return;
  const dpr = window.devicePixelRatio || 1, r = stage.getBoundingClientRect(); if (!r.width) return;
  if (stage.width !== Math.round(r.width * dpr) || stage.height !== Math.round(r.height * dpr)) { stage.width = Math.round(r.width * dpr); stage.height = Math.round(r.height * dpr); }
  const ctx = sctx; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const W = r.width, H = r.height, t = st.t;
  ctx.fillStyle = C.ink; ctx.fillRect(0, 0, W, H);
  const idx = clamp(Math.round(t / sim.dt), 0, sim.N - 1);
  let s = sim.S[idx];
  const trueSpin = !sc.exag && sim.k < 1 && getRate() * sim.wmax <= 220;
  if (trueSpin) s = { ...s, qv: s.q };
  if (sc.draw) { drawStars(ctx, W, H); sc.draw(ctx, W, H, s, t, st.P, { samples: sim.S, sim }); }
  else drawDefault(ctx, W, H, s, t, sc, st.P);
  if (sc.overlay) sc.overlay(ctx, W, H, s, t, st.P, { samples: sim.S });
  /* HUD */
  if (!sc.draw) {
    const m = modeAt(sc, st.P, t), lines = [];
    lines.push('Estimation  ' + m.est + ' · ' + EST[m.est]);
    lines.push('Control  ' + m.ctl + ' · ' + CTL[m.ctl]);
    if (sc.hud) lines.push(...sc.hud(s, t, st.P));
    ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
    lines.forEach((ln, k) => { ctx.fillStyle = k < 2 ? C.text : C.sun; ctx.font = (k < 2 ? '600 ' : '500 ') + '13px "Instrument Sans", system-ui, sans-serif'; ctx.fillText(ln, 16, 24 + k * 19); });
  }
  if (sim.k < 0.97 && !sc.draw && !trueSpin) { ctx.fillStyle = C.dim; ctx.font = '11.5px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'right'; ctx.fillText('spin rate shown schematically', W - 14, 22); }
  if (!sc.draw || sc.id === 17) {
    const f = v => (Math.abs(v) < 0.1 ? v.toFixed(3) : Math.abs(v) < 10 ? v.toFixed(2) : v.toFixed(1));
    const rows = [['Slew rate', f(s.slew) + ' °/s'], ['Body rate', 'x ' + f(s.rate[0]) + '  y ' + f(s.rate[1]) + '  z ' + f(s.rate[2])], ['Attitude', 'R ' + f(s.eul[0]) + '  P ' + f(s.eul[1]) + '  Y ' + f(s.eul[2]) + ' °']];
    ctx.textAlign = 'right'; ctx.textBaseline = 'alphabetic';
    rows.forEach(([k, v], i) => { const y = 44 + i * 18; ctx.font = '600 12.5px "Instrument Sans", system-ui, sans-serif'; ctx.fillStyle = i ? C.text : '#F4BB45'; const wv = ctx.measureText(v).width; ctx.fillText(v, W - 14, y); ctx.fillStyle = C.dim; ctx.font = '11.5px "Instrument Sans", system-ui, sans-serif'; ctx.fillText(k, W - 14 - wv - 8, y); });
  }
  /* current command caption */
  const cmds = st.cmds; let ai = -1; cmds.forEach((c, i) => { if (t >= c.t) ai = i; });
  if (ai !== st.activeIdx) { st.activeIdx = ai; document.querySelectorAll('.cmd').forEach((n, i) => { n.classList.toggle('done', i < ai); n.classList.toggle('now', i === ai); }); const n = document.querySelectorAll('.cmd')[ai]; if (n) { const box = n.parentElement; if (box.scrollHeight > box.clientHeight) box.scrollTop = n.offsetTop - box.offsetTop - 40; } }
  $('#cap').innerHTML = ai >= 0 ? `<b>${cmds[ai].title}</b> ${cmds[ai].detail}` : '';
  /* charts */
  document.querySelectorAll('canvas.chart').forEach((cv, i) => drawChart(cv, st.charts[i], sim.S, sim.T, t));
  $('#scrub').value = Math.round(t / sim.T * 1000);
  $('#clock').textContent = fmtT(t) + ' of ' + fmtT(sim.T);
}

let lastTs = 0;
function frame(ts) {
  const dt = Math.min(0.05, (ts - lastTs) / 1000 || 0); lastTs = ts;
  if (st.playing && st.sim) {
    st.t += dt * getRate();
    if (st.t >= st.sim.T) { st.t = st.sim.T; setPlaying(false); }
    const sc = st.scene, idx = clamp(Math.round(st.t / st.sim.dt), 0, st.sim.N - 1), s = st.sim.S[idx];
    if (sc.show && sc.show.wheels && s.wheel) sc.show.wheels.forEach(a => { st.wa[a] += clamp(s.wheel[a] * 0.12, -700, 700) * dt; });
  }
  drawStage();
  requestAnimationFrame(frame);
}

function setPlaying(p) {
  st.playing = p;
  const b = $('#play'); b.setAttribute('aria-label', p ? 'Pause' : (st.t >= (st.sim ? st.sim.T : 1) ? 'Replay' : 'Play'));
  b.innerHTML = p ? '<svg viewBox="0 0 20 20"><path d="M5 3h3.5v14H5zM11.5 3H15v14h-3.5z"/></svg>' : (st.t >= (st.sim ? st.sim.T : 1) ? '<svg viewBox="0 0 20 20"><path d="M10 3a7 7 0 1 0 6.6 9.3h-2.2A5 5 0 1 1 10 5c1.4 0 2.6.6 3.5 1.5L11 9h6V3l-2.1 2.1A7 7 0 0 0 10 3z"/></svg>' : '<svg viewBox="0 0 20 20"><path d="M6 3.5v13l11-6.5z"/></svg>');
}

/* ----------------------------------------------------------------- scenes */
function params(sc) { const o = {}; (sc.params || []).forEach(p => { o[p.id] = p.val; }); return o; }
const val = (x, P) => (typeof x === 'function' ? x(P) : x);

function loadScene(id, keepParams) {
  VIEW.az = 0; VIEW.el = 0; VIEW.zoom = 1;
  const sc = SCENES.find(s => s.id === id); st.scene = sc;
  if (!keepParams) st.P = params(sc);
  st.sim = simulate(sc, st.P); st.t = 0; st.wa = [0, 0, 0]; st.activeIdx = -2;
  st.cmds = val(sc.cmds, st.P); st.charts = val(sc.charts, st.P);
  renderChartsDom(); renderCmds(); renderTlm(); renderNote();
  $('#scrub').value = 0;
  setPlaying(!reduceMotion);
}

function renderControls(sc) {
  const box = $('#params'); box.innerHTML = '';
  (sc.params || []).forEach(p => {
    const row = el('div', 'prm');
    row.appendChild(el('span', 'prm-l', p.label));
    if (p.type === 'seg') {
      const g = el('div', 'seg'); g.setAttribute('role', 'group'); g.setAttribute('aria-label', p.label);
      p.opts.forEach(([v, l]) => { const b = el('button', null, l); b.type = 'button'; b.setAttribute('aria-pressed', st.P[p.id] === v); b.onclick = () => { st.P[p.id] = v; g.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b)); reload(); }; g.appendChild(b); });
      row.appendChild(g);
    } else {
      const inp = el('input'); inp.type = 'range'; inp.min = p.min; inp.max = p.max; inp.step = p.step; inp.value = st.P[p.id]; inp.setAttribute('aria-label', p.label);
      const out = el('output', null, p.fmt(st.P[p.id]));
      inp.oninput = () => { out.textContent = p.fmt(+inp.value); };
      inp.onchange = () => { st.P[p.id] = +inp.value; reload(); };
      row.appendChild(inp); row.appendChild(out);
    }
    box.appendChild(row);
  });
}

function reload() {
  const sc = st.scene, keep = st.t / (st.sim ? st.sim.T : 1);
  st.sim = simulate(sc, st.P); st.cmds = val(sc.cmds, st.P); st.charts = val(sc.charts, st.P); st.activeIdx = -2;
  st.t = sc.id === 12 || sc.id === 14 ? 0 : keep * st.sim.T;
  renderChartsDom(); renderCmds(); renderTlm(); renderNote();
  if (sc.id === 12 || sc.id === 14) setPlaying(!reduceMotion);
}

function renderChartsDom() {
  const box = $('#charts'); box.innerHTML = '';
  box.className = 'charts n' + st.charts.length;
  st.charts.forEach(c => { const f = el('figure'); f.appendChild(el('figcaption', null, `<b>${c.title}</b>${c.unit ? ' <span>' + c.unit + '</span>' : ''}`)); const cv = el('canvas', 'chart'); cv.setAttribute('role', 'img'); cv.setAttribute('aria-label', c.title); f.appendChild(cv); box.appendChild(f); });
}
function renderCmds() {
  const ol = $('#cmds'); ol.innerHTML = '';
  st.cmds.forEach((c, i) => {
    const li = el('li', 'cmd ' + (c.kind || 'cmd'), `<span class="ct">${fmtT(c.t)}</span><span class="cb"><b>${c.title}</b><span>${c.detail}</span></span>`);
    li.onclick = () => { st.t = Math.min(c.t + 0.01, st.sim.T); setPlaying(false); };
    ol.appendChild(li);
  });
}
function renderTlm() {
  const rows = val(st.scene.tlm, st.P);
  $('#tlm').innerHTML = rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('');
}
function renderNote() { const n = st.scene.note ? st.scene.note(st.P) : ''; $('#note').textContent = n || ''; $('#note').hidden = !n; }

function showStep(id, keep) {
  const sc = SCENES.find(s => s.id === id); if (!sc) return;
  $('#view-step').hidden = false; $('#view-pass').hidden = true; $('#view-safe').hidden = true;
  $('#h-n').textContent = sc.id; $('#h-t').textContent = sc.title;
  $('#h-sec').textContent = `Manual section ${sc.sec}, pages ${sc.pages}`;
  const m0 = modeAt(sc, params(sc), 1e9);
  $('#spec-est').textContent = (typeof sc.modes === 'function' ? sc.modes(params(sc)) : sc.modes).map(x => x.est).filter((v, i, a) => a.indexOf(v) === i).map(v => v + ' ' + EST[v]).join('  →  ');
  $('#spec-ctl').textContent = (typeof sc.modes === 'function' ? sc.modes(params(sc)) : sc.modes).map(x => x.ctl).filter((v, i, a) => a.indexOf(v) === i).map(v => v + ' ' + CTL[v]).join('  →  ');
  $('#spec-dur').textContent = sc.duration; $('#spec-pre').textContent = sc.prereq;
  $('#story').textContent = sc.story;
  $('#pass').innerHTML = sc.pass.map(p => `<li>${p}</li>`).join('');
  $('#trouble').innerHTML = sc.trouble.map(([h, p]) => `<details><summary>${h}</summary><p>${p}</p></details>`).join('');
  document.querySelectorAll('#nav a[data-id]').forEach(a => a.setAttribute('aria-current', a.dataset.id == id ? 'step' : 'false'));
  document.querySelectorAll('#nav a[data-page]').forEach(a => a.removeAttribute('aria-current'));
  st.P = params(sc);
  renderControls(sc); renderTool(sc);
  loadScene(id, true);
  document.title = `Step ${sc.id}: ${sc.title} | SAT-2 ADCS commissioning`;
  $('#prev').disabled = id === 1; $('#next').disabled = id === SCENES.length;
  $('#prev').dataset.go = id - 1; $('#next').dataset.go = id + 1;
}

/* ------------------------------------------------------------------ tools */
const WHEELS = { s: ['CubeWheel Small', 2.11e-6], m: ['CubeWheel Medium', 1.72e-5], l: ['CubeWheel Large', 4.87e-5] };
function renderTool(sc) {
  const box = $('#tool'); box.innerHTML = ''; box.hidden = !sc.tool; if (!sc.tool) return;
  const T = {
    inertia: () => ['Check your inertia ratio', `<p>Y-Thomson is only stable if body Y has the largest moment of inertia, by at least 5% over the middle one. Defaults are the 3U example from the manual (Table 21).</p>
      <div class="fields"><label>Ixx<input id="t-a" type="number" step="0.001" value="0.007"></label><label>Iyy<input id="t-b" type="number" step="0.001" value="0.04"></label><label>Izz<input id="t-c" type="number" step="0.001" value="0.038"></label></div><p class="out" id="t-out"></p>`, () => {
      const a = +$('#t-a').value, b = +$('#t-b').value, c = +$('#t-c').value, mid = [a, b, c].sort((x, y) => x - y)[1], mx = Math.max(a, b, c);
      const pct = (b - (b === mx ? Math.max(a, c) : mid)) / (b === mx ? Math.max(a, c) : mid) * 100;
      $('#t-out').innerHTML = b === mx ? (pct >= 5 ? `<b class="ok">Good.</b> Iyy is ${pct.toFixed(1)}% above the next largest.` : `<b class="bad">Too close.</b> Iyy is only ${pct.toFixed(1)}% above the next. Add mass symmetric about the CoM, near body Z and far from Y, or bias the Y wheel by −10 to −20% of capacity.`) : `<b class="bad">Y is not the largest.</b> Iyy must exceed the other axes. Add mass or use a negative wheel momentum bias of 10–20% of capacity.`;
    }],
    wheel: () => ['Wheel speed for the ramp-up test', `<p>ω<sub>wheeltest</sub> [rpm] = 0.1667 × I<sub>yy</sub> × ω<sub>y-ref</sub> / I<sub>wheel</sub></p>
      <div class="fields"><label>Iyy (kg·m²)<input id="t-a" type="number" step="0.001" value="0.05"></label><label>Reference rate (deg/s)<input id="t-b" type="number" step="0.1" value="-1"></label><label>Wheel<select id="t-c"><option value="s">CubeWheel Small</option><option value="m">CubeWheel Medium</option><option value="l">CubeWheel Large</option></select></label></div><p class="out" id="t-out"></p>`, () => {
      const rpm = 0.1667 * +$('#t-a').value * +$('#t-b').value / WHEELS[$('#t-c').value][1];
      $('#t-out').innerHTML = `Command <b>${Math.round(rpm)} rpm</b> (keep the sign). The manual\'s 3U example (0.05 kg·m², −1 deg/s, Small) quotes −3948 rpm.`;
    }],
    gyro: () => ['Gyro bias from a 5 minute average', `<p>X bias = avg ωx, Y bias = avg ωy − ω<sub>orbit</sub>, Z bias = avg ωz. ω<sub>orbit</sub> = 360° / orbit period.</p>
      <div class="fields"><label>Orbit period (s)<input id="t-p" type="number" step="1" value="5818"></label><label>avg ωx<input id="t-a" type="number" step="0.01" value="0.12"></label><label>avg ωy<input id="t-b" type="number" step="0.01" value="0.262"></label><label>avg ωz<input id="t-c" type="number" step="0.01" value="-0.08"></label></div><p class="out" id="t-out"></p>`, () => {
      const wo = 360 / +$('#t-p').value;
      $('#t-out').innerHTML = `ω<sub>orbit</sub> = ${wo.toFixed(4)} deg/s. Offsets to load: <b>X ${(+$('#t-a').value).toFixed(3)}, Y ${(+$('#t-b').value - wo).toFixed(3)}, Z ${(+$('#t-c').value).toFixed(3)}</b> deg/s.`;
    }],
    target: () => ['Ground target reference', `<p>Follows the manual's five steps (section 14.1). Defaults are its worked example.</p>
      <div class="fields"><label>Geodetic latitude (°)<input id="t-a" type="number" step="0.0001" value="-34.0919"></label><label>Longitude (°)<input id="t-b" type="number" step="0.0001" value="21.2742"></label><label>Altitude (m)<input id="t-c" type="number" step="1" value="100"></label></div><p class="out" id="t-out"></p>`, () => {
      const e2 = 0.081819 ** 2, Rt = 6378.14, gd = +$('#t-a').value * D2R, lon = +$('#t-b').value, alt = +$('#t-c').value / 1000;
      const gc = Math.atan((1 - e2) * Math.tan(gd)), rd = Math.asin(Math.sin(gc) / Math.sqrt(1 - e2 * Math.cos(gc) ** 2));
      const rs = Rt * Math.sqrt(1 - e2 * Math.sin(rd) ** 2), dr = rs + alt - Rt;
      $('#t-out').innerHTML = `Geocentric latitude <b>${(gc * R2D).toFixed(2)}°</b>, geocentric longitude <b>${lon.toFixed(2)}°</b>, relative altitude <b>${Math.round(dr * 1000)} m</b> (site radius ${rs.toFixed(2)} km).`;
    }],
  }[sc.tool]();
  box.innerHTML = `<h3>${T[0]}</h3>${T[1]}`;
  const run = T[2]; box.querySelectorAll('input,select').forEach(i => i.addEventListener('input', run)); run();
}

/* ------------------------------------------------------------ extra pages */
function showPage(name) {
  $('#view-step').hidden = true; $('#view-pass').hidden = name !== 'pass'; $('#view-safe').hidden = name !== 'safe';
  setPlaying(false);
  document.querySelectorAll('#nav a').forEach(a => a.setAttribute('aria-current', a.dataset.page === name ? 'page' : 'false'));
  document.title = (name === 'pass' ? 'Every overpass' : 'Built-in safeguards') + ' | SAT-2 ADCS commissioning';
}
function initSafeguard() {
  const btn = $('#fault'), out = $('#fault-out'), led = $('#led'); let n = 0;
  const draw = () => {
    led.dataset.s = n === 0 ? 'ok' : n <= 5 ? 'cycle' : 'off';
    out.textContent = n === 0 ? 'Module healthy. 0 of 5 power cycles used.' : n <= 5 ? `Module faulted for 3 cycles in a row. Power cycle ${n} of 5.` : 'Five power cycles used. Module switched off for good. Any estimator or controller that needs it drops to none (mode 0).';
    btn.textContent = n > 5 ? 'Reset demo' : 'Inject a fault';
  };
  btn.onclick = () => { n = n > 5 ? 0 : n + 1; draw(); };
  draw();
}

/* -------------------------------------------------------------------- init */
function buildNav() {
  const nav = $('#nav-list'); let phase = null, ol;
  SCENES.forEach(sc => {
    if (sc.phase !== phase) { phase = sc.phase; nav.appendChild(el('p', 'phase', PHASES[phase])); ol = el('ol'); nav.appendChild(ol); }
    const li = el('li'), a = el('a', null, `<i>${sc.id}</i><span>${sc.title}</span>`); a.href = '#/' + sc.id; a.dataset.id = sc.id; li.appendChild(a); ol.appendChild(li);
  });
}
function route() {
  const h = location.hash.replace(/^#\/?/, '');
  if (h === 'pass' || h === 'safe') return showPage(h);
  const id = parseInt(h, 10); showStep(SCENES.some(s => s.id === id) ? id : 1);
}
buildNav();
window.addEventListener('hashchange', route);
/* orbit view */
{
  const pts = new Map(); let pinch = 0;
  stage.style.touchAction = 'none'; stage.style.cursor = 'grab';
  stage.addEventListener('pointerdown', e => { stage.setPointerCapture(e.pointerId); pts.set(e.pointerId, [e.clientX, e.clientY]); stage.style.cursor = 'grabbing'; pinch = 0; });
  stage.addEventListener('pointermove', e => {
    const p = pts.get(e.pointerId); if (!p) return;
    if (pts.size === 2) { const [a, b] = [...pts.values()]; const d0 = Math.hypot(a[0] - b[0], a[1] - b[1]); pts.set(e.pointerId, [e.clientX, e.clientY]); const [c, d] = [...pts.values()]; const d1 = Math.hypot(c[0] - d[0], c[1] - d[1]); if (d0) VIEW.zoom = clamp(VIEW.zoom * d1 / d0, 0.4, 3.5); return; }
    VIEW.az += (e.clientX - p[0]) * 0.5; VIEW.el = clamp(VIEW.el + (e.clientY - p[1]) * 0.4, -70, 70); pts.set(e.pointerId, [e.clientX, e.clientY]);
  });
  const up = e => { pts.delete(e.pointerId); stage.style.cursor = 'grab'; };
  stage.addEventListener('pointerup', up); stage.addEventListener('pointercancel', up);
  stage.addEventListener('wheel', e => { e.preventDefault(); VIEW.zoom = clamp(VIEW.zoom * Math.exp(-e.deltaY * 0.0015), 0.4, 3.5); }, { passive: false });
  stage.addEventListener('dblclick', () => { VIEW.az = 0; VIEW.el = 0; VIEW.zoom = 1; });
}
$('#play').onclick = () => { if (st.t >= st.sim.T) st.t = 0; setPlaying(!st.playing); };
$('#restart').onclick = () => { st.t = 0; st.wa = [0, 0, 0]; setPlaying(true); };
$('#scrub').oninput = e => { st.t = e.target.value / 1000 * st.sim.T; setPlaying(false); };
document.querySelectorAll('#speed button').forEach(b => { b.onclick = () => { st.speed = b.dataset.s; document.querySelectorAll('#speed button').forEach(x => x.setAttribute('aria-pressed', x === b)); }; });
document.querySelectorAll('.stepnav button').forEach(b => { b.onclick = () => { location.hash = '#/' + b.dataset.go; }; });
document.addEventListener('keydown', e => {
  if (/INPUT|SELECT|TEXTAREA/.test(e.target.tagName) && e.target.type !== 'range') return;
  if (e.key === 'ArrowRight' && st.scene && st.scene.id < SCENES.length && !$('#view-step').hidden) location.hash = '#/' + (st.scene.id + 1);
  else if (e.key === 'ArrowLeft' && st.scene && st.scene.id > 1 && !$('#view-step').hidden) location.hash = '#/' + (st.scene.id - 1);
  else if (e.key === ' ' && e.target.tagName !== 'BUTTON' && !$('#view-step').hidden) { e.preventDefault(); $('#play').click(); }
});
initSafeguard();
if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => {});
route();
requestAnimationFrame(frame);
