"""Writes slicer-ready STLs, each turned into its print orientation and standing on z = 0, then re-reads every file and checks it, including how much of the
surface overhangs more than 40 degrees from vertical (a flat ceiling is 90 degrees).

    python export_print_ready.py        # needs numpy + manifold3d

  Frame_Base.stl      outside face (x = 22) on the bed: the motor mount lies on the bed with its screw-head pockets, the pads, stubs and tenons point up.
  Frame_Cap.stl       ring face (x = -22) on the bed, collars pointing up.
  Wheel_D74_2804.stl  the floor's outside face (z = 0) on the bed, the cup opening up, the weight-bolt counterbores opening up.
  (no pin: the hub hole stays, but no pin is printed or glued in)
  Joint_Test.stl      one corner of the base and one of the cap, to test the tenon fit before printing the big parts.

Units are mm. The files are the same solids as in the assembly, only moved, so the checks in ../analysis still apply.
"""
import importlib.util
import struct
from pathlib import Path

import numpy as np
import manifold3d as m3

HERE = Path(__file__).parent
OUT = HERE.parent / 'print_ready' / 'stl'
spec = importlib.util.spec_from_file_location('cube', HERE / 'make_cube_parts.py')
cube = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cube)
box, F = cube.box, cube.F
LIMIT = 40.0                                   # degrees from vertical


def centre_xy(m):
    bb = np.asarray(m.bounding_box())
    return m.translate((-(bb[0] + bb[3]) / 2, -(bb[1] + bb[4]) / 2, -bb[2]))


def orient_base(m):
    """(x, y, z) -> (z, y, -x), then x = HX (the ring's outer face) lands on z = 0."""
    return m.rotate((0, 90, 0)).translate((0, 0, cube.HX))


def orient_cap(m):
    """(x, y, z) -> (-z, y, x), then x = -HX lands on z = 0."""
    return m.rotate((0, -90, 0)).translate((0, 0, cube.HX))


def read_stl(path):
    raw = Path(path).read_bytes()
    n = struct.unpack('<I', raw[80:84])[0]
    rec = np.frombuffer(raw, np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), n, 84)
    return rec['v'].astype(np.float64)


def analyse(path, expect_volume):
    T = read_stl(path)
    V = T.reshape(-1, 3)
    a, b, c = T[:, 0], T[:, 1], T[:, 2]
    vol = np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6
    ids = {}
    idx = np.array([ids.setdefault(tuple(r), len(ids)) for r in np.round(V, 4)]).reshape(-1, 3)
    edges = np.concatenate([idx[:, [0, 1]], idx[:, [1, 2]], idx[:, [2, 0]]])
    directed = {}
    for e in map(tuple, edges):
        directed[e] = directed.get(e, 0) + 1
    open_edges = sum(1 for e, k in directed.items() if directed.get((e[1], e[0]), 0) != k or k != 1)
    nrm = np.cross(b - a, c - a)
    ln = np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)
    area = ln / 2
    nz = nrm[:, 2] / ln
    zmin = T[..., 2].min(1)
    bed = area[(zmin < 0.02) & (T[..., 2].max(1) < 0.02) & (nz < -0.99)].sum()
    down = (nz < 0) & (zmin > 0.2)                                           # faces that look down and are not on the bed
    ang = np.degrees(np.arcsin(np.clip(-nz, 0, 1)))                          # overhang angle from vertical
    over = area[down & (ang > LIMIT)].sum()
    flat = area[down & (ang > 85)].sum()
    heights = sorted({round(float(h), 1) for h in T[..., 2].mean(1)[down & (ang > 85)]})
    return dict(tris=len(T), lo=V.min(0), hi=V.max(0), vol=vol, dvol=100 * (vol / expect_volume - 1), open_edges=open_edges, bed=bed,
                over=over, flat=flat, share=100 * over / area.sum(), heights=heights, worst=float(ang[down].max()) if down.any() else 0.0)


def layer_check(m, h=0.2, limit=LIMIT):
    """What a slicer sees: each layer is compared with the one below it grown by h * tan(limit). Whatever sticks out beyond that is an overhang steeper than the
    limit (a flat ceiling sticks out entirely). Returns the worst single-layer area (mm2), the layer count that exceeds 0.5 mm2, and the height of the worst one."""
    d = h * np.tan(np.radians(limit))
    top = np.asarray(m.bounding_box())[5]
    worst, bad, zw = 0.0, 0, 0.0
    z = h * 1.5
    prev = m.slice(h * 0.5)
    while z < top:
        cur = m.slice(z)
        a = (cur - prev.offset(d, m3.JoinType.Round)).area()
        if a > 0.5:
            bad += 1
        if a > worst:
            worst, zw = a, z
        prev = cur
        z += h
    return worst, bad, zw


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hb, hc = cube.base(), cube.cap()
    wheel = cube.wheel()
    H = cube.H

    # joint test: one corner of each part, cut from the real geometry (corner y, z > 0 side)
    jb = (cube.base_frame() - cube.x_edge_cutters()) ^ box(cube.JOINT_X - cube.TENON_L - 1, cube.HX + 1, 28.0, H + 1, 28.0, H + 1)
    jc = hc ^ box(-cube.HX - 1, cube.JOINT_X + 1, 28.0, H + 1, 28.0, H + 1)
    jb, jc = centre_xy(orient_base(jb)).translate((-14.0, 0, 0)), centre_xy(orient_cap(jc)).translate((14.0, 0, 0))

    fit_sockets, fit_peg, fit_pins = cube.fit_test_parts()
    parts = {'Frame_Base': centre_xy(orient_base(hb)), 'Frame_Cap': centre_xy(orient_cap(hc)),
             'Wheel_D74_2804': centre_xy(wheel), 'Joint_Test': jb + jc, 'Fit_Test': centre_xy(cube.fit_test()),
             'Fit_Test_Sockets': centre_xy(fit_sockets), 'Fit_Test_Peg': centre_xy(fit_peg), 'Fit_Test_Pins': centre_xy(fit_pins)}
    print(f"{'file':16s} {'triangles':>9} {'size X x Y x Z (mm)':>22} {'volume cm3':>10} {'vs CAD':>7} {'open':>5} {'bed contact':>11} {'over 40 deg':>12} {'share':>6} {'worst':>6}")
    for n, m in parts.items():
        assert m.status() == m3.Error.NoError and not m.is_empty(), n
        F.write_stl(OUT / f'{n}.stl', m)
        r = analyse(OUT / f'{n}.stl', m.volume())
        sz = r['hi'] - r['lo']
        print(f"{n:16s} {r['tris']:9d} {sz[0]:6.1f} x {sz[1]:5.1f} x {sz[2]:5.1f} {r['vol'] / 1000:10.2f} {r['dvol']:+6.2f}% {r['open_edges']:5d} {r['bed']:8.0f} mm2 {r['over']:8.0f} mm2 {r['share']:5.1f}% {r['worst']:5.0f}d   z min {r['lo'][2]:+.3f}")
        wst, nbad, zw = layer_check(m)
        print(f"{'':16s} layer check at {LIMIT:.0f} deg, 0.2 mm layers: worst layer overhangs {wst:.1f} mm2 (at z = {zw:.1f}), {nbad} layers above 0.5 mm2")
        if r['flat'] > 0:
            print(f"{'':16s} flat ceilings {r['flat']:.0f} mm2 at heights {', '.join(str(h) for h in r['heights'][:8])} mm")
    # negative control: the same base with plain flat-roofed counterbores for the screw heads must show an overhang, or the check is not testing anything
    wst, nbad, zw = layer_check(centre_xy(orient_base(cube.base(flat_roof=True))))
    print(f"control: the base with flat-roofed screw-head pockets instead of tapered ones: worst layer overhangs {wst:.1f} mm2 at z = {zw:.1f}, {nbad} layers above 0.5 mm2")
    print('wrote', OUT)


if __name__ == '__main__':
    main()
