"""Weight basket for the right wall: two plug-hooks go into the two top-middle windows, a small open basket sits outside.

    python make_weight_basket.py        # needs numpy + manifold3d; reads ../frame_parts/make_frame_parts.py for the wall

Writes Weight_Basket.stl, in assembly position on the right wall (x = 75, outward = +x) and printed as it sits: the basket
floor and the flange's bottom edge on the bed, walls vertical, no supports. Drop steel washers, nuts or lead shot into the
basket to trim the balance.

  - hooks: two 22.2 x 22.2 mm plugs in the two 23 x 23 mm windows (y = +-15, z = 55), 2.9 mm deep, with 0.5 mm crush ribs
    on their side faces for a light press fit (0.1 mm interference); the flange behind the basket sits on the outside face
  - basket: 60 wide, 16 deep, 29 tall, 2 mm walls, 2.5 mm floor, 56 x 14 x 26.5 mm inside, about 20 cm3
"""
import importlib.util
from pathlib import Path

import numpy as np
import manifold3d as m3

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('mfp', HERE.parent / 'frame_parts' / 'make_frame_parts.py')
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)
box, place, union = F.box, F.place, F.union

WALL_C, WALL_T = F.C, F.WALL_T                    # right wall centre x = 75, 3 mm thick
X_IN, X_OUT = WALL_C - WALL_T / 2, WALL_C + WALL_T / 2
WIN, PLUG_CLR, PLUG_R = 23.0, 0.4, 2.6            # window size, clearance per side, plug corner radius
PLUG = WIN - 2 * PLUG_CLR                         # 22.2
WIN_U, WIN_Z = 15.0, 55.0                         # window centres: y = +-15, z = 55 (the top-middle pair)
PLUG_RECESS, RIB_H, RIB_W = 0.1, 0.5, 1.2         # plug inner face 0.1 mm inside the wall's face; crush rib height and width
FL_T, BW, Z0, Z1 = 3.0, 30.0, 41.0, 70.0          # flange thickness, basket half width, basket z span
DEPTH, WALL, FLOOR = 16.0, 2.0, 2.5               # basket depth from the flange face, wall and floor thickness

R = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float)      # prism (y, z, extrusion) -> world (x, y, z)


def rbox_yz(y0, y1, z0, z1, r, x0, x1):
    """Rounded rectangle in the wall plane (y-z), extruded along x."""
    return place(F.rbox(y0, y1, z0, z1, r, 0, x1 - x0), R, (x0, 0, 0))


def profile_xz(poly, y0, y1):
    """Polygon in (x, z) extruded along y from y0 to y1."""
    return F.prism(poly, 0, y1 - y0).rotate((90, 0, 0)).translate((0, y1, 0))


def basket():
    x_p0 = X_IN + PLUG_RECESS
    parts = []
    for c in (-WIN_U, WIN_U):                                                       # the two hooks: plugs with crush ribs
        parts.append(rbox_yz(c - PLUG / 2, c + PLUG / 2, WIN_Z - PLUG / 2, WIN_Z + PLUG / 2, PLUG_R, x_p0, X_OUT))
        for side in (-1, 1):
            for dz in (-6.0, 6.0):
                yf = c + side * PLUG / 2
                parts.append(box(x_p0, X_OUT, min(yf, yf + side * RIB_H), max(yf, yf + side * RIB_H), WIN_Z + dz - RIB_W / 2, WIN_Z + dz + RIB_W / 2))
    body = union(parts)
    cham = profile_xz([(x_p0, WIN_Z - PLUG / 2), (x_p0 + 1.4, WIN_Z - PLUG / 2), (x_p0, WIN_Z - PLUG / 2 + 1.4)], -30, 30)
    body = body - cham                                                              # 45 degree chamfer under the inner edge of the plugs
    xf = X_OUT + FL_T
    flange = rbox_yz(-BW, BW, Z0, Z1, 3.0, X_OUT, xf)                              # also the back wall of the basket
    shell = F.rbox(xf - 0.5, xf + DEPTH, -BW, BW, 3.0, Z0, Z1)
    inside = F.rbox(xf - 1.0, xf + DEPTH - WALL, -BW + WALL, BW - WALL, 1.0, Z0 + FLOOR, Z1 + 1)
    return body + flange + (shell - inside)


def main():
    h = basket()
    assert h.status() == m3.Error.NoError and not h.is_empty()
    wall = F.wall_panel()
    wall_left = place(wall, np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float), (-F.C - F.WALL_T / 2, -F.WALL_LEN / 2, -F.POCKET))
    wall_right = wall_left.rotate((0, 0, 180))
    ov = (h ^ wall_right).volume()
    bb = np.asarray(h.bounding_box())
    mesh = h.to_mesh()
    T = np.asarray(mesh.vert_properties, np.float64)[:, :3][np.asarray(mesh.tri_verts, np.int64)]
    nn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); area = np.linalg.norm(nn, axis=1) / 2
    nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-12
    off_bed = T[..., 2].mean(axis=1) > bb[2] + 0.25
    flat_under = ((-nn[:, 2]) > 0.95) & off_bed                                     # horizontal undersides off the bed
    steep = ((-nn[:, 2]) > 0.72) & off_bed
    print(f'basket: {h.volume() / 1000:.1f} cm3, about {h.volume() * 1.24e-3:.1f} g; '
          f'x {bb[0]:.1f}..{bb[3]:.1f}, y {bb[1]:.0f}..{bb[4]:.0f}, z {bb[2]:.0f}..{bb[5]:.1f}')
    print(f'interference with the right wall: {ov:.2f} mm3 (the eight crush ribs); '
          f'overhang steeper than 45 degrees off the bed: {area[steep].sum():.0f} mm2, of which fully horizontal {area[flat_under].sum():.0f} mm2 (the plug undersides, 1.5 mm deep)')
    assert ov < 6.0, 'plugs hit the wall'
    F.write_stl(HERE / 'Weight_Basket.stl', h)
    print(HERE / 'Weight_Basket.stl')


if __name__ == '__main__':
    main()
