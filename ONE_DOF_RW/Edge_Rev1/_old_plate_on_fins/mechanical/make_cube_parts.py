"""Balancing wheel module: a thin 90 x 90 x 44 mm frame that stands on one edge, with the 2804 motor and a D74 wheel inside and nothing else on board but
the IMU. The ESP32, motor driver and power supply stay off the body on a light cable.

    python make_cube_parts.py        # needs numpy + manifold3d (the toolchain of ONE_DOF_RW/String_Rev3 and SWINGUP_RWP)

Every surface that faces down in the print orientation is designed to lean no more than OVERHANG degrees from vertical (the limit asked for is 40), so the
parts print without supports. A flat ceiling would be 90 degrees. To get there the module is four printed parts:

  Frame_Base.stl   +x end ring, four corner stubs ending in tenons, four fins on the ring bars (on the y and z axes) with pegs, IMU pad and two trim pads.
                   Ring face (x = 22) down.
  Motor_Plate.stl  a flat cross on the y and z axes with a ring round the middle. The motor + encoder unit's four corner standoffs (its feet, as the kit comes)
                   stand on its front face and four M2.5 screws go in from behind, through slots, into them. The arm ends glue onto the base's fins, whose pegs
                   pass through square holes in the arms. Front face (x = 13.6) down.
  Frame_Cap.stl    -x end ring with four tapered collars carrying the sockets. Ring face (x = -22) down.
  Wheel_D74_2804.stl  a cup over the rotor end of the motor: the floor bolts to the rotor face (4 x M2.5 on D16), a thin inner wall hugs the spinning can,
                   and the rim (r 30..37) runs back along the motor with eight M4 weight bolts in its far end. Floor (outside face) down.
  (No pin is printed. The floor keeps its D6.5 centre hole; a D6.4 pin, such as the headed one on Fit_Test_Pins, can be pushed through it into the motor's bore as
   a removable alignment jig while the four M2.5 screws are tightened, then pulled out. pin() below is that jig, used by the checks only.)

The motor and encoder are one bought unit, used as the kit comes (listing B0FSZ7XWG2): two brass standoffs hold the AS5600 board off the motor's wire end, on two of
its D19 holes, and four more brass standoffs, nutted into the board's corner slots, stick out of the back of the board. Those four are the unit's feet. The frame
does not use the motor's own holes.

Frame axes: centre at the origin, x = the wheel axis = the pivot edge direction (the depth, 44 mm), (y, z) the 90 x 90 cross-section. The module stands on the
edge at (y, z) = (-45, +45). The four edges parallel to x are rounded R1.5 so it rolls; the edges around the end faces stay sharp, which keeps the bed face clean.

Stack along x: rotor screw heads -21 | wheel floor -19.5..-17 | motor: rotor face -17, can to -6, wire end -2, magnet boss to 2.5 | board 5.0..6.6 |
feet 6.6..13.6 | plate 13.6..17 (19 inside the ring) | end ring 17..22. The wheel's rim runs from -19.5 to 6.5, its bolt heads to 10.5.
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
REV3 = HERE.parent.parent.parent / 'String_Rev3' / 'mechanical'   # this folder is ONE_DOF_RW/Edge_Rev1/_old_plate_on_fins/mechanical


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
# ---------------------------------------------------------------- motor + AS5600 encoder unit, as the kit comes (Amazon.ca B0FSZ7XWG2: the listing's drawings and photos)
MOTOR_D, MOTOR_BORE, BODY, CAN_L = 34.5, 6.5, 15.0, 11.0   # the first 11 mm from the rotor face is the spinning can; the last 4 mm, where the leads leave, is the fixed stator base
HUB_D, HUB_L = 12.0, 4.5                   # the magnet boss on the wire end (19.5 overall - 15 body)
ROTOR_PCD, STATOR_PCD, M25 = 16.0, 19.0, 2.5   # rotor face: 4 x M2.5 on D16 at 0/90/180/270, 3 mm deep at most. Wire end: 4 x M2.5 on D19 at 45 degrees, 4 mm deep at most
ENC_W, ENC_T = 33.0, 1.6                   # the AS5600 board: 33 x 33, four slotted corner lobes, two short slots on its centre line (thickness ASSUMED)
KIT_GAP = 7.0                              # ASSUMED: the kit's two centre standoffs hold the board's chip side this far from the wire end (hub 4.5 + chip 1.5 + about 1 mm of air)
KIT_FOOT = 7.0                             # ASSUMED from the 7 mm on the board drawing: the four corner standoffs on the back of the board, the unit's feet
FOOT_R1 = 12.0 * math.sqrt(2)              # 16.97: the outer ends of the board's corner slots, 24 mm apart (the drawing's 24). The feet sit there, out towards the corners
SLOT_R = (15.5, 17.5)                      # the plate's screw slots: about 1 mm of play either way round that 24 mm square
HEX_D = 5.8                                # M2.5 brass standoff and nut, 5 mm across flats, 5.8 across corners
MOTOR_G, ROTOR_G, ENC_G = 40.0, 22.0, 8.0  # motor with leads; its spinning part; board + six brass standoffs + four nuts + two screws (ASSUMED)
KIT_HW_G = 5.0                             # of which the brass and screws (ASSUMED)
# ---------------------------------------------------------------- motor plate: a flat cross the unit's feet screw to from behind
SLAB_X1 = RING_BASE[0]                     # 17: the arms' back face, glued against the base ring and its fins
SLAB_X0 = 13.6                             # the plate's front face, where the feet land (the bed face when printed)
SLAB_RIB, SLAB_RIB_R = 2.0, 32.5           # inside the ring the arms and the middle ring are 2 mm thicker (x 17..19), out to r = 32.5
ARM_W, ARM_R0, ARM_R1 = 9.0, 13.0, 44.0    # four arms on the y and z axes; they start at r 13 so the middle stays open for the board's connectors (clear even at 7.5 mm tall) and cable
MID_R0, MID_R1 = 19.0, 25.0                # the ring that joins the arms, outside the connectors (r < 15.2) and inside the IMU (r > 27)
FIN_R0, FIN_W = 34.0, 8.0                  # four fins on the base ring's bars, on the axes, r 34..40, x 17..22
PEG_R = 37.0                               # the fins' pegs, the same 3.4 mm tenon, 3.4 long: through square holes in the arms, tips flush with the plate's front face
# stack along x, from the plate forwards
BOARD_X1 = SLAB_X0 - KIT_FOOT              # 6.6: back of the board
BOARD_X0 = BOARD_X1 - ENC_T                # 5.0: chip side
STATOR_X = BOARD_X0 - KIT_GAP              # -2.0: the motor's wire end
MOT_X0 = STATOR_X - BODY                   # -17.0: rotor face, where the wheel mounts
# ---------------------------------------------------------------- wheel: a cup over the rotor end
WD = 74.0                                  # outside diameter, as before: 3 mm from the cap ring's bars
FLOOR_T = 2.5                              # M2.5 x 5 button heads then engage 2.5 mm in the rotor, under the drawing's 3 mm
HEAD_H = 1.5                               # those heads stand proud of the floor's outside face (ISO 7380 M2.5)
CUP_BORE, CUP_WALL, CUP_L = 34.8, 1.6, 10.0   # the inner wall: 0.15 mm per side over the D34.5 can; it stops 1 mm short of the fixed stator base
RIM_R0, RIM_L = 30.0, 26.0                 # the rim, r 30..37, 26 mm long from the floor's outside face
TRIM_R, TRIM_DEPTH = 33.5, 12.5            # eight M4 holes in the rim's far end
N_BOLT, BOLT_G = 8, 2.3                    # M4 x 12 socket head, 2.3 g
THREAD_DEPTH = 0.25                        # drawn thread depth: 0.25 over a 0.35 flank is 35.5 degrees from vertical (rev3 used 0.38, 47 degrees); the hole is then 3.3, the M4 tap drill
PIN_D, PIN_L = 6.4, 12.0                   # removable alignment pin diameter: all of D6.1..6.4 from Fit_Test_Pins fitted, so the largest (least play) is used. Length 12 (2.5 through the floor + 9.5 into the motor)
PIN_HOLE = PIN_D + 0.1                     # the floor hole for it: 0.05 mm per side, the same slide fit as the tenons
W3.M4_MINOR = W3.M4_MAJOR - 2 * THREAD_DEPTH
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


def pcd_holes(pcd, d, x0, x1, a0):
    return union([cx(d / 2 + 0.1, x0, x1, pcd / 2 * math.cos(math.radians(a0 + 90 * k)), pcd / 2 * math.sin(math.radians(a0 + 90 * k)), 24) for k in range(4)])


def diag(m, angles=(45, 135, 225, 315)):
    """Copies of a part built along +y, turned about x to each corner direction."""
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


def fins():
    """Four fins in the ring's plane (x 17..22), one on the middle of each bar, reaching in from the bar (r 40) to r = 34. The plate's arm ends glue to their face."""
    return diag(box(SLAB_X1, HX, FIN_R0, H - S + 0.5, -FIN_W / 2, FIN_W / 2), AXES)


def base_frame():
    """The base's bars: end ring, four plain stubs with tenons, the fins. Also what the joint test is cut from."""
    h = ring(*RING_BASE) + stubs(JOINT_X, RING_BASE[0]) + fins()
    for sy, sz in corners():                                                    # tenons into the cap's sockets
        h = h + tenon_at(sy * JC, sz * JC)
    return h


def fin_pegs():
    """Four square pegs on the fins' faces (x = 17), pointing -x through square holes in the plate's arms: the same 3.4 mm tenon and 0.4 mm lead-in as the frame
    joints, 3.4 long so the tips end flush with the plate's front face. They stand up when the base prints ring face down."""
    return diag(tenon_at(PEG_R, 0.0, length=SLAB_X1 - SLAB_X0, x_end=SLAB_X1), AXES)


def base():
    h = base_frame() + fin_pegs()
    # IMU pad at the pivot corner (that corner lies on the vertical diagonal, so it only moves the centre of mass up or down). Small trim pads at the two
    # corners across it, which are the ones that can move the centre of mass sideways.
    h = h + corner_pad(PIVOT[0], PIVOT[1], 'imu') + corner_pad(PIVOT[0], -PIVOT[1], 'trim') + corner_pad(-PIVOT[0], PIVOT[1], 'trim')
    return h - x_edge_cutters()


def ann(r0, r1, x0, x1, seg=128):
    outer = cx(r1, x0, x1, 0, 0, seg)
    return outer if r0 <= 0 else outer - cx(r0, x0 - 1, x1 + 1, 0, 0, seg)


def plate():
    """The motor plate: four arms on the y and z axes (x 13.6..17, 2 mm thicker inside the ring) joined by a ring at r 19..25. The unit's four feet land on the arms'
    front face; four M2.5 x 8 screws go in from behind through short slots (r 15.5..17.5, round the board's 24 mm square) into the feet. The arm ends glue onto
    the base's fins with the fins' pegs through square holes. The middle is open: the board's connectors stand there and its cable leaves through it."""
    arm = box(SLAB_X0, SLAB_X1, ARM_R0, ARM_R1, -ARM_W / 2, ARM_W / 2) + box(SLAB_X1 - 0.01, SLAB_X1 + SLAB_RIB, ARM_R0, SLAB_RIB_R, -ARM_W / 2, ARM_W / 2)
    h = diag(arm, AXES) + ann(MID_R0, MID_R1, SLAB_X0, SLAB_X1 + SLAB_RIB)
    slot = hull([cx(M25 / 2 + 0.15, SLAB_X0 - 1, SLAB_X1 + SLAB_RIB + 1, r, 0.0, 24) for r in SLOT_R])
    h = h - diag(slot, AXES)
    hole = socket_at(PEG_R, 0.0, depth=SLAB_X1 - SLAB_X0 + 1.0, x_mouth=SLAB_X1)  # straight through, lead-in at the back face where the pegs come in
    return h - diag(hole, AXES)


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


def wheel(threaded=True):
    """A cup over the rotor end. The floor bolts to the rotor face; the inner wall hugs the spinning can (it covers the motor's top and sides as far as the fixed
    stator base); the rim runs back along the motor and takes the weight bolts in its far end. Every hole is vertical in print, so nothing overhangs."""
    floor = W3.cyl(0, 0, WD, 0, FLOOR_T)
    wall = W3.cyl(0, 0, CUP_BORE + 2 * CUP_WALL, FLOOR_T - 0.01, FLOOR_T + CUP_L) - W3.cyl(0, 0, CUP_BORE, FLOOR_T - 0.1, FLOOR_T + CUP_L + 1)
    rim = W3.cyl(0, 0, WD, FLOOR_T - 0.01, RIM_L) - W3.cyl(0, 0, 2 * RIM_R0, FLOOR_T - 0.1, RIM_L + 1)
    body = union([floor, wall, rim])
    cuts = [W3.cyl(0, 0, PIN_HOLE, -1, FLOOR_T + 1)]                            # centre hole, for the removable alignment pin
    for k in range(4):                                                          # 4 x M2.5 on the rotor face's D16 cross, button heads on the outside
        a = math.radians(90 * k)
        cuts.append(W3.cyl(ROTOR_PCD / 2 * math.cos(a), ROTOR_PCD / 2 * math.sin(a), M25 + 0.2, -1, FLOOR_T + 1))
    for x, y in trim_xy():                                                      # M4 weight-bolt holes, blind, opening at the rim's far end
        z0 = RIM_L - TRIM_DEPTH
        cuts.append(W3.thread_cutter(x, y, z0, RIM_L + 0.2, W3.M4_MAJOR - W3.UNDERSIZE) if threaded else W3.cyl(x, y, 3.6, z0, RIM_L + 1))
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
    """A point given in the board's own axes (its connectors on +-bx, its centre slots on +-by) -> (y, z). The board is turned 45 degrees so its corner slots,
    and the feet in them, land on the frame's y and z axes, on the plate's arms."""
    c = math.sqrt(0.5)
    return c * (bx - by), c * (bx + by)


def enc_board():
    """The AS5600 board with its two connectors on the back (envelopes)."""
    plate_ = box(BOARD_X0, BOARD_X1, -ENC_W / 2, ENC_W / 2, -ENC_W / 2, ENC_W / 2).rotate((45, 0, 0))
    conns = [box(BOARD_X1, BOARD_X1 + 6.5, lo, hi, -6.0, 6.0) for lo, hi in ((8.0, 14.0), (-14.0, -8.0))]   # local y, z = the board's own bx, by
    return plate_ + union(conns).rotate((45, 0, 0))                          # PH2.0 4-pin, side entry, about 12 x 6 x 6.5 (ASSUMED), cables leave sideways


def kit_hardware():
    """The kit's brass: two centre standoffs from the wire end to the board (screw heads on the back), four corner standoffs (the feet) behind the board with their
    nuts in front of it. Envelopes, hexes drawn round."""
    out = []
    for s in (1, -1):
        y, z = on_board(0.0, s * STATOR_PCD / 2)
        out.append(cx(HEX_D / 2, STATOR_X, BOARD_X0, y, z, 6))
        out.append(cx(2.25, BOARD_X1, BOARD_X1 + 1.7, y, z, 24))
    for a in AXES:
        y, z = FOOT_R1 * math.cos(math.radians(a)), FOOT_R1 * math.sin(math.radians(a))
        out.append(cx(HEX_D / 2, BOARD_X1, SLAB_X0, y, z, 6))
        out.append(cx(HEX_D / 2, BOARD_X0 - 2.0, BOARD_X0, y, z, 6))
    return union(out)


def block(d):
    if 'u' in d:                                                                # in the gravity-aligned frame (see IMU)
        return tilted(*d['x'], *d['u'], *d['s'])
    return box(*d['x'], *d['y'], *d['z'])


def bolt_meshes():
    """The eight M4 x 12 weight bolts: shank in the rim's far end, socket head (D7 x 4) standing on it."""
    out = []
    for X, Y in trim_xy():
        out.append(place_wheel(W3.cyl(X, Y, 4.0, RIM_L - 12.0, RIM_L) + W3.cyl(X, Y, 7.0, RIM_L, RIM_L + 4.0)))
    return out


def rotor_screws():
    """The four M2.5 x 5 button-head screws: heads on the floor's outside face."""
    out = []
    for k in range(4):
        a = math.radians(90 * k)
        X, Y = ROTOR_PCD / 2 * math.cos(a), ROTOR_PCD / 2 * math.sin(a)
        out.append(place_wheel(W3.cyl(X, Y, 4.7, -HEAD_H, 0.0) + W3.cyl(X, Y, 2.5, 0.0, 5.0)))
    return union(out)


def plate_screws(r=FOOT_R1):
    """The four M2.5 x 8 button-head screws that go in from behind the plate into the feet."""
    xb = SLAB_X1 + SLAB_RIB
    return union([cx(2.35, xb, xb + HEAD_H, r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), 24) +
                  cx(1.25, xb - 8.0, xb, r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), 24) for a in AXES])


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
    hb, hp, hc = base(), plate(), cap()
    wl, wlf = wheel(True), wheel(False)
    wp, wpf = place_wheel(wl), place_wheel(wlf)
    mot, enc, hw, imu, teth = motor(), enc_board(), kit_hardware(), block(IMU), block(TETHER)
    bolts, rs, ps = bolt_meshes(), rotor_screws(), plate_screws()
    print('--- printed parts')
    for n, m in (('Frame_Base', hb), ('Motor_Plate', hp), ('Frame_Cap', hc), ('Wheel_D74_2804', wp)):
        check(m, n)
    bb = np.asarray(union([hb, hp, hc, wpf, mot, enc, hw, imu, teth, rs, ps] + bolts).bounding_box())
    print(f'envelope of everything: x {bb[0]:.1f}..{bb[3]:.1f}, y {bb[1]:.1f}..{bb[4]:.1f}, z {bb[2]:.1f}..{bb[5]:.1f}   (box {A:.0f} x {A:.0f} x {D:.0f}: nothing may exceed +-{H:.0f}, +-{HX:.0f})')
    print(f'stack: rotor screw heads {MOT_X0 - FLOOR_T - HEAD_H:.1f} | floor {MOT_X0 - FLOOR_T:.1f}..{MOT_X0:.1f} | wire end {STATOR_X:.1f} | magnet boss to {STATOR_X + HUB_L:.1f} | '
          f'board {BOARD_X0:.1f}..{BOARD_X1:.1f} (chip-side air gap to the boss about {KIT_GAP - HUB_L - 1.5:.1f}) | feet to {SLAB_X0:.1f} | plate {SLAB_X0:.1f}..{SLAB_X1:.1f}..{SLAB_X1 + SLAB_RIB:.1f} | '
          f'rim end {MOT_X0 - FLOOR_T + RIM_L:.1f}, bolt heads to {MOT_X0 - FLOOR_T + RIM_L + 4:.1f}')

    solids = {'base': hb, 'plate': hp, 'cap': hc, 'wheel': wpf, 'motor': mot, 'board': enc, 'kit brass': hw, 'imu': imu, 'tether': teth,
              'weight bolts': union(bolts), 'rotor screws': rs, 'plate screws': ps}
    names = list(solids)
    threaded = {('wheel', 'weight bolts'), ('motor', 'rotor screws'), ('kit brass', 'plate screws')}   # a screw in the part it threads into: overlap expected
    worst, eng = [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            v = (solids[names[i]] ^ solids[names[j]]).volume()
            if abs(v) > 0.01:
                (eng if (names[i], names[j]) in threaded else worst).append((names[i], names[j], v))
    print(f'--- static fits, {len(names)} parts: ' + ('every pair 0 mm3' if not worst else '; '.join(f'{a} x {b}: {v:.2f}' for a, b, v in worst)) +
          '   (threads, expected: ' + ', '.join(f'{a} x {b} {v:.0f}' for a, b, v in eng) + ')')

    y0, z0 = PIVOT[0] * H, PIVOT[1] * H
    items = [('base (printed)', hb, FILL_FRAME * RHO, 'vol'), ('plate (printed)', hp, FILL_FRAME * RHO, 'vol'), ('cap (printed)', hc, FILL_FRAME * RHO, 'vol'),
             ('wheel (printed)', wp, FILL_WHEEL * RHO, 'vol'),
             ('motor + leads', mot, MOTOR_G, 'g'), ('encoder board', enc, ENC_G - KIT_HW_G, 'g'), ('kit standoffs, nuts, screws', hw, KIT_HW_G, 'g'),
             ('M2.5 rotor + plate screws', rs + ps, 8 * 0.35, 'g'), ('IMU board', imu, IMU_G, 'g'), ('cable dragged by the IMU', teth, TETHER_G, 'g')]
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

    for n, m in (('Frame_Base', hb), ('Motor_Plate', hp), ('Frame_Cap', hc), ('Wheel_D74_2804', wp)):
        F.write_stl(HERE / f'{n}.stl', m)
    parts = {'base': (hb, '#e6dcc4'), 'plate': (hp, '#d6cdb4'), 'cap': (hc, '#e6dcc4'), 'wheel': (wpf, '#d9902f'), 'bolts': (union(bolts) + rs, '#8d9aa3'),
             'motor': (mot, '#b23a2e'), 'board': (enc, '#1f5fa8'), 'hw': (hw + ps, '#c9a227'), 'imu': (imu, '#222222')}
    out = {'parts': {n: {'color': c, 'positions_b64': base64.b64encode(tris(m).astype(np.float32).tobytes()).decode()} for n, (m, c) in parts.items()}}
    (HERE / 'viewer_data.json').write_text(json.dumps(out))
    json.dump(dict(M_kg=M, l_m=l, e_m=e, Mgl=Mgl, J1=J1, Jw=Jw, Jt=Jt, trim_g=trim_g, centroid_mm=[float(c) for c in C]), open(HERE / 'cad_numbers.json', 'w'))
    print('wrote', HERE)


if __name__ == '__main__':
    main()
