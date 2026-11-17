"""Checks for the balancing wheel module: wheel spin clearance with a negative control, the assembly paths, screw and cable paths, tie slots, joint fit, edge
rounding, then the simulated recovery on the CAD numbers with sensitivity.

    python check_cube.py     # needs numpy and manifold3d; run ../mechanical/make_cube_parts.py first
"""
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MECH = HERE.parent / 'mechanical'
spec = importlib.util.spec_from_file_location('cube', MECH / 'make_cube_parts.py')
cube = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cube)
sys.path.insert(0, str(HERE))
import cube_sim as sim

box, cx, union, sr, ann = cube.box, cube.cx, cube.union, cube.sr, cube.ann
H, HX, MX0 = cube.H, cube.HX, cube.MOT_X0
hb, hp, hc = cube.base(), cube.plate(), cube.cap()
frame = union([hb, hp, hc])
enc, hw, mot, imu, teth = cube.enc_board(), cube.kit_hardware(), cube.motor(), cube.block(cube.IMU), cube.block(cube.TETHER)
wl = cube.wheel(False)
wheel_pl, pin_pl = cube.place_wheel(wl), cube.place_wheel(cube.pin())
bolts, rs, ps = union(cube.bolt_meshes()), cube.rotor_screws(), cube.plate_screws()
X_FLOOR, X_RIM, X_HEADS = MX0 - cube.FLOOR_T, MX0 - cube.FLOOR_T + cube.RIM_L, MX0 - cube.FLOOR_T + cube.RIM_L + 4.0
X_CAN = MX0 + cube.CAN_L                                                          # where the spinning can ends and the fixed stator base starts

print('stack along the wheel axis')
print(f'  rotor screw heads {X_FLOOR - cube.HEAD_H:.1f}: {X_FLOOR - cube.HEAD_H + HX:.1f} mm inside the cube\'s -x face')
print(f'  board {cube.BOARD_X0:.1f}..{cube.BOARD_X1:.1f}, its connectors to {cube.BOARD_X1 + 6.5:.1f}, feet to {cube.SLAB_X0:.1f}, plate screw heads to {cube.SLAB_X1 + cube.SLAB_RIB + cube.HEAD_H:.1f} '
      f'(the cube\'s +x face is {HX:.0f})')
c7 =union([box(cube.BOARD_X1, cube.SLAB_X0 + 0.5, lo, hi, -6.0, 6.0) for lo, hi in ((8.0, 14.0), (-14.0, -8.0))]).rotate((45, 0, 0))
cc = box(cube.BOARD_X1, cube.SLAB_X0 + 0.5, cube.FOOT_R1 - 3.0, cube.FOOT_R1 + 3.0, -3.0, 3.0)
print(f'  the connectors, even if 7.5 mm tall (through the plate\'s face plane): overlap with the plate {(c7 ^ hp).volume():.3f} mm3 (the middle of the plate is open); '
      f'control, the same block under an arm: {(cc ^ hp).volume():.1f} mm3')

print('\nwheel spin clearance: the volume the wheel sweeps (floor, inner wall, rim, bolt heads, screw heads) against everything that does not spin')
def swept(d=cube.WD, rim_end=X_HEADS):
    r = d / 2
    return union([ann(0.0, r, X_FLOOR, MX0), ann(cube.CUP_BORE / 2, cube.CUP_BORE / 2 + cube.CUP_WALL, MX0 - 0.01, MX0 + cube.CUP_L),
                  ann(cube.RIM_R0, r, MX0 - 0.01, rim_end), ann(0.0, cube.ROTOR_PCD / 2 + 2.4, X_FLOOR - cube.HEAD_H, X_FLOOR + 0.01)])
still = union([frame, enc, hw, ps, imu, teth, mot ^ box(X_CAN, 40, -60, 60, -60, 60)])
for d in (74.0, 78.0, 80.0, 84.0):
    v = (swept(d) ^ still).volume()
    tag = ' (the design)' if d == 74.0 else (' NEGATIVE CONTROL' if d >= 84 else '')
    print(f'  D{d:3.0f}  overlap {v:8.2f} mm3{tag}')
lo, hi = 70.0, 100.0
for _ in range(20):
    mid = (lo + hi) / 2
    if (swept(mid) ^ still).volume() > 0.01:
        hi = mid
    else:
        lo = mid
print(f'  the wheel could grow to about D{lo:.1f} before touching the frame bars: D74 leaves {(lo - 74) / 2:.1f} mm')
print(f'  control, rim plus bolt heads 4 mm longer (to {X_HEADS + 4:.1f}): {(swept(rim_end=X_HEADS + 4.0) ^ still).volume():.1f} mm3 (must be above zero: it reaches the fin pegs at {cube.SLAB_X0})')
print(f'  gaps: bolt heads to the plate and pegs {cube.SLAB_X0 - X_HEADS:.1f} mm; inner wall to the fixed stator base {X_CAN - (MX0 + cube.CUP_L):.1f} mm; '
      f'rim (r {cube.RIM_R0:.0f}) to the board corners (r {cube.ENC_W / math.sqrt(2):.1f}) {cube.RIM_R0 - cube.ENC_W / math.sqrt(2):.1f} mm; '
      f'inner wall to the can {(cube.CUP_BORE - cube.MOTOR_D) / 2:.2f} mm per side')
print(f'  lying on a long face, the wheel axis is {H:.0f} mm above the table and the D74 rim reaches {H - 37:.0f} mm above it: it cannot touch')

print('\nassembly paths (every step must read 0 until the part seats; each control must read above zero)')
steps = [x * 1.5 for x in range(-40, -3)] + [x * 0.25 for x in range(-24, 1)]       # 1.5 mm steps, then 0.25 mm over the last 6 mm
fixed = union([hb, imu, teth])
worst = max((hp.translate((dx, 0, 0)) ^ fixed).volume() for dx in steps)
print(f'  1. plate slid in from the -x end with the IMU on its pad, 60 mm to seated: worst overlap {worst:8.3f} mm3')
print(f'     control, 1 mm past seated: {(hp.translate((1.0, 0, 0)) ^ fixed).volume():8.3f} mm3; pegs half in but 0.5 mm off to one side: '
      f'{(hp.translate((-1.7, 0.5, 0.0)) ^ fixed).volume():8.3f} mm3 (the pegs locate it)')
print(f'     pegs in their holes: {(cube.fin_pegs() ^ hp).volume():.3f} mm3; {cube.TENON} mm pegs in {cube.SOCKET} mm holes, {(cube.SOCKET - cube.TENON) / 2:.2f} mm per side, '
      f'walls {(cube.ARM_W - cube.SOCKET) / 2:.2f} mm, tips flush with the front face')
unit = union([mot, enc, hw, wheel_pl, bolts, rs])
fixed = union([hb, imu, teth, hp])
worst = max((unit.translate((dx, 0, 0)) ^ fixed).volume() for dx in [x * 1.5 for x in range(-40, -3)] + [x * 0.25 for x in range(-24, 1)])
print(f'  2. motor unit (motor, board, kit brass, wheel, bolts) slid in from the -x end onto the plate, 60 mm: worst overlap {worst:8.3f} mm3')
print(f'     control, 1 mm past seated (feet into the plate): {(unit.translate((1.0, 0, 0)) ^ fixed).volume():8.3f} mm3')
bad = sum((cube.plate_screws(r) ^ hp).volume() for r in (cube.SLOT_R[0] + 0.05, cube.FOOT_R1, cube.SLOT_R[1] - 0.05))
drv = union([cx(2.6, cube.SLAB_X1 + cube.SLAB_RIB, 60.0, cube.FOOT_R1 * math.cos(math.radians(a)), cube.FOOT_R1 * math.sin(math.radians(a)), 24) for a in cube.AXES])
ctrl = (cx(1.25, cube.SLAB_X0, cube.SLAB_X1, cube.FOOT_R1, 3.0, 24) ^ hp).volume()
print(f'  3. four M2.5 x 8 from behind into the feet: screws vs plate at both ends of the slots {bad:.3f} mm3 (control 3 mm to the side {ctrl:.2f}); '
      f'a D5.2 driver from outside the +x face to each head vs base + IMU {(drv ^ union([hb, imu, teth])).volume():.3f} mm3')
fix = union([hb, imu, teth, hp, unit, ps])
worst = max((hc.translate((dx, 0, 0)) ^ fix).volume() for dx in [x * 1.5 for x in range(-40, 1)])
print(f'  4. cap slid on from the -x end over the wheel, to seated: worst overlap {worst:8.3f} mm3; control, 1 mm past seated: {(hc.translate((1.0, 0, 0)) ^ fix).volume():8.3f} mm3')
worst = max((imu.translate((dx, 0, 0)) ^ union([hb, hp])).volume() for dx in [-x * 1.0 for x in range(1, 45)])
print(f'  IMU taken out along -x with the plate in: worst overlap {worst:.3f} mm3 (so the plate may go in before or after it); '
      f'with the motor unit in: {max((imu.translate((dx, 0, 0)) ^ unit).volume() for dx in [-x * 1.0 for x in range(1, 45)]):.1f} mm3 (blocked: fit the IMU first)')

print('\nscrew and cable paths (probe = a screw-sized cylinder; a control probe offset 3 mm must read above zero)')
rh = [(cube.ROTOR_PCD / 2 * math.cos(math.radians(90 * k)), cube.ROTOR_PCD / 2 * math.sin(math.radians(90 * k))) for k in range(4)]
bad = sum((cube.W3.cyl(x, y, 2.5, -0.5, cube.FLOOR_T + 0.5) ^ wl).volume() for x, y in rh)
ctrl = (cube.W3.cyl(rh[0][0] + 3.0, rh[0][1], 2.5, -0.5, cube.FLOOR_T + 0.5) ^ wl).volume()
print(f'  wheel to rotor, 4 x M2.5 on the D16 cross through the floor  overlap {bad:7.3f} mm3   control {ctrl:7.3f}; '
      f'M2.5 x 5 engages {5 - cube.FLOOR_T:.1f} mm (the drawing allows 3)')
print(f'  removable alignment pin D{cube.PIN_D} through the floor hole D{cube.PIN_HOLE} into the motor bore D{cube.MOTOR_BORE}: pin vs wheel {(pin_pl ^ wheel_pl).volume():.3f} mm3, vs motor {(pin_pl ^ mot).volume():.3f} mm3')
probe = cx(5.0, cube.BOARD_X1 + 2.0, HX + 1, 0, 0, 48)
print(f'  encoder cable out through the open middle of the plate (a D10 bundle from behind the board to the +x face) vs base + plate: {(probe ^ union([hb, hp])).volume():.3f} mm3')

print('\nzip-tie slots in the three corner pads (a 3 x 1.4 strap through each; control through solid pad)')
tot = 0.0
for (sy, sz, ys, zs) in ((cube.PIVOT[0], -cube.PIVOT[1], (28.4, 31.6), ((24.0, 25.6), (37.4, 39.0))),
                         (-cube.PIVOT[0], cube.PIVOT[1], (28.4, 31.6), ((24.0, 25.6), (37.4, 39.0)))):
    for a, b in zs:
        strap = box(HX - cube.PAD_T - 0.5, HX + 0.5, *sr(sy, ys[0] + 0.1, ys[1] - 0.1), *sr(sz, a + 0.1, b - 0.1))
        tot += (strap ^ hb).volume()
for sg in (-1, 1):                                                              # the IMU pad's two slots, in the gravity-aligned frame: a 3 x 1.4 strap each
    c, hu = cube.IMU_SLOT_S * sg, cube.IMU_H
    tot += (cube.tilted(HX - cube.PAD_T - 0.5, HX + 0.5, hu - 1.5, hu + 1.5, c - 0.7, c + 0.7) ^ hb).volume()
ctrl = (cube.tilted(HX - cube.PAD_T - 0.5, HX + 0.5, cube.IMU_H - 1.5, cube.IMU_H + 1.5, 4.0, 6.0) ^ hb).volume()   # through the solid pad under the board
print(f'  six slots overlap {tot:7.3f} mm3   control {ctrl:7.3f}')
print(f'  IMU envelope vs the base {(imu ^ hb).volume():.3f} mm3, vs the plate {(imu ^ hp).volume():.3f} mm3, vs the board {(imu ^ enc).volume():.3f} mm3')

print('\njoint (four glued tenons, 6.5 mm long)')
print(f'  tenon {cube.TENON} mm square in a {cube.SOCKET} mm socket: {(cube.SOCKET - cube.TENON) / 2:.2f} mm clearance per side, 0.2 mm at the bottom; base and cap overlap {(hb ^ hc).volume():.3f} mm3')
xb = cube.JOINT_X - cube.TENON_L - 0.2
inner = (H - cube.S) - (xb - cube.RING_CAP[1]) * cube.TAN_OV
print(f'  wall left outside the socket {H - (cube.JC + cube.SOCKET / 2):.1f} mm; inside, at the socket bottom where the taper is {(H - cube.S) - inner:.1f} mm out, {cube.JC - cube.SOCKET / 2 - inner:.1f} mm')

print('\nedge rounding: cross-section of a corner stub (a 5 x 5 square has 25.00 mm2)')
cs = (hb ^ box(0.0, 4.0, H - cube.S, H, H - cube.S, H)).volume() / 4.0
print(f'  one rounded outer edge (R{cube.RE}): {cs:.2f} mm2 (expected {25 - (1 - math.pi / 4) * cube.RE ** 2:.2f})')

d = json.load(open(MECH / 'cad_numbers.json'))
M, l, Mgl, J1, Jw = d['M_kg'], d['l_m'], d['Mgl'], d['J1'], d['Jw']
print(f'\nCAD numbers: M {M * 1e3:.0f} g, l {l * 1e3:.1f} mm, Mgl {Mgl:.3f} N m, J1 {J1:.3e}, Jw {Jw:.3e}; sideways CoM offset {d["e_m"] * 1e3:+.2f} mm')
print(f'  each millimetre of sideways offset moves the balance point by {math.degrees(math.atan(1e-3 / l)):.2f} deg; 1 g on a side trim pad moves it by {math.degrees(math.atan(1e-3 * 0.0445 / M / l)):.2f} deg')
print(f'  the 44 mm pivot edge is stable on its own along its length up to {math.degrees(math.atan((cube.D / 2) / (l * 1e3))):.0f} deg of lean')
p = dict(M=M, l=l, Mgl=Mgl, J1=J1, Jw=Jw)
print('\nsimulated recovery from rest (ideal sensing, back-EMF derated at 12 V)')
print(f"{'torque limit':>13} {'torque/Mgl':>10} | {'recovers from':>13} {'wheel peak':>11} {'static hold angle':>18}")
for tau in (0.015, 0.020, 0.030, 0.045):
    lean, wpk = sim.max_lean(p, tau)
    print(f'{tau:10.3f} Nm {tau / Mgl:10.2f} | {lean:10.1f} deg {wpk:8.0f} r/s {math.degrees(math.asin(min(1.0, tau / Mgl))):13.1f} deg')
ok = n = 0
for fm in (0.8, 1.0, 1.2):
    for fj in (0.8, 1.0, 1.2):
        for dl in (-0.005, 0.0, 0.005):
            q = dict(M=M * fm, l=l + dl, Mgl=M * fm * 9.81 * (l + dl), J1=J1 * fm * fj, Jw=Jw * fj)
            ok += 1 if sim.max_lean(q, 0.030)[0] > 4.0 else 0
            n += 1
print(f'sensitivity at 0.030 N m (+-20% mass and inertia, +-5 mm on the centre of mass): {ok} of {n} combinations still recover from more than 4 degrees')
