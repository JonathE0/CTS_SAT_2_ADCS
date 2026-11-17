"""Balancing wheel module: a thin 90 x 90 x 44 mm frame that stands on one edge, with the 2804 motor and a D74 wheel inside and nothing else on board but
the IMU. The ESP32, motor driver and power supply stay off the body on a light cable.

    python make_cube_parts.py        # needs numpy + manifold3d (the toolchain of ONE_DOF_RW/rev3 and SWINGUP_RWP)

Every surface that faces down in the print orientation is designed to lean no more than OVERHANG degrees from vertical (the limit asked for is 40), so the
parts print without supports. A flat ceiling would be 90 degrees. The module is three printed parts:

  Frame_Base.stl   +x end ring, four corner stubs ending in tenons, and the motor mount: a hub ring on four arms, in the ring's own 5 mm slab. Four raised
                   pads on the hub take the motor unit's four brass feet; four M2.5 x 8 screws go in from the outside face, through short slots, into the
                   feet. Their heads sit in pockets whose roofs taper at OVERHANG, so the pockets print without supports. IMU pad and two trim pads as
                   before. Outside face (x = 22) down.
  Frame_Cap.stl    -x end ring with four tapered collars carrying the sockets. Ring face (x = -22) down.
  Wheel_D74_2804.stl  a cup over the rotor end of the motor: the floor bolts to the rotor face (4 x M2.5 on D16), a thin inner wall goes over the spinning
                   can, and the rim (r 27..37) lies alongside the motor only. It ends before the motor's back face, where the leads come out, so nothing
                   that spins is near a wire. Eight M4 x 12 weight bolts go into the rim's back end, heads sunk flush. Floor (outside face) down.
  (No pin is printed. The floor keeps its D6.5 centre hole; a D6.4 pin, such as the headed one on Fit_Test_Pins, can be pushed through it into the motor's bore as
   a removable alignment jig while the four M2.5 screws are tightened, then pulled out. pin() below is that jig, used by the checks only.)

The motor and encoder are one bought unit, used as the kit comes (listing B0FSZ7XWG2): two brass standoffs hold the AS5600 board off the motor's back face, on two
of its D19 holes, and four more brass standoffs, nutted into the board's corner slots, stick out of the back of the board. Those four are the unit's feet. The
frame does not use the motor's own holes. What the listing's drawings give, and what is still assumed, is marked on each constant below.

Frame axes: centre at the origin, x = the wheel axis = the pivot edge direction (the depth, 44 mm), (y, z) the 90 x 90 cross-section. The module stands on the
edge at (y, z) = (-45, +45). The four edges parallel to x are rounded R1.5 so it rolls; the edges around the end faces stay sharp, which keeps the bed face clean.

Stack along x: rotor screw heads -19.1 | wheel floor -17.6..-15.1 | motor: rotor face -15.1, can to -4.1, back face -0.1, magnet ring to 4.4 | board 6.9..8.5,
its connectors to 13.9 | feet 8.5..15.5 | pads 15.5..17 | base slab 17..22. The wheel's rim runs from -17.6 to -1.3.
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
REV3 = HERE.parent.parent / 'ONE_DOF_RW' / 'rev3' / 'mechanical'


def load(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


F = load('mfp', REV3 / 'frame_parts' / 'make_frame_parts.py')
W3 = load('fly', REV3 / 'flywheel' / 'make_flywheel_d100.py')
box = F.box

# ---------------------------------------------------------------- module
A, D, S, RE = 90.0, 44.0, 5.0, 1.5      # cross-section side, depth along x, bar section, edge round radius
H, HX = A / 2, D / 2                    # 45, 22
PIVOT = (-1, +1)                        # pivot edge at (y, z) = (PIVOT[0] * H, PIVOT[1] * H), length D
OVERHANG = 38.0                         # design limit for downward-facing surfaces, degrees from vertical (the asked-for limit is 40)
TAN_OV = math.tan(math.radians(OVERHANG))
RING_BASE, RING_CAP = (HX - S, HX), (-HX, -HX + S)   # x ranges of the two end rings
JOINT_X = -8.0                          # base stubs end here; the cap's collars reach this plane
COLLAR, COLLAR_RUN = 8.0, 3.0           # collar footprint 8 x 8; it widens 3 mm over a taper that is OVERHANG degrees from vertical
CLR_TENON = 0.05                        # clearance per side between a tenon and its socket. MEASURED: socket 2 (0.05) of Fit_Test_Sockets was a perfect fit on the user's printer. Was 0.20, then 0.10.
TENON, TENON_L = 3.4, 6.5               # glued tenon (base) in a socket (cap)
SOCKET = TENON + 2 * CLR_TENON
JC = (H - S) + TENON / 2                # tenon centre: puts its inner face exactly flush with the stub's (y or z = 40), so it adds no overhang
LEAD_IN = 0.4                           # 45 degree lead-in on the tenon tip and the socket mouth, so a snug fit still starts easily (both face up when printed: no overhang)
# ---------------------------------------------------------------- motor + AS5600 encoder unit, as the kit comes (Amazon.ca B0FSZ7XWG2). DRAWING = dimensioned on the listing's drawings.
MOTOR_D, MOTOR_BORE, BODY, CAN_L = 34.5, 6.5, 15.0, 11.0   # DRAWING: D34.5 x 15; the first 11 mm from the rotor face is the spinning can, the last 4 mm is the fixed stator base; D6.5 bore at the rotor face
HUB_D, HUB_L = 12.0, 4.5                   # DRAWING: the magnet ring on the back face, D12, 19.5 overall - 15 body. It spins
ROTOR_PCD, STATOR_PCD, M25 = 16.0, 19.0, 2.5   # DRAWING: rotor face 4 x M2.5 on D16 at 0/90/180/270, 3 mm deep at most. Back face 4 x M2.5 on D19 at 45 degrees, 4 mm deep at most
LEAD_W, LEAD_T = 5.0, 2.5                  # the three leads leave through the back face beside the magnet ring and lie on it, running straight out between two D19 holes (the listing's 3D view)
ENC_W, ENC_T = 33.0, 1.6                   # DRAWING: the board is 33 x 33; 1.6 thick scales off its side view
ENC_LOBE_R, ENC_SIDE_R = 4.5, 25.6         # DRAWING: 8-R4.5 lobes round the corner slots, 4-R25.6 hollow sides
ENC_SLOT = 12.0                            # DRAWING: the four corner slots are centred on a 24 mm square
CHIP = (8.3, 5.8, 1.7)                     # DRAWING: the part on the motor side, 8.7 overall - 7
CONN_BX, CONN_BY, CONN_H = (8.0, 14.0), 6.0, 5.4   # DRAWING (side view): two connectors on the back, 7 from the chip face = 5.4 above the board. The photos show them side entry, mouths outward
WIRE_REACH = 40.0                          # the plug's cable and the motor's leads are drawn as straight strips out to the ring bars (r 40): the worst case, nothing tied back
KIT_GAP = 7.0                              # ASSUMED: the kit's two centre standoffs hold the board's chip face this far from the back face (ring 4.5 + chip 1.7 + about 0.8 of air). The photo scales to 6..8.5
KIT_FOOT = 7.0                             # ASSUMED: the four corner standoffs behind the board, the unit's feet. The photo scales to 6..7.5; they must clear the 5.4 connectors
FOOT_R1 = ENC_SLOT * math.sqrt(2)          # 16.97: the corner slots' centres from the axis. The slots are 3.1 x 5, so a foot can sit anywhere from 16.0 to 17.9
HEX_D = 5.8                                # M2.5 brass standoff and nut, 5 mm across flats, 5.8 across corners
MOTOR_G, ROTOR_G, ENC_G = 40.0, 22.0, 8.0  # motor with leads (listing: 37 g bare, 50 g for the kit); its spinning part (ASSUMED); board + six brass standoffs + four nuts + two screws
KIT_HW_G = 5.0                             # of which the brass and screws (ASSUMED)
BOARD_ROT = 135.0                          # the board's connector axis is turned onto the pivot diagonal, so its corner slots, and the feet, land on the frame's y and z axes
# ---------------------------------------------------------------- motor mount, part of the base: a hub ring on four arms in the ring's slab (x 17..22)
FOOT_PAD_H = 1.5                           # the feet land on pads this far proud of the slab's inner face, so an M2.5 x 8 from outside engages 4 mm of the foot's thread
PAD_X = RING_BASE[0] - FOOT_PAD_H          # 15.5: where the feet land
FOOT_PAD_R = 4.0                           # each pad is a slot shape 8 wide round its screw slot
HUB_R0, HUB_R1 = 11.5, 22.5                # the hub ring: all four pads sit on it. Its middle is open
ARM_W, ARM_ROOT_W, ARM_FLARE_R = 12.0, 24.0, 31.0   # four arms on the y and z axes, 12 wide, widening from r 31 to 24 at the ring bar
SLOT_R, SLOT_W = (16.4, 17.6), 2.8         # short radial screw slots, 0.6 either way of the 24 mm square. Kept short so each foot still bears on 12 mm2 of pad; the board's own slots (16.0..17.9) take up the rest
POCKET_W, POCKET_STRAIGHT = 5.6, 2.0       # the head pockets, open on the outside face: 5.6 wide and 2 deep, then the roof narrows to the slot at OVERHANG
SCREW_HEAD_D, SCREW_L = 4.7, 8.0           # M2.5 x 8 button head (a pan head up to D5 also fits)
X_TAPER0 = HX - POCKET_STRAIGHT            # 20.0: the roof starts
X_TAPER1 = X_TAPER0 - (POCKET_W - SLOT_W) / 2 / TAN_OV          # 18.21: the roof has closed to the slot
X_SEAT = X_TAPER0 - (POCKET_W - SCREW_HEAD_D) / 2 / TAN_OV      # 19.42: a D4.7 head stops here, on the roof
# stack along x, from the pads forwards
BOARD_X1 = PAD_X - KIT_FOOT                # 8.5: back of the board
BOARD_X0 = BOARD_X1 - ENC_T                # 6.9: chip face
STATOR_X = BOARD_X0 - KIT_GAP              # -0.1: the motor's back face
MOT_X0 = STATOR_X - BODY                   # -15.1: rotor face, where the wheel mounts
# ---------------------------------------------------------------- wheel: a cup over the rotor end
WD = 74.0                                  # outside diameter: 3 mm from the cap ring's bars
FLOOR_T = 2.5                              # M2.5 x 5 button heads then engage 2.5 mm in the rotor, under the drawing's 3 mm
HEAD_H = 1.5                               # those heads stand proud of the floor's outside face (ISO 7380 M2.5)
RELIEF_D, RELIEF_H = 10.5, 0.4             # a shallow recess round the centre hole, so the floor seats on the rotor face even if the shaft end stands a little proud
CUP_BORE, CUP_WALL, CUP_L = 34.8, 1.6, 10.0   # the inner wall: 0.15 mm per side over the D34.5 can; it stops 1 mm short of the fixed stator base
RIM_R0 = 27.0                              # the rim, r 27..37
RIM_SETBACK = 1.2                          # the rim ends this far before the motor's back face, where the leads come out
RIM_L = FLOOR_T + BODY - RIM_SETBACK       # 16.3 from the floor's outside face
TRIM_R = 32.0                              # eight M4 holes through the rim
N_BOLT, BOLT_L, BOLT_G = 8, 12.0, 2.05     # M4 x 12 socket head. 2.05 g is CALCULATED from the screw's volume (weigh one); the last version used 2.3
BOLT_HOLE = 3.5                            # the bolts cut their own thread in a plain hole
CBORE_D, CBORE_H = 7.6, RIM_L - BOLT_L     # counterbore for the D7 x 4 head, 4.3 deep: head 0.3 under the rim's back face, tip level with the front face
PIN_D, PIN_L = 6.4, 12.0                   # removable alignment pin diameter: all of D6.1..6.4 from Fit_Test_Pins fitted, so the largest (least play) is used. Length 12 (2.5 through the floor + 9.5 into the motor)
PIN_HOLE = PIN_D + 0.1                     # the floor hole for it: 0.05 mm per side, the same slide fit as the tenons
# ---------------------------------------------------------------- corner pads on the base ring (flush with its outer face), tie slots, and the parts that ride on them
PAD_T = 2.4
IMU_G, TETHER_G = 3.0, 3.0                 # ASSUMED MPU6050 breakout 21 x 16 x 3, and the weight of the cable it drags
# The IMU is lined up with gravity: when the module balances on the PIVOT edge, 'up' in the (y, z) cross-section is the diagonal from that corner to the centre,
# so the board is turned 45 degrees from the frame's bars. Its axes are then vertical and horizontal at the balance point, and the horizontal one reads 0 there.
# u = height above the pivot edge along that diagonal, s = across it (horizontal at balance).
UP = (-PIVOT[0] / math.sqrt(2), -PIVOT[1] / math.sqrt(2))
IMU_H, IMU_UP, IMU_SIDE = 28.6, 16.0, 21.0  # board centre height above the edge, and the board's size along 'up' and across it
IMU_SLOT_S = 13.0                           # the two strap slots sit this far either side of the board's centre line (the board's edge is at 10.5)
IMU = dict(x=(HX - PAD_T - 3.0, HX - PAD_T), u=(IMU_H - IMU_UP / 2, IMU_H + IMU_UP / 2), s=(-IMU_SIDE / 2, IMU_SIDE / 2))
TETHER = dict(x=(HX - PAD_T - 4.8, HX - PAD_T - 3.0), u=(IMU_H - 1.0, IMU_H + 1.0), s=(-1.0, 1.0))
RHO = 1.24e-3
FILL_FRAME, FILL_WHEEL = 0.85, 0.48        # sliced mass / solid mass


def cx(r, x0, x1, y=0.0, z=0.0, seg=64):
    return m3.Manifold.cylinder(x1 - x0, r, r, seg).rotate((0, 90, 0)).translate((x0, y, z))


def union(ms):
    return m3.Manifold.batch_boolean(list(ms), m3.OpType.Add)


def hull(ms):
    return m3.Manifold.batch_hull(list(ms))


def sr(s, lo, hi):
    """(lo, hi) on the + side, mirrored for s = -1."""
    return (lo, hi) if s > 0 else (-hi, -lo)


def corners():
    for sy in (-1, 1):
        for sz in (-1, 1):
            yield sy, sz


def ann(r0, r1, x0, x1, seg=128):
    outer = cx(r1, x0, x1, 0, 0, seg)
    return outer if r0 <= 0 else outer - cx(r0, x0 - 1, x1 + 1, 0, 0, seg)


def obround(w, r0, r1, x0, x1, seg=32):
    """A slot-shaped prism along x: width w, its two end centres on the +y axis at y = r0 and r1."""
    return hull([cx(w / 2, x0, x1, r, 0.0, seg) for r in (r0, r1)])


# ---------------------------------------------------------------- frame pieces
def ring(x0, x1):
    return union([box(x0, x1, -H, H, H - S, H), box(x0, x1, -H, H, -H, -H + S), box(x0, x1, H - S, H, -H, H), box(x0, x1, -H, -H + S, -H, H)])


def stubs(x0, x1):
    return union([box(x0, x1, *sr(sy, H - S, H), *sr(sz, H - S, H)) for sy, sz in corners()])


def x_edge_cutters():
    """Takes the sharp outer corner (radius RE) off the four edges parallel to x. Those are vertical when printed, so rounding them adds no overhang."""
    cuts = []
    for su in (-1, 1):
        for sv in (-1, 1):
            cuts.append(box(-HX - 2, HX + 2, *sr(su, H - RE, H + 1), *sr(sv, H - RE, H + 1)) - cx(RE, -HX - 3, HX + 3, su * (H - RE), sv * (H - RE), 32))
    return union(cuts)


def diag(m, angles=(45, 135, 225, 315)):
    """Copies of a part built along +y, turned about x to each given direction."""
    return union([m.rotate((a, 0, 0)) for a in angles])


def tilted(x0, x1, u0, u1, s0, s1):
    """A box that is square to gravity at balance: u runs up the diagonal from the pivot edge, s across it (both in mm from the pivot corner)."""
    ang = math.degrees(math.atan2(UP[1], UP[0]))
    return box(x0, x1, u0, u1, s0, s1).rotate((ang, 0, 0)).translate((0.0, PIVOT[0] * H, PIVOT[1] * H))


def corner_pad(sy, sz, kind):
    """A pad in one inner corner of the base ring, flush with the ring's outer face (x = 22), with two zip-tie slots. 'imu': turned to line up with gravity, about
    34 wide, carries the IMU on the vertical diagonal; its strap runs across (horizontally at balance), through a slot either side of the board.
    'trim': 18 x 18, takes trim weight."""
    if kind == 'imu':
        pad = tilted(HX - PAD_T, HX, 10.0, IMU_H + IMU_UP / 2 + 3.0, -17.0, 17.0) ^ box(HX - PAD_T - 1, HX + 1, -H, H, -H, H)    # clipped to the cube: it narrows to the corner
        for sg in (-1, 1):
            pad = pad - tilted(HX - PAD_T - 1, HX + 1, IMU_H - 1.6, IMU_H + 1.6, sg * IMU_SLOT_S - 0.8, sg * IMU_SLOT_S + 0.8)
        return pad
    else:
        (ya, yb), (za, zb) = (22.5, H - S + 0.5), (22.5, H - S + 0.5)
        sl_y, sl_z = (28.4, 31.6), ((24.0, 25.6), (37.4, 39.0))
    pad = box(HX - PAD_T, HX, *sr(sy, ya, yb), *sr(sz, za, zb))
    for a, b in sl_z:
        pad = pad - box(HX - PAD_T - 1, HX + 1, *sr(sy, *sl_y), *sr(sz, a, b))
    return pad


def tenon_at(yc, zc, w=None, length=None, x_end=None, lead=LEAD_IN):
    """A square tenon pointing towards -x from x = x_end (default the joint plane), with a 45 degree lead-in on its tip."""
    w = TENON if w is None else w
    length = TENON_L if length is None else length
    x_end = JOINT_X if x_end is None else x_end
    xt = x_end - length                                                          # tip
    body = box(xt + lead, x_end, yc - w / 2, yc + w / 2, zc - w / 2, zc + w / 2)
    tip = hull([box(xt + lead, xt + lead + 0.02, yc - w / 2, yc + w / 2, zc - w / 2, zc + w / 2),
                box(xt, xt + 0.02, yc - w / 2 + lead, yc + w / 2 - lead, zc - w / 2 + lead, zc + w / 2 - lead)])
    return body + tip


def socket_at(yc, zc, w=None, depth=None, x_mouth=None, lead=LEAD_IN):
    """The matching socket, open at x = x_mouth (default the joint plane), 0.2 mm deeper than the tenon is long, with a 45 degree lead-in at its mouth."""
    w = SOCKET if w is None else w
    depth = TENON_L + 0.2 if depth is None else depth
    x_mouth = JOINT_X if x_mouth is None else x_mouth
    bore = box(x_mouth - depth, x_mouth - lead, yc - w / 2, yc + w / 2, zc - w / 2, zc + w / 2)
    flare = hull([box(x_mouth - lead - 0.02, x_mouth - lead, yc - w / 2, yc + w / 2, zc - w / 2, zc + w / 2),
                  box(x_mouth, x_mouth + 0.02, yc - w / 2 - lead, yc + w / 2 + lead, zc - w / 2 - lead, zc + w / 2 + lead)])
    return bore + flare + box(x_mouth, x_mouth + 1.0, yc - w / 2 - lead, yc + w / 2 + lead, zc - w / 2 - lead, zc + w / 2 + lead)


AXES = (0, 90, 180, 270)                    # +y, +z, -y, -z


def base_frame():
    """The base's bars: end ring and four plain stubs with tenons. Also what the joint test is cut from."""
    h = ring(*RING_BASE) + stubs(JOINT_X, RING_BASE[0])
    for sy, sz in corners():                                                    # tenons into the cap's sockets
        h = h + tenon_at(sy * JC, sz * JC)
    return h


def spider():
    """The motor mount, in the ring's own slab (x 17..22): a hub ring, four arms on the y and z axes that widen into the ring bars, and four pads, 1.5 mm proud of
    the slab's inner face, where the unit's feet land. Everything rises straight from the bed, so nothing overhangs."""
    x0, x1 = RING_BASE
    arm = box(x0, x1, HUB_R1 - 1.0, H - S + 0.5, -ARM_W / 2, ARM_W / 2)
    flare = hull([box(x0, x1, ARM_FLARE_R, ARM_FLARE_R + 0.02, -ARM_W / 2, ARM_W / 2), box(x0, x1, H - S, H - S + 0.5, -ARM_ROOT_W / 2, ARM_ROOT_W / 2)])
    pad = obround(2 * FOOT_PAD_R, *SLOT_R, PAD_X, x0 + 0.01)
    return ann(HUB_R0, HUB_R1, x0, x1) + diag(arm + flare + pad, AXES)


def screw_pocket(flat_roof=False):
    """One mount-screw opening, built along +y: the head pocket on the outside face (the bed face), its roof narrowing at OVERHANG to the radial slot the screw's
    shank passes through. flat_roof=True is a plain counterbore with a flat ceiling: the overhang check's negative control."""
    head = obround(POCKET_W, *SLOT_R, X_TAPER0 - 0.01, HX + 1.0)
    if flat_roof:
        return head + obround(SLOT_W, *SLOT_R, PAD_X - 1.0, X_TAPER0)
    roof = hull([cx(POCKET_W / 2, X_TAPER0 - 0.02, X_TAPER0, r, 0.0, 32) for r in SLOT_R] + [cx(SLOT_W / 2, X_TAPER1, X_TAPER1 + 0.02, r, 0.0, 32) for r in SLOT_R])
    return head + roof + obround(SLOT_W, *SLOT_R, PAD_X - 1.0, X_TAPER1 + 0.03)


def base(flat_roof=False):
    h = base_frame() + spider()
    # IMU pad at the pivot corner (that corner lies on the vertical diagonal, so it only moves the centre of mass up or down). Small trim pads at the two
    # corners across it, which are the ones that can move the centre of mass sideways.
    h = h + corner_pad(PIVOT[0], PIVOT[1], 'imu') + corner_pad(PIVOT[0], -PIVOT[1], 'trim') + corner_pad(-PIVOT[0], PIVOT[1], 'trim')
    h = h - diag(screw_pocket(flat_roof), AXES)
    return h - x_edge_cutters()


def cap():
    h = ring(*RING_CAP)
    x0 = RING_CAP[1]                                                            # the ring's inner face, x = -17
    x1 = x0 + COLLAR_RUN / TAN_OV                                               # the collar has widened to 8 x 8 here (3.8 mm later)
    for sy, sz in corners():
        a = box(x0 - 0.5, x0, *sr(sy, H - S, H), *sr(sz, H - S, H))
        b = box(x1, x1 + 0.02, *sr(sy, H - COLLAR, H), *sr(sz, H - COLLAR, H))
        h = h + hull([a, b]) + box(x1, JOINT_X, *sr(sy, H - COLLAR, H), *sr(sz, H - COLLAR, H))
    for sy, sz in corners():                                                    # sockets for the base's tenons, open at the joint plane
        h = h - socket_at(sy * JC, sz * JC)
    return h - x_edge_cutters()


# ---------------------------------------------------------------- wheel: local frame z = spin axis, z = 0 on the outside of the floor (the bed face when printed), growing towards the motor
def trim_xy():
    return [(TRIM_R * math.cos(math.radians(22.5 + 45 * i)), TRIM_R * math.sin(math.radians(22.5 + 45 * i))) for i in range(N_BOLT)]


def rotor_xy():
    return [(ROTOR_PCD / 2 * math.cos(math.radians(90 * k)), ROTOR_PCD / 2 * math.sin(math.radians(90 * k))) for k in range(4)]


def wheel(rim_l=RIM_L):
    """A cup over the rotor end. The floor bolts to the rotor face; the inner wall goes over the spinning can as far as the fixed stator base; the rim lies
    alongside the motor and stops RIM_SETBACK before its back face. The weight bolts go in from the rim's back end, heads in counterbores, tips level with the
    front. Every wall is vertical in print and every hole opens upward or goes straight through, so nothing overhangs."""
    floor = W3.cyl(0, 0, WD, 0, FLOOR_T)
    wall = W3.cyl(0, 0, CUP_BORE + 2 * CUP_WALL, FLOOR_T - 0.01, FLOOR_T + CUP_L) - W3.cyl(0, 0, CUP_BORE, FLOOR_T - 0.1, FLOOR_T + CUP_L + 1)
    rim = W3.cyl(0, 0, WD, FLOOR_T - 0.01, rim_l) - W3.cyl(0, 0, 2 * RIM_R0, FLOOR_T - 0.1, rim_l + 1)
    body = union([floor, wall, rim])
    cuts = [W3.cyl(0, 0, PIN_HOLE, -1, FLOOR_T + 1),                            # centre hole, for the removable alignment pin
            W3.cyl(0, 0, RELIEF_D, FLOOR_T - RELIEF_H, FLOOR_T + 1)]            # relief round it, on the face that meets the rotor
    for x, y in rotor_xy():                                                     # 4 x M2.5 on the rotor face's D16 cross, button heads on the outside
        cuts.append(W3.cyl(x, y, M25 + 0.2, -1, FLOOR_T + 1))
    for x, y in trim_xy():                                                      # M4 weight bolts: plain through holes, counterbored from the back end
        cuts.append(W3.cyl(x, y, BOLT_HOLE, -1, rim_l + 1))
        cuts.append(W3.cyl(x, y, CBORE_D, rim_l - CBORE_H, rim_l + 1))
    return body - union(cuts)


def pin():
    return W3.cyl(0, 0, PIN_D, 0.5, PIN_L)                                       # alignment jig, not part of the module: through the floor hole and 9.5 mm into the motor's bore


def place_wheel(m):
    """Local (X, Y, Z) -> module: x = MOT_X0 - FLOOR_T + Z, y = X, z = Y (a proper rotation)."""
    return m.transform(np.array([[0, 0, 1, MOT_X0 - FLOOR_T], [1, 0, 0, 0], [0, 1, 0, 0]], float))


# ---------------------------------------------------------------- bought parts as envelopes
def motor():
    body = cx(MOTOR_D / 2, MOT_X0, STATOR_X, 0, 0, 96) + cx(HUB_D / 2, STATOR_X - 0.1, STATOR_X + HUB_L, 0, 0, 64)
    return body - cx(MOTOR_BORE / 2, MOT_X0 - 1, STATOR_X + HUB_L + 1, 0, 0, 48)


def on_board(bx, by):
    """A point given in the board's own axes (its connectors on +-bx, its centre slots on +-by) -> (y, z). The board is turned BOARD_ROT about the wheel axis:
    +bx points at the pivot corner, and the corner slots, with the feet in them, land on the frame's y and z axes."""
    a = math.radians(BOARD_ROT)
    return bx * math.cos(a) - by * math.sin(a), bx * math.sin(a) + by * math.cos(a)


def board_outline(x0, x1):
    """The board as drawn: four R4.5 lobes on a 24 mm square, joined, with the four sides hollowed at R25.6 (33 across the lobes, 28 across the waist)."""
    body = hull([cx(ENC_LOBE_R, x0, x1, sy * ENC_SLOT, sz * ENC_SLOT, 48) for sy, sz in corners()])
    d = ENC_SLOT + math.sqrt((ENC_SIDE_R + ENC_LOBE_R) ** 2 - ENC_SLOT ** 2)
    return body - union([cx(ENC_SIDE_R, x0 - 1, x1 + 1, y, z, 128) for y, z in ((d, 0), (-d, 0), (0, d), (0, -d))])


def enc_board():
    """The AS5600 board: its outline, the chip on the motor side, the two connectors on the back (envelopes)."""
    chip = box(BOARD_X0 - CHIP[2], BOARD_X0, -CHIP[0] / 2, CHIP[0] / 2, -CHIP[1] / 2, CHIP[1] / 2)
    conns = [box(BOARD_X1, BOARD_X1 + CONN_H, lo, hi, -CONN_BY, CONN_BY) for lo, hi in (CONN_BX, (-CONN_BX[1], -CONN_BX[0]))]
    return (board_outline(BOARD_X0, BOARD_X1) + chip + union(conns)).rotate((BOARD_ROT, 0, 0))


def plug():
    """Keep-out for the encoder plug and its cable: the plug goes into the connector that faces the pivot corner, from the side, and the cable is drawn running
    straight on towards that corner."""
    return box(BOARD_X1 + 0.2, BOARD_X1 + CONN_H, CONN_BX[1], WIRE_REACH, -5.5, 5.5).rotate((BOARD_ROT, 0, 0))


def leads():
    """Keep-out for the motor's three leads: they lie on the back face and are drawn running straight out from it, along -y (one of the two lower arms at
    balance), as far as the ring bar."""
    return box(STATOR_X, STATOR_X + LEAD_T, 7.0, WIRE_REACH, -LEAD_W / 2, LEAD_W / 2).rotate((180, 0, 0))


def kit_hardware():
    """The kit's brass: two centre standoffs from the back face to the board (screw heads on the back of the board), four corner standoffs (the feet) behind the
    board with their nuts and stud ends in front of it. Envelopes, hexes drawn across corners."""
    out = []
    for s in (1, -1):
        y, z = on_board(0.0, s * STATOR_PCD / 2)
        out.append(cx(HEX_D / 2, STATOR_X, BOARD_X0, y, z, 6))
        out.append(cx(2.25, BOARD_X1, BOARD_X1 + 1.7, y, z, 24))
    for sy, sz in corners():
        y, z = on_board(sy * ENC_SLOT, sz * ENC_SLOT)
        out.append(cx(HEX_D / 2, BOARD_X1, PAD_X, y, z, 6))
        out.append(cx(HEX_D / 2, BOARD_X0 - 2.0, BOARD_X0, y, z, 6))
        out.append(cx(M25 / 2, BOARD_X0 - 3.0, BOARD_X0 - 1.9, y, z, 16))
    return union(out)


def block(d):
    if 'u' in d:                                                                # in the gravity-aligned frame (see IMU)
        return tilted(*d['x'], *d['u'], *d['s'])
    return box(*d['x'], *d['y'], *d['z'])


def bolt_meshes():
    """The eight M4 x 12 weight bolts: shank through the rim, socket head (D7 x 4) in its counterbore at the back end."""
    z1 = RIM_L - CBORE_H
    return [place_wheel(W3.cyl(X, Y, 4.0, z1 - BOLT_L, z1) + W3.cyl(X, Y, 7.0, z1, z1 + 4.0)) for X, Y in trim_xy()]


def rotor_screws():
    """The four M2.5 x 5 button-head screws: heads on the floor's outside face."""
    return union([place_wheel(W3.cyl(X, Y, SCREW_HEAD_D, -HEAD_H, 0.0) + W3.cyl(X, Y, 2.5, 0.0, 5.0)) for X, Y in rotor_xy()])


def mount_screws(r=FOOT_R1):
    """The four M2.5 x 8 button-head screws that go in from the outside face into the feet. Their heads stop on the pockets' roofs."""
    xs = X_SEAT + 0.01
    return union([cx(SCREW_HEAD_D / 2, xs, xs + HEAD_H, r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), 24) +
                  cx(M25 / 2, xs - SCREW_L, xs, r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), 24) for a in AXES])


# ---------------------------------------------------------------- fit test coupon
FIT_CLEARANCES = (0.00, 0.05, 0.10, 0.15, 0.20)      # per side, sockets 1..5
FIT_PINS = (6.1, 6.2, 6.3, 6.4)                      # pin diameters 1..4, to try in the motor's real hollow shaft


def fit_test():
    """All three coupon pieces in one file, side by side."""
    blk, pegs, pins = fit_test_parts()
    return blk + pegs.translate((0, 28.0, 0)) + pins.translate((0, 46.0, 0))


def fit_test_parts():
    """Graded fit coupon, printed as built (z up, nothing overhangs). Three separate pieces, returned as (sockets, peg, pins):
    a block with five square sockets for the tenon peg, at 0.00 to 0.20 mm clearance per side (1 to 5 dots);
    a base with one tenon peg (the real 3.4 mm tenon, same lead-in);
    four headed pins, D6.1 to D6.4 (1 to 4 dots), to try in the motor's hollow shaft (D6.4 was chosen)."""
    pitch, hb, lead = 13.0, 9.0, LEAD_IN
    blk = box(0, pitch * len(FIT_CLEARANCES), 0, 22.0, 0, hb)
    for i, c in enumerate(FIT_CLEARANCES):
        xc, yc, w = pitch * (i + 0.5), 7.0, TENON + 2 * c
        bore = box(xc - w / 2, xc + w / 2, yc - w / 2, yc + w / 2, hb - (TENON_L + 0.2), hb - lead)
        flare = hull([box(xc - w / 2, xc + w / 2, yc - w / 2, yc + w / 2, hb - lead - 0.02, hb - lead),
                      box(xc - w / 2 - lead, xc + w / 2 + lead, yc - w / 2 - lead, yc + w / 2 + lead, hb, hb + 0.02)])
        top = box(xc - w / 2 - lead, xc + w / 2 + lead, yc - w / 2 - lead, yc + w / 2 + lead, hb, hb + 1.0)
        blk = blk - (bore + flare + top)
        for k in range(i + 1):                                                   # i + 1 dots near the front edge say which socket this is
            blk = blk - W3.cyl(xc - 1.5 * i + 3.0 * k, 17.0, 1.2, hb - 0.8, hb + 1.0)
    # the tenon peg stands on a flat handle: hold the handle, push the peg into a socket, pull it back out. 40 x 12 x 3.5 mm, with the peg at one end.
    pw, hz = TENON, 3.5
    pegs = box(0, 40.0, 0, 12.0, 0, hz)
    pegs = pegs + box(6.0 - pw / 2, 6.0 + pw / 2, 6.0 - pw / 2, 6.0 + pw / 2, hz - 0.1, hz + TENON_L - lead)
    pegs = pegs + hull([box(6.0 - pw / 2, 6.0 + pw / 2, 6.0 - pw / 2, 6.0 + pw / 2, hz + TENON_L - lead - 0.02, hz + TENON_L - lead),
                        box(6.0 - pw / 2 + lead, 6.0 + pw / 2 - lead, 6.0 - pw / 2 + lead, 6.0 + pw / 2 - lead, hz + TENON_L, hz + TENON_L + 0.02)])
    # each pin has its own round D12 head to hold it by (and to stop it going in too far); dots on the head say which diameter it is
    pins = None
    for j, d in enumerate(FIT_PINS):
        xc, yc, hh = 8.0 + 16.0 * j, 6.0, 3.0
        one = W3.cyl(xc, yc, 12.0, 0, hh) + W3.cyl(xc, yc, d, hh - 0.1, hh + PIN_L - lead)
        one = one + m3.Manifold.cylinder(lead, d / 2, d / 2 - lead, 48).translate((xc, yc, hh + PIN_L - lead))
        for k in range(j + 1):
            a = math.radians(360.0 * k / (j + 1) + 45.0)
            one = one - W3.cyl(xc + 4.7 * math.cos(a), yc + 4.7 * math.sin(a), 1.0, hh - 0.8, hh + 0.5)
        pins = one if pins is None else pins + one
    return blk, pegs, pins


# ---------------------------------------------------------------- mesh helpers
def tris(m):
    me = m.to_mesh()
    v = np.asarray(me.vert_properties, np.float64)[:, :3]
    return v[np.asarray(me.tri_verts, np.int64)]


def moments(T_):
    a, b, c = T_[:, 0], T_[:, 1], T_[:, 2]
    v6 = np.einsum('ij,ij->i', a, np.cross(b, c))
    s = a + b + c
    V = v6.sum() / 6
    S1 = (v6[:, None] / 24 * s).sum(0)
    q = (v6[:, None] / 120 * ((a ** 2 + b ** 2 + c ** 2) + s ** 2)).sum(0)
    return V, S1, q


def body_props(m, mass_g, y0, z0):
    """Mass (kg), centroid (x, y, z in mm) and inertia (kg m^2) about the axis parallel to x through (y0, z0), for a mesh given its real mass."""
    V, S1, q = moments(tris(m))
    rho = mass_g * 1e-3 / V
    j = rho * ((q[1] + q[2]) - 2 * y0 * S1[1] - 2 * z0 * S1[2] + (y0 ** 2 + z0 ** 2) * V) * 1e-6
    return mass_g * 1e-3, S1 / V, j


def check(m, name):
    assert m.status() == m3.Error.NoError and not m.is_empty(), name
    bb = np.asarray(m.bounding_box())
    print(f'{name:22s} {m.volume() / 1000:6.1f} cm3  solid {m.volume() * RHO:6.1f} g   '
          f'x {bb[0]:6.1f}..{bb[3]:6.1f}  y {bb[1]:6.1f}..{bb[4]:6.1f}  z {bb[2]:6.1f}..{bb[5]:6.1f}')


def main():
    hb, hc = base(), cap()
    wl = wheel()
    wp = place_wheel(wl)
    mot, enc, hw, imu, teth, plg, lds = motor(), enc_board(), kit_hardware(), block(IMU), block(TETHER), plug(), leads()
    bolts, rs, ms = bolt_meshes(), rotor_screws(), mount_screws()
    print('--- printed parts')
    for n, m in (('Frame_Base', hb), ('Frame_Cap', hc), ('Wheel_D74_2804', wp)):
        check(m, n)
    bb = np.asarray(union([hb, hc, wp, mot, enc, hw, imu, teth, rs, ms, plg, lds] + bolts).bounding_box())
    print(f'envelope of everything: x {bb[0]:.1f}..{bb[3]:.1f}, y {bb[1]:.1f}..{bb[4]:.1f}, z {bb[2]:.1f}..{bb[5]:.1f}   (box {A:.0f} x {A:.0f} x {D:.0f}: nothing may exceed +-{H:.0f}, +-{HX:.0f})')
    x_floor = MOT_X0 - FLOOR_T
    print(f'stack: rotor screw heads {x_floor - HEAD_H:.1f} | floor {x_floor:.1f}..{MOT_X0:.1f} | can to {MOT_X0 + CAN_L:.1f} | back face {STATOR_X:.1f} | magnet ring to {STATOR_X + HUB_L:.1f} | '
          f'board {BOARD_X0:.1f}..{BOARD_X1:.1f} (chip to ring air gap {KIT_GAP - HUB_L - CHIP[2]:.1f}), connectors to {BOARD_X1 + CONN_H:.1f} | feet to {PAD_X:.1f} | slab {RING_BASE[0]:.0f}..{RING_BASE[1]:.0f} | '
          f'rim {x_floor:.1f}..{x_floor + RIM_L:.1f}')
    print(f'mount screws: head seat at x {X_SEAT:.2f}, head top {X_SEAT + HEAD_H:.2f} ({HX - X_SEAT - HEAD_H:.2f} under the outside face); M2.5 x {SCREW_L:.0f} has {X_SEAT - PAD_X:.2f} mm in the base '
          f'and {SCREW_L - (X_SEAT - PAD_X):.2f} mm in the foot; pocket roof {math.degrees(math.atan((POCKET_W - SLOT_W) / 2 / (X_TAPER0 - X_TAPER1))):.0f} degrees from vertical')

    solids = {'base': hb, 'cap': hc, 'wheel': wp, 'motor': mot, 'board': enc, 'kit brass': hw, 'imu': imu, 'tether': teth,
              'weight bolts': union(bolts), 'rotor screws': rs, 'mount screws': ms, 'plug + cable': plg, 'motor leads': lds}
    names = list(solids)
    threaded = {('wheel', 'weight bolts'), ('motor', 'rotor screws'), ('kit brass', 'mount screws')}   # a screw in the part it threads into: overlap expected
    worst, eng = [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            v = (solids[names[i]] ^ solids[names[j]]).volume()
            if abs(v) > 0.01:
                (eng if (names[i], names[j]) in threaded else worst).append((names[i], names[j], v))
    print(f'--- static fits, {len(names)} parts: ' + ('every pair 0 mm3' if not worst else '; '.join(f'{a} x {b}: {v:.2f}' for a, b, v in worst)) +
          '   (threads, expected: ' + ', '.join(f'{a} x {b} {v:.0f}' for a, b, v in eng) + ')')

    y0, z0 = PIVOT[0] * H, PIVOT[1] * H
    items = [('base (printed)', hb, FILL_FRAME * RHO, 'vol'), ('cap (printed)', hc, FILL_FRAME * RHO, 'vol'), ('wheel (printed)', wp, FILL_WHEEL * RHO, 'vol'),
             ('motor + leads', mot, MOTOR_G, 'g'), ('encoder board', enc, ENC_G - KIT_HW_G, 'g'), ('kit standoffs, nuts, screws', hw, KIT_HW_G, 'g'),
             ('M2.5 rotor + mount screws', rs + ms, 8 * 0.35, 'g'), ('IMU board', imu, IMU_G, 'g'), ('cable dragged by the IMU', teth, TETHER_G, 'g')]
    rows = []
    for nm, m, v, kind in items:
        rows.append((nm, *body_props(m, v * m.volume() if kind == 'vol' else v, y0, z0)))
    for k, b in enumerate(bolts):
        rows.append((f'bolt {k + 1}', *body_props(b, BOLT_G, y0, z0)))
    M = sum(r[1] for r in rows)
    C = sum(r[1] * r[2] for r in rows) / M
    d = np.array([C[1] - y0, C[2] - z0])
    u = np.array([-PIVOT[0], -PIVOT[1]]) / math.sqrt(2)
    w = np.array([-PIVOT[1], PIVOT[0]]) / math.sqrt(2)
    l, e = float(d @ u) * 1e-3, float(d @ w) * 1e-3
    Jt = sum(r[3] for r in rows)
    side_arm = 0.0445                                                              # a small trim pad (centre at 31.5, 31.5) is 44.5 mm to the side of the vertical
    trim_g = abs(e) * M / side_arm * 1e3
    Vw, Sw, qw = moments(tris(wl))
    jw_print = RHO * FILL_WHEEL * (qw[0] + qw[1]) * 1e-9
    pr = TRIM_R * 1e-3
    Jw = jw_print + N_BOLT * BOLT_G * 1e-3 * pr ** 2 + ROTOR_G * 1e-3 * 0.0145 ** 2
    J1 = Jt - Jw
    Mgl = M * 9.81 * l
    print('--- mass and balance about the pivot edge')
    for nm, mg, c, j in rows:
        if nm.startswith('bolt'):
            continue
        print(f'  {nm:26s} {mg * 1e3:6.1f} g   centre x {c[0]:6.1f} y {c[1]:6.1f} z {c[2]:6.1f}   J {j:.2e}')
    print(f'  8 bolts                    {N_BOLT * BOLT_G:6.1f} g')
    print(f'  total M = {M * 1e3:.0f} g, centre of mass above the edge l = {l * 1e3:.1f} mm, sideways offset e = {e * 1e3:+.2f} mm '
          f'(balance point shifted {math.degrees(math.atan2(e, l)):+.2f} deg)')
    print(f'  trim: 1 g on a side pad moves e by {1e-3 * side_arm / M * 1e3:.2f} mm ({math.degrees(math.atan2(1e-3 * side_arm / M, l)):.2f} deg); to zero the modelled offset: {trim_g:.2f} g')
    print(f'  Mgl = {Mgl:.3f} N m, J1 = {J1:.3e}, Jt = {Jt:.3e}, Jw = {Jw:.3e} kg m2 (wheel {jw_print:.2e}, bolts {N_BOLT * BOLT_G * 1e-3 * pr ** 2:.2e}, rotor {ROTOR_G * 1e-3 * 0.0145 ** 2:.2e})')

    sys.path.insert(0, str(HERE.parent / 'analysis'))
    import cube_sim as sim
    p = dict(M=M, l=l, Mgl=Mgl, J1=J1, Jw=Jw)
    print('--- simulated recovery (ideal sensing, torque limit and back-EMF derating at 12 V)')
    for tau in (0.045, 0.030, 0.020):
        lean, wpk = sim.max_lean(p, tau)
        print(f'  torque limit {tau:.3f} N m (torque/Mgl {tau / Mgl:.2f}): recovers from {lean:.1f} deg, wheel peak {wpk:.0f} rad/s')

    for n, m in (('Frame_Base', hb), ('Frame_Cap', hc), ('Wheel_D74_2804', wp)):
        F.write_stl(HERE / f'{n}.stl', m)
    parts = {'base': (hb, '#e6dcc4'), 'cap': (hc, '#e6dcc4'), 'wheel': (wp, '#d9902f'), 'bolts': (union(bolts) + rs, '#8d9aa3'),
             'motor': (mot, '#b23a2e'), 'board': (enc, '#1f5fa8'), 'hw': (hw, '#c9a227'), 'screws': (ms, '#8d9aa3'), 'imu': (imu, '#222222'), 'wires': (plg + lds, '#7a7a7a')}
    out = {'parts': {n: {'color': c, 'positions_b64': base64.b64encode(tris(m).astype(np.float32).tobytes()).decode()} for n, (m, c) in parts.items()}}
    (HERE / 'viewer_data.json').write_text(json.dumps(out))
    json.dump(dict(M_kg=M, l_m=l, e_m=e, Mgl=Mgl, J1=J1, Jw=Jw, Jt=Jt, trim_g=trim_g, centroid_mm=[float(c) for c in C]), open(HERE / 'cad_numbers.json', 'w'))
    print('wrote', HERE)


if __name__ == '__main__':
    main()
