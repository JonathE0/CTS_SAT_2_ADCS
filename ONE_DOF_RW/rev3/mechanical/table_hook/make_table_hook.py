"""Table-edge hook for the far end of the string: an L-bracket that hangs over a square table edge, with a pinhole for the string.

    python make_table_hook.py        # needs numpy + manifold3d; reads ../frame_parts/make_frame_parts.py for helpers

Writes Table_Hook.stl. The tab lies on the table top, a 90 degree bend carries the plate down the edge's face, and a small stub at
the bottom, a 16 mm wide round-ended tab with a 7 mm pinhole, carries the string like the lid eye. It works for any table thickness: the plate just hangs
down the face and nothing grips the underside. Print it lying on its side (the profile flat on the bed), no supports; the
layers then run along the bending direction. Frame: face of the table at x = 0 (table at x < 0), table top at z = 0, y along the edge.
"""
import importlib.util
from pathlib import Path

import numpy as np
import manifold3d as m3

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('mfp', HERE.parent / 'frame_parts' / 'make_frame_parts.py')
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

T, LT, W = 5.0, 45.0, 30.0                 # plate and tab thickness, tab length on the table top, width along the edge
PL = 96.5                                  # plate length down the face
EYE_R, EYE_HOLE, EYE_T = 8.0, 7.0, 10.0    # stub: round-ended tab 16 mm wide, 10 mm thick along the hole, 7 mm hole (hole axis along y, like the lid eye)
EYE_X, EYE_Z = T / 2, -(PL + 5.5)          # stub centre: on the plate's centre line, 102 mm below the table top
STRING_X, STRING_Z = EYE_X, EYE_Z          # where the string leaves the hook
PIN_Z = [-15.0, -25.0, -35.0, -45.0, -55.0]        # 5.4 mm holes through the plate at y = 0: the slider's pin stops, 10 mm apart
PIN_HOLE = 5.4


def arc(cx, cz, r, a0, a1, n=8):
    t = np.radians(np.linspace(a0, a1, n))
    return [(cx + r * np.cos(u), cz + r * np.sin(u)) for u in t]


def profile():
    p = [(-LT + 1.5, 0), (-1.5, 0), (0, -1.5), (0, -PL), (T, -PL), (T, 1.0)]         + arc(T - 4.0, 1.0, 4.0, 0, 90, 10)[1:] + [(-LT + 1.5, T), (-LT, T - 1.5), (-LT, 1.5)]
    return p


def stub_profile():
    """Round-ended stub below the plate, flared 45 degrees into it like the lid's eye."""
    r, x0 = EYE_R, EYE_X
    return [(0, -PL + 6.5), (T, -PL + 6.5), (T, -PL), (x0 + r, EYE_Z)] + arc(x0, EYE_Z, r, 0, -180, 16)[1:] + [(x0 - r, EYE_Z), (0, -PL)]


def hook():
    pts = profile()
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if a < 0:
        pts = pts[::-1]
    h = F.prism(pts, 0, W).rotate((90, 0, 0)).translate((0, W / 2, 0))
    stub = F.prism(stub_profile(), 0, EYE_T).rotate((90, 0, 0)).translate((0, EYE_T / 2, 0))
    h = h + stub - m3.Manifold.cylinder(EYE_T + 2, EYE_HOLE / 2, EYE_HOLE / 2, 48).rotate((90, 0, 0)).translate((EYE_X, EYE_T / 2 + 1, EYE_Z))   # string pinhole
    for z in PIN_Z:
        h = h - m3.Manifold.cylinder(T + 1.0, PIN_HOLE / 2, PIN_HOLE / 2, 32).rotate((0, 90, 0)).translate((-0.5, 0, z))
    return h


def main():
    h = hook()
    assert h.status() == m3.Error.NoError and not h.is_empty()
    bb = np.asarray(h.bounding_box())
    print(f'table hook: {h.volume() / 1000:.1f} cm3, about {h.volume() * 1.24e-3:.0f} g; '
          f'x {bb[0]:.0f}..{bb[3]:.0f}, y {bb[1]:.0f}..{bb[4]:.0f}, z {bb[2]:.0f}..{bb[5]:.0f}; string at x={STRING_X:.1f}, {-STRING_Z:.0f} mm below the table top')
    F.write_stl(HERE / 'Table_Hook.stl', h)


if __name__ == '__main__':
    main()
