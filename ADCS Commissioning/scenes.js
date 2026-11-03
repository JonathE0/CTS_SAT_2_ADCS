'use strict';
/* The 18 commissioning steps (CubeADCS Commissioning Manual V7.1, Table 1).
   Curves are schematic: shaped from the manual's figures and described behaviour, not flight data. */

const ORBIT_T = 5818, W_ORB = 360 / ORBIT_T;
const Borc = t => { const u = TAU * t / ORBIT_T, phi = 2 * u + 0.35; return [34 * Math.cos(phi), 15 + 8 * Math.sin(u), 34 * Math.sin(phi)]; };
const ENV = t => {
  const u = TAU * t / ORBIT_T, cb = Math.cos(22 * D2R), sb = Math.sin(22 * D2R);
  const sun = [-cb * Math.sin(u), -sb, -cb * Math.cos(u)];
  return { sun, ecl: sun[2] > 0.39, B: Borc(t) };
};
const ECL = [{ t0: 1840, t1: 3830, label: 'eclipse' }];
const cc = chartColors;
const ser = (name, color, get, o) => Object.assign({ name, color, get }, o || {});
const XYZc = [cc.x, cc.y, cc.z];
const xyz = (key, names) => [0, 1, 2].map(i => ser((names || ['X', 'Y', 'Z'])[i], XYZc[i], s => s[key][i]));
const EST = { 0: 'none', 1: 'MEMS rate sensing', 2: 'Magnetometer rate filter', 3: 'Mag rate filter + pitch', 5: 'Full-state EKF', 6: 'MEMS Gyro EKF' };
const CTL = { 0: 'none', 1: 'Detumbling', 2: 'Y-Thomson', 3: 'Initial Y-momentum', 4: 'Steady Y-momentum', 5: 'XYZ wheel control', 6: 'Sun tracking', 7: 'Target tracking', 8: 'Very fast spin detumble', 9: 'Fast spin detumble' };

const noisy = (v, i, s, a) => v + a * noise(i, s);
const seg = (id, label, opts, val) => ({ id, label, type: 'seg', opts, val: val == null ? opts[0][0] : val });
const range = (id, label, min, max, step, val, fmt) => ({ id, label, type: 'range', min, max, step, val, fmt });
const nadirQ = (s, i, amp) => Q.euler(amp * Math.sin(i / 37), amp * 0.6 * Math.sin(i / 23 + 1), amp * Math.cos(i / 41));

/* -------------------------------------------------------------- step 5 data */
const IGRF = [[0, 23.5], [500, 27], [1000, 31], [1500, 43], [1850, 47.5], [2300, 42], [2800, 33], [3300, 27], [3600, 25.5], [3900, 26.5], [4300, 28.5], [4700, 26], [5100, 23.5], [5500, 21.5]];
const igrf = t => {
  for (let k = 1; k < IGRF.length; k++) if (t <= IGRF[k][0]) { const u = (t - IGRF[k - 1][0]) / (IGRF[k][0] - IGRF[k - 1][0]); return lerp(IGRF[k - 1][1], IGRF[k][1], (1 - Math.cos(u * Math.PI)) / 2); }
  return IGRF[IGRF.length - 1][1];
};
const CAL_E = [[0.103, 0.054, 0.0], [0.054, -0.073, 0.042], [0.0, 0.042, 0.067]], CAL_B = [2.3, -1.8, 1.3];

/* ---------------------------------------------------------- step 12 stars */
const STARS = [[0.52, 0.34, 255], [0.58, 0.31, 200], [0.62, 0.36, 180], [0.43, 0.52, 150], [0.47, 0.57, 220], [0.25, 0.25, 90], [0.72, 0.62, 80], [0.35, 0.78, 70], [0.82, 0.24, 60], [0.16, 0.5, 52], [0.66, 0.84, 44], [0.9, 0.55, 38], [0.12, 0.84, 30]];
const SPECKS = [3, 4, 5, 6, 6, 7, 8, 8, 9, 9, 10, 11].map((b, i) => [hash(i, 11), hash(i, 13), b]);

const SCENES = [];

/* ------------------------------------------------------------------ 1 */
SCENES.push({
  id: 1, title: 'Determine initial angular rates', phase: 'a', sec: '3', pages: '12–15', T: 300, dur: 16, N: 300,
  modes: [{ t: 0, est: 0, ctl: 0 }, { t: 10, est: 2, ctl: 0 }],
  duration: '5 min (nominal)', prereq: 'Satellite just released, still tumbling. Ground contact.',
  story: 'You don\'t know how fast the satellite is spinning. A Kalman filter watches the magnetometer: the field direction seen in body axes sweeps round at the spin rate, so the filter can back the rates out. The MEMS rate sensors are only the cross-check. Here the satellite is spinning about +Y at 2.4 deg/s, so the X and Z field components trace sine waves about 150 s apart.',
  cmds: () => [
    { t: 0, title: 'ADCS Run Mode', detail: 'State = Enabled (1)' },
    { t: 5, title: 'Power Control', detail: 'CubeControl Signal and/or Motor = On (1), all others Off (0)' },
    { t: 10, title: 'Set Estimation Mode', detail: 'Mode = Magnetometer rate filter (2)' },
    { t: 30, kind: 'wait', title: 'Keep logging', detail: 'The filter should converge within 15 s. Log for about 5 min.' },
  ],
  tlm: [['Estimated Angular Rates', '10 s'], ['Rate Sensor Rates', '10 s'], ['Magnetometer Measurement', '10 s']],
  pass: ['Estimated XYZ rates match the MEMS rate sensor reading to within 1 deg/s.', 'Magnetometer measurements change with a period that matches the estimated rate (150 s period here means 2.4 deg/s about Y; Z lagging X by 90° means a positive spin).'],
  trouble: [
    ['Main magnetometer faulty', 'A channel sits constant instead of varying. Sample it through the Motor microcontroller instead (Power Control, or Set Mode of Magnetometer Operation = 2 on ACP v5+), or switch to the redundant magnetometer (mode 1) if fitted.'],
    ['Calibration or mounting wrong', 'Estimated X, Y, Z come out interchanged (maybe sign-flipped) against the MEMS rates. Fix mounting, offset, scaling and sensitivity. At this point sensitivity should still be identity and offset zero.'],
    ['Spinning too fast', 'The filter is only accurate below 35 deg/s per axis. The MEMS gyros saturate near ±85 deg/s on the default ±75 range; raise RateSensorMult (1 = ±75, 2 = ±150, 4 = ±300, 12 = ±900 deg/s), use MEMS estimation (mode 1) and go on to fast detumbling.'],
  ],
  build() {
    const w = t => [-0.12 + 0.03 * Math.sin(t / 40), 2.4 + 0.04 * Math.sin(t / 25), 0.08 * Math.cos(t / 33)];
    return {
      q0: Q.euler(10, 25, 5),
      f(t, i) {
        const ww = w(t), e = Math.exp(-t / 5);
        return { w: ww, B: Borc(t), est: [noisy(ww[0] - 0.9 * e, i, 1, 0.03), noisy(ww[1] - 2.9 * e, i, 2, 0.03), noisy(ww[2] + 1.8 * e, i, 3, 0.03)], mems: noisy(ww[1], i, 4, 0.05) };
      },
    };
  },
  charts: () => [
    { title: 'Estimated rates (X, Y, Z) and MEMS Y rate', unit: 'deg/s', series: [...xyz('est'), ser('Y MEMS', cc.ink, s => s.mems, { dash: true })], marks: [{ t: 25, label: 'filter settled' }] },
    { title: 'Magnetometer, body frame', unit: 'µT', series: xyz('bBody') },
  ],
  show: { b: true },
});

/* ------------------------------------------------------------------ 2 */
SCENES.push({
  id: 2, title: 'Initial detumbling', phase: 'a', sec: '4', pages: '16–19', dur: 20, N: 400,
  params: [seg('rate', 'Tumble rate', [['n', '~10 deg/s'], ['f9', '80 deg/s'], ['f8', '400 deg/s'], ['bad', '80 deg/s, wrong mode']])],
  modes: P => [{ t: 0, est: 2, ctl: 0 }, { t: 60, est: 2, ctl: { n: 1, f9: 9, f8: 8, bad: 1 }[P.rate] }],
  duration: '1 orbit for the initial activations', prereq: 'Rates known (step 1). Motor microcontroller on for MEMS rate data.',
  story: 'B-dot detumbling pushes the magnetorquers against the changing field to bleed off X and Z spin. It needs no rate knowledge, so it works before the estimator is trusted. The very first activation is capped at 600 s: if a torquer polarity is wrong it would spin the satellite up, and the timeout limits the damage.',
  note: P => ({
    n: 'Normal detumbling (mode 1) works up to roughly 40 deg/s.',
    f9: 'Fast Spin Detumbling (mode 9) handles anything under 100 deg/s.',
    f8: 'Very Fast Spin Detumbling (mode 8) runs a 10 Hz magnetometer loop inside CubeControl Signal and can recover from about 1000 deg/s. Decay time here is a sketch.',
    bad: 'Don\'t: above about 40 deg/s the 1 s loop is too slow, the torque lands late, and rates can grow instead of shrinking.',
  }[P.rate]),
  cmds: P => [
    { t: 0, title: 'ADCS Run Mode', detail: 'State = Enabled (1)' },
    { t: 20, title: 'Power Control', detail: 'CubeControl Signal and/or Motor = On (1), all others Off (0)' },
    { t: 40, title: 'Set Estimation Mode', detail: 'Magnetometer rate filter (2) or MEMS rate sensing (1)' },
    { t: 60, title: 'Set Control Mode', detail: { n: 'Detumbling (1), Timeout = 600 s (first activation)', f9: 'Fast Spin Detumbling (9)', f8: 'Very Fast Spin Detumbling (8)', bad: 'Detumbling (1), Timeout = 600 s' }[P.rate] },
    { t: 200, kind: 'wait', title: 'Next pass', detail: 'Compare estimated and MEMS rates to confirm the torquers are damping, not spinning you up.' },
  ],
  tlm: [['Estimated Angular Rates', '10 s'], ['Rate Sensor Rates', '10 s'], ['Magnetic Field Measurement', '10 s'], ['Magnetorquer Commands', '10 s']],
  pass: ['X and Z rates fall.', 'Y rate moves toward the reference spin rate.'],
  trouble: [
    ['Torquer or magnetometer mismatch', 'A wrong magnetometer calibration/mounting or torquer configuration makes torquers fire against a mismatched field. Default torquer config is usually 1 = +X, 2 = +Y, 3 = +Z, but differs for non-standard mounting. Check polarity after delivery, then fix magnetometer calibration and mounting.'],
    ['Boom may have deployed itself', 'If torquers and calibration are right and detumbling still performs badly, set the mounting angles to the deployed magnetometer and try again (see step 4).'],
  ],
  build(P) {
    const v = P.rate, T = { n: 7000, f9: 16000, f8: 10000, bad: 7000 }[v];
    return {
      T, q0: Q.euler(30, 10, 45),
      f(t, i) {
        let w, m;
        if (v === 'n') { const k = Math.exp(-t / 1400); w = [5 * Math.cos(t / 90) * k, -0.9 + 10.9 * k, -4 * Math.sin(t / 90) * k]; m = k; }
        else if (v === 'f9') { const k = Math.pow(Math.max(0, 1 - t / 15000), 1.1); w = [1.6 * Math.cos(t / 400) * k, 80 * k, 1.2 * Math.sin(t / 400) * k]; m = k; }
        else if (v === 'f8') { const k = Math.pow(Math.max(0, 1 - t / 8500), 1.4); w = [4 * Math.cos(t / 120) * k, 400 * k, 3 * Math.sin(t / 120) * k]; m = k; }
        else { const g = 1 - Math.exp(-t / 2500); w = [6 * Math.sin(t / 200) * (1 + t / 3000), 80 + 25 * g, 5 * Math.cos(t / 200) * (1 + t / 3000)]; m = 1; }
        const on = t > 60 ? 1 : 0;
        return { w, B: Borc(t), mtq: [on * Math.sin(t / 7) * clamp(m + 0.15, 0, 1), on * Math.sin(t / 5 + 1) * clamp(m + 0.15, 0, 1), on * Math.sin(t / 9 + 2) * clamp(m + 0.15, 0, 1)] };
      },
    };
  },
  charts: P => [{ title: 'Body rates', unit: 'deg/s', series: xyz('w'), marks: [{ t: 60, label: 'torquers on' }] }],
  show: { b: true, mtq: true },
});

/* ------------------------------------------------------------------ 3 */
SCENES.push({
  id: 3, title: 'Continued detumbling to Y-Thomson', phase: 'a', sec: '4', pages: '16–18', T: ORBIT_T, dur: 22, N: 500,
  modes: [{ t: 0, est: 2, ctl: 2 }], tool: 'inertia',
  duration: '1 orbit, then until the spin is steady', prereq: 'MEMS rate sensing or the magnetometer rate filter is running (Y-Thomson needs the estimated Y rate).',
  story: 'Y-Thomson adds a target: it damps X and Z, and drives the Y body rate to a reference of −1 or −2 deg/s. The satellite ends up rotating slowly about the orbit normal like a wheel rolling along the track. That stable spin is the starting point for the rest of the commissioning.',
  cmds: () => [
    { t: 0, title: 'Set Control Mode', detail: 'Initial activation: Y-Thomson (2), Timeout = 600 s' },
    { t: 700, kind: 'wait', title: 'Next pass', detail: 'X and Z rates dropping, Y heading for the reference.' },
    { t: 1500, title: 'Set Control Mode', detail: 'Final activation: Y-Thomson (2), Timeout = 0 s (indefinite)' },
    { t: 3000, kind: 'wait', title: 'Hold', detail: 'Until X and Z ≈ 0 and Y sits at the reference.' },
  ],
  tlm: [['Estimated Angular Rates', '10 s'], ['Rate Sensor Rates', '10 s'], ['Magnetic Field Measurement', '10 s'], ['Magnetorquer Commands', '10 s']],
  pass: ['Initial activations: X and Z rates decrease, Y heads toward the reference.', 'Final: X and Z around 0 deg/s, Y at −1 or −2 deg/s (the QB50 satellites used −2.2).'],
  trouble: [
    ['Spin axis must be the orbit normal', 'In a good Y-Thomson spin the field\'s X and Z components swing sinusoidally while Y moves slowly. A big Y component (small orbit-normal component in a polar orbit) just means it needs more time to settle.'],
    ['Inertia ratio', 'Body Y moment of inertia must be the largest, and exceed the middle one by at least 5%. Add mass symmetrically about the centre of mass, near body Z and far from Y. If that isn\'t practical, command a negative wheel momentum of 10–20% of wheel capacity (−800 to −1600 rpm for a 3U with a CubeWheel Small).'],
  ],
  build() {
    return {
      q0: Q.euler(15, 20, 30),
      f(t, i) {
        const a = 1 - Math.exp(-t / 900), k = Math.exp(-t / 700), j = 0.12 * (1 - Math.exp(-t / 700));
        const w = [1.0 * k * Math.cos(t / 80) + j * Math.sin(t / 35), -0.9 - 1.3 * a + j * 0.5 * Math.sin(t / 51), -1.0 * k * Math.sin(t / 80) + j * Math.cos(t / 29)];
        return { w, B: Borc(t), mtq: [Math.sin(t / 7) * (k + 0.1), Math.sin(t / 5) * (k + 0.1), Math.sin(t / 9) * (k + 0.1)] };
      },
    };
  },
  charts: () => [
    { title: 'Body rates', unit: 'deg/s', series: xyz('w'), marks: [{ t: 1500, label: 'final activation' }] },
    { title: 'Magnetometer, body frame', unit: 'µT', series: xyz('bBody'), y: [-50, 50] },
  ],
  show: { b: true, mtq: true },
});

/* ------------------------------------------------------------------ 4 */
SCENES.push({
  id: 4, title: 'Magnetometer deployment', phase: 'b', sec: '5', pages: '20–21', T: 70, dur: 18, N: 350,
  modes: [{ t: 0, est: 2, ctl: 0 }],
  duration: '1 min', prereq: 'Y-Thomson spin. Do this during a ground pass: you need 1 s telemetry to see it happen.',
  story: 'The boom moves the magnetometer away from solar-panel currents, wire loops and wheel magnets. When it swings out, the raw reading steps, and because the sensor frame has rotated, two of the estimated rate components swap places while the third (the hinge axis) doesn\'t change. The battery current blips as the burn wire fires. Then you tell the ADCS the new mounting angles, and the estimate matches the gyros again.',
  cmds: () => [
    { t: 0, title: 'ADCS Run Mode', detail: 'State = Enabled (1)' },
    { t: 4, title: 'Power Control', detail: 'CubeControl Signal and Motor = On (1), all others Off (0)' },
    { t: 8, title: 'Set Estimation Mode', detail: 'Magnetometer rate estimator (2)' },
    { t: 12, title: 'Set Control Mode', detail: 'None (0)' },
    { t: 18, title: 'Deploy Magnetometer Boom', detail: 'First attempt Timeout = 2 s; second 5 s; third 10 s' },
    { t: 42, title: 'Set Magnetometer Mounting Configuration', detail: 'Deployed magnetometer angles (Set Magnetometer Configuration on ACP v5+). Only temporary.' },
    { t: 56, title: 'Save Configuration', detail: 'Makes it permanent once the estimate matches the gyro again.' },
  ],
  tlm: [['Fine Estimated Angular Rates', '1 s'], ['Rate Sensor Rates', '1 s'], ['RAW Magnetometer Measurement', '1 s'], ['CubeControl Current (VBat)', '1 s']],
  pass: ['A step change shows in the RAW magnetometer measurements.', 'Two estimated rate axes swap; the hinge axis is unchanged.', 'After the new mounting is set, estimated Y rate matches the MEMS Y rate again.'],
  trouble: [
    ['Nothing seen', 'Try longer burns: 2 s, then 5 s, then 10 s. If still nothing, deployment either failed or already happened earlier. Either way, carry on to the next step.'],
    ['Proving it was attempted', 'Watch the VBat Current channel in CubeControl Current Measurements at 1 s sampling.'],
  ],
  build() {
    const tD = 18, tM = 42;
    return {
      q0: Q.euler(0, 0, 10),
      f(t, i) {
        const w = [0.1 + 0.03 * Math.sin(t / 7), -2.2, 0.05];
        const est = t < tD ? w : t < tM ? [w[1], -w[0], w[2]] : w;
        const burn = t >= tD && t < tD + 2.2;
        return { w, B: Borc(t), boom: sstep(t, tD, tD + 2), estr: [noisy(est[0], i, 1, 0.03), noisy(est[1], i, 2, 0.03), noisy(est[2], i, 3, 0.03)], mems: noisy(w[1], i, 4, 0.04), cur: noisy(burn ? 520 : 45, i, 5, burn ? 25 : 4) };
      },
      derive(s, i, t) { const b = s.bBody; s.raw = t < tD ? [b[0] + 8 + noise(i, 6) * 1.5, b[1] - 5 + noise(i, 7) * 1.5, b[2] + 3 + noise(i, 8) * 1.5] : [b[1] + noise(i, 6) * 0.4, -b[0] + noise(i, 7) * 0.4, b[2] + noise(i, 8) * 0.4]; },
    };
  },
  charts: () => [
    { title: 'RAW magnetometer', unit: 'µT', series: xyz('raw'), marks: [{ t: 18, label: 'deploy' }] },
    { title: 'Estimated rates vs MEMS Y rate', unit: 'deg/s', series: [...xyz('estr'), ser('Y MEMS', cc.ink, s => s.mems, { dash: true })], marks: [{ t: 42, label: 'mounting set' }] },
    { title: 'VBat current (schematic)', unit: 'mA', series: [ser('current', cc.amber, s => s.cur)] },
  ],
  show: { b: true },
});

/* ------------------------------------------------------------------ 5 */
SCENES.push({
  id: 5, title: 'Magnetometer calibration', phase: 'b', sec: '6', pages: '22–25', T: 7000, dur: 24, N: 700,
  modes: [{ t: 0, est: 2, ctl: 2 }],
  duration: '1 orbit of logging, then ground processing', prereq: 'All angular rate components between −3 and +3 deg/s. Y-Thomson is ideal.',
  story: 'The ground calibration drifts and doesn\'t match the satellite exactly. Log the magnetometer every 10 s for a full orbit, then fit a bias and a sensitivity (non-orthogonality) matrix by batch least squares in CubeSupport against the IGRF field along an SGP4 orbit. Each dot is one measurement divided by the model field magnitude. Uncalibrated, the dots form an offset, squashed shell. After the fit it is a unit sphere.',
  cmds: () => [
    { t: 0, title: 'ADCS Run Mode', detail: 'State = Enabled (1)' },
    { t: 10, title: 'Power Control', detail: 'CubeControl Signal and Motor = On (1), all others Off (0)' },
    { t: 20, title: 'Set Estimation Mode', detail: 'Magnetometer rate estimator (2)' },
    { t: 30, title: 'Set Control Mode', detail: 'Preferred: Y-Thomson (2)' },
    { t: 40, kind: 'wait', title: 'Delay', detail: '1 orbit, logging calibrated magnetometer every 10 s' },
    { t: 5500, kind: 'ground', title: 'On-ground processing', detail: 'CubeSupport fits bias and sensitivity matrix. Needs the nearest TLE and accurate sample times.' },
    { t: 6300, title: 'Set Magnetometer Configuration', detail: 'Updated sensitivity matrix and offset vector (Set Redundant Magnetometer Configuration for the redundant one)' },
    { t: 6700, title: 'Save Configuration', detail: 'Otherwise the parameters are lost at reset.' },
  ],
  tlm: [['Fine Estimated Angular Rates', '10 s'], ['Rate Sensor Rates', '10 s'], ['Calibrated Magnetometer Measurement', '10 s']],
  pass: ['The measurement error (σ, RMS against the model field magnitude) has been determined.', 'The manual\'s example drops from σ = 2.848 µT to σ = 0.365 µT.'],
  trouble: [
    ['Bad result', 'Electromagnetic interference can upset the field measurement; a UHF transmitter is a prime suspect. Transmit at lower power, or pause non-critical transmissions while collecting samples. If it can\'t be cured, use the redundant magnetometer.'],
    ['Main and redundant separately', 'Calibrate them separately. ACP v3 has one parameter set for whichever is selected; v5 and later keep two.'],
  ],
  build() {
    const dir = t => { const a = (-2.2 * t * D2R) * 0.6, b = 0.9 * Math.sin(TAU * t / ORBIT_T * 1.3) + 0.25 * Math.sin(t / 700); return V.norm([Math.cos(a) * Math.cos(b), Math.sin(b), Math.sin(a) * Math.cos(b)]); };
    return {
      f(t, i) {
        const k = i * 10, logging = k <= 5500;
        if (!logging) return { euler: [0, 0, 0] };
        const d = dir(k), g = igrf(k), B = V.mul(d, g);
        const meas = V.add(CAL_B, [0, 1, 2].map(r => B[r] + CAL_E[r][0] * B[0] + CAL_E[r][1] * B[1] + CAL_E[r][2] * B[2]));
        const post = V.add(B, [0.64 * noise(i, 2), 0.64 * noise(i, 3), 0.64 * noise(i, 4)]);
        return { euler: [0, 0, 0], igrf: g, pre: meas, post, preM: V.len(meas), postM: V.len(post) };
      },
      derive(s, i, t, all) { if (i === all.length - 1) { /* sigma over logged data */ let a = 0, b = 0, n = 0; for (const p of all) if (p.igrf) { a += (p.preM - p.igrf) ** 2; b += (p.postM - p.igrf) ** 2; n++; } SCENES[4].sigma = [Math.sqrt(a / n), Math.sqrt(b / n)]; } },
    };
  },
  charts: () => [{
    title: 'Field magnitude vs IGRF model', unit: 'µT', xmax: 5500,
    series: [ser('IGRF model', '#C0392B', s => s.igrf), ser('measured', '#2F78BF', s => s.preM, { rev: t => Math.min(1, t / 5500) }),
      ser('calibrated', '#1F9D6B', s => s.postM, { rev: t => sstep(t, 6300, 6700), when: t => t >= 6300 })],
    marks: [{ t: 5500, label: 'end of logging' }],
  }],
  draw(ctx, W, H, s, t, P, ui) {
    const S = ui.samples, k = sstep(t, 6300, 6600), n = Math.min(550, Math.floor(clamp(t / 5500, 0, 1) * 550));
    const cam = makeCam(W * 0.5, H * 0.52, Math.min(W, H) * 0.31, -35 + t / 70, 18);
    ctx.strokeStyle = 'rgba(214,228,240,0.22)'; ctx.lineWidth = 1;
    for (const ax of [0, 1, 2]) { ctx.beginPath(); for (let a = 0; a <= 48; a++) { const u = a / 48 * TAU, p = [0, 0, 0]; p[(ax + 1) % 3] = Math.cos(u); p[(ax + 2) % 3] = Math.sin(u); const q = cam.p(p); a ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); } ctx.stroke(); }
    [[1, 0, 0], [0, 1, 0], [0, 0, 1]].forEach((e, i) => { drawArrow(ctx, cam, [0, 0, 0], V.mul(e, 1.45), AX[i], 'XYZ'[i], { w: 1.3, head: 5, alpha: 0.7 }); });
    const pts = [];
    for (let i = 0; i < n; i++) {
      const p = S[i]; if (!p.igrf) continue;
      const a = V.mul(p.pre, 1 / p.igrf), b = V.mul(p.post, 1 / p.igrf);
      pts.push([V.add(V.mul(a, 1 - k), V.mul(b, k)), i]);
    }
    pts.sort((u, v) => cam.p(v[0])[2] - cam.p(u[0])[2]);
    for (const [v] of pts) { const q = cam.p(v), al = clamp(0.62 - q[2] * 0.4, 0.2, 1); ctx.fillStyle = k < 0.5 ? `rgba(240,113,76,${al})` : `rgba(77,187,140,${al})`; ctx.beginPath(); ctx.arc(q[0], q[1], 2.6, 0, TAU); ctx.fill(); }
    ctx.fillStyle = C.text; ctx.font = '600 14px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'left';
    const sg = SCENES[4].sigma || [0, 0];
    ctx.fillText(k < 0.02 ? 'Measured field, ÷ model magnitude' : 'Calibration applied', 16, H - 44);
    ctx.fillStyle = C.dim; ctx.font = '13px "Instrument Sans", system-ui, sans-serif';
    ctx.fillText(n + ' samples at 10 s   ·   σ before ' + sg[0].toFixed(2) + ' µT, after ' + sg[1].toFixed(2) + ' µT', 16, H - 24);
  },
});

/* ------------------------------------------------------------------ 6 */
SCENES.push({
  id: 6, title: 'Angular rate and pitch angle estimation', phase: 'b', sec: '7', pages: '26', T: ORBIT_T, dur: 22, N: 500,
  modes: [{ t: 0, est: 3, ctl: 2 }],
  duration: '1 orbit of logging', prereq: 'Y-Thomson spin held for at least 1 orbit. Time synchronised to Unix, recent TLEs uploaded.',
  story: 'Before the momentum wheel can be trusted you need to know where the satellite is pointing about the orbit normal. Estimation mode 3 adds a pitch angle to the rate estimate, using the IGRF model, which is why the satellite position (TLE) and the clock must be right. In Y-Thomson the pitch angle simply winds round at the reference spin rate.',
  cmds: () => [
    { t: 0, title: 'ADCS Run Mode', detail: 'State = Enabled (1)' },
    { t: 10, title: 'Power Control', detail: 'CubeControl Signal and Motor = On (1), all others Off (0)' },
    { t: 20, title: 'Set Estimation Mode', detail: 'Magnetometer rate filter with pitch estimation (3)' },
    { t: 30, title: 'Set Control Mode', detail: 'Y-Thomson (2)' },
    { t: 60, kind: 'wait', title: 'Log one orbit', detail: 'Attitude and rates every 10 s' },
  ],
  tlm: [['Fine Estimated Angular Rates', '10 s'], ['Estimated Attitude Angles', '10 s'], ['Rate Sensor Rates', '10 s'], ['Magnetometer Measurement', '10 s']],
  pass: ['The satellite stays in Y-Thomson.', 'The pitch angle changes at the reference spin rate.'],
  trouble: [['Pitch wanders or jumps', 'Check the clock is on Unix time and the TLEs are recent (NORAD data from space-track.org or celestrak.com). Position error feeds straight into the field model.']],
  build() {
    return {
      q0: Q.euler(0, 40, 0),
      f(t, i) {
        const w = [0.08 * Math.sin(t / 37), -2.2 + 0.07 * Math.sin(t / 53), 0.07 * Math.cos(t / 41)];
        return { w, B: Borc(t) };
      },
      derive(s, i) { const e = Math.exp(-s.t / 160); s.pitch = wrap180(s.ang[1] + 40); s.pitchEst = wrap180(s.pitch + 35 * e * Math.cos(s.t / 50) + noise(i, 3) * 1.2); s.west = [noisy(s.w[0], i, 4, 0.04), noisy(s.w[1], i, 5, 0.04), noisy(s.w[2], i, 6, 0.04)]; },
    };
  },
  charts: () => [
    { title: 'Pitch angle', unit: 'deg', y: [-180, 180], series: [ser('true', cc.y, s => s.pitch), ser('estimated', cc.ink, s => s.pitchEst, { dash: true })] },
    { title: 'Estimated rates', unit: 'deg/s', series: xyz('west') },
  ],
  overlay(ctx, W, H, s) { pitchDial(ctx, W - 70, 112, 44, s.pitch, s.pitchEst); },
  show: { b: true },
});

/* ------------------------------------------------------------------ 7 */
SCENES.push({
  id: 7, title: 'Y-wheel ramp-up test', phase: 'c', sec: '8', pages: '27–28', T: 360, dur: 22, N: 360,
  params: [seg('pol', 'Wheel polarity', [['ok', 'Correct'], ['bad', 'Reversed']])],
  modes: [{ t: 0, est: 3, ctl: 2 }, { t: 40, est: 3, ctl: 0 }, { t: 230, est: 3, ctl: 2 }], tool: 'wheel',
  duration: '1 pass, with the satellite in view of the ground station', prereq: 'Mode 3 estimation has been active for 1 min. Y-Thomson held for at least 1 orbit.',
  story: 'Before Y-momentum mode, prove the wheel can be commanded and that its momentum has the right sign. Y-Thomson is switched off, then the wheel is spun to the speed that would swallow all of the satellite\'s spin momentum. If the polarity is right the body Y rate falls to zero and pitch stops changing. When the wheel stops, the momentum flows back and the spin returns.',
  note: P => P.pol === 'bad' ? 'Reversed polarity: the body Y rate increases during the ramp, the opposite of the expected result. Fix the wheel polarity in the ADCS configuration.' : 'Y rate falls toward zero as the wheel ramps, then returns to the reference when the wheel stops.',
  cmds: () => [
    { t: 0, title: 'ADCS Run Mode', detail: 'State = Enabled (1)' },
    { t: 10, title: 'Power Control', detail: 'Signal + Motor On. Y-Momentum unit: Motor power On. 3-Axis unit: CubeWheel-Y On. All others Off.' },
    { t: 20, title: 'Set Estimation Mode', detail: 'Magnetometer rate filter with pitch estimation (3)' },
    { t: 40, title: 'Set Control Mode', detail: 'None (0): switch Y-Thomson off first' },
    { t: 50, title: 'Wheel Speed Command', detail: 'Commanded Y speed = ω_wheeltest (see calculator, about −3950 rpm in the manual\'s 3U example)' },
    { t: 55, kind: 'wait', title: 'Delay', detail: '2 min at constant speed' },
    { t: 175, title: 'Wheel Speed Command', detail: 'Commanded Y speed = 0 rpm' },
    { t: 230, title: 'Set Control Mode', detail: 'Y-Thomson (2) again' },
  ],
  tlm: [['Fine Estimated Angular Rates', '1 s'], ['Estimated Attitude Angles', '1 s'], ['Rate Sensor Rates', '1 s'], ['Measured Wheel Speed', '1 s'], ['Magnetometer Measurement', '1 s']],
  pass: ['Measured wheel speed matches the commanded speed.', 'Estimated Y rate goes to zero as the wheel ramps up, and back to the reference spin rate when it stops.', 'Pitch angle is near-constant, or slowly varying, while the wheel spins.'],
  trouble: [['Y rate went up, not down', 'The wheel polarity is wrong. Correct it by updating the ADCS configuration.']],
  build(P) {
    const W = -3950, wref = -1, slew = 150; let rpm = 0;
    return {
      q0: Q.euler(0, 0, 0),
      f(t, i) {
        const cmd = t >= 50 && t < 175 ? W : 0;
        const d = clamp(cmd - rpm, -slew, slew); rpm += d;
        const r = P.pol === 'ok' ? 1 - rpm / W : 1 + rpm / W;
        const wy = wref * (t < 40 ? 1 : t < 230 ? r : lerp(r, 1, sstep(t, 230, 250)));
        return { w: [0.03 * Math.sin(t / 9), wy, 0.03 * Math.cos(t / 11)], B: Borc(t), wheel: [0, rpm, 0], cmd: [0, cmd, 0], yest: noisy(wy, i, 2, 0.02), mems: noisy(wy, i, 3, 0.05) };
      },
      derive(s) { s.pitch = wrap180(s.ang[1]); },
    };
  },
  charts: () => [
    { title: 'Y wheel speed', unit: 'rpm', series: [ser('commanded', cc.grey, s => s.cmd[1], { dash: true }), ser('measured', cc.violet, s => s.wheel[1])] },
    { title: 'Body Y rate', unit: 'deg/s', series: [ser('estimated', cc.y, s => s.yest), ser('MEMS', cc.ink, s => s.mems, { dash: true })] },
    { title: 'Pitch angle', unit: 'deg', y: [-180, 180], series: [ser('pitch', cc.ink, s => s.pitch)] },
  ],
  show: { b: false, wheels: [1] },
});

/* ------------------------------------------------------------------ 8 */
const S8 = (() => {
  const o = { tc: 300, tau: 250 }; o.tB = o.tc + 6 * o.tau;
  o.unw = t => (t < o.tc ? 550 + 2.2 * (o.tc - t) : 550 - 2.2 * o.tau * (1 - Math.exp(-(t - o.tc) / o.tau)));
  o.rate = t => (t < o.tc ? -2.2 : -2.2 * Math.exp(-(t - o.tc) / o.tau));
  o.pitch = t => { if (t < o.tB) return wrap180(o.unw(t)); const e0 = wrap180(o.unw(o.tB)), s = t - o.tB; return e0 * Math.exp(-s / 500) + 8 * Math.sin(s / 500) * Math.exp(-s / 900) * sstep(s, 0, 100); };
  o.ta = 0; for (let t = o.tc; t < 4200; t += 2) if (Math.abs(o.pitch(t)) >= 50) o.ta = t;
  o.te = o.ta; for (let t = o.ta; t < 4200; t += 2) if (Math.abs(o.pitch(t)) > 10) o.te = t;
  o.ta = Math.round(o.ta / 10) * 10; o.te = Math.round(o.te / 10) * 10 + 30;
  return o;
})();
SCENES.push({
  id: 8, title: 'Initial Y-momentum activation', phase: 'c', sec: '9', pages: '29–35', dur: 26, N: 600,
  modes: [{ t: 0, est: 3, ctl: 2 }, { t: S8.tc, est: 3, ctl: 3 }, { t: S8.ta, est: 3, ctl: 4 }, { t: S8.te, est: 5, ctl: 4 }],
  duration: 'One orbit for the first activation', prereq: 'Mode 3 estimation active for 1 min, Y-Thomson held for 1 orbit.',
  story: 'Now the wheel takes over. The satellite is spinning at −2.2 deg/s; the wheel absorbs that momentum and the pitch angle is pulled to nadir. Magnetometer-only inputs are all that is trusted for now, so the Sun, nadir, CSS and star-tracker masks are switched off. Control mode 3 captures the pitch; the ADCS drops into steady mode 4 on its own once the momentum is in the wheel and pitch is within 50° of nadir. When pitch settles within ±10° you move to the Full-state EKF.',
  cmds: () => [
    { t: 0, title: 'ADCS Run Mode', detail: 'State = Enabled (1)' },
    { t: 40, title: 'Set Unix time', detail: 'Current Unix time' },
    { t: 70, title: 'Set Orbit Parameters', detail: 'Current TLEs, then Save Orbit Parameters to flash' },
    { t: 120, title: 'Set Estimation Parameters', detail: 'Use Sun, Nadir, CSS and Star Tracker = 0 (false). All other noise covariances at default (from AdcsConfig XML).' },
    { t: 180, title: 'Set Estimation Mode', detail: 'Magnetometer rate filter with pitch estimation (3)' },
    { t: 300, title: 'Set Control Mode', detail: 'First time: Initial Y-momentum (3), duration 1 orbit. Later: Steady Y-momentum (4), indefinite.' },
    { t: S8.ta, kind: 'wait', title: 'Auto switch', detail: 'Control changes itself to mode 4 once pitch is within 50° of nadir' },
    { t: S8.ta + 60, kind: 'wait', title: 'Delay', detail: 'Until pitch angle is between −10° and +10°' },
    { t: S8.te, title: 'Set Estimation Mode', detail: 'Full-state EKF (5)' },
  ],
  tlm: [['Fine Estimated Angular Rates', '10 s'], ['Estimated Attitude Angles', '10 s'], ['Rate Sensor Rates', '10 s'], ['Measured wheel speed', '10 s'], ['Magnetometer Measurement', '10 s'], ['Satellite position (LLH)', '10 s']],
  pass: ['Pitch angle is controlled to zero.', 'Angular rates are controlled to zero.', 'Wheel momentum stays around the reference value.'],
  trouble: [['Log the on-board position', 'At least for the first activation, check on-board position and velocity so you know the TLE upload took.'], ['Simulate before adjusting', 'Gains and noise covariances will likely need tuning, so logging is essential. Simulation testing before changes is strongly advised.']],
  build() {
    const tc = S8.tc;
    return {
      T: 4200, q0: Q.euler(0, 0, 0),
      f(t, i) {
        const pitch = S8.pitch(t), s2 = Math.max(0, t - tc), nut = s2 > 0 ? Math.exp(-s2 / 700) : 0, late = sstep(t, S8.tB, S8.tB + 400);
        const roll = 18 * nut * Math.cos(s2 / 160) + 3 * Math.sin(t / 500) * late, yaw = -14 * nut * Math.sin(s2 / 190) + 2 * Math.cos(t / 450) * late;
        return { euler: [roll, pitch, yaw], w: [0, S8.rate(t), 0], wheel: [0, -3000 * sstep(t, tc, tc + 600) * (1 - 0.1 * sstep(t, 2000, 3000)), 0], B: Borc(t) };
      },
    };
  },
  charts: () => [
    { title: 'Estimated attitude angles', unit: 'deg', y: [-180, 180], series: [ser('roll', cc.x, s => s.eul[0]), ser('pitch', cc.y, s => s.eul[1]), ser('yaw', cc.z, s => s.eul[2])], marks: [{ t: S8.tc, label: 'mode 3' }, { t: S8.ta, label: 'auto mode 4', row: 1 }, { t: S8.te, label: 'EKF', row: 2 }] },
    { title: 'Y wheel speed', unit: 'rpm', series: [ser('wheel Y', cc.violet, s => s.wheel[1])] },
  ],
  overlay(ctx, W, H, s) { pitchDial(ctx, W - 70, 112, 44, s.eul[1], null); },
  show: { wheels: [1], nadir: true },
});

/* ------------------------------------------------------------------ 9 */
SCENES.push({
  id: 9, title: 'Continued Y-momentum activation and magnetometer EKF', phase: 'c', sec: '9', pages: '29–36', T: ORBIT_T * 3, dur: 24, N: 600,
  params: [range('gain', 'Momentum-management gain', 1, 5, 0.5, 1, v => '×' + v)],
  modes: [{ t: 0, est: 5, ctl: 4 }], exag: 1.0,
  duration: 'Indefinite', prereq: 'Pitch within ±10°, Full-state EKF running on magnetometer only.',
  story: 'The satellite now holds nadir on the wheel alone. Real disturbance torques (drag, solar pressure) push it away from zero roll, pitch and yaw, and the wheel pushes back, so wheel momentum builds up and breathes over each orbit. The attitude stays within about ±10° with magnetometer-only sensing. Turning up the magnetic momentum-management gain makes the torquers dump that build-up faster.',
  cmds: () => [
    { t: 0, title: 'Set Control Mode', detail: 'Steady Y-momentum (4), duration indefinite' },
    { t: 0, title: 'Set Estimation Mode', detail: 'Full-state EKF (5), magnetometer measurements only' },
    { t: 1000, kind: 'wait', title: 'Tune', detail: 'Adjust gains from logged data: Y-wheel gains, reference momentum, momentum-management gain' },
  ],
  tlm: [['Fine Estimated Angular Rates', '10 s'], ['Estimated Attitude Angles', '10 s'], ['Measured wheel speed', '10 s'], ['Magnetometer Measurement', '10 s']],
  pass: ['Roll, pitch and yaw errors of about ±10° or better.', 'Wheel momentum stays around the reference value (it will swing with orbit-period disturbance).'],
  trouble: [
    ['Better estimation', 'Use Full-state EKF with Y-momentum control, add Sun and/or Nadir (step 10–11), calibrate the magnetometer, add the star tracker, or use the gyro-based EKF.'],
    ['Wheel gains', 'Gains are set by CubeSpace from the Mission Overview and verified in simulation. With strong aerodynamic torque, change them via Set Y-Wheel Control Parameters.'],
    ['Reference momentum', 'With large external disturbance torques, a larger reference momentum adds gyroscopic stiffness.'],
    ['Momentum build-up', 'Raise the momentum-management gain, or fly at a different non-zero pitch angle to cut aerodynamic torque (simulate with full aero modelling).'],
  ],
  build(P) {
    const g = P.gain, a = 1 / Math.sqrt(g);
    return {
      q0: Q.euler(0, 0, 0),
      f(t, i) {
        const u = TAU * t / ORBIT_T, sw = sstep(t, 0, 800);
        const roll = 6.5 * a * Math.sin(u + 0.4) * sw + 0.4 * noise(i, 1), pitch = 3 * a * Math.sin(2 * u) * sw + 0.3 * noise(i, 2), yaw = 7 * a * Math.cos(u + 0.2) * sw + 0.4 * noise(i, 3);
        const wheel = -2900 - (700 / g) * Math.sin(u - 0.5) * sw;
        return { euler: [roll, pitch, yaw], wheel: [0, wheel, 0], B: Borc(t), w: [0, 0, 0] };
      },
    };
  },
  charts: () => [
    { title: 'Estimated attitude angles', unit: 'deg', series: [ser('roll', cc.x, s => s.eul[0]), ser('pitch', cc.y, s => s.eul[1]), ser('yaw', cc.z, s => s.eul[2])], y: [-12, 12] },
    { title: 'Y wheel speed', unit: 'rpm', series: [ser('wheel Y', cc.violet, s => s.wheel[1])], y: [-4200, -1800] },
  ],
  show: { wheels: [1], nadir: true },
});

/* ------------------------------------------------------------------ 10 */
function sensorScene(o) { return o; }
SCENES.push({
  id: 10, title: 'CubeSense Sun/nadir commissioning', phase: 'd', sec: '10', pages: '37–39', T: ORBIT_T, dur: 26, N: 600,
  params: [seg('cfg', 'Camera settings', [['good', 'Good exposure'], ['bad', 'Wrong exposure or threshold']])],
  modes: [{ t: 0, est: 5, ctl: 4 }],
  duration: '1 orbit', prereq: 'Stable nadir pointing in Y-momentum control.',
  story: 'Run a full orbit with the CubeSense cameras powered but not yet trusted: the Sun and nadir masks stay at 0, so the EKF ignores them while you check them. The nadir camera should see the Earth as a disc dead ahead, giving a vector near [0, 0, 1]. The Sun camera sees a bright dot whose position follows the Sun round the orbit. In eclipse both should report an invalid, all-zero detection with no false hits in sunlight.',
  note: P => P.cfg === 'bad' ? 'Wrong exposure or threshold: random detection failures in sunlight. Capture an image, compare, and adjust the exposure and detection threshold.' : 'Zero or few detection errors in sunlight; zeros in eclipse.',
  cmds: () => [
    { t: 0, title: 'Power Control', detail: 'ACP v3/5: CubeSense On. ACP v6+: CubeSense1 (and CubeSense2 if fitted) On. All others default.' },
    { t: 15, title: 'Set Estimation Parameters', detail: 'Use Sun sensor mask = 0, Use Nadir sensor mask = 0, all others defaults' },
    { t: 30, title: 'Set Estimation Mode', detail: 'Full-state or Gyro EKF (5 or 6)' },
    { t: 60, kind: 'wait', title: 'Log one orbit', detail: 'Raw CSS, Cam1 (and Cam2) measurements, fine Sun vector, nadir vector' },
  ],
  tlm: [['Estimated Fine Angular Rates', '10 s'], ['Estimated Attitude Angles', '10 s'], ['Rate Sensor Rates', '10 s'], ['Raw CSS Measurements', '10 s'], ['Raw Cam1 Measurements', '10 s'], ['Raw Cam2 Measurements (if fitted)', '10 s'], ['Fine Sun Vector', '10 s'], ['Nadir Vector', '10 s']],
  pass: ['Nadir: X and Y angles near zero, few or no detection errors in sunlight, invalid result in eclipse.', 'Sun: X and Y vary in step with the CSS measurements, few or no detection errors in sunlight, invalid result in eclipse.'],
  trouble: [
    ['Detection errors in sunlight', 'Camera gain or exposure is probably wrong. Capture and download images (Save Image Command), then adjust. Sun exposure default 0, nadir exposure default 35; Sun detection threshold default 200, nadir default 150.'],
    ['Valid detections, wrong vector', 'Likely the mounting transform. See the configuration sheet (Ref 5) for how to work out the rotation angles, then set them with CubeSense Configuration.'],
    ['Capturing an image', 'Save Image Command: Camera Select Cam1 = 0, Cam2 = 1. Image Size 0 = 1024², 1 = 512², 2 = 256², 3 = 128², 4 = 64² pixels. Download over the file transfer protocol.'],
  ],
  build(P) {
    return {
      q0: Q.id(),
      f(t, i) {
        const e = ENV(t), drop = P.cfg === 'bad' && !e.ecl && hash(i, 5) > 0.76;
        const ok = !e.ecl && !drop;
        return { euler: [1.5 * Math.sin(t / 700), 0.8 * Math.sin(t / 380 + 1), 1.2 * Math.cos(t / 620)], sun: e.sun, ecl: e.ecl, B: e.B, w: [0, 0, 0], ok,
          sm: ok ? [noisy(e.sun[0], i, 1, 0.012), noisy(e.sun[1], i, 2, 0.012), noisy(e.sun[2], i, 3, 0.012)] : [0, 0, 0],
          nm: ok ? [noisy(0, i, 4, 0.012), noisy(0, i, 5, 0.012), 1] : [0, 0, 0] };
      },
    };
  },
  charts: () => [
    { title: 'CubeSense Sun vector', unit: '', y: [-1.1, 1.1], series: xyz('sm'), bands: ECL },
    { title: 'CubeSense nadir vector', unit: '', y: [-0.2, 1.2], series: xyz('nm'), bands: ECL },
  ],
  overlay(ctx, W, H, s, t, P, ui) { cameraInsets(ctx, W, H, s, t); },
  show: { sun: true, nadir: true, orbit: true, masks: { sun: false, nadir: false } },
});

/* ------------------------------------------------------------------ 11 */
SCENES.push({
  id: 11, title: 'EKF activation with Sun and nadir measurements', phase: 'd', sec: '10', pages: '38', T: ORBIT_T, dur: 24, N: 600, exag: 4,
  modes: [{ t: 0, est: 5, ctl: 4 }],
  duration: '1 orbit', prereq: 'Step 10 passed: Sun and nadir sensors verified.',
  story: 'Once the cameras check out, flip their use masks to true and the Full-state EKF starts using them. Until now the attitude was held by magnetometer only. With Sun and nadir vectors in the sunlit half of the orbit, attitude error drops to a fraction of a degree. In eclipse, with only the magnetometer, it creeps up again. The motion of the satellite is exaggerated four times in the view so the difference is visible.',
  cmds: () => [
    { t: 0, kind: 'wait', title: 'Running', detail: 'Full-state EKF (5) on magnetometer only, masks = 0' },
    { t: 900, title: 'Set Estimation Parameters', detail: 'Use Sun sensor mask = 1, Use Nadir sensor mask = 1. Everything else at the default values from the latest ADCS configuration XML.' },
  ],
  tlm: [['Estimated Fine Angular Rates', '10 s'], ['Estimated Attitude Angles', '10 s'], ['Fine Sun Vector', '10 s'], ['Nadir Vector', '10 s'], ['Estimated Innovation', '10 s']],
  pass: ['Attitude error falls once the masks go true (about 0.4° in sunlight and under 1° in eclipse in the manual\'s simulation, down from about ±10° on magnetometer alone).'],
  trouble: [['Large errors after enabling', 'Go back to step 10: the raw detections or mounting transform are probably wrong. Set the masks back to 0.']],
  build() {
    return {
      q0: Q.id(),
      f(t, i) {
        const e = ENV(t), m = sstep(t, 900, 1000), amp = lerp(8, e.ecl ? 0.9 : 0.3, m);
        return { euler: [amp * Math.sin(t / 310 + 0.3) + 0.1 * noise(i, 1), 0.6 * amp * Math.sin(t / 230) + 0.1 * noise(i, 2), 0.9 * amp * Math.cos(t / 360) + 0.1 * noise(i, 3)], sun: e.sun, ecl: e.ecl, B: e.B, w: [0, 0, 0], useSN: t >= 900 };
      },
    };
  },
  charts: () => [{ title: 'True attitude error', unit: 'deg', series: [ser('roll', cc.x, s => s.eul[0]), ser('pitch', cc.y, s => s.eul[1]), ser('yaw', cc.z, s => s.eul[2])], bands: ECL, marks: [{ t: 900, label: 'masks on' }] }],
  hud: s => ['EKF inputs: magnetometer ✓', 'Sun ' + (s.useSN ? '✓' : '✗') + '   Nadir ' + (s.useSN ? '✓' : '✗')],
  show: { sun: true, nadir: true, orbit: true },
});

/* ------------------------------------------------------------------ 12 */
SCENES.push({
  id: 12, title: 'CubeStar star tracker commissioning', phase: 'd', sec: '11', pages: '40–42', T: 60, dur: 16, N: 300,
  params: [range('thr', 'Detection threshold', 2, 40, 1, 10, v => String(v))],
  modes: [{ t: 0, est: 5, ctl: 4 }],
  duration: '1 orbit of logs, then check the flags', prereq: 'Stable nadir pointing in Y-momentum or 3-axis wheel control. Use mask for the star tracker still 0.',
  story: 'This replays what one CubeStar frame goes through: capture, detect bright blobs, match them against the catalogue, then solve for attitude. Each stage sets a status bit. Drag the detection threshold. Too low and noise specks count as stars (more than 15 detected means thresholds or exposure are off). Too high and real stars are lost, and below three the tracker can\'t identify anything.',
  cmds: () => [
    { t: 0, title: 'Power Control', detail: 'CubeStar Power = On (1), all others default' },
    { t: 8, title: 'Set Estimation Parameters', detail: 'Use star tracker mask = 0 (false), all others defaults' },
    { t: 16, title: 'Set Estimation Mode', detail: 'Full-state or Gyro EKF (5 or 6)' },
    { t: 24, kind: 'wait', title: 'Log one orbit', detail: 'Download the log and check the Star Tracker Status flags, star counts, timing and quaternion' },
  ],
  tlm: [['Estimated Fine Angular Rates', '10 s'], ['Estimated Attitude Angles', '10 s'], ['Rate Sensor Rates', '10 s'], ['Raw Star Tracker measurements', '10 s']],
  pass: ['Stars identified; detected and identified counts stay within expected bounds (typically 3–15).', 'Status flags show no errors.', 'Confidence and magnitude, centroids and catalogue numbers for stars 1–3 are sensible.', 'Capture, detection and identification times are reasonable; estimated rates and quaternion look right.'],
  trouble: [
    ['Too many stars (> 15)', 'Detection threshold or star threshold too low (defaults 10 and 5), or exposure time wrong (default 2704). Set Star Tracker Configuration.'],
    ['Detected but none identified', 'Error margin too tight (default 0.85).'],
    ['Wrong vectors', 'Probably the mounting transform. See the configuration sheet (Ref 5).'],
    ['Capturing an image', 'Save Image Command with Camera Select = 2. Always full resolution, 1280 × 1038 pixels.'],
  ],
  build() { return { f: () => ({ euler: [0, 0, 0] }) }; },
  charts: () => [],
  draw(ctx, W, H, s, t, P, ui) { starScene(ctx, W, H, t, P.thr, ui); },
});

/* ------------------------------------------------------------------ 13 */
SCENES.push({
  id: 13, title: 'EKF activation with star vector measurements', phase: 'd', sec: '11', pages: '40–41', T: ORBIT_T, dur: 24, N: 600, exag: 8,
  modes: [{ t: 0, est: 5, ctl: 4 }],
  duration: 'Continuous', prereq: 'Step 12 passed.',
  story: 'Star vectors work in eclipse too, which is exactly when Sun and nadir drop out. Setting the star tracker mask to true puts them into the EKF. Watch the error on a log scale: it was a quarter of a degree in daylight and about a degree in eclipse, and falls to a couple of hundredths of a degree all the way round. Motion is exaggerated eight times in the view.',
  cmds: () => [
    { t: 0, kind: 'wait', title: 'Running', detail: 'EKF with magnetometer, Sun and nadir. Star tracker mask = 0.' },
    { t: 1000, title: 'Set Estimation Parameters', detail: 'Use star tracker mask = 1 (true), everything else at defaults' },
  ],
  tlm: [['Estimated Attitude Angles', '10 s'], ['Estimated Innovation', '10 s'], ['Quaternion Error Vector', '10 s'], ['Raw Star Tracker', '10 s']],
  pass: ['Attitude error falls and stays low through eclipse.'],
  trouble: [['No improvement', 'Re-check the star tracker flags and mounting transform (step 12) and make sure the mask really is 1.']],
  build() {
    return {
      q0: Q.id(),
      f(t, i) {
        const e = ENV(t), m = sstep(t, 1000, 1100), base = e.ecl ? 1.0 : 0.25, err = lerp(base, 0.02, m) * (1 + 0.15 * noise(i, 1));
        return { euler: [err * Math.sin(t / 220 + 0.3), 0.7 * err * Math.sin(t / 170), 0.9 * err * Math.cos(t / 260)], err, sun: e.sun, ecl: e.ecl, B: e.B, w: [0, 0, 0], useStar: t >= 1000 };
      },
    };
  },
  charts: () => [{ title: 'Attitude error magnitude (log scale)', unit: 'deg', log: true, y: [0.01, 2], series: [ser('error', cc.ink, s => s.err)], bands: ECL, marks: [{ t: 1000, label: 'star mask on' }] }],
  hud: s => ['EKF inputs: magnetometer ✓  Sun ✓  Nadir ✓', 'Star tracker ' + (s.useStar ? '✓' : '✗')],
  show: { sun: true, nadir: true, orbit: true },
});

/* ------------------------------------------------------------------ 14 */
SCENES.push({
  id: 14, title: 'Zero-bias 3-axis reaction wheel control', phase: 'e', sec: '12', pages: '43–50', dur: 24, N: 600,
  params: [seg('part', 'Part', [['pol', 'X wheel polarity test'], ['xyz', 'Enable XYZ control']])],
  modes: P => P.part === 'pol' ? [{ t: 0, est: 5, ctl: 4 }, { t: 15, est: 5, ctl: 0 }, { t: 110, est: 5, ctl: 4 }] : [{ t: 0, est: 6, ctl: 4 }, { t: 6000, est: 6, ctl: 5 }],
  duration: 'One pass for each test', prereq: 'Stable Y-momentum mode with low body rates, Full-state or MEMS Gyro EKF.',
  story: 'Each wheel is checked before it is trusted. With control set to none, the X wheel is spun to +200 rpm for a minute. The body\'s X rate must jump negative when the wheel speeds up (momentum conservation), and jump positive again when it stops. The Z rate follows more slowly in the same direction. Repeat for Z. Then XYZ control (mode 5) takes over from Y-momentum: the Y wheel\'s bias momentum is dumped and all three wheels hold attitude to about half a degree.',
  note: P => P.part === 'pol' ? 'Attitude motion exaggerated ×5. The Y wheel is commanded to its current measured speed so Y-momentum is kept.' : 'Attitude motion exaggerated ×5. Wheel momentum dumping uses the magnetorquers.',
  cmds: P => P.part === 'pol' ? [
    { t: 0, title: 'Power Control', detail: 'CubeControl Signal, Motor and CubeWheel-1, -2, -3 = On (1). Others default.' },
    { t: 8, title: 'Set Control Mode', detail: 'None (0)' },
    { t: 12, title: 'Set Estimation Mode', detail: 'Full-state or Gyro EKF (5 or 6)' },
    { t: 15, title: 'Wheel Speed Command', detail: 'X = 200 rpm, Y = measured speed, Z = 0 rpm' },
    { t: 20, kind: 'wait', title: 'Delay', detail: '1 min' },
    { t: 95, title: 'Wheel Speed Command', detail: 'X = 0, Y = measured, Z = 0' },
    { t: 110, title: 'Set Control Mode', detail: 'Y-momentum (4)' },
  ] : [
    { t: 0, title: 'Power Control', detail: 'Signal, Motor, CubeWheel-1, -2, -3 = On (1). Others default.' },
    { t: 40, title: 'Set Rate Sensor Configuration', detail: 'X, Y, Z rate-sensor offsets (step 15), Rate Sensor Multiplier = 1' },
    { t: 80, title: 'Set Estimation Mode', detail: 'MEMS Gyro EKF (6)' },
    { t: 120, kind: 'wait', title: 'Delay', detail: '1 orbit, ensure the Gyro EKF has converged in Y-momentum control' },
    { t: 6000, title: 'Set Control Mode', detail: 'XYZ reaction wheel control (5)' },
  ],
  tlm: P => P.part === 'pol' ? [['Estimated Fine Angular Rates', '1 s'], ['Estimated Attitude Angles', '1 s'], ['Rate Sensor Rates', '1 s'], ['Measured wheel speed', '1 s']] : [['Estimated Fine Angular Rates', '10 s'], ['Estimated Attitude Angles', '10 s'], ['Estimated Gyro Bias', '10 s'], ['Estimation Innovation', '10 s'], ['Magnetic Field Vector', '10 s'], ['Fine Sun Vector', '10 s'], ['Nadir Vector', '10 s'], ['Rate Sensor Rates', '10 s'], ['Measured Wheel Speeds', '10 s'], ['Magnetorquer Command', '10 s'], ['Wheel Speed Commands', '10 s'], ['IGRF Modelled Vector', '10 s'], ['Quaternion Error Vector', '10 s']],
  pass: ['Measured wheel speeds match the commands.', 'MEMS X rate jumps negative when X ramps to 200 rpm and positive again at stop; Z changes slower in the same direction.', 'XYZ control: EKF innovation magnitude small, quaternion error small (under 0.5° in the manual\'s simulation, versus under 2° in Y-momentum).'],
  trouble: [['Z wheel', 'Once Y-momentum is stable again with low rates, repeat the X-wheel test on the Z wheel.'], ['Why Gyro EKF', 'Large unmodelled disturbance torques can give better results with the MEMS Gyro EKF (6) than with the Full-state EKF (5).']],
  build(P) {
    if (P.part === 'pol') {
      return {
        T: 200, q0: Q.id(), f(t, i) {
          const t0 = 15, t1 = 95; const wheelX = t < t0 ? 0 : t < t1 ? 200 * sstep(t, t0, t0 + 4) : 200 * (1 - sstep(t, t1, t1 + 4));
          const a = t - t0, b = t - t1;
          const x = t < t0 ? 0.002 : t < t1 ? -0.045 + 0.105 * sstep(a, 0, 80) * sstep(a, 0, 80) : 0.075 * Math.exp(-b / 40) * sstep(b, -1, 3) - 0.03 * sstep(b, 0, 6) * Math.exp(-b / 30);
          const z = t < t0 ? 0 : t < t1 ? -0.065 * sstep(a, 0, 55) : -0.065 * Math.exp(-b / 70) + 0.095 * sstep(b, 0, 60) * Math.exp(-b / 50);
          const y = t < t0 ? 0 : 0.012 * sstep(a, 0, 70) - 0.045 * sstep(b, 40, 120);
          const w = [x + 0.003 * noise(i, 1), y + 0.003 * noise(i, 2), z + 0.003 * noise(i, 3)];
          return { w, wheel: [wheelX, -2900, 0], B: Borc(t) };
        },
      };
    }
    return {
      T: 11500, q0: Q.id(), f(t, i) {
        const s = Math.max(0, t - 6000), on = sstep(t, 6000, 6020);
        const wy = lerp(-4750 + 40 * Math.sin(t / 400), 0, 0) + (-4750 + 40 * Math.sin(t / 400)) * 0 ;
        const Y = t < 6000 ? -4750 + 60 * Math.sin(t / 300) : -4750 * Math.exp(-s / 130) - 160 * (1 - Math.exp(-s / 130)) + 90 * sstep(s, 3500, 5400);
        const X = on * (460 * (1 - Math.exp(-s / 140)) * Math.exp(-s / 1100) - 340 * sstep(s, 1600, 2400) * Math.exp(-(s - 1600) / 2000) * 0.9 + 60 * sstep(s, 3500, 5400));
        const Z = on * (700 * (1 - Math.exp(-s / 160)) * Math.exp(-s / 1000) - 160 * sstep(s, 2300, 3200) * 0.9);
        const err = t < 6000 ? 1.3 + 0.9 * Math.sin(t / 700) : lerp(1.3, 0.3, sstep(s, 0, 600));
        const mt = t < 6000 ? 0.1 * noise(i, 9) : (0.8 * Math.exp(-s / 120) + 0.03 * noise(i, 9));
        return { euler: [err * Math.sin(t / 380), 0.8 * err * Math.sin(t / 290) + (t < 6000 && t > 100 ? 0 : 0), 1.1 * err * Math.cos(t / 450)], wheel: [X, Y, Z], mtq: [mt, 0.1 * noise(i, 4), -mt], B: Borc(t), w: [0, 0, 0] };
      },
    };
  },
  charts: P => P.part === 'pol' ? [
    { title: 'X wheel speed', unit: 'rpm', series: [ser('X wheel', cc.x, s => s.wheel[0])] },
    { title: 'Body rates (MEMS)', unit: 'deg/s', series: xyz('w'), marks: [{ t: 15, label: 'X → 200' }, { t: 95, label: 'X → 0', row: 1 }] },
  ] : [
    { title: 'Wheel speeds', unit: 'rpm', series: [ser('X', cc.x, s => s.wheel[0]), ser('Y', cc.y, s => s.wheel[1]), ser('Z', cc.z, s => s.wheel[2])], marks: [{ t: 6000, label: 'XYZ control' }] },
    { title: 'True attitude angles', unit: 'deg', series: [ser('roll', cc.x, s => s.eul[0]), ser('pitch', cc.y, s => s.eul[1]), ser('yaw', cc.z, s => s.eul[2])], y: [-3, 3] },
    { title: 'Magnetorquer on-time', unit: 's', series: [ser('X', cc.x, s => s.mtq[0]), ser('Z', cc.z, s => s.mtq[2])] },
  ],
  exag: 5,
  show: { wheels: [0, 1, 2], nadir: true, mtq: true },
});

/* ------------------------------------------------------------------ 15 */
SCENES.push({
  id: 15, title: 'EKF with rate gyro measurements, adding star tracker', phase: 'e', sec: '12', pages: '45–47', T: 6200, dur: 26, N: 620, exag: 8,
  params: [seg('star', 'Inputs', [['no', 'Sun + nadir'], ['yes', 'With CubeStar']])],
  modes: [{ t: 0, est: 5, ctl: 4 }, { t: 380, est: 6, ctl: 4 }], tool: 'gyro',
  duration: '5 min of rate sampling, then 1 orbit', prereq: 'Stable Y-momentum mode, low rates.',
  story: 'The MEMS gyros carry a constant offset. In nadir hold the average gyro reading over about five minutes should equal the true body rate, so average, take away the orbital rate on Y, and what is left is bias. Load those offsets with Set Rate Sensor Configuration, switch to MEMS Gyro EKF (mode 6), and let it learn any remaining drift. With the star tracker also in, eclipse stops being the weak point.',
  note: P => P.star === 'yes' ? 'Star vectors in the EKF all orbit: error stays low in eclipse.' : 'Magnetometer, Sun and nadir only: in eclipse the attitude error grows.',
  cmds: () => [
    { t: 0, kind: 'wait', title: 'Sample the gyros', detail: 'About 5 min in Y-momentum mode. Average X, Y and Z.' },
    { t: 300, kind: 'ground', title: 'Compute bias', detail: 'X bias = avg ωx;  Y bias = avg ωy − ω_orbit;  Z bias = avg ωz' },
    { t: 360, title: 'Set Rate Sensor Configuration', detail: 'X, Y, Z offsets, Rate Sensor Multiplier = 1' },
    { t: 380, title: 'Set Estimation Mode', detail: 'MEMS Gyro EKF (6)' },
    { t: 400, kind: 'wait', title: 'Delay', detail: '1 orbit for the estimator to converge' },
  ],
  tlm: [['Estimated Fine Angular Rates', '10 s'], ['Estimated Attitude Angles', '10 s'], ['Estimated Gyro Bias', '10 s'], ['Estimation Innovation', '10 s'], ['Rate Sensor Rates', '10 s'], ['Quaternion Error Vector', '10 s']],
  pass: ['Estimated gyro bias settles close to a constant.', 'Attitude error stays small through the orbit, including eclipse once star vectors are in.'],
  trouble: [['Sign of the Y term', 'Subtract the orbital rate on Y only. The orbit period gives ω_orbit = 360° / period (about 0.062 deg/s for a 5818 s orbit). The calculator below does it for you.']],
  build(P) {
    const bias = [0.12, 0.2, -0.08], wo = W_ORB, res = [0.015, -0.012, 0.009];
    return {
      q0: Q.id(),
      f(t, i) {
        const e = ENV(t), applied = t >= 360 ? bias : [0, 0, 0];
        const raw = [bias[0] + noise(i, 1) * 0.05, bias[1] + wo + noise(i, 2) * 0.05, bias[2] + noise(i, 3) * 0.05].map((v, k) => v - applied[k] + (t >= 360 ? res[k] : 0));
        const g = t < 380 ? 0 : 1 - Math.exp(-(t - 380) / 700);
        const est = res.map((r, k) => g * r + 0.002 * noise(i, 6 + k));
        const base = e.ecl ? 1.0 : 0.25, err = P.star === 'yes' && t >= 1000 ? 0.02 : base;
        const a = err * (1 + 0.1 * noise(i, 9));
        return { euler: [a * Math.sin(t / 240), 0.7 * a * Math.sin(t / 180), 0.9 * a * Math.cos(t / 280)], raw, est, ecl: e.ecl, sun: e.sun, B: e.B, err: a, w: [0, 0, 0] };
      },
    };
  },
  charts: P => [
    { title: 'Rate sensor output', unit: 'deg/s', series: xyz('raw'), marks: [{ t: 300, label: 'average' }, { t: 360, label: 'offsets set', row: 1 }], y: [-0.2, 0.45] },
    { title: 'Gyro EKF bias estimate (residual)', unit: 'deg/s', series: xyz('est') },
    { title: 'Attitude error (log scale)', unit: 'deg', log: true, y: [0.01, 2], series: [ser('error', cc.ink, s => s.err)], bands: ECL },
  ],
  show: { sun: true, nadir: true, orbit: true },
});

/* ------------------------------------------------------------------ 16 */
SCENES.push({
  id: 16, title: 'Sun tracking 3-axis control', phase: 'e', sec: '13', pages: '51–53', T: ORBIT_T, dur: 28, N: 700,
  params: [seg('facet', 'Tracking facet', [['-Y', '−Y (default)'], ['+Y', '+Y'], ['-Z', '−Z'], ['+X', '+X (ACP v6+)'], ['-X', '−X (ACP v6+)']])],
  modes: [{ t: 0, est: 6, ctl: 5 }, { t: 300, est: 6, ctl: 6 }],
  duration: '1 pass', prereq: 'Stable nadir-pointing wheel control with low rates, MEMS Gyro EKF converged.',
  story: 'During the sunlit part of the orbit, one chosen facet (the solar panel) is steered at the Sun. As the Sun sweeps round the orbit frame, the satellite follows with large, smooth angles. When the satellite enters eclipse the controller falls back to nadir pointing by itself, then returns to the Sun on exit. The big wheel-momentum spikes in the manual\'s figure sit at those two transitions.',
  cmds: () => [
    { t: 0, title: 'Power Control', detail: 'Signal, Motor, CubeWheel-1, -2, -3 = On (1). Others default.' },
    { t: 60, title: 'Set Rate Sensor Configuration', detail: 'X, Y, Z offsets, Rate Sensor Multiplier = 1' },
    { t: 120, title: 'Set Estimation Mode', detail: 'MEMS Gyro EKF (6)' },
    { t: 160, kind: 'wait', title: 'Delay', detail: '1 orbit so the Gyro EKF converges in XYZ wheel control' },
    { t: 300, title: 'Set Control Mode', detail: 'Sun tracking control (6)' },
  ],
  tlm: [['Estimated Fine Angular Rates', '10 s'], ['Estimated Attitude Angles', '10 s'], ['Estimated Gyro Bias', '10 s'], ['Estimation Innovation', '10 s'], ['Fine Sun Vector', '10 s'], ['Nadir Vector', '10 s'], ['Measured Wheel Speeds', '10 s'], ['Quaternion Error Vector', '10 s']],
  pass: ['Measured wheel speeds follow the commands.', 'EKF innovation small.', 'RPY angles change smoothly for Sun tracking; the Sun vector sits on the chosen facet axis in the body frame.', 'Quaternion error small.'],
  trouble: [['Which facet', 'Set SunPointFacet in the ADCS configuration XML: PosY, NegY or NegZ on ACP v5+; PosX and NegX only on ACP v6+. On ACP v3 the PosY/NegY/NegZ facets use a different XML parameter. Contact CubeSpace if the default NegY is wrong.']],
  build(P) {
    const fb = { '-Y': [0, -1, 0], '+Y': [0, 1, 0], '-Z': [0, 0, -1], '+X': [1, 0, 0], '-X': [-1, 0, 0] }[P.facet];
    return {
      T: ORBIT_T, q0: Q.id(),
      f(t, i) {
        const e = ENV(t);
        const lit = t < 1840 ? 1 - sstep(t, 1780, 1880) : sstep(t, 3830, 3930);
        const b = sstep(t, 300, 420) * lit;
        const q = Q.slerp(Q.id(), Q.fromTo(fb, V.norm(e.sun)), b);
        return { q, sun: e.sun, ecl: e.ecl, B: e.B, w: [0, 0, 0], track: b > 0.5, sunB: Q.rot(Q.conj(q), e.sun) };
      },
    };
  },
  charts: () => [
    { title: 'Sun vector, body frame', unit: '', y: [-1.1, 1.1], series: xyz('sunB'), bands: ECL, marks: [{ t: 300, label: 'tracking' }] },
    { title: 'Attitude angles', unit: 'deg', series: [ser('roll', cc.x, s => s.eul[0]), ser('pitch', cc.y, s => s.eul[1]), ser('yaw', cc.z, s => s.eul[2])], bands: ECL },
  ],
  hud: (s, t, P) => [s.track ? 'Tracking facet ' + P.facet.replace('-', '−') + ' to the Sun' : s.ecl ? 'Eclipse: nadir pointing' : 'Nadir pointing'],
  hi: (s, t, P) => (s.track ? [P.facet] : []),
  show: { sun: true, nadir: true, orbit: true },
});

/* ------------------------------------------------------------------ 17 */
SCENES.push({
  id: 17, title: 'Ground target tracking controller', phase: 'e', sec: '14', pages: '54–57', T: ORBIT_T, dur: 28, N: 700,
  params: [range('off', 'Target distance from ground track', 0, 300, 10, 25, v => v + ' km')],
  modes: [{ t: 0, est: 6, ctl: 5 }, { t: 3000, est: 6, ctl: 7 }, { t: 4500, est: 6, ctl: 5 }], tool: 'target',
  duration: '1 pass', prereq: 'Stable nadir-pointing wheel control with low rates, and the Gyro or Full EKF converged.',
  story: 'Close to a target the +Z facet is pointed at a spot on the ground. The pitch angle sweeps from about +65° as the satellite approaches, through zero overhead, to about −65° as it leaves; any cross-track offset shows up as roll. The controller makes no visibility check: it points at the target even if it is on the far side of the Earth. So the switch to tracking has to be timed by you, at least 300 s before closest range, and back to nadir at least 300 s after.',
  cmds: () => [
    { t: 0, title: 'Power Control', detail: 'Signal, Motor, CubeWheel-1, -2, -3 = On (1). Others default.' },
    { t: 40, title: 'Set Rate Sensor Configuration', detail: 'X, Y, Z offsets, Rate Sensor Multiplier = 1' },
    { t: 80, title: 'Set Estimation Mode', detail: 'Full or MEMS Gyro EKF (5 or 6)' },
    { t: 120, kind: 'wait', title: 'Delay', detail: '1 orbit so the estimator converges in XYZ wheel control' },
    { t: 2900, title: 'Set Ground Target Reference', detail: 'Geocentric longitude, latitude and relative altitude of a target near the ground track (calculator below)' },
    { t: 3000, title: 'Set Control Mode', detail: 'Target tracking control (7), at least 300 s before closest range' },
    { t: 4500, title: 'Set Control Mode', detail: 'Nadir pointing control (5), at least 300 s after closest range' },
  ],
  tlm: [['Estimated Fine Angular Rates', '10 s'], ['Estimated Attitude Angles', '10 s'], ['Estimated Gyro Bias', '10 s'], ['Estimation Innovation', '10 s'], ['Rate Sensor Rates', '10 s'], ['Measured Wheel Speeds', '10 s'], ['Quaternion Error Vector', '10 s'], ['Satellite LLH position', '10 s'], ['Commanded Attitude Angles', '10 s']],
  pass: ['Measured wheel speed matches the command.', 'Innovation vector magnitude small.', 'RPY attitude changes during tracking.', 'Satellite latitude, longitude and altitude near the target area at closest range.'],
  trouble: [['Check the target numbers', 'Wrong geocentric conversion points the wrong way. Use the calculator below; it follows the manual\'s five steps.']],
  build(P) {
    const a = 6371 + 500, Re = 6371, c = P.off / Re, tca = 3750;
    const Tg = [0, Math.sin(c) * Re, Math.cos(c) * Re];
    return {
      q0: Q.id(),
      f(t, i) {
        const th = W_ORB * (t - tca) * D2R, r = [a * Math.sin(th), 0, a * Math.cos(th)];
        const n = V.mul(r, -1 / a), vhat = [Math.cos(th), 0, -Math.sin(th)], Yo = V.cross(n, vhat);
        const d = V.sub(Tg, r), dn = V.norm(d), dO = [V.dot(dn, vhat), V.dot(dn, Yo), V.dot(dn, n)];
        const b = (t >= 3000 && t < 4500) ? sstep(t, 3000, 3070) * (1 - sstep(t, 4440, 4500)) : 0;
        const q = Q.slerp(Q.id(), Q.fromTo([0, 0, 1], dO), b);
        return { q, th, r, range: V.len(d), b, w: [0, 0, 0], dO };
      },
    };
  },
  charts: () => [
    { title: 'Attitude angles', unit: 'deg', series: [ser('roll', cc.x, s => s.eul[0]), ser('pitch', cc.y, s => s.eul[1]), ser('yaw', cc.z, s => s.eul[2])], marks: [{ t: 3000, label: 'tracking' }, { t: 3750, label: 'closest', row: 1 }, { t: 4500, label: 'nadir', row: 2 }] },
    { title: 'Range to target', unit: 'km', series: [ser('range', cc.ink, s => s.range)], y: [0, 4000] },
  ],
  draw(ctx, W, H, s, t, P, ui) { targetScene(ctx, W, H, s, t, P, ui); },
});

/* ------------------------------------------------------------------ 18 */
SCENES.push({
  id: 18, title: 'GPS receiver commissioning', phase: 'f', sec: '15', pages: '58', T: ORBIT_T, dur: 24, N: 580,
  modes: [{ t: 0, est: 5, ctl: 5 }],
  duration: '1 orbit', prereq: 'Stable nadir pointing in a 3-axis wheel mode, rates known from MEMS or Full-state EKF.',
  story: 'The GPS receiver isn\'t needed by the ADCS software, so it can be switched on at any time without upsetting control. It gets its power from a direct command to the EPS (a switched 3.3 V line), then the ADCS enables its LNA. The test is whether it finds enough satellites for a valid solution, whether GPS time agrees with Unix time, and whether the ECEF position agrees with the SGP4 latitude, longitude and altitude. Sky positions and the lock-up timing here are illustrative.',
  cmds: () => [
    { t: 0, kind: 'ext', title: 'EPS command', detail: 'Switch on the GPS receiver\'s 3.3 V line (not an ADCS command)' },
    { t: 40, title: 'Power Control', detail: 'GPS LNA = On (1), all others default' },
    { t: 80, kind: 'wait', title: 'Log one orbit', detail: 'Satellite LLH, raw GPS status, time, X, Y, Z' },
  ],
  tlm: [['Satellite LLH Position', '10 s'], ['Raw GPS Status', '10 s'], ['Raw GPS Time', '10 s'], ['Raw GPS X', '10 s'], ['Raw GPS Y', '10 s'], ['Raw GPS Z', '10 s']],
  pass: ['GPS status shows enough satellites tracked and a successful solution.', 'GPS time matches Unix time.', 'ECEF XYZ position and velocity agree with the SGP4 WGS-84 latitude, longitude and altitude.'],
  trouble: [['No lock', 'Confirm the EPS 3.3 V line is on and the LNA enabled, and that the antenna is pointing toward the sky (nadir pointing keeps it out of the Earth\'s shadow).']],
  build() {
    return {
      q0: Q.id(),
      f(t, i) {
        const tr = t < 40 ? 0 : clamp(Math.floor((t - 60) / 22), 0, 9) + (t > 60 ? 0 : 0);
        const sol = t > 260 ? 1 : 0;
        const diff = t < 260 ? NaN : 1.5 + 6 * Math.exp(-(t - 260) / 180) + 0.2 * noise(i, 3);
        return { euler: [0, 0, 0], w: [0, 0, 0], trk: tr, sol, diff, B: Borc(t) };
      },
    };
  },
  charts: () => [
    { title: 'Satellites tracked', unit: '', y: [0, 12], series: [ser('tracked', cc.teal, s => s.trk)] },
    { title: 'GPS vs SGP4 position difference (schematic)', unit: 'km', series: [ser('difference', cc.ink, s => s.diff)], marks: [{ t: 260, label: 'solution valid' }] },
  ],
  draw(ctx, W, H, s, t, P, ui) { gpsScene(ctx, W, H, s, t); },
});

/* ============================================================ overlays ==== */
function cameraInsets(ctx, W, H, s, t) {
  const sz = Math.min(110, W * 0.17), y = H - sz - 16;
  const boxes = [['Nadir camera', W - sz * 2 - 28], ['Sun camera', W - sz - 14]];
  boxes.forEach(([label, x], k) => {
    ctx.save(); ctx.fillStyle = '#04090F'; ctx.fillRect(x, y, sz, sz);
    ctx.beginPath(); ctx.rect(x, y, sz, sz); ctx.clip();
    if (s.ok) {
      if (k === 0) {
        const g = ctx.createRadialGradient(x + sz * 0.5, y + sz * 0.5, sz * 0.1, x + sz * 0.5, y + sz * 0.5, sz * 0.34);
        g.addColorStop(0, '#F0F4F6'); g.addColorStop(1, '#AEB8BE');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x + sz * 0.5 + s.nm[0] * sz, y + sz * 0.5 + s.nm[1] * sz, sz * 0.32, 0, TAU); ctx.fill();
        ctx.strokeStyle = '#6DE3A5'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x + sz * 0.5, y + sz * 0.5, sz * 0.36, 0, TAU); ctx.stroke();
      } else {
        const u = Math.atan2(s.sm[0], -s.sm[2]) / (Math.PI / 2), v = Math.asin(clamp(s.sm[1], -1, 1)) / (Math.PI / 2);
        const dx = x + sz * 0.5 + u * sz * 0.4, dy = y + sz * 0.5 + v * sz * 0.4;
        ctx.fillStyle = '#FFFFFF'; ctx.beginPath(); ctx.arc(dx, dy, 4, 0, TAU); ctx.fill();
        ctx.strokeStyle = '#6DE3A5'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(dx, dy, 9, 0, TAU); ctx.stroke();
      }
    } else { ctx.fillStyle = '#E0603E'; ctx.font = '600 11px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.fillText('invalid', x + sz / 2, y + sz / 2 + 4); }
    ctx.restore();
    ctx.strokeStyle = 'rgba(214,228,240,0.35)'; ctx.strokeRect(x, y, sz, sz);
    ctx.fillStyle = C.dim; ctx.font = '11.5px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'left'; ctx.fillText(label, x, y - 6);
  });
}

function starScene(ctx, W, H, t, thr, ui) {
  const iw = Math.min(W * 0.58, (H - 40) * 1280 / 1038), ih = iw * 1038 / 1280, x0 = 20, y0 = (H - ih) / 2;
  ctx.fillStyle = '#2C3033'; ctx.fillRect(x0, y0, iw, ih);
  const phase = t < 10 ? 0 : t < 25 ? 1 : t < 45 ? 2 : 3;
  const flash = t < 4 ? 1 - t / 4 : 0;
  const stars = STARS.map(s => ({ x: s[0], y: s[1], b: s[2], real: true })), specks = SPECKS.map(s => ({ x: s[0], y: s[1], b: s[2], real: false }));
  const all = [...stars, ...specks];
  ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, iw, ih); ctx.clip();
  all.forEach(s => { const a = clamp(s.b / 255, 0.1, 1); ctx.fillStyle = `rgba(255,255,255,${0.25 + a * 0.75})`; ctx.beginPath(); ctx.arc(x0 + s.x * iw, y0 + s.y * ih, 1 + a * 2.2, 0, TAU); ctx.fill(); });
  const det = all.filter(s => s.b > thr), ident = det.filter(s => s.real && s.b > 150).slice(0, 3);
  if (phase >= 1) det.forEach(s => { const k = clamp((t - 10) / 8, 0, 1); ctx.strokeStyle = `rgba(109,227,165,${k})`; ctx.lineWidth = 1.3; ctx.beginPath(); ctx.arc(x0 + s.x * iw, y0 + s.y * ih, 8, 0, TAU); ctx.stroke(); });
  if (phase >= 2 && ident.length >= 3) {
    const k = clamp((t - 25) / 10, 0, 1); ctx.strokeStyle = `rgba(244,187,69,${k})`; ctx.lineWidth = 1.6; ctx.beginPath();
    ident.forEach((s, i) => { const x = x0 + s.x * iw, y = y0 + s.y * ih; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); ctx.closePath(); ctx.stroke();
    ctx.fillStyle = '#F4BB45'; ctx.font = '600 11px "Instrument Sans", system-ui, sans-serif';
    ident.forEach((s, i) => ctx.fillText('cat #' + (4210 + i * 977), x0 + s.x * iw + 12, y0 + s.y * ih - 8));
  }
  if (flash > 0) { ctx.fillStyle = `rgba(255,255,255,${flash * 0.6})`; ctx.fillRect(x0, y0, iw, ih); }
  ctx.restore();
  ctx.fillStyle = C.dim; ctx.font = '11.5px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'left';
  ctx.fillText('1280 × 1038 frame, schematic', x0, y0 - 7);
  const nd = det.length, ni = ident.length >= 3 ? 3 : 0;
  const bits = [
    ['0', 'Image captured', phase >= 0 && t > 3], ['1', 'Stars detected', phase >= 1 && t > 18 && nd >= 1], ['2', 'Stars identified', phase >= 2 && t > 35 && ni > 0], ['3', 'Attitude solved', phase >= 3 && ni > 0],
    ['4', 'Processing time error', false], ['5', 'Tracking module', false], ['6', 'Prediction enabled', false], ['7', 'Communication error', false],
  ];
  const px = x0 + iw + 24, pw = W - px - 16;
  ctx.fillStyle = C.text; ctx.font = '600 13px "Instrument Sans", system-ui, sans-serif'; ctx.fillText('Star tracker status', px, y0 + 6);
  bits.forEach(([n, name, on], k) => {
    const y = y0 + 28 + k * 22;
    ctx.fillStyle = on ? '#4DBB8C' : 'rgba(214,228,240,0.18)'; ctx.fillRect(px, y - 11, 14, 14);
    ctx.fillStyle = C.dim; ctx.font = '600 10px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.fillText(n, px + 7, y);
    ctx.fillStyle = on ? C.text : C.dim; ctx.font = '12px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'left'; ctx.fillText('bit ' + n + '  ' + name, px + 22, y);
  });
  const ys = y0 + 28 + 8 * 22 + 14;
  ctx.fillStyle = C.text; ctx.font = '600 13px "Instrument Sans", system-ui, sans-serif';
  ctx.fillText('Stars detected: ' + (phase >= 1 ? nd : '…'), px, ys);
  ctx.fillStyle = nd > 15 ? '#FF9A7A' : nd < 3 ? '#FFD27A' : C.dim; ctx.font = '12px "Instrument Sans", system-ui, sans-serif';
  const verdict = phase < 1 ? '' : nd > 15 ? 'More than 15: threshold or exposure too low' : nd < 3 ? 'Fewer than 3: cannot identify' : ni ? 'Identified 3 stars, attitude solved' : 'Detected, but none bright enough to match';
  ctx.fillText(verdict, px, ys + 18);
}

function targetScene(ctx, W, H, s, t, P, ui) {
  const lw = W * 0.6, cx = lw / 2, Re = 6371, a = Re + 500, zc = 5600;
  const sc = Math.min(lw * 0.46 / 5200, H * 0.46 / 1400);
  const X = p => [cx + p[0] * sc, H * 0.5 - (p[2] - zc) * sc];
  ctx.save(); ctx.beginPath(); ctx.rect(0, 0, lw, H); ctx.clip();
  const ec = X([0, 0, 0]);
  ctx.fillStyle = '#1A4F7E'; ctx.beginPath(); ctx.arc(ec[0], ec[1], Re * sc, 0, TAU); ctx.fill();
  ctx.strokeStyle = 'rgba(150,205,255,0.8)'; ctx.lineWidth = 2; ctx.stroke();
  ctx.strokeStyle = 'rgba(214,228,240,0.25)'; ctx.setLineDash([4, 5]); ctx.beginPath(); ctx.arc(ec[0], ec[1], a * sc, 0, TAU); ctx.stroke(); ctx.setLineDash([]);
  const c = P.off / Re, tp = X([0, 0, Re * Math.cos(c)]);
  const sp = X(s.r);
  if (s.b > 0.05) { ctx.strokeStyle = `rgba(244,187,69,${0.4 + 0.5 * s.b})`; ctx.lineWidth = 1.6; ctx.setLineDash([6, 4]); ctx.beginPath(); ctx.moveTo(sp[0], sp[1]); ctx.lineTo(tp[0], tp[1]); ctx.stroke(); ctx.setLineDash([]); }
  ctx.fillStyle = C.sun; ctx.beginPath(); ctx.arc(tp[0], tp[1], 5, 0, TAU); ctx.fill();
  ctx.fillStyle = C.text; ctx.font = '600 12px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.fillText('target', tp[0], tp[1] + 20);
  ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(sp[0], sp[1], 5, 0, TAU); ctx.fill();
  ctx.fillText('satellite', sp[0], sp[1] - 12);
  ctx.restore();
  const m = modeAt(SCENES[16], P, t);
  ctx.textAlign = 'left'; ctx.fillStyle = C.text; ctx.font = '600 13px "Instrument Sans", system-ui, sans-serif';
  ctx.fillText('Control  ' + m.ctl + ' · ' + CTL[m.ctl], 16, 24);
  ctx.fillStyle = s.b > 0.5 ? C.sun : C.dim; ctx.font = '500 13px "Instrument Sans", system-ui, sans-serif';
  ctx.fillText(s.b > 0.5 ? '+Z points at the target' : 'Nadir pointing', 16, 43);
  ctx.fillStyle = C.dim; ctx.font = '11.5px "Instrument Sans", system-ui, sans-serif'; ctx.fillText('Orbit plane view, altitude exaggerated', 16, H - 16);
  const cam = makeCam(lw + (W - lw) / 2, H * 0.46, Math.min(W - lw, H) * 0.2, -35, 20);
  ctx.strokeStyle = 'rgba(214,228,240,0.12)'; ctx.beginPath(); ctx.moveTo(lw, 10); ctx.lineTo(lw, H - 10); ctx.stroke();
  drawArrow(ctx, cam, [0, 0, 0], [0, 0, 3.2], 'rgba(214,228,240,0.6)', 'nadir', { dash: [4, 4], w: 1.3, head: 5 });
  drawSat(ctx, cam, s.q, { hi: s.b > 0.5 ? ['+Z'] : [] });
  ctx.fillStyle = C.dim; ctx.font = '11.5px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'center';
  ctx.fillText('range to target ' + Math.round(s.range) + ' km', lw + (W - lw) / 2, H - 16);
}

function gpsScene(ctx, W, H, s, t) {
  const r = Math.min(W * 0.28, H * 0.4), cx = W * 0.3, cy = H * 0.5;
  ctx.strokeStyle = 'rgba(214,228,240,0.3)'; ctx.lineWidth = 1;
  [1, 0.66, 0.33].forEach(f => { ctx.beginPath(); ctx.arc(cx, cy, r * f, 0, TAU); ctx.stroke(); });
  ctx.beginPath(); ctx.moveTo(cx - r, cy); ctx.lineTo(cx + r, cy); ctx.moveTo(cx, cy - r); ctx.lineTo(cx, cy + r); ctx.stroke();
  ctx.fillStyle = C.dim; ctx.font = '11.5px "Instrument Sans", system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.fillText('antenna sky view', cx, cy - r - 10);
  for (let i = 0; i < 24; i++) {
    const az = hash(i, 21) * TAU + t * 0.0008 * (1 + hash(i, 4)), el = Math.pow(hash(i, 22), 0.7) * r;
    const x = cx + Math.cos(az) * el, y = cy + Math.sin(az) * el, trk = i < s.trk;
    ctx.fillStyle = trk ? '#6DE3A5' : 'rgba(214,228,240,0.4)'; ctx.beginPath(); ctx.arc(x, y, trk ? 5 : 3, 0, TAU); ctx.fill();
    if (trk) { ctx.strokeStyle = 'rgba(109,227,165,0.5)'; ctx.beginPath(); ctx.arc(x, y, 9, 0, TAU); ctx.stroke(); }
  }
  const px = W * 0.58; let y = H * 0.22;
  const rows = [['EPS 3.3 V line', t > 0 ? 'on' : 'off', t > 0], ['GPS LNA', t > 40 ? 'on' : 'off', t > 40], ['Satellites tracked', String(s.trk), s.trk >= 4], ['Solution status', s.sol ? 'successful' : 'no solution', !!s.sol], ['GPS time vs Unix', s.sol ? 'agrees' : 'not valid', !!s.sol]];
  ctx.textAlign = 'left';
  rows.forEach(([a, b, ok]) => {
    ctx.fillStyle = ok ? '#4DBB8C' : 'rgba(214,228,240,0.2)'; ctx.fillRect(px, y - 11, 12, 12);
    ctx.fillStyle = C.dim; ctx.font = '13px "Instrument Sans", system-ui, sans-serif'; ctx.fillText(a, px + 22, y);
    ctx.fillStyle = C.text; ctx.font = '600 13px "Instrument Sans", system-ui, sans-serif'; ctx.fillText(b, px + 22 + 150, y); y += 30;
  });
}
