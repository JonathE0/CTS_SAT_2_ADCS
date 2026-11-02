"""Printable parts for the rw1dof testbed frame, rev 2 (same layout as the RW1DOF Testbed Frame model).

    python make_frame_parts.py        # needs numpy + manifold3d

Writes parts/*.stl (one part each, in print orientation), plates/*.stl (laid out
for a Prusa CORE One 250 x 220 bed) and assembly_check.stl (everything in place,
for eyeballing fits; don't print it). Units mm. Rev 1 (four truss arms, caps, hook
hub, 9 V holder) is kept in ../../../archive/rev1/frame_parts/.

Rev 3 changes only the pack tray: its screw tabs became L-hooks that latch into the rev 2 baseplate's existing slits, so
the baseplate (base_pillars) is exactly the rev 2 part. Rev 2: one-piece X lid on the pillar tops, two printed lock rods that slide from
pillar to pillar through the lid blocks and pillars, walls 17 mm shorter so they
sit under the rods, rib-lattice walls, a windowed baseplate, and a tray under the
plate for the 12.6 V 3S pack. Fillets and chamfers: flared pillar feet, rounded
vertical edges, chamfered rod holes, a flared and rounded eye, X arms tapered in
plan and depth.

Assembly frame: origin on the spin axis at the baseplate top, +Z up, -X is the
driver wall (the flipped TT motor's plugs face it).
"""
import math
from pathlib import Path

import numpy as np
import manifold3d as m3

OUT = Path(__file__).parent
SEG = 48
BED = (250.0, 220.0)                              # Prusa CORE One
MARGIN, PART_GAP = 10.0, 3.0                      # keep-out from the bed edges, gap between parts

# ---- frame, same numbers as the 3D model ----
PLATE, PLATE_T, H = 160.0, 5.0, 80.0
POCKET = 2.0                                      # motor-case inset and wall-channel depth
PILLAR, PILLAR_H = 10.0, 100.0
C = H - PILLAR / 2                                # 75: pillar centres, wall centre-lines
SPAN = C - PILLAR / 2                             # 70: pillar inner faces
WALL_T, SLOT_D = 3.0, 3.0
R_EDGE = 1.5                                      # vertical edge radius on pillars and the plate corners
FOOT = 2.0                                        # pillar foot flare, per side, over 6 mm of height

# ---- fit clearances, per side. FDM prints holes and slots ~0.1 mm tight. ----
CLR_SLIDE = 0.30      # wall panel in pillar slot and base channel: slides in by hand
CLR_POCKET = 0.25     # lid pocket over the pillar top
CLR_ROD = 0.20        # lock rod in its holes
SLOT_W = WALL_T + 2 * CLR_SLIDE                   # 3.6
WALL_LEN = 2 * SPAN + 2 * (SLOT_D - CLR_SLIDE)    # 145.4: reaches 2.7 mm into each slot
WALL_TOP = 83.0                                   # panels stop 17 mm under the pillar tops, 2 mm under the lid blocks
WALL_H = WALL_TOP + POCKET                        # sits in the channel
WALL_HOLE, WALL_PITCH = 3.3, 10.0                 # M3 grid for standoffs, any board
RIB = 7.0                                         # lightening lattice: ribs on every 3rd hole column and row, M3 holes only on ribs

# ---- lid: flat X on the pillar tops, corner blocks wrap the pillar tops ----
BLK = 18.0                                        # corner block, square
BLK_R = 3.0                                       # its vertical edge radius
SKIRT_Z = 85.0                                    # block bottom: the pocket wraps the top 15 mm of the pillar
LID_T = 10.0                                      # roof and X arms, above the pillar top
LID_TOP = PILLAR_H + LID_T
ARM_DEEP = PILLAR_H - 6.0                         # underside of the arms at the centre; they taper up to the pillar top by 70 mm out
EYE_W, EYE_T, EYE_HOLE = 18.0, 7.0, 7.0           # printed eye on the spin axis, round top, flared foot
EYE_HOLE_Z = LID_TOP + 13.0

# ---- lock rods: printed, 5 mm, along y at x = +-C, through both blocks and both pillars on a side ----
ROD_D, ROD_Z = 5.0, 93.0                          # 7 mm of pillar above the hole, 5 mm of block below it
ROD_HOLE = ROD_D + 2 * CLR_ROD                    # 5.4
ROD_CHAMFER = 0.8                                 # lead-in on every hole mouth
ROD_FREE = 7.0                                    # rod end past the block face, room for the cotter
ROD_LEN = 2 * (C + BLK / 2) + ROD_FREE            # 175, head extra
HEAD_D, HEAD_T = 9.0, 3.0
COTTER_D, COTTER_L = 2.2, 11.0
COTTER_HEAD_D, COTTER_HEAD_T = 5.0, 1.6
COTTER_HOLE = COTTER_D + 0.4
COTTER_X = ROD_FREE / 2                           # cross-hole centre from the free end

# ---- baseplate features ----
# TT case inset (case flipped toward -x), 0.5 mm clearance round the case outline
INSET = [(15.5, -12.9), (-10.25, -12.9), (-10.25, -26.6), (-23.25, -26.6), (-23.25, -12.9), (-55.2, -12.9),
         (-55.2, 12.9), (-23.25, 12.9), (-23.25, 26.6), (-10.25, 26.6), (-10.25, 12.9), (15.5, 12.9)]
CASE_EAR_HOLES = [(-16.77, 19.36), (-16.77, -19.36)]   # measured off the case STL, M3 self-tap
WIRE_HOLE = (-62.0, -24.0, 8.0)
# four lightening windows: leaves a 14 mm rim (wall channels, pillars), a centre web (motor inset), a 10 mm rib,
# and room for the pack tray's slotted screw holes at y = +-36
WIN_X, WIN_Y, WIN_R = (5.0, 66.0), (46.0, 66.0), 6.0

# ---- 12.6 V 3S pack tray under the plate. PACK is the pack's size in x, y, z: MEASURE YOURS and edit this line. ----
PACK = (70.0, 58.0, 21.0)
PACK_CLR, TRAY_WALL, TRAY_FLOOR = 0.5, 2.5, 2.5
R_TRAY = 3.0                                       # fillet: tray outer and closed-end cavity corners
WIRE_D, WIRE_X, WIRE_SIDE = 13.0, 25.0, -1         # wire hole through a side wall: diameter, distance from the closed end, which side (-1 = -y)
PACK_EXTRA_W = 6.0                                 # extra cavity width, so a pack can shift 3 mm each way or a wider one fits
TAB_DX, TAB_Y = 28.0, 39.0                         # the four spring leaves sit under the plate's slits, x = +-28 from the tray centre, y = +-39
SLIT_X, SLIT_YT = (0.0, 30.0), 1.5                 # the plate's four slits, unchanged from rev 2: x = +-28 + 0..30, y = +-39, 6.4 wide
TRAY_X, TRAY_X_TRAVEL = 20.0, (5.0, 25.0)          # default centre and the leaves' x slide range inside those slits
LEAF_X, LEAF_T, LEAF_CLR = 8.0, 2.0, 0.2           # leaf width and thickness; its outer face sits 0.2 mm inside the slit's outer edge
BARB, BARB_FLAT = 1.1, 0.4                         # barb: 45 degree ramps up and down, protrudes 1.1 mm, 0.4 mm flat tip
ROOT_H, ROOT_FILLET = 6.0, 3.0                     # root block at the foot of each leaf, and the 45 degree fillets either side of the leaf
WIRE_EXT = 5.0                                     # the wire hole is this much taller than round: a 13 mm capsule with a 45 degree roof


def box(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def cyl(x, y, d, z0, z1):
    return m3.Manifold.cylinder(z1 - z0, d / 2, circular_segments=SEG).translate((x, y, z0))


def cyl_x(y, z, d, x0, x1):
    return m3.Manifold.cylinder(x1 - x0, d / 2, circular_segments=SEG).rotate((0, 90, 0)).translate((x0, y, z))


def cyl_y(x, z, d, y0, y1):
    return m3.Manifold.cylinder(y1 - y0, d / 2, circular_segments=SEG).rotate((-90, 0, 0)).translate((x, y0, z))


def cone_y(x, z, d0, d1, y0, y1):
    """Cone along +y, diameter d0 at y0 widening to d1 at y1."""
    return m3.Manifold.cylinder(y1 - y0, d0 / 2, d1 / 2, SEG).rotate((-90, 0, 0)).translate((x, y0, z))


def rbox(x0, x1, y0, y1, r, z0, z1):
    """Rounded rectangle prism."""
    return union([box(x0 + r, x1 - r, y0, y1, z0, z1), box(x0, x1, y0 + r, y1 - r, z0, z1)] +
                 [cyl(x, y, 2 * r, z0, z1) for x in (x0 + r, x1 - r) for y in (y0 + r, y1 - r)])


def prism(poly, z0, z1):
    return m3.Manifold.extrude(m3.CrossSection([poly], m3.FillRule.EvenOdd), z1 - z0).translate((0, 0, z0))


def frustum(poly, height, scale_top):
    return m3.Manifold.extrude(m3.CrossSection([poly], m3.FillRule.EvenOdd), height, 0, 0.0, scale_top)


def union(ms):
    return m3.Manifold.batch_boolean(list(ms), m3.OpType.Add)


def place(m, R, t):
    return m.transform(np.column_stack([R, t]))


def rod_chamfers(face_y):
    """Lead-in cones on both rod holes, at the faces y = +-face_y."""
    c, d = ROD_CHAMFER, ROD_HOLE
    cs = []
    for x in (-C, C):
        cs.append(cone_y(x, ROD_Z, d, d + 2 * c + 0.02, face_y - c, face_y + 0.01))
        cs.append(cone_y(x, ROD_Z, d + 2 * c + 0.02, d, -face_y - 0.01, -face_y + c))
    return cs


# ---------------------------------------------------------------- parts (assembly coords)

def base_pillars():
    P = PILLAR
    slab = rbox(-H, H, -H, H, R_EDGE, -PLATE_T, 0)
    pillars = [rbox(sx * C - P / 2, sx * C + P / 2, sy * C - P / 2, sy * C + P / 2, R_EDGE, -0.5, PILLAR_H)
               for sx in (-1, 1) for sy in (-1, 1)]
    q = P / 2 + FOOT                              # foot flare, clipped to the plate; the slot cuts pass through it
    foot = [(-q, -q), (q, -q), (q, q), (-q, q)]
    s = P / (P + 2 * FOOT)
    feet = [frustum(foot, 6.0, (s, s)).translate((sx * C, sy * C, 0)) ^ box(-H, H, -H, H, -1, 7)
            for sx in (-1, 1) for sy in (-1, 1)]
    body = union([slab] + pillars + feet)
    w, L, top = SLOT_W / 2, SPAN + SLOT_D, PILLAR_H + 1
    cuts = [box(x - w, x + w, -L, L, -POCKET, top) for x in (-C, C)]      # channel + slots, left/right
    cuts += [box(-L, L, y - w, y + w, -POCKET, top) for y in (-C, C)]     # channel + slots, back/front
    cuts.append(prism(INSET, -POCKET, 0.5))
    cuts += [rbox(min(sx * WIN_X[0], sx * WIN_X[1]), max(sx * WIN_X[0], sx * WIN_X[1]),
                  min(sy * WIN_Y[0], sy * WIN_Y[1]), max(sy * WIN_Y[0], sy * WIN_Y[1]), WIN_R, -PLATE_T - 1, 1)
             for sx in (-1, 1) for sy in (-1, 1)]
    cuts.append(cyl(WIRE_HOLE[0], WIRE_HOLE[1], WIRE_HOLE[2], -PLATE_T - 1, 1))
    cuts += [cyl(x, y, 2.5, -PLATE_T - 1, 1) for x, y in CASE_EAR_HOLES]
    for sx in (-1, 1):                                                     # slotted screw holes for the pack tray tabs
        for sy in (-1, 1):
            cuts.append(rbox(sx * TAB_DX + SLIT_X[0] - 1.7, sx * TAB_DX + SLIT_X[1] + 1.7,
                             sy * TAB_Y - SLIT_YT - 1.7, sy * TAB_Y + SLIT_YT + 1.7, 3.0, -PLATE_T - 1, 1))
    ylim = C + PILLAR / 2 + 1                                              # lock-rod holes, left and right pillar pairs
    cuts += [cyl_y(x, ROD_Z, ROD_HOLE, -ylim, ylim) for x in (-C, C)]
    cuts += rod_chamfers(C + PILLAR / 2)
    return body - union(cuts)


def wall_panel():
    """Print orientation: length along X, height along Y (y=0 is the edge in the channel), 3 mm in Z."""
    panel = rbox(0, WALL_LEN, 0, WALL_H, 2.0, 0, WALL_T)
    nx, ny = int(120 // WALL_PITCH) + 1, 7
    xs = [WALL_LEN / 2 + (i - (nx - 1) / 2) * WALL_PITCH for i in range(nx)]
    ys = [12 + j * WALL_PITCH for j in range(ny)]
    holes = [cyl(x, y, WALL_HOLE, -1, WALL_T + 1) for i, x in enumerate(xs) for j, y in enumerate(ys) if i % 3 == 0 or j % 3 == 0]
    wins = [rbox(xs[i] + RIB / 2, xs[i + 3] - RIB / 2, ys[j] + RIB / 2, ys[j + 3] - RIB / 2, 3.0, -1, WALL_T + 1)
            for i in range(0, nx - 3, 3) for j in range(0, ny - 3, 3)]
    return panel - union(holes + wins)


def lid_arm():
    """One X arm along +x. Tapered in plan (wide at the centre, narrow in the span, flared where it meets a block)
    and in depth (deepest at the centre, where the bending is)."""
    L = 2 * C * math.sqrt(2)
    half = [(-L / 2, 5.5), (-100, 5.5), (-86, 4), (-60, 4), (-20, 6.5), (20, 6.5), (60, 4), (86, 4), (100, 5.5), (L / 2, 5.5)]
    plan = half + [(x, -y) for x, y in reversed(half)]
    side = [(-L / 2, PILLAR_H), (-70, PILLAR_H), (-18, ARM_DEEP), (18, ARM_DEEP), (70, PILLAR_H), (L / 2, PILLAR_H),
            (L / 2, LID_TOP), (-L / 2, LID_TOP)]
    side_m = prism(side, 0, 16).rotate((90, 0, 0)).translate((0, 8, 0))     # profile in x-z, 16 mm wide in y
    return side_m ^ prism(plan, ARM_DEEP - 1, LID_TOP + 1)


def lid():
    """In assembly position. Print it right way up (block bottoms on the bed), tree supports under the X arms."""
    corners = [(sx, sy) for sx in (-1, 1) for sy in (-1, 1)]
    arm = lid_arm()
    blocks = [rbox(sx * C - BLK / 2, sx * C + BLK / 2, sy * C - BLK / 2, sy * C + BLK / 2, BLK_R, SKIRT_Z, LID_TOP) for sx, sy in corners]
    tab = box(-EYE_W / 2, EYE_W / 2, -EYE_T / 2, EYE_T / 2, LID_TOP - 1, EYE_HOLE_Z) + cyl_y(0, EYE_HOLE_Z, EYE_W, -EYE_T / 2, EYE_T / 2)
    foot = frustum([(-13, -EYE_T / 2), (13, -EYE_T / 2), (13, EYE_T / 2), (-13, EYE_T / 2)], 5.0, (EYE_W / 26, 1.0)).translate((0, 0, LID_TOP - 0.5))
    body = union([arm.rotate((0, 0, 45)), arm.rotate((0, 0, -45)), tab, foot] + blocks)
    p = PILLAR / 2 + CLR_POCKET
    cuts = [box(sx * C - p, sx * C + p, sy * C - p, sy * C + p, SKIRT_Z - 1, PILLAR_H) for sx, sy in corners]
    ylim = C + BLK / 2 + 1
    cuts += [cyl_y(x, ROD_Z, ROD_HOLE, -ylim, ylim) for x in (-C, C)]
    cuts += rod_chamfers(C + BLK / 2)
    cuts.append(cyl_y(0, EYE_HOLE_Z, EYE_HOLE, -EYE_T / 2 - 1, EYE_T / 2 + 1))
    return body - union(cuts)


def rod():
    """Lock rod lying flat, free end at x=0, head at x=ROD_LEN. The head is flat on the same plane as the rod."""
    body = cyl_x(0, 0, ROD_D, 0, ROD_LEN)
    head = cyl_x(0, 0, HEAD_D, ROD_LEN, ROD_LEN + HEAD_T) ^ box(ROD_LEN - 1, ROD_LEN + HEAD_T + 1, -HEAD_D, HEAD_D, -ROD_D / 2, HEAD_D)
    return body + head - cyl(COTTER_X, 0, COTTER_HOLE, -ROD_D, ROD_D)


def cotter():
    """Straight pin with a small head, axis along +Z, head on top. Pushes through the rod's cross-hole."""
    return cyl(0, 0, COTTER_D, 0, COTTER_L) + cyl(0, 0, COTTER_HEAD_D, COTTER_L, COTTER_L + COTTER_HEAD_T)


def pack_tray():
    """Tray under the plate, centred on x=0, y=0. Closed at -x, open at +x with a low stopper at the very end of the porch.
    Four spring leaves with a barb snap up through the plate's slits and click over their outer edges; pull the tray down
    firmly (or squeeze the barbs in) to take it off. Print as it sits, floor on the bed: every overhang is 45 degrees or
    less, and the wire hole has a 45 degree roof, so no supports."""
    L, W, T = PACK
    cl, cw, ch = L + 2 * PACK_CLR, W + 2 * PACK_CLR + PACK_EXTRA_W, T + PACK_CLR           # cavity
    top = -PLATE_T
    z0 = top - TRAY_FLOOR - ch
    ow = cw + 2 * TRAY_WALL
    x0, x1 = -cl / 2 - TRAY_WALL, cl / 2 + 6                                 # 6 mm porch past the pack end
    body = rbox(x0, x1, -ow / 2, ow / 2, R_TRAY, z0, top) - rbox(-cl / 2, x1 + 1 + R_TRAY, -cw / 2, cw / 2, R_TRAY, z0 + TRAY_FLOOR, top + 1)
    body += box(x1 - 2, x1, -cw / 2, cw / 2, z0 + TRAY_FLOOR, z0 + TRAY_FLOOR + 3)                    # low stopper at the very end of the porch

    zr = z0 + ROOT_H                                  # top of each leaf's root block
    zt = 2 * BARB + BARB_FLAT                         # top of the leaf; the barb's underside starts level with the plate top (z = 0)
    ye = TAB_Y + SLIT_YT + 1.7                        # the slit's outer edge
    yo = ye - LEAF_CLR
    yi = yo - LEAF_T
    R = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float)                                  # prism (y, z, extrusion) -> world (x, y, z)
    leaves = []
    for sx in (-1, 1):                                                                       # (sx, +y) and, rotated 180 degrees, (-sx, -y)
        xc = sx * TAB_DX
        x_lo = xc - LEAF_X / 2
        pr = lambda poly: place(prism(poly, 0, LEAF_X), R, (x_lo, 0, 0))
        root = box(x_lo, x_lo + LEAF_X, ow / 2 - 1.5, yo + ROOT_FILLET, z0, zr)             # root block, 1.5 mm into the wall
        leaf = box(x_lo, x_lo + LEAF_X, yi, yo, zr, zt)
        fil_in = pr([(yi, zr), (yi - ROOT_FILLET, zr), (yi, zr + ROOT_FILLET)])             # 45 degree fillets at the foot of the leaf
        fil_out = pr([(yo, zr), (yo + ROOT_FILLET, zr), (yo, zr + ROOT_FILLET)])
        barb = pr([(yo, 0.0), (yo + BARB, BARB), (yo + BARB, BARB + BARB_FLAT), (yo, zt)])
        h = root + leaf + fil_in + fil_out + barb
        leaves += [h, h.rotate((0, 0, 180))]
    body = body + union(leaves)

    # wire hole in a side wall: a capsule 13 wide, straight sides, round bottom on the floor, 45 degree roof
    r = WIRE_D / 2
    zb = z0 + TRAY_FLOOR + r
    arc = [(r * math.cos(math.radians(t)), zb + r * math.sin(math.radians(t))) for t in np.linspace(180, 360, 24)]
    outline = arc + [(r, zb + WIRE_EXT), (0.0, zb + WIRE_EXT + r), (-r, zb + WIRE_EXT)]
    cutter = prism(outline, 0, TRAY_WALL + 2).rotate((90, 0, 0))                           # profile in x-z, runs toward -y
    xh = -cl / 2 + WIRE_X
    if WIRE_SIDE < 0:
        body -= cutter.translate((xh, -(cw / 2 - 1), 0))
    else:
        body -= cutter.translate((-xh, -(cw / 2 - 1), 0)).rotate((0, 0, 180))
    return body


# ---------------------------------------------------------------- io + checks

def write_stl(path, man):
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties, np.float32)[:, :3]
    f = np.asarray(mesh.tri_verts, np.int64)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(f), dtype=[('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
    rec['n'], rec['v'] = n, tri
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as fh:
        fh.write(path.stem.encode().ljust(80, b' '))
        fh.write(np.uint32(len(f)).tobytes())
        fh.write(rec.tobytes())


def to_bed(m, x, y):
    """Drop a part onto the bed with its bounding-box min corner at (x, y)."""
    lo = np.asarray(m.bounding_box()[:3])
    return m.translate((x - lo[0], y - lo[1], -lo[2]))


def check_plate(name, items):
    bb = [(n, np.asarray(m.bounding_box())) for n, m in items]
    for i, (a_name, a) in enumerate(bb):
        assert a[0] >= MARGIN - 1e-6 and a[1] >= MARGIN - 1e-6 and a[3] <= BED[0] - MARGIN + 1e-6 and a[4] <= BED[1] - MARGIN + 1e-6,             f'{name}: {a_name} inside the {MARGIN} mm edge margin {a}'
        for b_name, b in bb[i + 1:]:
            sep = max(b[0] - a[3], a[0] - b[3], b[1] - a[4], a[1] - b[4])     # bounding-box gap in x or y
            assert sep >= PART_GAP - 1e-6, f'{name}: {a_name} and {b_name} only {sep:.1f} mm apart'
    lo = np.min([b[:3] for _, b in bb], axis=0); hi = np.max([b[3:] for _, b in bb], axis=0)
    return lo, hi


def build_parts():
    bp, wall, ld, rd, ct, tray = base_pillars(), wall_panel(), lid(), rod(), cotter(), pack_tray()
    for nm, m in [('base_pillars', bp), ('wall', wall), ('lid', ld), ('rod', rd), ('cotter', ct), ('tray', tray)]:
        assert m.status() == m3.Error.NoError and not m.is_empty(), nm
    return bp, wall, ld, rd, ct, tray


def assembly(bp, wall, ld, rd, ct, tray):
    """Every printed part where it goes (walls left + right, the balanced build)."""
    wall_left = place(wall, np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float), (-C - WALL_T / 2, -WALL_LEN / 2, -POCKET))
    y0 = -(C + BLK / 2 + ROD_FREE)                      # free end of the left rod
    rod_l = rd.rotate((0, 0, 90)).translate((-C, y0, ROD_Z))
    cot_l = ct.translate((-C, y0 + COTTER_X, ROD_Z + ROD_D / 2 - COTTER_L))     # head sits on top of the rod
    L, W, T = PACK
    zb = -PLATE_T - PACK_CLR - T                        # pack sits on the tray floor, 0.5 mm under the plate
    pack = box(TRAY_X - L / 2, TRAY_X + L / 2, -W / 2, W / 2, zb, zb + T)
    return {'base_pillars': bp, 'wall_left': wall_left, 'wall_right': wall_left.rotate((0, 0, 180)),
            'lid': ld, 'rod_left': rod_l, 'rod_right': rod_l.rotate((0, 0, 180)),
            'cotter_left': cot_l, 'cotter_right': cot_l.rotate((0, 0, 180)),
            'tray': tray.translate((TRAY_X, 0, 0)), 'pack': pack}


def main():
    bp, wall, ld, rd, ct, tray = build_parts()

    # ---- assembly: place every part where it goes and check the fits ----
    a = assembly(bp, wall, ld, rd, ct, tray)
    wall_left, wall_right, lid_a, tray_a, pack_a = a['wall_left'], a['wall_right'], a['lid'], a['tray'], a['pack']
    rods, cotters = [a['rod_left'], a['rod_right']], [a['cotter_left'], a['cotter_right']]

    assert (wall_left ^ bp).volume() < 1e-6, 'wall hits the base/pillars'
    side_gap = wall_left.translate((0, 0, 1)).min_gap(bp, 2.0)      # lifted 1 mm so only the slot sides count
    assert abs(side_gap - CLR_SLIDE) < 0.02, f'wall slot gap {side_gap:.3f}'
    assert (lid_a ^ bp).volume() < 1e-6, 'lid hits the pillars'
    assert (lid_a ^ wall_left).volume() < 1e-6, 'lid hits a wall'
    wall_lid = wall_left.min_gap(lid_a, 5.0)
    assert wall_lid >= 1.9, f'wall to lid only {wall_lid:.2f} mm'
    for r, c in zip(rods, cotters):
        assert (r ^ bp).volume() < 1e-6 and (r ^ lid_a).volume() < 1e-6, 'rod hits the pillars or the lid'
        assert abs(r.min_gap(bp, 2.0) - CLR_ROD) < 0.03, f'rod hole clearance {r.min_gap(bp, 2.0):.3f}'
        assert (c ^ r).volume() < 1e-6 and (c ^ lid_a).volume() < 1e-6, 'cotter collides'
        assert min(r.min_gap(wall_left, 10.0), r.min_gap(wall_right, 10.0)) > 6, 'rod too close to a wall'
    assert (tray_a ^ bp).volume() < 1e-6, 'tray hits the plate'
    tray_at = lambda x, dz=0.0: tray.translate((x, 0, dz))
    for x in (TRAY_X_TRAVEL[0], TRAY_X, TRAY_X_TRAVEL[1]):
        assert (tray_at(x) ^ bp).volume() < 1e-6, f'tray hits the plate at x={x}'
        assert (tray_at(x, -1.5) ^ bp).volume() > 0.05, f'tray not latched at x={x}'          # lowered 1.5 mm the barbs catch the plate
    ye = TAB_Y + SLIT_YT + 1.7
    overlap = (ye - LEAF_CLR + BARB) - ye                                                       # how far the barb reaches over the plate
    defl = overlap + 0.3                                                                        # leaf deflection needed to pass the slit
    zr_ = (-PLATE_T - TRAY_FLOOR - (PACK[2] + PACK_CLR)) + ROOT_H
    Lfree = (2 * BARB + BARB_FLAT) - (zr_ + ROOT_FILLET)
    eps = 1.5 * LEAF_T * defl / Lfree ** 2                                                      # 3 h d / (2 L^2)
    k = 3 * 2500 * (LEAF_X * LEAF_T ** 3 / 12) / Lfree ** 3                                     # N/mm, E = 2.5 GPa
    assert overlap >= 0.8 and eps < 0.015, f'leaf out of range: overlap {overlap:.2f}, strain {eps:.3f}'
    print(f'snap leaves: barb overlap {overlap:.1f} mm, deflect {defl:.1f} mm over {Lfree:.1f} mm free length: strain {100 * eps:.2f} %, '
          f'about {k * defl:.1f} N per leaf ({4 * k * defl:.0f} N to push on or pull off)')
    assert (pack_a ^ tray_a).volume() < 1e-6 and (pack_a ^ bp).volume() < 1e-6, 'pack hits the tray or the plate'
    print(f'fits ok: wall slot gap {side_gap:.2f} mm, wall to lid {wall_lid:.1f} mm, rod hole clearance {CLR_ROD} mm, '
          f'rod length {ROD_LEN:.0f} + head, string touches the eye at z={EYE_HOLE_Z + EYE_HOLE / 2:.1f}, '
          f'pack {PACK[0]:.0f} x {PACK[1]:.0f} x {PACK[2]:.0f} in the tray')

    # ---- individual parts, print orientation ----
    parts = {
        'base_pillars': bp.translate((0, 0, PLATE_T)),
        'wall_panel': wall,
        'lid': ld.translate((0, 0, -SKIRT_Z)),
        'lock_rod': to_bed(rd, 0, 0),
        'cotter': to_bed(ct.rotate((0, 90, 0)), 0, 0),
        'pack_tray': to_bed(tray, 0, 0),
    }
    for nm, m in parts.items():
        write_stl(OUT / 'parts' / f'{nm}.stl', m)

    # ---- plates for the CORE One ----
    rod_up = rd.rotate((0, 0, 90))                    # along y, so it fits beside the base
    cot_flat = ct.rotate((0, 90, 0))
    frame = [('base_pillars', to_bed(parts['base_pillars'], 10, 15))]
    frame += [(f'rod{i}', to_bed(rod_up, 178 + 13 * i, 15)) for i in range(2)]
    frame += [(f'cotter{i}', to_bed(cot_flat, 207, 15 + 8 * i)) for i in range(4)]       # 2 needed, 2 spare
    # two 145 x 85 walls fit inside the margins standing lengthwise, side by side
    upright = wall.rotate((0, 0, 90))
    walls = [('wall0', to_bed(upright, 18, 10)), ('wall1', to_bed(upright, 18 + WALL_H + 10, 10))]
    walls_spare = walls + [(f'rod{i}', to_bed(rod_up, 206 + 13 * i, 15)) for i in range(2)]   # back/front panels + spare rods
    lids = [('lid', to_bed(parts['lid'], 35, 20))]
    trays = [('pack_tray', to_bed(parts['pack_tray'], 10, 10))]
    for nm, items in [('plate1_frame', frame), ('plate2_walls', walls), ('plate3_walls', walls_spare),
                      ('plate4_lid', lids), ('plate5_pack_tray', trays)]:
        lo, hi = check_plate(nm, items)
        write_stl(OUT / 'plates' / f'{nm}.stl', union(m for _, m in items))
        print(f'{nm}: {len(items)} parts, x {lo[0]:.1f}-{hi[0]:.1f}, y {lo[1]:.1f}-{hi[1]:.1f}, tallest {hi[2]:.0f} mm '
              f'(edge clearance {min(lo[0], lo[1], BED[0] - hi[0], BED[1] - hi[1]):.1f} mm)')

    for nm, m in a.items():                           # every part in assembly position, for Fusion or any CAD that imports meshes
        if nm != 'pack':
            write_stl(OUT / 'assembly_parts' / f'{nm}.stl', m)
    asm = union([bp, wall_left, wall_right, lid_a, tray_a, pack_a] + rods + cotters)
    write_stl(OUT / 'assembly_check.stl', asm)
    for nm, m in parts.items():
        print(f'  {nm:18s} {m.volume() / 1000:6.1f} cm^3')


if __name__ == '__main__':
    main()
