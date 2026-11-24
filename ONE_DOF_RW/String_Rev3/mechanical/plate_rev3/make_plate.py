"""Orient every new or changed rev 3 part for printing, lay them out on one build plate and write Rev3_plate.stl.

    python make_plate.py        # needs numpy

Reads ../../printing/print_ready/stl/*.stl (assembly positions), writes ./inputs/*.stl lying on z = 0, each in its print orientation, and
../../printing/print_ready/stl/Rev3_plate.stl with all of them laid out (about 220 x 162 mm, 6 mm apart):
hook + slider on its side (profile flat), basket upright (floor down, supports under the lips), screw knob down, pin head down,
pad flat, wheel and tray as they are.
"""
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
SRC = HERE / '..' / '..' / 'printing' / 'print_ready' / 'stl'
OUT = HERE / 'inputs'
JOBS = [('Table_Hook_Slider.stl', (90, 0, 90)), ('Weight_Basket.stl', (0, 0, 0)), ('Slider_Screw.stl', (0, 0, 0)),
        ('Slider_Pad.stl', (0, 0, 0)), ('Slider_Pin.stl', (0, 90, 0)), ('Flywheel_D100.stl', (0, 0, 0)), ('parts/pack_tray.stl', (0, 0, 0))]


def read_stl(p):
    b = Path(p).read_bytes()
    n = int(np.frombuffer(b, '<u4', 1, 80)[0])
    return np.frombuffer(b, np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), n, 84)['v'].astype(np.float64)


def write_stl(p, t):
    rec = np.zeros(len(t), np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    nn = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-12
    rec['n'], rec['v'] = nn, t
    Path(p).write_bytes(b'rev3 plate'.ljust(80, b' ') + np.uint32(len(t)).tobytes() + rec.tobytes())


def rot(t, deg):
    a, b, c = np.radians(deg)
    Rx = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    Ry = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    Rz = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    return t @ (Rz @ Ry @ Rx).T


SLOT = {'Flywheel_D100.stl': (0, 0), 'pack_tray.stl': (106, 0), 'Weight_Basket.stl': (192, 0), 'Table_Hook_Slider.stl': (0, 106),
        'Slider_Screw.stl': (121, 106), 'Slider_Pad.stl': (159, 106), 'Slider_Pin.stl': (193, 106)}     # lower left corner of each part on the plate


def main():
    OUT.mkdir(exist_ok=True)
    plate = []
    for name, deg in JOBS:
        t = rot(read_stl(SRC / name), deg)
        t -= t.reshape(-1, 3).min(axis=0)
        write_stl(OUT / Path(name).name, t)
        plate.append(t + np.array([*SLOT[Path(name).name], 0]))
        print(f'{Path(name).name:24s} {t[..., 0].max():6.1f} x {t[..., 1].max():6.1f} x {t[..., 2].max():6.1f} mm at {SLOT[Path(name).name]}')
    allt = np.concatenate(plate)
    print('plate:', allt[..., 0].max().round(1), 'x', allt[..., 1].max().round(1), 'mm')
    write_stl(SRC / 'Rev3_plate.stl', allt)


if __name__ == '__main__':
    main()
