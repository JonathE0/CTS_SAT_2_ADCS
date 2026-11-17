"""Preview renders of the balancing wheel module: standing on its pivot edge, and exploded along the wheel axis.

    python render_cube.py     # numpy + matplotlib; reads ../mechanical/viewer_data.json, writes ../preview/cube_standing.png and cube_exploded.png
"""
import base64
import json
import math
from pathlib import Path

import matplotlib
import numpy as np
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

PROJ = Path(__file__).resolve().parent.parent
data = json.load(open(PROJ / 'mechanical' / 'viewer_data.json'))
parts = {n: (np.frombuffer(base64.b64decode(p['positions_b64']), np.float32).reshape(-1, 3, 3).astype(float), p['color']) for n, p in data['parts'].items()}
UP = 90.0 / math.sqrt(2)                         # centre height above the pivot edge, 63.6 mm


def standing(P):
    """Cube-local (x, y, z) -> scene (X = x, Y = -z', Z = y' + UP) after turning the cube 45 degrees about x so the (-y, +z) edge points down."""
    c = s = math.sqrt(0.5)
    y, z = P[..., 1], P[..., 2]
    out = P.copy()
    yp, zp = y * c - z * s, y * s + z * c
    out[..., 1], out[..., 2] = -zp, yp + UP
    return out


def collect(shifts, tf, table=None):
    light = np.array([0.45, -0.5, 0.75]); light /= np.linalg.norm(light)
    polys, cols = [], []
    for n, (T, col) in parts.items():
        P = T.copy()
        P[..., 0] += shifts.get(n, 0.0)
        P = tf(P)
        nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        nl = np.linalg.norm(nrm, axis=1, keepdims=True); nl[nl == 0] = 1
        sh = np.clip(np.abs((nrm / nl) @ light), 0, 1) * 0.55 + 0.45
        base = np.array(matplotlib.colors.to_rgb(col))
        polys.append(P)
        cols.append(np.clip(base[None, :] * sh[:, None], 0, 1))
    P = np.concatenate(polys); C = np.concatenate(cols)
    if table is not None:
        x0, x1, y0, y1, z0, z1 = table
        v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]])
        quads = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4]]
        tri = []
        for q in quads:
            tri.append([v[q[0]], v[q[1]], v[q[2]]]); tri.append([v[q[0]], v[q[2]], v[q[3]]])
        P = np.concatenate([P, np.array(tri)])
        C = np.concatenate([C, np.tile(np.array([[0.79, 0.64, 0.48]]), (len(tri), 1))])
    return P, C


def draw(ax, shifts, tf, lims, aspect, view, title, table=None, zoom=1.0):
    P, C = collect(shifts, tf, table)
    ax.add_collection3d(Poly3DCollection(P, facecolors=C, edgecolors='none', linewidths=0))
    ax.set_xlim(*lims[0]); ax.set_ylim(*lims[1]); ax.set_zlim(*lims[2])
    ax.set_box_aspect(aspect, zoom=zoom)
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_axis_off()
    ax.set_title(title, fontsize=11)


# ---- standing on the pivot edge
fig = plt.figure(figsize=(14, 6.5), dpi=110)
for i, (az, t) in enumerate(((-58, 'Standing on its pivot edge'), (-120, 'From the other side'))):
    ax = fig.add_subplot(1, 2, i + 1, projection='3d')
    draw(ax, {}, standing, ((-70, 70), (-70, 70), (-6, 132)), (140, 140, 138), (16, az), t,
         table=(-100, 100, -100, 100, -8, 0), zoom=1.25)
fig.suptitle('Balancing wheel module, 90 x 90 x 44 mm: 2804 motor and D74 wheel, IMU on the pivot-corner pad, all other electronics off the body', fontsize=11)
fig.subplots_adjust(left=0, right=1, bottom=0, top=0.92, wspace=0)
fig.savefig(PROJ / 'preview' / 'cube_standing.png')

# ---- exploded along the wheel axis (cube-local, x horizontal)
fig = plt.figure(figsize=(14, 6.2), dpi=110)
ax = fig.add_subplot(1, 1, 1, projection='3d')
sh = {'cap': -66.0, 'wheel': -46.0, 'bolts': -46.0, 'motor': -10.0, 'board': -10.0, 'hw': -10.0, 'wires': -10.0, 'base': 34.0, 'imu': 34.0, 'screws': 52.0}
draw(ax, sh, lambda P: P, ((-100, 90), (-52, 52), (-52, 52)), (190, 104, 104), (20, -62),
     'Exploded along the wheel axis: cap ring, wheel cup, motor with its encoder board on the kit standoffs, base with the motor mount', zoom=1.2)
fig.subplots_adjust(left=0, right=1, bottom=0, top=0.94)
fig.savefig(PROJ / 'preview' / 'cube_exploded.png')
print('wrote', PROJ / 'preview')
