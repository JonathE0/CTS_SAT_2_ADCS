"""Exploded detail of the motor mount at the arm tip: motor (stator back faces the arm), arm with window, M2.5 holes, board recess and lead channels,
and the AS5600 board envelope. Left: seen from the outboard side with the board lifted out. Right: seen from the table side with the motor pulled away.

    python render_mount_detail.py     # numpy + matplotlib; reads ../mechanical/viewer_data.json, writes ../preview/motor_mount_detail.png
"""
import base64
import json
from pathlib import Path

import matplotlib
import numpy as np
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

PROJ = Path(__file__).resolve().parent.parent
data = json.load(open(PROJ / 'mechanical' / 'viewer_data.json'))
parts = {n: (np.frombuffer(base64.b64decode(p['positions_b64']), np.float32).reshape(-1, 3, 3).astype(float), p['color']) for n, p in data['parts'].items()}
ZT = data['pivot'][2] - 100.0                      # arm tip centre height (L = 100)


def draw(ax, shifts, elev, azim, title):
    """All polygons go into ONE collection so matplotlib depth-sorts them against each other (separate collections are not sorted together)."""
    light = np.array([0.5, -0.4, 0.75]); light /= np.linalg.norm(light)
    polys, cols = [], []
    for n in ('arm', 'motor', 'board'):
        T, col = parts[n]
        P = T.copy()
        P[..., 0] += shifts.get(n, 0.0)
        if n == 'arm':
            P = P[P[..., 2].min(1) < ZT + 60]            # only the part of the arm near the tip, so the view stays close
        nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        nl = np.linalg.norm(nrm, axis=1, keepdims=True); nl[nl == 0] = 1
        sh = np.clip(np.abs((nrm / nl) @ light), 0, 1) * 0.55 + 0.45
        base = np.array(matplotlib.colors.to_rgb(col))
        polys.append(P)
        cols.append(np.clip(base[None, :] * sh[:, None], 0, 1))
    ax.add_collection3d(Poly3DCollection(np.concatenate(polys), facecolors=np.concatenate(cols), edgecolors='none', linewidths=0))
    ax.set_xlim(20, 85); ax.set_ylim(-35, 35); ax.set_zlim(ZT - 38, ZT + 62)
    ax.set_box_aspect((65, 70, 100), zoom=1.35)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=11)


fig = plt.figure(figsize=(14, 7.5), dpi=110)
ax1 = fig.add_subplot(1, 2, 1, projection='3d')
draw(ax1, {'board': 16.0, 'motor': -2.0}, 22, 28, 'Outboard side: board lifted out of its recess')
ax2 = fig.add_subplot(1, 2, 2, projection='3d')
draw(ax2, {'motor': -22.0, 'board': 16.0}, 22, 152, 'Table side: motor pulled away from the arm')
fig.suptitle('Motor mount on the stator back: 4 x M2.5 on D19 at 45 deg go board -> arm -> motor. The rotor\'s D12 hub sits in the window.', fontsize=11)
fig.subplots_adjust(left=0, right=1, bottom=0, top=0.92, wspace=0)
out = PROJ / 'preview'
out.mkdir(exist_ok=True)
fig.savefig(out / 'motor_mount_detail.png')
print('wrote', out / 'motor_mount_detail.png')
