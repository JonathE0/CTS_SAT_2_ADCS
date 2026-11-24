"""Clearance check with a negative control, then the swing-up + catch simulation on the CAD-derived mass and inertia.

    python check_design.py     # needs numpy, scipy, manifold3d; run ../mechanical/make_swingup_parts.py first

The wheel is checked as a solid D100 disc over the rim's x range, because the spokes sweep every angle when it spins. The two NEGATIVE
CONTROL rows move the wheel toward the clip until it hits the slider pin head: if they ever read 0, the check is not testing anything.
The simulation is a first-pass feasibility study (ideal torque, back-EMF derating, no sensor noise, delay, friction or quantisation).
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MECH = HERE.parent / 'mechanical'
spec = importlib.util.spec_from_file_location('swp', MECH / 'make_swingup_parts.py')
swp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(swp)
sys.path.insert(0, str(HERE))
import swingup_sim as sz

hook = swp.pivot_hook()
R = swp.rider_ext(swp.ZH)
SC, PD = swp.S.screw().translate((0, 0, swp.ZH)), swp.S.pad().translate((0, 0, swp.ZH))
PN = swp.pin_long().translate((0, 0, swp.ZH))
table = swp.box(-300, 0.0, -150, 150, -swp.TABLE_T, 0)
fixed = swp.union([hook, R, SC, PD, PN, table, swp.bearing(swp.B1_X0), swp.bearing(swp.B2_X0)])
arm, mot, rod, cap, sp, enc = swp.arm(), swp.motor(), swp.rod(), swp.magnet_cap(), swp.spacer(), swp.board()
env = swp.cx(50.0, swp.MOT_X0 - 12.0, swp.MOT_X0, 0, swp.ZP - swp.L, 128)


def sweep(wheel_dx, label):
    mv = swp.union([arm, mot, enc, rod, cap, sp, env.translate((wheel_dx, 0, 0))])
    worst, wa = 0.0, None
    for ang in range(0, 360, 2):
        v = (swp.rot_about_pivot(mv, ang) ^ fixed).volume()
        if v > worst:
            worst, wa = v, ang
    print(f'{label:52s} worst overlap {worst:9.3f} mm3' + (f' at {wa} deg' if worst > 0.01 else '  (clear)'))


print('clearance sweep, every 2 degrees')
sweep(0.0, 'as designed (wheel x 21..33)')
sweep(-3.0, 'wheel moved 3 mm toward the clip')
sweep(-4.0, 'NEGATIVE CONTROL: wheel moved 4 mm toward the clip')
sweep(-8.0, 'NEGATIVE CONTROL: wheel moved 8 mm')

print('\nmotor mount and wire paths (probe volumes; 0 = free, a control probe must read > 0)')
zt, X0, X1 = swp.ZP - swp.L, swp.HUB_X0, swp.HUB_X1
box, cx = swp.box, swp.cx
import math
# 1. the four M2.5 screws of the stator back: from the board's outer face (x = X0 + ENC_PLANE + ENC_T) through the arm to the stator back (x = X0)
holes = [(swp.STATOR_PCD / 2 * math.cos(math.radians(45 + 90 * k)), zt + swp.STATOR_PCD / 2 * math.sin(math.radians(45 + 90 * k))) for k in range(4)]
bad = sum((cx(1.25, X0 - 0.5, X0 + swp.ENC_PLANE + swp.ENC_T, y, z, 24) ^ arm).volume() for y, z in holes)
ctrl = (cx(1.25, X0 - 0.5, X0 + swp.ENC_PLANE + swp.ENC_T, holes[0][0] + 3.0, holes[0][1], 24) ^ arm).volume()
print(f'  stator-back screws (4 x M2.5 through the arm)    overlap {bad:7.3f} mm3   control (offset 3 mm) {ctrl:7.3f}')
# 2. the rotor's rear hub in the arm window, and the board in its recess
print(f'  rear hub D12 x 4.5 in the window                 overlap {(mot ^ arm).volume():7.3f} mm3')
print(f'  AS5600 board envelope in its recess              overlap {(enc ^ arm).volume():7.3f} mm3   air gap hub end to board chip face: {swp.ENC_PLANE - swp.MOTOR_HUB_L:.1f} mm')
# 3. the wheel's four M2.5 screws into the rotor face (wheel local frame: z = 0 on the rotor face, head seat at z = 3.5)
wl = swp.wheel(False)
rh = [(swp.ROTOR_PCD / 2 * math.cos(math.radians(90 * k)), swp.ROTOR_PCD / 2 * math.sin(math.radians(90 * k))) for k in range(4)]
bad = sum((swp.W3.cyl(x, y, 2.5, -0.5, 8.5) ^ wl).volume() for x, y in rh)
ctrl = (swp.W3.cyl(rh[0][0] + 3.0, rh[0][1], 2.5, -0.5, 8.5) ^ wl).volume()
print(f'  wheel screws (4 x M2.5 on D16, cross pattern)    overlap {bad:7.3f} mm3   control (offset 3 mm) {ctrl:7.3f}')
# 4. the lead and cable channels in the arm
e = swp.ENC_W + 0.6
probes = {
    'phase-lead channel (table side)': box(X0 + 0.2, X0 + 2.2, -6.3, -3.1, zt + 4.5, swp.ZP - 22.5),
    'encoder channel (table side)': box(X0 + 0.2, X0 + 2.2, 3.1, 6.3, zt + 4.5, swp.ZP - 22.5),
    'encoder channel on the outboard face': box(X1 - 2.2, X1, 3.1, 6.3, zt + e / 2 - 0.2, swp.ZP - 22.5),
    'slot through the bar to the table side': box(X0, X1, 3.1, 6.3, swp.ZP - 25.5, swp.ZP - 22.5),
}
for name, p in probes.items():
    print(f'  {name:40s} overlap {(p ^ arm).volume():7.3f} mm3')
print(f'  control: probe across the ridge between channels overlap {(box(X0 + 0.2, X0 + 2.2, -1.0, 1.0, zt + 4.5, swp.ZP - 22.5) ^ arm).volume():7.3f}')

d = json.load(open(MECH / 'cad_inertia.json'))
M, l, Jt, Jw = d['M_kg'], d['l_m'], d['Jt'], d['Jw']
print(f'\nCAD numbers: M {M * 1e3:.0f} g, l {l * 1e3:.1f} mm, Mgl {M * 9.81 * l:.3f} N m, Jt {Jt:.3e}, Jw {Jw:.3e}')
print('swing-up + catch (torque limit, back-EMF derated at 12 V):')
print(f"{'torque N m':>10} {'tau/Mgl':>8} | {'caught':>6} {'t_catch':>8} {'w_peak rad/s':>13}")
for tau in (0.030, 0.025, 0.020, 0.015):
    r = sz.simulate(M, l, Jt, Jw, tau, 272.0)
    tc = '--' if r['t_catch'] is None else f"{r['t_catch']:.1f}s"
    print(f"{tau:10.3f} {tau / (M * 9.81 * l):8.2f} | {str(r['ok']):>6} {tc:>8} {r['wpk']:13.0f}")
ok = [sz.simulate(M * fm, l + dl, Jt * fm * fj, Jw * fj, 0.025, 272.0)['ok']
      for fm in (0.75, 1.0, 1.25) for fj in (0.75, 1.0, 1.25) for dl in (-0.010, 0.0, 0.010)]
print(f'robustness at 0.025 N m (+-25% mass and inertia, +-10 mm on l): {sum(ok)}/{len(ok)} combinations caught')
