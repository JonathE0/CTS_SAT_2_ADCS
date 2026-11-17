"""A labelled section through the wheel axis, cut from the CAD: ../preview/cube_section.png.

    python render_section.py     # numpy + matplotlib + manifold3d

The lower half is cut along the -y arm (through a brass foot, its mount screw and the motor's leads). The upper half is cut 22.5 degrees round from +y, through a
weight bolt and between two arms.
"""
import importlib.util
import math
from pathlib import Path

import matplotlib
import numpy as np
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('cube', HERE.parent / 'mechanical' / 'make_cube_parts.py')
cube = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cube)
box, union = cube.box, cube.union

mot = cube.motor()
x_can = cube.MOT_X0 + cube.CAN_L
parts = [('frame', union([cube.base(), cube.cap()]), '#cfc6ad'),
         ('wheel', cube.place_wheel(cube.wheel()), '#e0962f'),
         ('bolts', union(cube.bolt_meshes()) + cube.rotor_screws(), '#8d9aa3'),
         ('can', mot ^ box(-60, x_can, -60, 60, -60, 60), '#b23a2e'),
         ('stator', mot ^ box(x_can, 60, -60, 60, -60, 60), '#7d2a22'),
         ('board', cube.enc_board(), '#1f5fa8'),
         ('brass', cube.kit_hardware(), '#c9a227'),
         ('screws', cube.mount_screws(), '#5f6b73'),
         ('leads', cube.leads(), '#3a3a3a')]


def patches(solid, upper):
    """The solid's section as matplotlib paths: upper half cut at 22.5 degrees from +y, lower half along -y."""
    m = solid.rotate((-22.5, 0, 0)) if upper else solid
    half = box(-60, 60, 0.0, 60, -1, 1) if upper else box(-60, 60, -60, 0.0, -1, 1)
    polys = (m ^ half).slice(0.0).to_polygons()
    if not polys:
        return None
    verts, codes = [], []
    for p in polys:
        p = np.asarray(p)
        verts += list(p) + [p[0]]
        codes += [MPath.MOVETO] + [MPath.LINETO] * (len(p) - 1) + [MPath.CLOSEPOLY]
    return MPath(np.array(verts), codes)


fig, ax = plt.subplots(figsize=(13, 10.5), dpi=110)
for name, solid, col in parts:
    for upper in (True, False):
        path = patches(solid, upper)
        if path is not None:
            ax.add_patch(PathPatch(path, facecolor=col, edgecolor='#222', linewidth=0.6))
ax.plot([-26, 26], [0, 0], color='#444', lw=0.8, ls=(0, (10, 3, 2, 3)))
ax.plot([-22, -22], [-49, 49], color='#999', lw=0.7, ls=':'); ax.plot([22, 22], [-49, 49], color='#999', lw=0.7, ls=':')


def note(text, xy, xytext, ha='left'):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=10, ha=ha, va='center',
                arrowprops=dict(arrowstyle='-', color='#333', lw=0.8, shrinkA=2, shrinkB=1))


xf = cube.MOT_X0 - cube.FLOOR_T
xr = xf + cube.RIM_L
note('wheel: the floor screws to the rotor face\n(4 x M2.5 x 5 on the 16 mm circle)', (xf + 1.2, 8.0), (-62, 20), 'left')
note('inner wall over the spinning can', (cube.MOT_X0 + 5, 18.2), (-62, 31), 'left')
note('rim, r 27 to 37: beside the motor only', (xf + 8, 35.5), (-62, 42), 'left')
note('M4 x 12 weight bolt, head sunk\ninto the rim\'s back end', (xr - 2.0, 32.0), (28, 46), 'left')
note('motor: spinning can', (cube.MOT_X0 + 5, 10.0), (-62, 9), 'left')
note('fixed stator base', (x_can + 2, -13.0), (-62, -12), 'left')
note('the three leads leave the back face here.\nThe rim ends 1.2 mm before it', (cube.STATOR_X + 1.2, -30.0), (-62, -24), 'left')
note('encoder board; its plugs go in from the side', (cube.BOARD_X0 + 0.8, 13.0), (28, 34), 'left')
note('magnet ring', (cube.STATOR_X + 3.0, 4.5), (28, 22), 'left')
note('brass foot (the kit\'s own standoff)', (cube.BOARD_X1 + 3.5, -17.0), (28, -6), 'left')
note('pad, part of the base', (cube.PAD_X + 0.8, -20.4), (28, -16), 'left')
note('M2.5 x 8 from outside; its head sits in a\npocket with a 38 degree roof (no supports)', (cube.X_SEAT + 0.8, -17.0), (28, -27), 'left')
note('motor mount: hub ring and arms in the\nbase ring\'s own 5 mm slab, flat on the bed', (19.5, -31.0), (28, -39), 'left')
note('cap ring', (-19.5, -42.5), (-62, -42), 'left')
note('2.9 mm spare for a longer kit', (-20.5, -5.5), (-62, -2), 'left')
ax.text(-22, 50.5, '-x face', ha='center', fontsize=9, color='#666'); ax.text(22, 50.5, '+x face (the bed face of the base)', ha='center', fontsize=9, color='#666')
ax.text(0, -53.5, 'Section through the wheel axis. Lower half: along one arm, through a foot, its screw and the leads. Upper half: through a weight bolt, between two arms.',
        ha='center', fontsize=9.5, color='#444')
ax.set_xlim(-64, 66); ax.set_ylim(-56, 53); ax.set_aspect('equal'); ax.axis('off')
ax.set_title('Balancing wheel module: how the wheel, the 2804 motor kit and the base go together (mm, to scale)', fontsize=12)
fig.tight_layout()
out = HERE.parent / 'preview' / 'cube_section.png'
fig.savefig(out)
print('wrote', out)
