'use strict';
/* Math, 3D drawing and chart helpers for the commissioning visualizer. */

const D2R = Math.PI / 180, R2D = 180 / Math.PI, TAU = Math.PI * 2;
const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
const lerp = (a, b, t) => a + (b - a) * t;
const sstep = (x, a, b) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const wrap180 = a => ((a + 180) % 360 + 360) % 360 - 180;
const hash = (i, s) => { const x = Math.sin(i * 12.9898 + (s || 1) * 78.233) * 43758.5453; return x - Math.floor(x); };
const noise = (i, s) => hash(i, s) * 2 - 1;

const V = {
  add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
  sub: (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]],
  mul: (a, k) => [a[0] * k, a[1] * k, a[2] * k],
  dot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],
  cross: (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]],
  len: a => Math.hypot(a[0], a[1], a[2]),
  norm: a => { const n = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / n, a[1] / n, a[2] / n]; },
};

/* Quaternions are [w, x, y, z], body -> orbit frame (ORC: X along track, Z to nadir). */
const Q = {
  id: () => [1, 0, 0, 0],
  mul(a, b) {
    return [a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3],
      a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2],
      a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1],
      a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0]];
  },
  conj: q => [q[0], -q[1], -q[2], -q[3]],
  norm(q) { const n = Math.hypot(q[0], q[1], q[2], q[3]); return q.map(x => x / n); },
  rot(q, v) {
    const [w, x, y, z] = q;
    const tx = 2 * (y * v[2] - z * v[1]), ty = 2 * (z * v[0] - x * v[2]), tz = 2 * (x * v[1] - y * v[0]);
    return [v[0] + w * tx + y * tz - z * ty, v[1] + w * ty + z * tx - x * tz, v[2] + w * tz + x * ty - y * tx];
  },
  euler(r, p, y) {
    const cr = Math.cos(r * D2R / 2), sr = Math.sin(r * D2R / 2);
    const cp = Math.cos(p * D2R / 2), sp = Math.sin(p * D2R / 2);
    const cy = Math.cos(y * D2R / 2), sy = Math.sin(y * D2R / 2);
    return [cr * cp * cy + sr * sp * sy, sr * cp * cy - cr * sp * sy, cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy];
  },
  toEuler(q) {
    const [w, x, y, z] = q;
    return [Math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)) * R2D,
      Math.asin(clamp(2 * (w * y - z * x), -1, 1)) * R2D,
      Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)) * R2D];
  },
  fromTo(a, b) {
    const d = V.dot(a, b);
    if (d > 0.999999) return [1, 0, 0, 0];
    if (d < -0.999999) { let ax = V.cross([1, 0, 0], a); if (V.len(ax) < 1e-3) ax = V.cross([0, 1, 0], a); return [0, ...V.norm(ax)]; }
    return Q.norm([1 + d, ...V.cross(a, b)]);
  },
  slerp(a, b, t) {
    let d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
    if (d < 0) { b = b.map(x => -x); d = -d; }
    if (d > 0.9995) return Q.norm(a.map((x, i) => x + (b[i] - x) * t));
    const th = Math.acos(d), s = Math.sin(th);
    const k1 = Math.sin((1 - t) * th) / s, k2 = Math.sin(t * th) / s;
    return a.map((x, i) => x * k1 + b[i] * k2);
  },
  step(q, w, dt) {
    const m = V.len(w), th = m * D2R * dt;
    if (th < 1e-12) return q;
    const s = Math.sin(th / 2) / m;
    return Q.norm(Q.mul(q, [Math.cos(th / 2), w[0] * s, w[1] * s, w[2] * s]));
  },
};

/* ------------------------------------------------------------------ colours */
const C = {
  x: '#4C9BE0', y: '#F0714C', z: '#4DBB8C', sun: '#F4BB45', field: '#3CC3D6',
  wheel: '#A98BE8', mtq: '#E6C35C', ink: '#0B1B2B', text: '#D6E4F0', dim: '#7F9BB5',
};
const AX = [C.x, C.y, C.z];
const chartColors = { x: '#2F78BF', y: '#DB5A36', z: '#2F9A6D', ink: '#0F2236', amber: '#C98A0B', teal: '#1B93A6', violet: '#7B5CC4', grey: '#6C8196' };

/* ------------------------------------------------------------------ camera */
/* user-controlled orbit view: drag to rotate, wheel/pinch to zoom, double-click to reset */
const VIEW = { az: 0, el: 0, zoom: 1 };
function makeCam(cx, cy, scale, az, el) {
  az += VIEW.az; el = clamp(el + VIEW.el, -88, 88); scale *= VIEW.zoom;
  const ca = Math.cos(az * D2R), sa = Math.sin(az * D2R), ce = Math.cos(el * D2R), se = Math.sin(el * D2R);
  const f = v => { const x1 = v[0] * ca - v[1] * sa, y1 = v[0] * sa + v[1] * ca; return [x1, v[2] * ce - y1 * se, y1 * ce + v[2] * se]; };
  return {
    cx, cy, scale,
    p(v) { const r = f(v), k = 1 / (1 - r[2] * 0.05); return [cx + r[0] * scale * k, cy + r[1] * scale * k, r[2]]; },
    depth(n) { return f(n)[2]; },
  };
}

const FACES = (() => {
  const out = [];
  for (let a = 0; a < 3; a++) for (const s of [1, -1]) {
    const b = (a + 1) % 3, c = (a + 2) % 3;
    const v = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([u, w]) => { const p = [0, 0, 0]; p[a] = s; p[b] = u; p[c] = w; return p; });
    const n = [0, 0, 0]; n[a] = s;
    out.push({ a, s, n, v, name: (s > 0 ? '+' : '-') + 'XYZ'[a] });
  }
  return out;
})();

const BODY = [1.5, 0.5, 0.5]; /* half extents, 3U reference body: long axis along X */
const LIGHT = V.norm([-0.4, -0.5, -0.8]);

function drawArrow(ctx, cam, from, to, color, label, o) {
  o = o || {};
  const a = cam.p(from), b = cam.p(to);
  ctx.save();
  ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = o.w || 2;
  ctx.globalAlpha = o.alpha == null ? 1 : o.alpha;
  if (o.dash) ctx.setLineDash(o.dash);
  ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
  ctx.setLineDash([]);
  const ang = Math.atan2(b[1] - a[1], b[0] - a[0]), h = o.head || 7;
  ctx.beginPath();
  ctx.moveTo(b[0], b[1]);
  ctx.lineTo(b[0] - h * Math.cos(ang - 0.4), b[1] - h * Math.sin(ang - 0.4));
  ctx.lineTo(b[0] - h * Math.cos(ang + 0.4), b[1] - h * Math.sin(ang + 0.4));
  ctx.closePath(); ctx.fill();
  if (label) {
    ctx.font = '600 12px "Instrument Sans", system-ui, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(label, b[0] + Math.cos(ang) * 12, b[1] + Math.sin(ang) * 12);
  }
  ctx.restore();
}

/* Draw the CubeSat at centre `c` (ORC coordinates) with attitude q. */
function drawSat(ctx, cam, q, o) {
  o = o || {};
  const c = o.center || [0, 0, 0];
  const hi = o.hi || [];
  const faces = FACES.map(f => {
    const n = Q.rot(q, f.n);
    const vs = f.v.map(s => V.add(c, Q.rot(q, [s[0] * BODY[0], s[1] * BODY[1], s[2] * BODY[2]])));
    const pts = vs.map(v => cam.p(v));
    return { f, n, pts, d: pts.reduce((m, p) => m + p[2], 0) / 4, vis: cam.depth(n) < 0 };
  }).sort((u, v) => v.d - u.d);

  for (const F of faces) {
    if (!F.vis) continue;
    const L = 0.5 + 0.5 * Math.max(0, -V.dot(F.n, LIGHT));
    const panel = F.f.a === 1;
    let base = panel ? [34, 62, 104] : F.f.a === 0 ? [168, 188, 208] : [122, 150, 178];
    const hot = hi.includes(F.f.name);
    if (hot) base = [244, 187, 69];
    ctx.beginPath();
    F.pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
    ctx.closePath();
    ctx.fillStyle = `rgb(${base.map(v => Math.round(v * (0.55 + 0.45 * L))).join(',')})`;
    ctx.fill();
    ctx.strokeStyle = hot ? '#FFE3A0' : 'rgba(214,228,240,0.55)'; ctx.lineWidth = hot ? 2 : 1; ctx.stroke();
    if (panel) { /* cell grid */
      ctx.strokeStyle = 'rgba(160,190,230,0.28)'; ctx.lineWidth = 1;
      const [p0, p1, p2, p3] = F.pts;
      for (let k = 1; k < 6; k++) {
        const t = k / 6;
        ctx.beginPath(); ctx.moveTo(lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t)); ctx.lineTo(lerp(p3[0], p2[0], t), lerp(p3[1], p2[1], t)); ctx.stroke();
      }
    }
  }
  if (o.boom != null) { /* magnetometer boom */
    const piv = [BODY[0], BODY[1], -BODY[2]], th = lerp(180, 90, o.boom) * D2R;
    const dir = [Math.cos(th), Math.sin(th), 0];
    const tip = V.add(piv, V.mul(dir, 1.6));
    const a = cam.p(V.add(c, Q.rot(q, piv))), b = cam.p(V.add(c, Q.rot(q, tip)));
    ctx.strokeStyle = C.field; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
    ctx.fillStyle = C.field; ctx.beginPath(); ctx.arc(b[0], b[1], 4.5, 0, TAU); ctx.fill();
  }
  if (!o.noAxes) {
    const len = [2.5, 1.5, 1.5];
    for (let i = 0; i < 3; i++) {
      const e = [0, 0, 0]; e[i] = len[i];
      drawArrow(ctx, cam, c, V.add(c, Q.rot(q, e)), AX[i], 'XYZ'[i], { w: 1.6, head: 6, alpha: 0.95 });
    }
  }
}

function drawStars(ctx, W, H) {
  ctx.fillStyle = 'rgba(214,228,240,0.55)';
  for (let i = 0; i < 70; i++) {
    const x = hash(i, 3) * W, y = hash(i, 5) * H * 0.8, r = 0.4 + hash(i, 7) * 0.9;
    ctx.globalAlpha = 0.25 + hash(i, 9) * 0.5; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function drawEarth(ctx, W, H, night) {
  const cx = W / 2, R = Math.max(W, H) * 1.05, cy = H * 0.98 + R * 0.62;
  ctx.save();
  const g = ctx.createRadialGradient(cx, cy - R * 0.2, R * 0.2, cx, cy, R);
  if (night) { g.addColorStop(0, '#0B2238'); g.addColorStop(1, '#07151F'); } else { g.addColorStop(0, '#2C78B4'); g.addColorStop(1, '#1A4F7E'); }
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.fill();
  ctx.strokeStyle = night ? 'rgba(120,160,200,0.35)' : 'rgba(150,205,255,0.8)'; ctx.lineWidth = 2.5; ctx.stroke();
  ctx.restore();
  return cy - R; /* y of the limb at centre */
}

function dial(ctx, x, y, r, angle, rpm, label, color) {
  ctx.save();
  ctx.strokeStyle = 'rgba(214,228,240,0.35)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.stroke();
  ctx.strokeStyle = color; ctx.lineWidth = 2.5;
  for (let k = 0; k < 3; k++) {
    const a = angle * D2R + k * TAU / 3;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(a) * r * 0.92, y + Math.sin(a) * r * 0.92); ctx.stroke();
  }
  ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x, y, 3, 0, TAU); ctx.fill();
  ctx.fillStyle = C.text; ctx.font = '600 11.5px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'center';
  ctx.fillText(label, x, y + r + 14);
  ctx.fillStyle = C.dim; ctx.fillText(Math.round(rpm) + ' rpm', x, y + r + 28);
  ctx.restore();
}

function pitchDial(ctx, x, y, r, trueDeg, estDeg) {
  ctx.save();
  ctx.strokeStyle = 'rgba(214,228,240,0.3)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.stroke();
  ctx.fillStyle = C.dim; ctx.font = '11px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'center';
  ctx.fillText('nadir', x, y + r + 13);
  const needle = (deg, col, dash, w) => {
    const a = (deg + 90) * D2R; /* 0 deg = pointing to nadir (down) */
    ctx.strokeStyle = col; ctx.lineWidth = w; ctx.setLineDash(dash);
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.sin(deg * D2R) * r, y + Math.cos(deg * D2R) * r); ctx.stroke();
  };
  needle(trueDeg, C.y, [], 3);
  if (estDeg != null) needle(estDeg, '#FFFFFF', [4, 3], 1.5);
  ctx.setLineDash([]);
  ctx.fillStyle = C.text; ctx.font = '600 12px "Instrument Sans", system-ui, sans-serif';
  ctx.fillText('pitch ' + Math.round(trueDeg) + '°', x, y - r - 8);
  ctx.restore();
}

/* ------------------------------------------------------------------ charts */
function fmtT(t) {
  t = Math.round(t);
  if (t < 90) return t + ' s';
  if (t < 10800) return (t / 60 >= 10 ? Math.round(t / 60) : (t / 60).toFixed(1).replace('.0', '')) + ' min';
  return (t / 3600).toFixed(1).replace('.0', '') + ' h';
}

function niceTicks(lo, hi, n) {
  const span = hi - lo || 1, raw = span / n, mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw) || mag * 10;
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-6; v += step) out.push(+v.toFixed(10));
  return out;
}

function fmtV(v, unit) {
  const a = Math.abs(v);
  const s = a >= 1000 ? Math.round(v).toString() : a >= 100 ? v.toFixed(0) : a >= 10 ? v.toFixed(1) : a >= 1 ? v.toFixed(2) : v.toFixed(3);
  return s;
}

/* def: {series:[{name,color,get,dash,rev,when}], log, y:[lo,hi], xmax, bands, marks}
   S: samples, T: total time, t: current time. */
function drawChart(cv, def, S, T, t) {
  const dpr = window.devicePixelRatio || 1, r = cv.getBoundingClientRect();
  if (!r.width) return;
  if (cv.width !== Math.round(r.width * dpr) || cv.height !== Math.round(r.height * dpr)) { cv.width = Math.round(r.width * dpr); cv.height = Math.round(r.height * dpr); }
  const ctx = cv.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const W = r.width, H = r.height, ml = 46, mr = 12, mt = 30, mb = 24;
  ctx.clearRect(0, 0, W, H);
  const N = S.length, dt = T / (N - 1), xmax = def.xmax || T;
  const tf = def.log ? v => Math.log10(Math.max(v, 1e-6)) : v => v;
  let lo = Infinity, hi = -Infinity;
  const vals = def.series.map(s => S.map((p, i) => { const v = s.get(p, i, i * dt); return Number.isFinite(v) && i * dt <= xmax + 1e-9 ? tf(v) : NaN; }));
  vals.forEach(a => a.forEach(v => { if (v < lo) lo = v; if (v > hi) hi = v; }));
  if (def.y) { lo = tf(def.y[0]); hi = tf(def.y[1]); }
  else { const pad = (hi - lo) * 0.08 || 1; lo -= pad; hi += pad; }
  const X = tt => ml + (W - ml - mr) * tt / xmax, Y = v => mt + (H - mt - mb) * (1 - (v - lo) / (hi - lo));

  /* bands */
  (def.bands || []).forEach(b => {
    ctx.fillStyle = 'rgba(15,34,54,0.08)'; ctx.fillRect(X(b.t0), mt, X(Math.min(b.t1, xmax)) - X(b.t0), H - mt - mb);
    ctx.fillStyle = '#5A7791'; ctx.font = '11px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'left';
    ctx.fillText(b.label, X(b.t0) + 4, H - mb - 5);
  });
  /* grid */
  ctx.font = '11px "Instrument Sans", system-ui, sans-serif'; ctx.lineWidth = 1;
  const yt = def.log ? [-3, -2, -1, 0, 1].filter(e => e >= lo && e <= hi) : niceTicks(lo, hi, 4);
  yt.forEach(v => {
    const y = Y(v);
    ctx.strokeStyle = v === 0 && !def.log ? 'rgba(15,34,54,0.35)' : 'rgba(15,34,54,0.1)';
    ctx.beginPath(); ctx.moveTo(ml, y); ctx.lineTo(W - mr, y); ctx.stroke();
    ctx.fillStyle = '#5A7791'; ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillText(def.log ? String(Math.pow(10, v)) : fmtV(v), ml - 6, y);
  });
  const tstep = [10, 30, 60, 120, 300, 600, 1200, 1800, 3600, 7200, 14400].find(s => xmax / s <= 5.5) || 14400;
  const xt = []; for (let v = 0; v <= xmax + 1e-6; v += tstep) xt.push(v);
  xt.forEach(v => {
    ctx.fillStyle = '#5A7791'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    ctx.fillText(fmtT(v), X(v), H - mb + 6);
  });
  /* series */
  def.series.forEach((s, k) => {
    if (s.when && !s.when(t)) { return; }
    const reveal = s.rev ? s.rev(t) * xmax : t;
    ctx.strokeStyle = s.color; ctx.lineWidth = 1.8; ctx.setLineDash(s.dash ? [5, 3] : []);
    for (const pass of [0, 1]) {
      ctx.globalAlpha = pass ? 1 : 0.16;
      ctx.beginPath(); let pen = false;
      for (let i = 0; i < N; i++) {
        const tt = i * dt, v = vals[k][i];
        if (!Number.isFinite(v) || (pass ? tt > reveal : tt < reveal - dt)) { pen = false; continue; }
        const x = X(tt), y = Y(v);
        if (pen) ctx.lineTo(x, y); else { ctx.moveTo(x, y); pen = true; }
      }
      ctx.stroke();
    }
    ctx.globalAlpha = 1; ctx.setLineDash([]);
  });
  /* marks */
  (def.marks || []).forEach(m => {
    if (m.t > xmax) return;
    const on = t >= m.t;
    ctx.strokeStyle = on ? 'rgba(15,34,54,0.55)' : 'rgba(15,34,54,0.2)'; ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(X(m.t), mt); ctx.lineTo(X(m.t), H - mb); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = on ? '#0F2236' : '#8FA4B7'; ctx.font = '600 11px "Instrument Sans", system-ui, sans-serif';
    ctx.textAlign = X(m.t) > W - 90 ? 'right' : 'left'; ctx.textBaseline = 'top';
    ctx.fillText(m.label, X(m.t) + (X(m.t) > W - 90 ? -4 : 4), mt + 2 + (m.row || 0) * 13);
  });
  /* cursor + legend */
  const cx = X(Math.min(t, xmax));
  ctx.strokeStyle = '#0F2236'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(cx, mt); ctx.lineTo(cx, H - mb); ctx.stroke();
  const idx = clamp(Math.round(Math.min(t, xmax) / dt), 0, N - 1);
  let lx = ml;
  ctx.textBaseline = 'middle'; ctx.textAlign = 'left'; ctx.font = '600 12px "Instrument Sans", system-ui, sans-serif';
  def.series.forEach((s, k) => {
    if (s.when && !s.when(t)) return;
    const raw = s.get(S[idx], idx, idx * dt), v = Number.isFinite(raw) ? raw : null;
    if (v != null) { ctx.fillStyle = s.color; ctx.beginPath(); ctx.arc(cx, Y(tf(v)), 3.5, 0, TAU); ctx.fill(); }
    const label = s.name + (v != null ? '  ' + fmtV(v) : '');
    ctx.fillStyle = s.color; ctx.fillRect(lx, 11, 12, 3);
    ctx.fillStyle = '#0F2236'; ctx.fillText(label, lx + 17, 13);
    lx += 17 + ctx.measureText(label).width + 14;
  });
}
