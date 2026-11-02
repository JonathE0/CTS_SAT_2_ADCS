"""Table-edge clamp with an eye for the far end of the string.

    python make_table_mount.py        # needs numpy + manifold3d; reads ../frame_parts/make_frame_parts.py for helpers

Writes Table_Mount.stl. A C-clamp for a table top up to 40 mm thick: the bottom jaw carries an M8 bolt (hex nut pocket,
bolt pushes up on the underside of the table), the top jaw carries the same eye as the lid (7 mm hole). Print it lying on
its side (the C flat on the bed), no supports, so the layers run along the clamp's bending direction. Frame: x out from the
table edge (spine at x < 0), z up, y along the edge.
"""
import importlib.util
from pathlib import Path

import numpy as np
import manifold3d as m3

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('mfp', HERE.parent / 'frame_parts' / 'make_frame_parts.py')
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

OPEN, JAW_B, JAW_T, SPINE, DEPTH, W = 42.0, 12.0, 10.0, 10.0, 45.0, 30.0   # table gap, jaw thicknesses, spine, jaw depth, width (y)
EYE_T, EYE_W, EYE_HOLE, EYE_UP, EYE_X = 10.0, 18.0, 7.0, 20.0, 22.0       # eye thickness, width, hole, hole height above top jaw, x
BOLT, NUT_AF, NUT_H, BOLT_X = 8.6, 13.6, 7.0, 25.0                         # M8 clearance, nut across flats + clearance, pocket depth, bolt x
C = 3.0                                                                    # 45 degree corner chamfer


def clamp():
    zt0, zt1 = JAW_B + OPEN, JAW_B + OPEN + JAW_T
    x0, x1 = -SPINE, DEPTH
    pts = [(x0 + C, 0), (x1 - C, 0), (x1, C), (x1, JAW_B), (0, JAW_B), (0, zt0), (x1, zt0), (x1, zt1 - C), (x1 - C, zt1),
           (x0 + C, zt1), (x0, zt1 - C), (x0, C)]
    body = F.prism(pts, 0, W).rotate((90, 0, 0)).translate((0, W / 2, 0))              # profile in x-z, centred in y
    ze = zt1 + EYE_UP
    r = EYE_W / 2
    tab = [(EYE_X - r - 6, zt1 - 0.5), (EYE_X + r + 6, zt1 - 0.5), (EYE_X + r, zt1 + 6), (EYE_X + r, ze)]
    th = np.linspace(0, np.pi, 24)
    tab += [(EYE_X + r * np.cos(t), ze + r * np.sin(t)) for t in th][1:-1] + [(EYE_X - r, ze), (EYE_X - r, zt1 + 6)]
    eye = F.prism(tab, 0, EYE_T).rotate((90, 0, 0)).translate((0, EYE_T / 2, 0))
    hole = m3.Manifold.cylinder(EYE_T + 2, EYE_HOLE / 2, EYE_HOLE / 2, 48).rotate((90, 0, 0)).translate((EYE_X, EYE_T / 2 + 1, ze))
    bolt = m3.Manifold.cylinder(JAW_B + 2, BOLT / 2, BOLT / 2, 48).translate((BOLT_X, 0, -1))
    nut = m3.Manifold.cylinder(NUT_H + 1, NUT_AF / np.sqrt(3), NUT_AF / np.sqrt(3), 6).translate((BOLT_X, 0, JAW_B - NUT_H))
    return body + eye - hole - bolt - nut


def main():
    h = clamp()
    assert h.status() == m3.Error.NoError and not h.is_empty()
    bb = np.asarray(h.bounding_box())
    print(f'table mount: {h.volume() / 1000:.1f} cm3, about {h.volume() * 1.24e-3:.0f} g; '
          f'x {bb[0]:.0f}..{bb[3]:.0f}, y {bb[1]:.0f}..{bb[4]:.0f}, z {bb[2]:.0f}..{bb[5]:.0f}')
    F.write_stl(HERE / 'Table_Mount.stl', h)


if __name__ == '__main__':
    main()
