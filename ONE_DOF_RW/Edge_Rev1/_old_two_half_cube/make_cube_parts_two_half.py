"""Edge-balancing cube, 90 mm, one 2804 hollow-shaft gimbal motor (Amazon.ca B0FSZ7XWG2) and a D74 reaction wheel inside.

    python make_cube_parts.py        # needs numpy + manifold3d (the toolchain of ONE_DOF_RW/String_Rev3 and SWINGUP_RWP)

Frame: cube-local axes, centre at the origin, x = the wheel axis = the pivot edge direction. The cube stands on the edge at (y, z) = (-45, +45), so the
vertical diagonal of the (y, z) square is the up direction. Twelve 5 x 5 bars, every outer edge rounded R1.5 so it rolls on any edge. Printed in two halves
joined at x = 0 by four glued tenons:

  Cube_Half_Motor.stl        +x end ring, four corner stubs, motor plate (40 x 40 pad on two diagonal ribs) with the motor window, the four M2.5 stator-back
                             holes, a recess for the kit's AS5600 board, two lead channels. Print ring face (x = 45) down, supports under the pad and ribs.
  Cube_Half_Electronics.stl  -x end ring, four corner stubs with tenons, and a 16 mm lattice for zip-tying the battery and boards. Print ring face (x = -45) down.
  Wheel_D74_2804.stl         screw-on hub (4 x M2.5, D16 cross pattern) and rim with eight M4 weight-bolt holes (rev3 thread). Print face down.

Stack along x: electronics lattice -45..-42.6 | battery -42.6..-25.6 | wheel 3..15 | motor 15..30 | motor plate 30..38 | AS5600 board 36..37.6, headers to 44.6.
Everything stays inside the 90 mm envelope, so the cube can fall on any face or edge without the board or wheel touching the table.

Writes the STLs, Assembly_standing.stl, viewer_data.json and cad_numbers.json (mass, balance, inertia), and prints the fit checks and the simulated recovery.
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
REV3 = HERE.parent.parent / 'String_Rev3' / 'mechanical'   # this folder is ONE_DOF_RW/Edge_Rev1/_old_two_half_cube


def load(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


F = load('mfp', REV3 / 'frame_parts' / 'make_frame_parts.py')
W3 = load('fly', REV3 / 'flywheel' / 'make_flywheel_d100.py')
box = F.box

# ---------------------------------------------------------------- cube
A, S, RE = 90.0, 5.0, 1.5              # outer side, bar section, edge round radius
H = A / 2
PIVOT = (-1, +1)                        # pivot edge at (y, z) = (PIVOT[0] * H, PIVOT[1] * H)
COLLAR, COLLAR_L = 8.0, 9.0             # 8 x 8 collars (9 long) round each joint at x = 0
TENON, SOCKET, TENON_L = 3.2, 3.6, 8.0  # glued tenon (half E) in a socket (half M), centred 41 mm out from the axis
JC = 41.0
LAT_T, LAT_PITCH, LAT_BAR = 2.4, 16.0, 4.0   # lattice for zip ties, in the electronics end
# ---------------------------------------------------------------- motor, from the drawing in the Amazon.ca listing (see SWINGUP_RWP)
MOTOR_D, MOTOR_BORE, BODY = 34.5, 6.5, 15.0
HUB_D, HUB_L = 12.0, 4.5
ROTOR_PCD, STATOR_PCD, M25 = 16.0, 19.0, 2.5
ENC_W, ENC_T, ENC_PLANE = 33.0, 1.6, 6.0   # board 33 x 33, chip plane 6 mm from the stator back (ASSUMED, see README)
MOTOR_G, ROTOR_G, ENC_G = 40.0, 22.0, 5.0
PAD_X0, PAD_X1, PAD_H = 30.0, 38.0, 20.0   # motor plate: x range, half width
RIB_X0, RIB_X1, RIB_W = 34.0, 38.0, 7.0    # diagonal ribs flush with the plate's outboard face
MOT_X0 = PAD_X0 - BODY                      # 15: rotor face, where the wheel mounts
# ---------------------------------------------------------------- wheel (rev3 D100 design scaled to D74, rim width kept at 11.5)
WD, WID = 74.0, 51.0
HUB_OD, WEB_T = 26.0, 8.0
N_BOLT, BOLT_G = 8, 2.3                    # M4 x 12 socket head, 2.3 g
# ---------------------------------------------------------------- parts we buy (placeholders for fit and balance): size, mass
BATTERY = dict(x=(-42.6, -25.6), y=(-10.5, 10.5), z=(-29.0, 29.0), g=38.0)     # ASSUMED 3S 450 mAh, 58 x 21 x 17, with its lead
ESP32 = dict(x=(-42.6, -30.6), y=(12.0, 40.0), z=(-26.0, 26.0), g=10.0)         # ASSUMED dev board 52 x 28 x 12
DRIVER = dict(x=(-42.6, -36.6), y=(-38.0, -12.0), z=(-30.0, -10.0), g=6.0)       # ASSUMED SimpleFOC mini ~ 26 x 20 x 6
IMU = dict(x=(-42.6, -39.6), y=(-38.0, -22.0), z=(22.0, 38.0), g=3.0)           # ASSUMED MPU6050 breakout 16 x 16 x 3, near the pivot edge
WIRES = dict(x=(-24.0, -22.0), y=(-1.0, 1.0), z=(-1.0, 1.0), g=6.0)
RHO = 1.24e-3
FILL_FRAME, FILL_WHEEL = 0.85, 0.48        # sliced mass / solid mass


def cx(r, x0, x1, y=0.0, z=0.0, seg=64):
    return m3.Manifold.cylinder(x1 - x0, r, r, seg).rotate((0, 90, 0)).translate((x0, y, z))


def union(ms):
    return m3.Manifold.batch_boolean(list(ms), m3.OpType.Add)


def sgn_range(s, lo, hi):
    """(lo, hi) on the + side, mirrored for s = -1."""
    return (lo, hi) if s > 0 else (-hi, -lo)


# ---------------------------------------------------------------- frame pieces
def ring(sx):
    x0, x1 = (H - S, H) if sx > 0 else (-H, -H + S)
    return union([box(x0, x1, -H, H, H - S, H), box(x0, x1, -H, H, -H, -H + S),
                  box(x0, x1, H - S, H, -H, H), box(x0, x1, -H, -H + S, -H, H)])


def corners():
    for sy in (-1, 1):
        for sz in (-1, 1):
            yield sy, sz


def stubs(x0, x1):
    return union([box(x0, x1, *sgn_range(sy, H - S, H), *sgn_range(sz, H - S, H)) for sy, sz in corners()])


def collars(x0, x1):
    return union([box(x0, x1, *sgn_range(sy, H - COLLAR, H), *sgn_range(sz, H - COLLAR, H)) for sy, sz in corners()])


def edge_cutters():
    """Removes the sharp outer corner (radius RE) from all twelve cube edges."""
    L = A + 10.0
    base = box(-L / 2, L / 2, H - RE, H + 1, H - RE, H + 1) - cx(RE, -L / 2 - 1, L / 2 + 1, H - RE, H - RE, 32)
    xs = union([base.rotate((90 * k, 0, 0)) for k in range(4)])
    return xs + xs.rotate((0, 0, 90)) + xs.rotate((0, -90, 0))


def pcd_holes(pcd, d, x0, x1, a0):
    cuts = []
    for k in range(4):
        a = math.radians(a0 + 90 * k)
        cuts.append(cx(d / 2 + 0.1, x0, x1, pcd / 2 * math.cos(a), pcd / 2 * math.sin(a), 24))
    return union(cuts)


def half_motor():
    h = ring(+1) + stubs(0.0, H) + collars(0.0, COLLAR_L)
    for sy, sz in corners():                                                    # sockets for half E's tenons
        h = h - box(-1.0, TENON_L, sy * JC - SOCKET / 2, sy * JC + SOCKET / 2, sz * JC - SOCKET / 2, sz * JC + SOCKET / 2)
    pad = box(PAD_X0, PAD_X1, -PAD_H, PAD_H, -PAD_H, PAD_H)
    L = 2 * (H - S / 2) * math.sqrt(2)                                          # rib tips end at the stub centres
    rib = box(RIB_X0, RIB_X1, -L / 2, L / 2, -RIB_W / 2, RIB_W / 2)
    h = h + pad + rib.rotate((45, 0, 0)) + rib.rotate((-45, 0, 0))
    h = h - cx(HUB_D / 2 + 1.0, PAD_X0 - 1, PAD_X1 + 1, 0, 0, 64)               # window for the rotor's rear hub, D14
    h = h - pcd_holes(STATOR_PCD, M25, PAD_X0 - 1, PAD_X1 + 1, 45)              # four M2.5 stator-back holes
    e = ENC_W + 0.6
    h = h - box(PAD_X0 + ENC_PLANE, PAD_X1 + 1, -e / 2, e / 2, -e / 2, e / 2)   # recess for the AS5600 board, chip plane 6 mm from the stator back
    for z0, z1 in ((-6.8, -2.6), (2.6, 6.8)):                                    # lead channels on the motor face: phase leads / encoder wires, towards +y
        h = h - box(PAD_X0 - 0.1, PAD_X0 + 2.4, 0.0, PAD_H + 1, z0, z1)
    return h - edge_cutters()


def half_electronics():
    h = ring(-1) + stubs(-H, 0.0) + collars(-COLLAR_L, 0.0)
    for sy, sz in corners():                                                    # tenons into half M's sockets
        h = h + box(0.0, TENON_L, sy * JC - TENON / 2, sy * JC + TENON / 2, sz * JC - TENON / 2, sz * JC + TENON / 2)
    cs = [(-2 * LAT_PITCH + i * LAT_PITCH) for i in range(5)]
    lat = [box(-H, -H + LAT_T, c - LAT_BAR / 2, c + LAT_BAR / 2, -H + S - 1, H - S + 1) for c in cs]
    lat += [box(-H, -H + LAT_T, -H + S - 1, H - S + 1, c - LAT_BAR / 2, c + LAT_BAR / 2) for c in cs]
    h = h + union(lat)
    return h - edge_cutters()


# ---------------------------------------------------------------- wheel: local frame z = spin axis, z = 0 on the rotor face, grows away from the motor
def wheel(threaded=True):
    rim = W3.cyl(0, 0, WD, 0, W3.RIM_H) - W3.cyl(0, 0, WID, -1, W3.RIM_H + 1)
    # The hub is full height (12) and the spokes sit flush with the rim's z = 12 face (z 4..12), so the wheel prints with that face on the bed and no supports;
    # the spigot then points up. (With the hub only 8 high, the hub and spokes would hang 4 mm above the bed.)
    hub = W3.cyl(0, 0, HUB_OD, 0, W3.RIM_H)
    r0, r1 = HUB_OD / 2 - 1, WID / 2 + 1
    parts = [hub, rim]
    for k in range(3):
        sp = W3.prism([(r0, -W3.SPOKE_W0 / 2), (r1, -W3.SPOKE_W1 / 2), (r1, W3.SPOKE_W1 / 2), (r0, W3.SPOKE_W0 / 2)], W3.RIM_H - WEB_T, W3.RIM_H)
        parts.append(sp.rotate((0, 0, 90 + 120 * k)))
    body = union(parts) + W3.cyl(0, 0, MOTOR_BORE - 0.3, -4.0, 0.5)             # centring spigot into the hollow shaft
    pr = (WD + WID) / 4
    cuts = []
    for i in range(N_BOLT):
        a = math.radians(90 + 180 / N_BOLT + 360 * i / N_BOLT)
        x, y = pr * math.cos(a), pr * math.sin(a)
        cuts.append(W3.thread_cutter(x, y, -0.2, W3.RIM_H - W3.CB_DEPTH + 0.2, W3.M4_MAJOR - W3.UNDERSIZE) if threaded else W3.cyl(x, y, 3.6, -1, W3.RIM_H + 1))
        cuts.append(W3.cyl(x, y, W3.CB_D, W3.RIM_H - W3.CB_DEPTH, W3.RIM_H + 1))
    for k in range(4):                                                          # 4 x M2.5, D16 cross pattern, 3.5 mm of hub under each head (M2.5 x 6)
        a = math.radians(90 * k)
        x, y = ROTOR_PCD / 2 * math.cos(a), ROTOR_PCD / 2 * math.sin(a)
        cuts.append(W3.cyl(x, y, M25 + 0.2, -1, W3.RIM_H + 1))
        cuts.append(W3.cyl(x, y, 5.0, 3.5, W3.RIM_H + 1))
    return body - union(cuts)


def place_wheel(m):
    """Local (X, Y, Z) -> cube: x = MOT_X0 - Z, y = -X, z = Y (a proper rotation)."""
    return m.transform(np.array([[0, 0, -1, MOT_X0], [-1, 0, 0, 0], [0, 1, 0, 0]], float))


# ---------------------------------------------------------------- bought parts as envelopes
def motor():
    body = cx(MOTOR_D / 2, MOT_X0, PAD_X0, 0, 0, 96) + cx(HUB_D / 2, PAD_X0 - 0.1, PAD_X0 + HUB_L, 0, 0, 64)
    return body - cx(MOTOR_BORE / 2, MOT_X0 - 1, PAD_X0 + HUB_L + 1, 0, 0, 48)


def enc_board():
    x0 = PAD_X0 + ENC_PLANE
    plate = box(x0, x0 + ENC_T, -ENC_W / 2, ENC_W / 2, -ENC_W / 2, ENC_W / 2)
    heads = [box(x0 + ENC_T, x0 + ENC_T + 7.0, y0, y0 + 6.0, -8.0, 8.0) for y0 in (-ENC_W / 2 + 2.0, ENC_W / 2 - 8.0)]
    return plate + heads[0] + heads[1]


def block(d):
    return box(*d['x'], *d['y'], *d['z'])


def bolt_meshes():
    pr = (WD + WID) / 4
    out = []
    for i in range(N_BOLT):
        a = math.radians(90 + 180 / N_BOLT + 360 * i / N_BOLT)
        X, Y = pr * math.cos(a), pr * math.sin(a)
        out.append(cx(2.0, MOT_X0 - 12.0, MOT_X0, -X, Y, 24))
    return out


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
    rho = mass_g * 1e-3 / V                                                      # kg per mm^3
    j = rho * ((q[1] + q[2]) - 2 * y0 * S1[1] - 2 * z0 * S1[2] + (y0 ** 2 + z0 ** 2) * V) * 1e-6
    return mass_g * 1e-3, S1 / V, j


def check(m, name):
    assert m.status() == m3.Error.NoError and not m.is_empty(), name
    bb = np.asarray(m.bounding_box())
    print(f'{name:26s} {m.volume() / 1000:6.1f} cm3  solid {m.volume() * RHO:6.1f} g   '
          f'x {bb[0]:6.1f}..{bb[3]:6.1f}  y {bb[1]:6.1f}..{bb[4]:6.1f}  z {bb[2]:6.1f}..{bb[5]:6.1f}')


def main():
    hm, he = half_motor(), half_electronics()
    wl, wlf = wheel(True), wheel(False)
    wp, wpf = place_wheel(wl), place_wheel(wlf)
    mot, enc = motor(), enc_board()
    bat, esp, drv, imu, wir = (block(d) for d in (BATTERY, ESP32, DRIVER, IMU, WIRES))
    bolts = bolt_meshes()
    print('--- printed parts')
    for n, m in (('Cube_Half_Motor', hm), ('Cube_Half_Electronics', he), ('Wheel_D74_2804', wp)):
        check(m, n)
    frame = union([hm, he])
    bb = np.asarray(union([frame, wpf, mot, enc, bat, esp, drv, imu, wir]).bounding_box())
    print(f'envelope of everything: x {bb[0]:.1f}..{bb[3]:.1f}, y {bb[1]:.1f}..{bb[4]:.1f}, z {bb[2]:.1f}..{bb[5]:.1f}   (cube side {A:.0f}: nothing may exceed +-{H:.0f})')

    print('--- static fits, overlap in mm3')
    solids = {'halfM': hm, 'halfE': he, 'wheel': wpf, 'motor': mot, 'board': enc, 'battery': bat, 'esp32': esp, 'driver': drv, 'imu': imu, 'wires': wir}
    names = list(solids)
    worst = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            v = (solids[names[i]] ^ solids[names[j]]).volume()
            if abs(v) > 0.01:
                worst.append((names[i], names[j], v))
    print('  ' + ('all pairs 0 mm3' if not worst else '; '.join(f'{a} x {b}: {v:.2f}' for a, b, v in worst)))

    # ---- mass, balance, inertia about the pivot edge
    y0, z0 = PIVOT[0] * H, PIVOT[1] * H
    items = [('half M (printed)', hm, FILL_FRAME * RHO, 'vol'), ('half E (printed)', he, FILL_FRAME * RHO, 'vol'), ('wheel (printed)', wp, FILL_WHEEL * RHO, 'vol'),
             ('motor', mot, MOTOR_G, 'g'), ('encoder board + screws', enc, ENC_G, 'g'), ('battery + lead', bat, BATTERY['g'], 'g'),
             ('ESP32 board', esp, ESP32['g'], 'g'), ('driver board', drv, DRIVER['g'], 'g'), ('IMU board', imu, IMU['g'], 'g'), ('wiring', wir, WIRES['g'], 'g')]
    rows = []
    for nm, m, v, kind in items:
        g = v * m.volume() if kind == 'vol' else v                               # g/mm3 * mm3 = g
        rows.append((nm, *body_props(m, g, y0, z0)))
    for k, b in enumerate(bolts):
        rows.append((f'bolt {k + 1}', *body_props(b, BOLT_G, y0, z0)))
    M = sum(r[1] for r in rows)
    C = sum(r[1] * r[2] for r in rows) / M                                       # centroid x, y, z (mm)
    Jt = sum(r[3] for r in rows)
    d = np.array([C[1] - y0, C[2] - z0])
    u = np.array([-PIVOT[0], -PIVOT[1]]) / math.sqrt(2)                          # from the pivot edge towards the cube centre
    wv = np.array([-PIVOT[1], PIVOT[0]]) / math.sqrt(2)                          # across it
    l, e = float(d @ u) * 1e-3, float(d @ wv) * 1e-3
    # wheel spin inertia: printed wheel about its own axis + bolts + rotor bell
    Vw, Sw, qw = moments(tris(wl))
    jw_print = RHO * FILL_WHEEL * (qw[0] + qw[1]) * 1e-9
    pr = (WD + WID) / 4 * 1e-3
    Jw = jw_print + N_BOLT * BOLT_G * 1e-3 * pr ** 2 + ROTOR_G * 1e-3 * 0.0145 ** 2
    J1 = Jt - Jw
    Mgl = M * 9.81 * l
    print('--- mass and balance about the pivot edge')
    for nm, mg, c, j in rows:
        if nm.startswith('bolt'):
            continue
        print(f'  {nm:24s} {mg * 1e3:6.1f} g   centre x {c[0]:6.1f} y {c[1]:6.1f} z {c[2]:6.1f}   J {j:.2e}')
    print(f'  8 bolts                  {N_BOLT * BOLT_G:6.1f} g')
    print(f'  total M = {M * 1e3:.0f} g, centre of mass above the edge l = {l * 1e3:.1f} mm, sideways offset e = {e * 1e3:+.2f} mm '
          f'(balance point shifted {math.degrees(math.atan2(e, l)):+.2f} deg)')
    print(f'  Mgl = {Mgl:.3f} N m, J1 = {J1:.3e}, Jt = {Jt:.3e}, Jw = {Jw:.3e} kg m2 (wheel {jw_print:.2e}, bolts {N_BOLT * BOLT_G * 1e-3 * pr ** 2:.2e}, rotor {ROTOR_G * 1e-3 * 0.0145 ** 2:.2e})')

    # ---- simulated recovery with these numbers (same model as the web page)
    sys.path.insert(0, str(HERE.parent / 'analysis'))
    import cube_sim as sim
    p = dict(M=M, l=l, Mgl=Mgl, J1=J1, Jw=Jw)
    print('--- simulated recovery (ideal sensing, torque limit and back-EMF derating at 12 V)')
    for tau in (0.045, 0.030, 0.020):
        lean, wpk = sim.max_lean(p, tau)
        print(f'  torque limit {tau:.3f} N m (torque/Mgl {tau / Mgl:.2f}): recovers from {lean:.1f} deg, wheel peak {wpk:.0f} rad/s')

    # ---- outputs
    for n, m in (('Cube_Half_Motor', hm), ('Cube_Half_Electronics', he), ('Wheel_D74_2804', wp)):
        F.write_stl(HERE / f'{n}.stl', m)
    F.write_stl(HERE / 'Assembly_standing.stl', union([hm, he, wpf, mot, enc, bat, esp, drv, imu]))
    parts = {'halfM': (hm, '#e6dcc4'), 'halfE': (he, '#e6dcc4'), 'wheel': (wpf, '#d9902f'), 'motor': (mot, '#b23a2e'), 'board': (enc, '#1f5fa8'),
             'battery': (bat, '#2f57a8'), 'esp32': (esp, '#1f6b4a'), 'driver': (drv, '#7a3fa0'), 'imu': (imu, '#222222')}
    out = {'parts': {n: {'color': c, 'positions_b64': base64.b64encode(tris(m).astype(np.float32).tobytes()).decode()} for n, (m, c) in parts.items()}}
    (HERE / 'viewer_data.json').write_text(json.dumps(out))
    json.dump(dict(M_kg=M, l_m=l, e_m=e, Mgl=Mgl, J1=J1, Jw=Jw, Jt=Jt, centroid_mm=[float(c) for c in C]), open(HERE / 'cad_numbers.json', 'w'))
    print('wrote', HERE)


if __name__ == '__main__':
    main()
