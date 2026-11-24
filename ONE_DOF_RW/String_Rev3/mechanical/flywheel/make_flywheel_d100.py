"""Flywheel, rebuilt from its parameters (tt_flywheel.py) so the rim can grow without distorting the weight holes.

    python make_flywheel_d100.py        # needs numpy + manifold3d

Builds the rev 2 wheel (OD 80) as a check against Flywheel_D80.stl, then the rev 3 wheel (OD 100): same hub, shaft
socket, rim height and rim width, three slotted spokes, ten weight-bolt holes on the rim. In rev 3 those ten holes are
threaded M4 x 0.7 (modelled helix) and 0.2 mm smaller than M4, so the bolt cuts its own thread and no nut is needed.
Writes Flywheel_D100.stl and ../../visualization/flywheel.json (hub end down: x, -y, 15 - z) and prints mass and Izz.
"""
import base64
import json
import math
import struct
from pathlib import Path

import numpy as np
import manifold3d as m3

HERE = Path(__file__).parent
VIEWER_JSON = HERE.parent.parent / 'visualization' / 'flywheel.json'
RHO = 1.24e-3                                     # g/mm^3, PLA
SEG = 96

# hub, shaft socket (TT double-D shaft), screw pocket
HUB_OD, RIM_H, RIM_LIFT = 16.0, 12.0, 3.0
HUB_H = RIM_H + RIM_LIFT
SHAFT_D, SHAFT_FLATS, FIT = 5.40, 3.70, 0.10
POCKET, FLOOR, SCREW_HOLE, SCREW_CB = 8.0, 2.0, 2.4, 4.5
WEB_T = 8.0                                       # spoke thickness, as exported in Flywheel_D80.stl
SPOKE_W0, SPOKE_W1, SLOT_W = 7.0, 12.0, 4.0
# weight bolts: 10 holes on the rim, heads in counterbores on the +Z face
HOLES, CB_D, CB_DEPTH = 10, 7.6, 4.2
# M4 x 0.7 internal thread, drawn 0.2 mm under nominal: crest (minor) and root (major) diameters
M4_MAJOR, M4_MINOR, PITCH, UNDERSIZE = 4.0, 3.242, 0.7, 0.2


def cyl(x, y, d, z0, z1):
    return m3.Manifold.cylinder(z1 - z0, d / 2, circular_segments=SEG).translate((x, y, z0))


def box(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def prism(poly, z0, z1):
    return m3.Manifold.extrude(m3.CrossSection([poly], m3.FillRule.EvenOdd), z1 - z0).translate((0, 0, z0))


def union(ms):
    return m3.Manifold.batch_boolean(list(ms), m3.OpType.Add)


def thread_cutter(x, y, z0, z1, d_hole):
    """Void of a right-handed internal thread: radius runs from the crest (minor) to the root (major) once per pitch.
    One extruded cross-section twisted a full turn per pitch makes the helix. d_hole is the major diameter."""
    r_root = d_hole / 2
    r_crest = r_root - (M4_MAJOR - M4_MINOR) / 2
    n = 48
    pts = []
    for i in range(n):
        u = i / n
        r = r_crest + (r_root - r_crest) * (1 - abs(2 * u - 1))
        pts.append((r * math.cos(2 * math.pi * u), r * math.sin(2 * math.pi * u)))
    turns = (z1 - z0) / PITCH
    cs = m3.CrossSection([pts], m3.FillRule.EvenOdd)
    return m3.Manifold.extrude(cs, z1 - z0, int(turns * 12), 360 * turns).translate((x, y, z0))


def build(od, rim_id, slot_r1, threaded):
    hub = cyl(0, 0, HUB_OD, 0, HUB_H)
    rim = cyl(0, 0, od, 0, RIM_H) - cyl(0, 0, rim_id, -1, RIM_H + 1)
    r0, r1 = HUB_OD / 2 - 1, rim_id / 2 + 1
    spokes = []
    for k in range(3):
        deg = 90 + 120 * k
        sp = prism([(r0, -SPOKE_W0 / 2), (r1, -SPOKE_W1 / 2), (r1, SPOKE_W1 / 2), (r0, SPOKE_W0 / 2)], 0, WEB_T)
        slot = box(15, slot_r1, -SLOT_W / 2, SLOT_W / 2, -1, WEB_T + 1) + cyl(15, 0, SLOT_W, -1, WEB_T + 1) + cyl(slot_r1, 0, SLOT_W, -1, WEB_T + 1)
        spokes.append((sp - slot).rotate((0, 0, deg)))
    body = union([hub, rim] + spokes)

    pitch_r = (od + rim_id) / 4
    cuts = []
    for i in range(HOLES):
        a = math.radians(90 + 180 / HOLES + 360 * i / HOLES)
        x, y = pitch_r * math.cos(a), pitch_r * math.sin(a)
        if threaded:
            cuts.append(thread_cutter(x, y, -0.2, RIM_H - CB_DEPTH + 0.2, M4_MAJOR - UNDERSIZE))
        else:
            cuts.append(cyl(x, y, 4.4, -1, RIM_H + 1))
        cuts.append(cyl(x, y, CB_D, RIM_H - CB_DEPTH, RIM_H + 1))
    # TT double-D socket (as drawn in tt_flywheel.py: arcs joined by chords of half-length f), screw pocket and hole
    r, f = (SHAFT_D + FIT) / 2, (SHAFT_FLATS + FIT) / 2
    y = math.sqrt(r * r - f * f)
    ang = [math.radians(a) for a in np.linspace(-math.degrees(math.atan2(y, f)), math.degrees(math.atan2(y, f)), 24)]
    right = [(r * math.cos(t), r * math.sin(t)) for t in ang]
    left = [(-px, -py) for px, py in right]
    cuts.append(prism(right + left, HUB_H - POCKET, HUB_H + 1))
    cuts.append(cyl(0, 0, SCREW_CB, -1, HUB_H - POCKET - FLOOR))
    cuts.append(cyl(0, 0, SCREW_HOLE, -1, HUB_H + 1))
    return body - union(cuts)


def mesh_tris(man):
    m = man.to_mesh()
    v = np.asarray(m.vert_properties, np.float64)[:, :3]
    return v[np.asarray(m.tri_verts, np.int64)]


def props(T):
    """Volume (cm^3), solid PLA mass (g), Izz (kg m^2) of a closed triangle mesh."""
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    v6 = np.einsum('ij,ij->i', a, np.cross(b, c))
    s = a + b + c
    ixx = (v6 / 6 / 20 * ((a[:, 0]**2 + b[:, 0]**2 + c[:, 0]**2) + s[:, 0]**2)).sum()
    iyy = (v6 / 6 / 20 * ((a[:, 1]**2 + b[:, 1]**2 + c[:, 1]**2) + s[:, 1]**2)).sum()
    vol = v6.sum() / 6
    return vol / 1000, vol * RHO, RHO * (ixx + iyy) * 1e-9


def write_stl(path, T, header=b'rw1dof flywheel D100, rev 3'):
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(T), dtype=[('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
    rec['n'], rec['v'] = n, T
    Path(path).write_bytes(header.ljust(80, b' ') + struct.pack('<I', len(T)) + rec.tobytes())


def main():
    raw = (HERE / 'Flywheel_D80.stl').read_bytes()
    n = struct.unpack('<I', raw[80:84])[0]
    ref = np.frombuffer(raw, np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), n, 84)['v'].astype(float)
    vr, mr, jr = props(ref)
    chk = mesh_tris(build(80, 57, 25, threaded=False))
    vc, mc, jc = props(chk)
    print(f'check  Flywheel_D80.stl  {vr:5.2f} cm3  Izz {jr:.3e}')
    print(f'check  rebuilt OD 80     {vc:5.2f} cm3  Izz {jc:.3e}  (volume {100 * (vc / vr - 1):+.1f} %, Izz {100 * (jc / jr - 1):+.1f} %)')

    wheel = build(100, 77, 33, threaded=True)
    assert wheel.status() == m3.Error.NoError and not wheel.is_empty()
    T = mesh_tris(wheel)
    P = T.reshape(-1, 3)
    v, m, j = props(T)
    print(f'rev 3  OD {np.hypot(P[:, 0], P[:, 1]).max() * 2:.1f}, height {P[:, 2].max():.1f} mm, {len(T)} triangles, '
          f'{v:.1f} cm3, solid {m:.1f} g, Izz {j:.3e} kg m2 ({j / jr:.2f}x the rev 2 wheel)')
    write_stl(HERE / 'Flywheel_D100.stl', T)
    V = T.copy()
    V[..., 1] = -V[..., 1]
    V[..., 2] = 15 - V[..., 2]                      # the viewer shows the wheel hub end down on the shaft
    VIEWER_JSON.write_text(json.dumps({'triangles': len(V), 'positions_b64': base64.b64encode(V.astype(np.float32).tobytes()).decode()}))
    print(HERE / 'Flywheel_D100.stl')


if __name__ == '__main__':
    main()
