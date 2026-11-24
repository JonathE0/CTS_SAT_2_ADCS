"""Table-edge swing-up reaction-wheel pendulum (RWP) for the 2804 hollow-shaft gimbal motor (Amazon.ca B0FSZ7XWG2).

    python make_swingup_parts.py        # needs numpy + manifold3d (the same toolchain as ONE_DOF_RW/String_Rev3)

Frame (same as rev3 table_hook): table face at x = 0 (table at x < 0), table top at z = 0, y along the table edge, x grows
away from the table. The pivot axis is parallel to x, ZP mm below the table top. The arm hangs straight down at ARM_DEG = 0.

Stack along x (mm):  0..5 clip plate | 5..12 pad | 4..6.4 AS5600 card slot | 7.5..12.5 magnet cap | 12.5..17.5 bearing 1 |
                     17.5..33 spacer | 33..38 bearing 2 | 38..40 washers | 40..48 arm | 25..40 motor (hangs on the arm's table side) |
                     13..25 wheel rim (z 0..12 of the wheel)  -> the wheel sits between the arm and the clip, at radius >= 50 from
                     the pivot, so it passes around the pivot boss instead of beyond it. That keeps the load close to the clip.

Writes (next to this script): Pivot_Clip_Hook.stl, Pivot_Clip_Hook_Slider.stl (hook + rider as one print), Pivot_Arm.stl,
Wheel_D100_2804.stl, Magnet_Cap.stl, Spacer_Sleeve.stl, Slider_Screw/Pad/Pin.stl (as rev3), Assembly_hanging.stl, viewer_data.json.
Then runs the swing sweep (0..355 deg) for collisions and feeds CAD-derived mass/inertia to the swing-up + catch simulation.

!! MOTOR VALUES MARKED ASSUMED ARE NOT IN THE AMAZON LISTING. Measure them on the motor and edit, then rerun. !!
"""
import base64
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import manifold3d as m3

HERE = Path(__file__).parent
REV3 = HERE.parent.parent / 'ONE_DOF_RW' / 'String_Rev3' / 'mechanical'


def load(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


F = load('mfp', REV3 / 'frame_parts' / 'make_frame_parts.py')
H = load('hook', REV3 / 'table_hook' / 'make_table_hook.py')
S = load('slider', REV3 / 'table_hook' / 'make_table_slider.py')
W3 = load('fly', REV3 / 'flywheel' / 'make_flywheel_d100.py')
box = F.box

# ---------------------------------------------------------------- motor (from the listing)
#   Dimensions below come from the dimension drawing in the listing's image gallery (gallery image 5 / description image 4).
MOTOR_D, MOTOR_H, MOTOR_BORE = 34.5, 15.0, 6.5        # body diameter; rotor can 11 + stator plate 4 = 15; hollow-shaft bore
MOTOR_G, ROTOR_G = 40.0, 22.0                         # listing: 37 g (spec table) plus leads; the encoder board is counted separately
ROTOR_PCD, ROTOR_SCREW, ROTOR_DEPTH = 16.0, 2.5, 3.0  # rotor face (wheel side): 4 x M2.5, thread depth 3 max, cross pattern (0/90/180/270 deg)
STATOR_PCD, STATOR_SCREW, STATOR_DEPTH = 19.0, 2.5, 4.0   # stator back (arm side): 4 x M2.5, thread depth 4 max, at 45 deg
MOTOR_HUB_D, MOTOR_HUB_L = 12.0, 4.5                  # rotor's rear hub (carries the encoder magnet) sticks out of the stator back: 19.5 overall
MOTOR_SHAFT_OD, SHAFT_STICKOUT = 8.0, 0.0             # the shaft boss is flush with the rotor face in the section drawing
ENC_W, ENC_T, ENC_G = 33.0, 1.6, 5.0                  # the kit's AS5600 board: 33 x 33 mm X-shape (drawing); thickness and 5 g with its screws are my estimates
# ---------------------------------------------------------------- ASSUMED, check on the real parts
ENC_PLANE = 6.0                                       # ASSUMED: the board sits 6 mm from the stator back (hub 4.5 + 1.5 mm air gap); compare with the kit's standoffs
PCB_W, PCB_H = 18.0, 18.0                             # ASSUMED: the second AS5600 board (pivot), width x height

# ---------------------------------------------------------------- layout
ZP = -112.0            # pivot axis below the table top
L = 100.0              # pivot axis to motor axis
T, W = H.T, H.W        # clip plate thickness 5 and width 30 (rev3 values, so the rev3 slider rides on it)
PL = 146.0             # plate length down the face
PAD_X, WEDGE_Z0 = 12.0, -80.0
SH = 8.0               # outboard shift of the bearing pair's far end, arm, motor and wheel: the longer slider pin head must clear the wheel
BOSS_R, BOSS_X1 = 15.0, 38.0 + SH
BRG_D, BRG_W, BRG_ID = 16.0, 5.0, 5.0                 # 625ZZ
B1_X0, B2_X0 = 12.5, 33.0 + SH
CAP_X0, CAP_X1, CAP_D = 7.5, 12.5, 8.4
ROD_D, ROD_X0, ROD_X1 = 5.0, 10.1, 48.1 + SH
HUB_X0, HUB_X1, HUB_R = 40.0 + SH, 48.0 + SH, 9.0
# longer slider pin: rev3's pin was 11.8 mm long (tip flat at x = 0.1, head 2.5 mm). The tip cannot go further in (the table face is at x = 0),
# so the rider grows a boss around the pin hole and the pin gets PIN_BOSS_LEN longer on the outboard side.
WALL_X1 = H.T + S.CL + S.WALL                          # 9.4: outer face of the rider's wall
PIN_BOSS_R, PIN_BOSS_LEN = 7.0, 6.0
MOT_X0 = HUB_X0 - MOTOR_H                             # 25: rotor top face
ARM_BAR_W = 16.0
TIP_R = 20.0
RHO = 1.24e-3          # g/mm^3 PLA
FILL_ARM, FILL_WHEEL = 0.75, 0.48                    # sliced mass / solid mass (wheel from the rev3 README: 25.8 / 53.9 g)
BOLT_G, N_BOLT = 2.3, 10                               # M4 x 12 steel socket head
ZH = -25.0             # rider on pin hole -25: a 35 mm table
TABLE_T = 35.0


def cx(r, x0, x1, y=0.0, z=0.0, seg=64):
    """Cylinder along +x."""
    return m3.Manifold.cylinder(x1 - x0, r, r, seg).rotate((0, 90, 0)).translate((x0, y, z))


def cy(r, y0, y1, x=0.0, z=0.0, seg=48):
    """Cylinder along +y."""
    return m3.Manifold.cylinder(y1 - y0, r, r, seg).rotate((-90, 0, 0)).translate((x, y0, z))


def ext_x(poly, x0, x1):
    """Extrude a polygon given as (y, z) points along x from x0 to x1."""
    p = F.prism(poly, 0, x1 - x0)                                  # local (X, Y, Z) -> (x = Z, y = X, z = Y)
    return p.transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]], float))


def union(ms):
    return m3.Manifold.batch_boolean(list(ms), m3.OpType.Add)


def pcd_holes(pcd, d, x0, x1, yc, zc, cb_d=None, cb_x0=None, a0=45):
    cuts = []
    for k in range(4):
        a = math.radians(a0 + 90 * k)
        y, z = yc + pcd / 2 * math.cos(a), zc + pcd / 2 * math.sin(a)
        cuts.append(cx(d / 2 + 0.1, x0, x1, y, z, 24))
        if cb_d:
            cuts.append(cx(cb_d / 2, cb_x0, x1, y, z, 24))
    return union(cuts)


# ---------------------------------------------------------------- clip hook with the pivot head
def hook_profile(pl):
    return [(-H.LT + 1.5, 0), (-1.5, 0), (0, -1.5), (0, -pl), (T, -pl), (T, 1.0)] \
        + H.arc(T - 4.0, 1.0, 4.0, 0, 90, 10)[1:] + [(-H.LT + 1.5, T), (-H.LT, T - 1.5), (-H.LT, 1.5)]


def y_prism(pts, w):
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if a < 0:
        pts = pts[::-1]
    return F.prism(pts, 0, w).rotate((90, 0, 0)).translate((0, w / 2, 0))


def pivot_hook():
    h = y_prism(hook_profile(PL), W)
    pad = y_prism([(T - 0.5, WEDGE_Z0), (PAD_X, WEDGE_Z0 - 8), (PAD_X, -PL), (T - 0.5, -PL)], W)
    boss = cx(BOSS_R, PAD_X - 0.5, BOSS_X1, 0, ZP, 96)
    h = h + pad + boss
    for z in H.PIN_Z:                                              # rev3 slider pin holes
        h = h - cx(H.PIN_HOLE / 2, -0.5, T + 0.5, 0, z, 32)
    h = h - cx(BRG_D / 2 + 0.075, B1_X0, BOSS_X1 + 1, 0, ZP, 96)   # both bearing seats, one through bore, shoulder at B1_X0
    h = h - cx(5.5, 4.0, B1_X0 + 0.1, 0, ZP, 64)                   # relief for the magnet cap
    h = h - box(4.0, 6.4, -(PCB_W / 2 + 0.25), PCB_W / 2 + 0.25, -PL - 1, ZP + PCB_H / 2 + 0.25)   # AS5600 card slot, opens at the bottom
    for y0 in (-13.4, 10.2):                                                                        # cable anchor: two zip-tie slots straight through plate and pad,
        h = h - box(-1.0, PAD_X + 1.0, y0, y0 + 3.2, ZP - 30.9, ZP - 29.1)                          # 30 mm below the pivot; the bundle lies on the pad face between them
    return h


# ---------------------------------------------------------------- arm
def arm():
    zt = ZP - L
    hub = cx(HUB_R, HUB_X0, HUB_X1, 0, ZP, 64)
    bar = ext_x([(-ARM_BAR_W / 2, ZP), (ARM_BAR_W / 2, ZP), (ARM_BAR_W / 2, zt), (-ARM_BAR_W / 2, zt)], HUB_X0, HUB_X1)
    tip = cx(TIP_R, HUB_X0, HUB_X1, 0, zt, 96)
    a = hub + bar + tip
    a = a - cx(ROD_D / 2 + 0.1, HUB_X0 - 1, HUB_X1 + 1, 0, ZP, 48)                    # rod bore 5.2
    a = a - box(HUB_X0 - 1, HUB_X1 + 1, -0.6, 0.6, ZP, ZP + HUB_R + 1)                 # clamp slit, on the side away from the bar
    zc = ZP + 6.0                                                                       # M3 clamp screw across the slit
    a = a - cy(1.6, -HUB_R - 1, HUB_R + 1, (HUB_X0 + HUB_X1) / 2, zc, 24)
    a = a - cy(3.1, -HUB_R - 1, -HUB_R + 2.5, (HUB_X0 + HUB_X1) / 2, zc, 24)           # head counterbore
    a = a - cy(3.4, HUB_R - 2.5, HUB_R + 1, (HUB_X0 + HUB_X1) / 2, zc, 6)              # hex nut trap, 5.7 across flats
    # Motor mount, on the stator back (listing drawing): 4 x M2.5 on a D19 circle at 45 deg, thread depth 4 max. The stator back sits on the arm's table-side
    # face; the rotor's D12 x 4.5 rear hub (encoder magnet) goes into the window. The kit's AS5600 board lies in a recess on the outboard face, chip towards the
    # hub, ENC_PLANE from the stator back, and the same four M2.5 screws clamp board, arm and motor together (board -> arm -> stator back).
    a = a - cx(MOTOR_HUB_D / 2 + 1.0, HUB_X0 - 1, HUB_X1 + 1, 0, zt, 64)               # window for the hub, 1 mm clearance all round
    a = a - pcd_holes(STATOR_PCD, STATOR_SCREW, HUB_X0 - 1, HUB_X1 + 1, 0, zt, a0=45)   # M2.5 clearance holes (2.7)
    e = ENC_W + 0.6                                                                     # recess for the board (33 x 33 plus 0.3 mm each side)
    a = a - box(HUB_X0 + ENC_PLANE, HUB_X1 + 1, -e / 2, e / 2, zt - e / 2, zt + e / 2)
    # two lead channels on the table-side face, from inside the motor window to 22 mm below the pivot: left = the 3 phase leads, right = the encoder
    # wires (kept apart so I2C does not ride on the phase leads). Wrap zip ties around the whole bar to hold them; the motor's stator base covers
    # the first part. Below the hub the bundle leaves the bar towards the clip as a free loop (see README, "Direct drive and wiring").
    for y0, y1 in ((-6.8, -2.6), (2.6, 6.8)):
        a = a - box(HUB_X0 - 0.1, HUB_X0 + 2.4, y0, y1, zt + 4.0, ZP - 22.0)
    # the board's encoder cable (4-pin PH2.0) leaves its connector on the outboard face: a channel up the outboard face, then a slot through the bar
    # 22 to 26 mm below the pivot, into the table-side encoder channel. Mount the motor with its lead notch (the stator plate's rim slot) towards the pivot.
    a = a - box(HUB_X1 - 2.4, HUB_X1 + 0.1, 2.6, 6.8, zt + e / 2 - 0.5, ZP - 22.0)
    a = a - box(HUB_X0 - 1, HUB_X1 + 1, 2.6, 6.8, ZP - 26.0, ZP - 22.0)
    return a


# ---------------------------------------------------------------- wheel (local frame: z = spin axis, z = 0 on the rotor face, grows away from the motor)
def wheel(threaded=True):
    od, rim_id, slot_r0, slot_r1 = 100.0, 77.0, 19.0, 33.0
    hub_od, web_t = 26.0, 8.0
    rim = W3.cyl(0, 0, od, 0, W3.RIM_H) - W3.cyl(0, 0, rim_id, -1, W3.RIM_H + 1)
    hub = W3.cyl(0, 0, hub_od, 0, web_t)
    r0, r1 = hub_od / 2 - 1, rim_id / 2 + 1
    parts = [hub, rim]
    for k in range(3):
        deg = 90 + 120 * k
        sp = W3.prism([(r0, -W3.SPOKE_W0 / 2), (r1, -W3.SPOKE_W1 / 2), (r1, W3.SPOKE_W1 / 2), (r0, W3.SPOKE_W0 / 2)], 0, web_t)
        slot = box(slot_r0, slot_r1, -W3.SLOT_W / 2, W3.SLOT_W / 2, -1, web_t + 1) + W3.cyl(slot_r0, 0, W3.SLOT_W, -1, web_t + 1) + W3.cyl(slot_r1, 0, W3.SLOT_W, -1, web_t + 1)
        parts.append((sp - slot).rotate((0, 0, deg)))
    body = union(parts)
    if SHAFT_STICKOUT <= 0:
        body = body + W3.cyl(0, 0, MOTOR_BORE - 0.3, -4.0, 0.5)                          # centring spigot into the hollow shaft
    # else: the shaft end enters the hub instead, so the hub is bored to take it (cut below with the screw holes)
    pitch_r = (od + rim_id) / 4
    cuts = []
    for i in range(W3.HOLES):                                                           # ten M4 weight bolts, as rev3
        a = math.radians(90 + 180 / W3.HOLES + 360 * i / W3.HOLES)
        x, y = pitch_r * math.cos(a), pitch_r * math.sin(a)
        cuts.append(W3.thread_cutter(x, y, -0.2, W3.RIM_H - W3.CB_DEPTH + 0.2, W3.M4_MAJOR - W3.UNDERSIZE) if threaded else W3.cyl(x, y, 3.6, -1, W3.RIM_H + 1))
        cuts.append(W3.cyl(x, y, W3.CB_D, W3.RIM_H - W3.CB_DEPTH, W3.RIM_H + 1))
    if SHAFT_STICKOUT > 0:
        cuts.append(W3.cyl(0, 0, MOTOR_SHAFT_OD + 0.3, -1, SHAFT_STICKOUT + 0.5))
    # the screw-on fitting: 4 x M2.5 into the rotor face (D16 circle, cross pattern, thread depth 3 max). 3.5 mm of hub under the head, so an M2.5 x 6
    # screw engages 2.5 mm (limit 3). Head counterbore 5.0 for an M2.5 socket head (4.5).
    for k in range(4):
        a = math.radians(90 * k)
        x, y = ROTOR_PCD / 2 * math.cos(a), ROTOR_PCD / 2 * math.sin(a)
        cuts.append(W3.cyl(x, y, ROTOR_SCREW + 0.2, -1, web_t + 1))
        cuts.append(W3.cyl(x, y, 5.0, 3.5, web_t + 1))
    return body - union(cuts)


def place_wheel(m):
    """Local wheel (X, Y, Z) -> assembly: x = MOT_X0 - Z, y = -X, z = (ZP - L) + Y (a proper rotation, no mirroring)."""
    return m.transform(np.array([[0, 0, -1, MOT_X0], [-1, 0, 0, 0], [0, 1, 0, ZP - L]], float))


# ---------------------------------------------------------------- small parts
def magnet_cap():
    c = cx(CAP_D / 2, CAP_X0, CAP_X1, 0, ZP, 48)
    c = c - cx(3.05, CAP_X0 - 1, CAP_X0 + 2.6, 0, ZP, 48)                              # 6 x 2.5 magnet pocket, open to the rear
    c = c - cx(ROD_D / 2, CAP_X0 + 2.5, CAP_X1 + 1, 0, ZP, 48)                         # rod bore (glued)
    return c


def spacer():
    return cx(3.5, B1_X0 + BRG_W, B2_X0, 0, ZP, 48) - cx(ROD_D / 2 + 0.1, B1_X0 + BRG_W - 1, B2_X0 + 1, 0, ZP, 32)


def bearing(x0):
    return cx(BRG_D / 2, x0, x0 + BRG_W, 0, ZP, 96) - cx(BRG_ID / 2, x0 - 1, x0 + BRG_W + 1, 0, ZP, 48)


def rod():
    return cx(ROD_D / 2 - 0.01, ROD_X0, ROD_X1, 0, ZP, 32)


def motor():
    zt = ZP - L
    body = cx(MOTOR_D / 2, MOT_X0, HUB_X0, 0, zt, 96) + cx(MOTOR_HUB_D / 2, HUB_X0 - 0.1, HUB_X0 + MOTOR_HUB_L, 0, zt, 64)     # body 15 + rear hub 4.5
    return body - cx(MOTOR_BORE / 2, MOT_X0 - 1, HUB_X0 + MOTOR_HUB_L + 1, 0, zt, 48)


def board():
    """The kit's AS5600 board in its recess, as an envelope: a 33 x 33 plate (the real board is X-shaped, so this is conservative) and the two 4-pin headers."""
    zt = ZP - L
    x0 = HUB_X0 + ENC_PLANE
    plate = box(x0, x0 + ENC_T, -ENC_W / 2, ENC_W / 2, zt - ENC_W / 2, zt + ENC_W / 2)
    heads = [box(x0 + ENC_T, x0 + ENC_T + 7.0, y0, y0 + 6.0, zt - 8.0, zt + 8.0) for y0 in (-ENC_W / 2 + 2.0, ENC_W / 2 - 8.0)]
    return plate + heads[0] + heads[1]


def rider_ext(zh):
    """rev3 rider plus a boss around the pin hole, so the pin is guided over 10 mm of rider instead of 4."""
    boss = cx(PIN_BOSS_R, WALL_X1 - 0.5, WALL_X1 + PIN_BOSS_LEN, 0, zh, 48) - cx(H.PIN_HOLE / 2, WALL_X1 - 1, WALL_X1 + PIN_BOSS_LEN + 1, 0, zh, 32)
    return S.rider(zh) + boss


def pin_long():
    """Pin, tip 0.2 mm inside the plate's back face (rev3: 0.1 mm), head just outside the boss. Origin = pin axis at z = 0."""
    xh = WALL_X1 + PIN_BOSS_LEN
    return cx(2.5, 0.2, xh + 0.5, 0, 0, 48) + cx(5.0, xh, xh + 2.5, 0, 0, 48)


def rot_about_pivot(m, deg):
    return m.translate((0, 0, -ZP)).rotate((deg, 0, 0)).translate((0, 0, ZP))


# ---------------------------------------------------------------- mesh helpers
def tris(m):
    me = m.to_mesh()
    v = np.asarray(me.vert_properties, np.float64)[:, :3]
    return v[np.asarray(me.tri_verts, np.int64)]


def moments(T_):
    """Volume (mm3), first moments (mm4) and second moments about the origin of a closed mesh (mm5): returns V, (Sx, Sy, Sz), (Ixx, Iyy, Izz)."""
    a, b, c = T_[:, 0], T_[:, 1], T_[:, 2]
    v6 = np.einsum('ij,ij->i', a, np.cross(b, c))
    s = a + b + c
    V = v6.sum() / 6
    S1 = (v6[:, None] / 24 * s).sum(0)
    q = (v6[:, None] / 120 * ((a ** 2 + b ** 2 + c ** 2) + s ** 2)).sum(0)             # sum of integral x^2, y^2, z^2
    return V, S1, q


def about_x_axis(m, rho, fill, y0=0.0, z0=ZP):
    """Mass (g), centre of mass (y, z) and inertia (kg m^2) about the pivot axis (parallel to x through (y0, z0))."""
    V, S1, q = moments(tris(m))
    mass = V * rho * fill
    j = rho * fill * ((q[1] + q[2]) - 2 * y0 * S1[1] - 2 * z0 * S1[2] + (y0 ** 2 + z0 ** 2) * V) * 1e-9
    return mass, (S1[1] / V, S1[2] / V), j


def check(m, name):
    assert m.status() == m3.Error.NoError and not m.is_empty(), name
    bb = np.asarray(m.bounding_box())
    print(f'{name:22s} {m.volume() / 1000:7.1f} cm3  solid {m.volume() * RHO:6.1f} g   '
          f'x {bb[0]:6.1f}..{bb[3]:6.1f}  y {bb[1]:6.1f}..{bb[4]:6.1f}  z {bb[2]:7.1f}..{bb[5]:7.1f}')


def main():
    hook = pivot_hook()
    arm_m = arm()
    wheel_l = wheel(True)
    wheel_pl = place_wheel(wheel_l)
    wheel_fast = place_wheel(wheel(False))                 # unthreaded copy for the collision sweep
    cap, sp = magnet_cap(), spacer()
    B1, B2, rod_m, mot, enc = bearing(B1_X0), bearing(B2_X0), rod(), motor(), board()
    R, SC, PD, PN = rider_ext(ZH), S.screw().translate((0, 0, ZH)), S.pad().translate((0, 0, ZH)), pin_long().translate((0, 0, ZH))
    table = box(-300, 0.0, -150, 150, -TABLE_T, 0)

    print('--- parts')
    for n, m in (('Pivot_Clip_Hook', hook), ('Pivot_Arm', arm_m), ('Wheel_D100_2804', wheel_pl), ('Magnet_Cap', cap), ('Spacer_Sleeve', sp)):
        check(m, n)

    # ---- fit checks (all mm3)
    static = {'hook': hook, 'rider': R, 'screw': SC, 'pad': PD, 'pin': PN, 'table': table, 'bearing1': B1, 'bearing2': B2}
    mover = {'arm': arm_m, 'wheel': wheel_fast, 'motor': mot, 'board': enc, 'rod': rod_m, 'cap': cap, 'spacer': sp}
    print('--- static fit (hanging pose), overlap in mm3')
    pairs = [('bearing1', 'hook'), ('bearing2', 'hook'), ('rider', 'hook'), ('rider', 'table'), ('pad', 'table'), ('pin', 'hook'),
             ('arm', 'rod'), ('wheel', 'motor'), ('motor', 'arm'), ('board', 'arm'), ('board', 'motor'), ('cap', 'rod'), ('cap', 'hook'),
             ('spacer', 'rod'), ('spacer', 'bearing1'), ('rod', 'bearing1'), ('rod', 'bearing2')]
    allp = {**static, **mover}
    for a, b in pairs:
        print(f'  {a:9s} x {b:9s} {(allp[a] ^ allp[b]).volume():8.3f}')
    print('--- swing sweep: moving group (arm, wheel, motor, rod, cap, spacer) vs fixed group, 5 degree steps')
    mv = union(mover.values())
    fixed = union(static.values())
    worst, wang, wname = 0.0, 0, ''
    clr = 1e9
    for ang in range(0, 360, 5):
        mm = rot_about_pivot(mv, ang)
        v = (mm ^ fixed).volume()
        if v > worst:
            worst, wang = v, ang
    print(f'  worst overlap {worst:.3f} mm3 at {wang} deg' if worst > 0.01 else '  0 mm3 overlap at every angle')
    if worst > 0.01:
        for nm, st in static.items():
            vv = max((rot_about_pivot(mv, wang) ^ st).volume() for _ in (0,))
            if vv > 0.01:
                print(f'    {nm}: {vv:.3f} mm3')

    # ---- mass and inertia about the pivot, from the CAD plus bought parts
    m_arm, c_arm, j_arm = about_x_axis(arm_m, RHO, FILL_ARM)
    m_wh, c_wh, j_wh = about_x_axis(wheel_pl, RHO, FILL_WHEEL)
    Vw, Sw, qw = moments(tris(wheel_l))                                               # local wheel: spin inertia about its own axis
    jw_print = RHO * FILL_WHEEL * (qw[0] + qw[1]) * 1e-9
    r_b = (100 + 77) / 4
    m_bolts = N_BOLT * BOLT_G
    jw_bolts = m_bolts * 1e-3 * (r_b * 1e-3) ** 2
    jw_rotor = ROTOR_G * 1e-3 * (0.0145) ** 2                                          # thin ring approximation for the bell
    Jw = jw_print + jw_bolts + jw_rotor
    zt = ZP - L
    j_bolts = m_bolts * 1e-3 * (((L * 1e-3) ** 2) + (r_b * 1e-3) ** 2)
    m_mot, j_mot = MOTOR_G, MOTOR_G * 1e-3 * (L * 1e-3) ** 2 + MOTOR_G * 1e-3 * (MOTOR_D * 1e-3 / 2) ** 2 / 2
    m_rod = math.pi * 2.5 ** 2 * (ROD_X1 - ROD_X0) * 7.85e-3
    m_screws = 2.0                                                                     # motor + wheel screws and the M3 clamp
    items = [('arm (printed)', m_arm, c_arm[1], j_arm), ('wheel (printed)', m_wh, c_wh[1], j_wh),
             ('10 x M4x12 bolts', m_bolts, zt, j_bolts), ('motor + leads', m_mot, zt, j_mot),
             ('encoder board + 4 screws', ENC_G, zt, ENC_G * 1e-3 * (L * 1e-3) ** 2),
             ('rod + magnet + misc', m_rod + m_screws, ZP, 0.0)]
    M = sum(i[1] for i in items)
    zc = sum(i[1] * i[2] for i in items) / M
    l = abs(zc - ZP) * 1e-3
    Jt = sum(i[3] for i in items)
    print('--- moving assembly about the pivot axis')
    for nm, mg, z, j in items:
        print(f'  {nm:22s} {mg:6.1f} g   z {z - ZP:7.1f} mm from pivot   J {j:.3e} kg m2')
    print(f'  total M = {M:.0f} g,   l = {l * 1e3:.1f} mm,   M g l = {M * 1e-3 * 9.81 * l:.3f} N m,   Jt = {Jt:.3e},   Jw (wheel + bolts + rotor) = {Jw:.3e} kg m2')
    print(f'  wheel alone: printed {m_wh:.1f} g, J own axis {jw_print:.2e}; bolts {m_bolts:.0f} g, {jw_bolts:.2e}; rotor bell {jw_rotor:.2e}')

    # ---- outputs
    for n, m in (('Pivot_Clip_Hook', hook), ('Pivot_Clip_Hook_Slider', hook + R), ('Pivot_Arm', arm_m), ('Wheel_D100_2804', wheel_pl),
                 ('Magnet_Cap', cap), ('Spacer_Sleeve', sp)):
        F.write_stl(HERE / f'{n}.stl', m)
    for n, m in (('Slider_Screw', S.screw()), ('Slider_Pad', S.pad()), ('Slider_Pin_Long', pin_long())):
        F.write_stl(HERE / f'{n}.stl', m)
    old, new = tris(S.pin()), tris(pin_long())
    print(f'pin length: rev3 {old[..., 0].max() - old[..., 0].min():.1f} mm -> {new[..., 0].max() - new[..., 0].min():.1f} mm '
          f'(tip x = {old[..., 0].min():.1f} -> {new[..., 0].min():.1f}, table face at x = 0)')
    pn_table = (pin_long().translate((0, 0, ZH)) ^ table).volume()
    print(f'pin vs table overlap: {pn_table:.3f} mm3 (rev3 pin: {(S.pin().translate((0, 0, ZH)) ^ table).volume():.3f} mm3)')
    F.write_stl(HERE / 'Assembly_hanging.stl', union([hook, R, SC, PD, PN, arm_m, wheel_fast, mot, enc, rod_m, cap, sp, B1, B2]))
    # viewer meshes: name -> (colour, moving?) ; wheel without threads keeps the file small
    parts = {'hook': (hook + R, '#4f81bd', 0), 'screw': (SC + PD + PN, '#8c8c8c', 0), 'bearings': (B1 + B2, '#c8c8c8', 0),
             'arm': (arm_m, '#e08a2e', 1), 'wheel': (wheel_fast, '#9aa3ad', 1), 'motor': (mot, '#c0392b', 1), 'board': (enc, '#1f5fa8', 1), 'rod': (rod_m + cap + sp, '#d0d0d0', 1),
             'table': (box(-300, 0, -150, 150, -TABLE_T, 0), '#c9a47a', 0)}
    out = {'pivot': [0, 0, ZP], 'parts': {}}
    for n, (m, col, mov) in parts.items():
        t = tris(m).astype(np.float32)
        out['parts'][n] = {'color': col, 'moving': mov, 'positions_b64': base64.b64encode(t.tobytes()).decode()}
    (HERE / 'viewer_data.json').write_text(json.dumps(out))
    json.dump({'M_kg': M * 1e-3, 'l_m': l, 'Jt': Jt, 'Jw': Jw, 'L_mm': L, 'ZP': ZP}, open(HERE / 'cad_inertia.json', 'w'))
    print('wrote', HERE)


if __name__ == '__main__':
    main()
