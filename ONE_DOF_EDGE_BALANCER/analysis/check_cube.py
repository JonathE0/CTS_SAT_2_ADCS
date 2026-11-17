"""Checks for the balancing wheel module: the stack and how much longer the bought motor unit may be than modelled, wheel spin clearance against the frame and
against the wires (with negative controls), the assembly paths, screw, driver and hex-key paths, tie slots, joint fit, edge rounding, then the simulated
recovery on the CAD numbers with sensitivity.

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
hb, hc = cube.base(), cube.cap()
frame = union([hb, hc])
enc, hw, mot, imu, teth, plg, lds = cube.enc_board(), cube.kit_hardware(), cube.motor(), cube.block(cube.IMU), cube.block(cube.TETHER), cube.plug(), cube.leads()
wl = cube.wheel()
wheel_pl, pin_pl = cube.place_wheel(wl), cube.place_wheel(cube.pin())
bolts, rs, ms = union(cube.bolt_meshes()), cube.rotor_screws(), cube.mount_screws()
X_FLOOR, X_RIM = MX0 - cube.FLOOR_T, MX0 - cube.FLOOR_T + cube.RIM_L
X_CAN = MX0 + cube.CAN_L                                                          # where the spinning can ends and the fixed stator base starts
BOX = box(-HX, HX, -H, H, -H, H)
AX = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in cube.AXES]

print('stack along the wheel axis')
print(f'  rotor screw heads {X_FLOOR - cube.HEAD_H:.1f}: {X_FLOOR - cube.HEAD_H + HX:.1f} mm inside the cube\'s -x face')
print(f'  board {cube.BOARD_X0:.1f}..{cube.BOARD_X1:.1f}, connectors to {cube.BOARD_X1 + cube.CONN_H:.1f} ({cube.KIT_FOOT - cube.CONN_H:.1f} short of the feet\'s ends, '
      f'{cube.RING_BASE[0] - cube.BOARD_X1 - cube.CONN_H:.1f} from the slab), feet to {cube.PAD_X:.1f}, mount screw heads to {cube.X_SEAT + cube.HEAD_H:.1f} (the cube\'s +x face is {HX:.0f})')

print('\nhow much the bought unit\'s length may differ from the model (rotor face to the feet\'s ends, modelled '
      f'{cube.BODY + cube.KIT_GAP + cube.ENC_T + cube.KIT_FOOT:.1f} mm). The motor, board, wheel and wires are moved together; the feet stay on the pads')
moving = union([mot, enc, wheel_pl, bolts, rs, plg, lds])
fixed = union([frame, imu, ms])                                                # not the IMU's own cable: a shorter unit brings the plug's cable up against it, cable on cable
for dl in (-2.0, -1.0, 0.0, 1.0, 2.0, 2.9, 3.5):
    m = moving.translate((-dl, 0, 0))
    out = (m - BOX).volume()
    tag = ' (the model)' if dl == 0 else (' NEGATIVE CONTROL: must stick out' if dl > 2.9 else '')
    print(f'  {dl:+.1f} mm: overlap with frame, IMU and mount screws {(m ^ fixed).volume():7.3f} mm3, sticking out of the 44 mm box {out:7.2f} mm3{tag}')

print('\nwheel spin clearance: the volume the wheel sweeps (floor, inner wall, rim with its sunk bolts, screw heads) against everything that does not spin,')
print('including the plug with its cable and the motor leads, both drawn running straight out to the ring bars')
def swept(d=cube.WD, rim_end=X_RIM):
    r = d / 2
    return union([ann(0.0, r, X_FLOOR, MX0), ann(cube.CUP_BORE / 2, cube.CUP_BORE / 2 + cube.CUP_WALL, MX0 - 0.01, MX0 + cube.CUP_L),
                  ann(cube.RIM_R0, r, MX0 - 0.01, rim_end), ann(0.0, cube.ROTOR_PCD / 2 + 2.4, X_FLOOR - cube.HEAD_H, X_FLOOR + 0.01)])
still = union([frame, enc, hw, ms, imu, teth, plg, lds, mot ^ box(X_CAN, 40, -60, 60, -60, 60)])
for d in (74.0, 76.0, 78.0, 80.0, 84.0):
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
print(f'  bolts and their heads inside the rim\'s envelope: bolts outside the swept volume {(bolts - swept()).volume():.3f} mm3')
print(f'  control, rim 2 mm longer (to {X_RIM + 2:.1f}, past the motor\'s back face at {cube.STATOR_X:.1f}): {(swept(rim_end=X_RIM + 2.0) ^ still).volume():.1f} mm3 '
      f'(must be above zero: it reaches the leads); the last version\'s rim, to x = 6.5 here: {(swept(rim_end=6.5) ^ still).volume():.0f} mm3')
print(f'  gaps: rim\'s back face to the plane the leads leave in {cube.RIM_SETBACK:.1f} mm, to the plug {cube.BOARD_X1 - X_RIM:.1f} mm, to the pads {cube.PAD_X - X_RIM:.1f} mm; '
      f'inner wall to the fixed stator base {X_CAN - (MX0 + cube.CUP_L):.1f} mm; inner wall to the can {(cube.CUP_BORE - cube.MOTOR_D) / 2:.2f} mm per side')
print(f'  lying on a long face, the wheel axis is {H:.0f} mm above the table and the D74 rim reaches {H - 37:.0f} mm above it: it cannot touch')

print('\nassembly paths (every step must read 0 until the part seats; each control must read above zero)')
far = [x * 1.5 for x in range(-48, -3)] + [x * 0.25 for x in range(-24, 1)]         # 72 mm of travel: 1.5 mm steps, then 0.25 mm over the last 6 mm
worst = max((hc.translate((dx, 0, 0)) ^ hb).volume() for dx in far)
print(f'  1. cap onto the base, tenons into sockets: worst overlap {worst:8.3f} mm3; control, 1 mm past seated: {(hc.translate((1.0, 0, 0)) ^ hb).volume():8.3f} mm3')
worst = max((union([imu, teth]).translate((dx, 0, 0)) ^ frame).volume() for dx in far)
print(f'  2. IMU onto its pad through the open end of the finished frame: worst overlap {worst:8.3f} mm3')
unit = union([mot, enc, hw, wheel_pl, bolts, rs, plg, lds])
fixed = union([frame, imu, teth])
worst = max((unit.translate((dx, 0, 0)) ^ fixed).volume() for dx in far)
print(f'  3. motor unit (motor, board, kit brass, wheel, bolts, plug in, leads out sideways) lowered through the cap ring onto the pads, 72 mm: worst overlap {worst:8.3f} mm3')
print(f'     control, 1 mm past seated (feet into the pads): {(unit.translate((1.0, 0, 0)) ^ fixed).volume():8.3f} mm3')
bad = sum((cube.mount_screws(r) ^ hb).volume() for r in (cube.SLOT_R[0] + 0.02, cube.FOOT_R1, cube.SLOT_R[1] - 0.02))
ctrl = (cx(1.25, cube.PAD_X, cube.X_TAPER1, cube.FOOT_R1, 3.0, 24) ^ hb).volume()
drv = union([cx(2.0, cube.X_SEAT + cube.HEAD_H, 60.0, cube.FOOT_R1 * c, cube.FOOT_R1 * s, 24) for c, s in AX])
print(f'  4. four M2.5 x 8 from outside into the feet: screws vs base at both ends and the middle of the slots {bad:.3f} mm3 (control 3 mm to the side {ctrl:.2f}); '
      f'a D4 driver from outside the +x face to each head vs base + IMU {(drv ^ union([hb, imu, teth])).volume():.3f} mm3')
foot_a = cube.cx(cube.HEX_D / 2, 0, 1, 0, 0, 6).volume()
for r in (16.0, cube.FOOT_R1, 17.9):
    foot = cx(cube.HEX_D / 2, cube.PAD_X, cube.PAD_X + 0.5, r, 0.0, 6)
    print(f'     a foot at r {r:.2f} (the board\'s slots allow 16.0..17.9) bears on {(foot ^ hb).volume() / 0.5:.1f} mm2 of pad, of its {foot_a:.1f} mm2 hexagon', end='')
    print('' if cube.SLOT_R[0] <= r <= cube.SLOT_R[1] else '   (outside the base\'s slot: loosen its nut and slide it in)')
worst = max((imu.translate((dx, 0, 0)) ^ unit).volume() for dx in [-x * 1.0 for x in range(1, 45)])
print(f'  IMU taken out along -x with the motor unit in: {worst:.1f} mm3 (blocked by the wheel: take the unit out first, four screws)')

print('\nhex-key path to the weight bolts from outside the +x face, through the openings in the motor mount (a D4 shaft to a bolt head at r 32, wheel turned to each angle)')
blockers = union([hb, imu, teth, enc, hw, ms, plg, lds])
free = []
for k in range(360):
    a = math.radians(k)
    if (cx(2.0, X_RIM - 0.2, 60.0, cube.TRIM_R * math.cos(a), cube.TRIM_R * math.sin(a), 16) ^ blockers).volume() < 1e-6:
        free.append(k)
runs, start = [], None
for k in range(361):
    inside = (k % 360) in free and k < 360
    if inside and start is None:
        start = k
    if not inside and start is not None:
        runs.append((start, k - 1)); start = None
best = max(sum(1 for b in range(cube.N_BOLT) if int(round(off + 22.5 + 45 * b)) % 360 in free) for off in range(45))
print(f'  open over {len(free)} of 360 degrees, in windows ' + ', '.join(f'{a}..{b}' for a, b in runs) + f'; without turning the wheel at most {best} of the 8 bolts are in a window, '
      'and every bolt can be turned into one')

print('\nscrew paths (probe = a screw-sized cylinder; a control probe offset 3 mm must read above zero)')
rh = cube.rotor_xy()
bad = sum((cube.W3.cyl(x, y, 2.5, -0.5, cube.FLOOR_T + 0.5) ^ wl).volume() for x, y in rh)
ctrl = (cube.W3.cyl(rh[0][0] + 3.0, rh[0][1], 2.5, -0.5, cube.FLOOR_T + 0.5) ^ wl).volume()
print(f'  wheel to rotor, 4 x M2.5 on the D16 cross through the floor  overlap {bad:7.3f} mm3   control {ctrl:7.3f}; '
      f'M2.5 x 5 engages {5 - cube.FLOOR_T:.1f} mm (the drawing allows 3)')
print(f'  removable alignment pin D{cube.PIN_D} through the floor hole D{cube.PIN_HOLE} into the motor bore D{cube.MOTOR_BORE}: pin vs wheel {(pin_pl ^ wheel_pl).volume():.3f} mm3, vs motor {(pin_pl ^ mot).volume():.3f} mm3')
t = cube.trim_xy()
bad = sum((cube.W3.cyl(x, y, cube.BOLT_HOLE - 0.02, -0.5, cube.RIM_L + 0.5) ^ wl).volume() + (cube.W3.cyl(x, y, 7.0, cube.RIM_L - cube.CBORE_H + 0.01, cube.RIM_L + 0.5) ^ wl).volume() for x, y in t)
print(f'  weight bolts: the D{cube.BOLT_HOLE} holes and the D7 head pockets are clear right through {bad:.3f} mm3; wall left outside a head pocket {cube.WD / 2 - cube.TRIM_R - cube.CBORE_D / 2:.1f} mm, '
      f'inside {cube.TRIM_R - cube.CBORE_D / 2 - cube.RIM_R0:.1f} mm; head {cube.CBORE_H - 4.0:.1f} mm under the back face, tip {cube.RIM_L - cube.CBORE_H - cube.BOLT_L:.1f} mm from the front face')

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
print(f'  IMU envelope vs the base {(imu ^ hb).volume():.3f} mm3, vs the board {(imu ^ enc).volume():.3f} mm3, vs the plug\'s cable {(union([imu, teth]) ^ plg).volume():.3f} mm3 '
      f'(the cable passes {cube.TETHER["x"][0] - cube.BOARD_X1 - cube.CONN_H:.1f} mm in front of the IMU\'s own cable)')

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
