"""Weight basket for the right wall: two J-hooks hang over the rib under the two top-middle windows, a wide open basket hangs below them on the outside.

    python make_weight_basket.py        # needs numpy + manifold3d; reads ../frame_parts/make_frame_parts.py for the wall

Writes Weight_Basket.stl, in assembly position on the right wall (x = 75, outward = +x) and print it on its back: the flat back face
on the bed, the hooks and basket standing up from it, no supports (the 2.5 mm lips are a 6 mm overhang). Drop steel washers, nuts or lead shot into the basket to trim the balance.

  - hooks: each is a J: an arm lies on the sill of a 23 x 23 mm window (y = +-15, z = 55), a lip on the inside drops behind the
    7 mm rib under the window, a strap on the outside runs down from each arm to the basket. The rib sits in the pocket.
  - fit: lift the basket 12 mm, push the lips through the windows, lower it. The weight pulls the lips against the inside of
    the rib, so it cannot pull off outward. Lift 12 mm and pull out to remove.
  - basket: 90 wide, 18 deep, 25.5 tall, 2 mm walls, 2.5 mm floor
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
WIN_U, WIN_Z, WIN = 15.0, 55.0, 23.0              # window centres y = +-15, z = 55; 23 mm square
SILL = WIN_Z - WIN / 2                            # 43.5, top of the rib under the window
CL, LIP_T, LIP_Z0 = 0.3, 3.0, 31.5                # clearance, lip thickness, lip bottom (5 mm below the rib's bottom edge, so it wraps the whole rib)
ARM_H, HOOK_HW = 8.0, 8.0                         # arm height, hook half width in y
BW, Z0, Z1 = 45.0, 18.0, SILL                     # basket half width (90 wide); it hangs below the window sill, z 18..43.5
FL_T, DEPTH, WALL, FLOOR = 3.0, 18.0, 2.0, 2.5    # flange thickness, basket depth from the flange face, wall, floor

R = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float)      # prism (y, z, extrusion) -> world (x, y, z)


def rbox_yz(y0, y1, z0, z1, r, x0, x1):
    """Rounded rectangle in the wall plane (y-z), extruded along x."""
    return place(F.rbox(y0, y1, z0, z1, r, 0, x1 - x0), R, (x0, 0, 0))


def profile_xz(poly, y0, y1):
    """Polygon in (x, z) extruded along y from y0 to y1."""
    return F.prism(poly, 0, y1 - y0).rotate((90, 0, 0)).translate((0, y1, 0))


def basket():
    xl, xo = X_IN - CL - LIP_T, X_OUT + CL                                          # lip inner face x, flange inner face x
    xf = xo + FL_T
    za = SILL + CL + ARM_H                                                          # top of the arms
    parts = []
    for c in (-WIN_U, WIN_U):                                                       # the two J-hooks, edges rounded
        y0, y1 = c - HOOK_HW, c + HOOK_HW
        parts.append(rbox_yz(y0, y1, SILL + CL, za, 2.5, xl, xo + 1))               # arm through the window
        parts.append(rbox_yz(y0, y1, LIP_Z0, za, 2.0, xl, xl + LIP_T))              # lip behind the rib
        parts.append(rbox_yz(y0, y1, Z0 + 3, za, 4.0, xo, xf))                      # strap down to the basket
    flange = rbox_yz(-BW, BW, Z0, Z1, 3.0, xo, xf)                                 # back wall of the basket, in front of the lower windows
    shell = F.rbox(xf - 0.5, xf + DEPTH, -BW, BW, 4.0, Z0, Z1)
    inside = F.rbox(xf - 1.0, xf + DEPTH - WALL, -BW + WALL, BW - WALL, 2.0, Z0 + FLOOR, Z1 + 1)
    FR = 3.0                                                                        # 45 degree fillets where the floor meets the back and the front
    fil = [profile_xz([(xf, Z0 + FLOOR), (xf + FR, Z0 + FLOOR), (xf, Z0 + FLOOR + FR)], -BW + WALL, BW - WALL),
           profile_xz([(xf + DEPTH - WALL, Z0 + FLOOR), (xf + DEPTH - WALL - FR, Z0 + FLOOR), (xf + DEPTH - WALL, Z0 + FLOOR + FR)], -BW + WALL, BW - WALL)]
    return union(parts) + flange + (shell - inside) + union(fil)


def main():
    h = basket()
    assert h.status() == m3.Error.NoError and not h.is_empty()
    wall = F.wall_panel()
    wall_left = place(wall, np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float), (-F.C - F.WALL_T / 2, -F.WALL_LEN / 2, -F.POCKET))
    wall_right = wall_left.rotate((0, 0, 180))
    ov = (h ^ wall_right).volume()
    lift = 0.0
    ok = [(dz, (h.translate((0, 0, dz)) ^ wall_right).volume()) for dz in (12.0, 13.0, 14.0)]
    bb = np.asarray(h.bounding_box())
    print(f'basket: {h.volume() / 1000:.1f} cm3, about {h.volume() * 1.24e-3:.1f} g; '
          f'x {bb[0]:.1f}..{bb[3]:.1f}, y {bb[1]:.0f}..{bb[4]:.0f}, z {bb[2]:.1f}..{bb[5]:.1f}')
    print(f'hung: {ov:.2f} mm3 overlap with the wall; lifted 12/13/14 mm (install position): ' + ', '.join(f'{v:.2f}' for _, v in ok))
    assert ov < 0.5, 'hooks hit the wall'
    F.write_stl(HERE / 'Weight_Basket.stl', h)
    print(HERE / 'Weight_Basket.stl')


if __name__ == '__main__':
    main()
