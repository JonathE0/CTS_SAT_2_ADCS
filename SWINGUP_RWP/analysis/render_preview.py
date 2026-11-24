import base64, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

PROJ = Path(__file__).resolve().parent.parent      # needs numpy + matplotlib; reads mechanical/viewer_data.json
data = json.load(open(PROJ / 'mechanical' / 'viewer_data.json'))
ZP = data['pivot'][2]
parts = {}
for n, p in data['parts'].items():
    parts[n] = (np.frombuffer(base64.b64decode(p['positions_b64']), np.float32).reshape(-1, 3, 3).astype(float), p['color'], p['moving'])


def rot(T, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    P = T.copy()
    y, z = P[..., 1], P[..., 2] - ZP
    P[..., 1], P[..., 2] = y * c - z * s, y * s + z * c + ZP
    return P


def draw(ax, ang, elev, azim, title):
    light = np.array([0.4, -0.5, 0.75]); light /= np.linalg.norm(light)
    for n, (T, col, mov) in parts.items():
        if n == 'table':
            continue
        P = rot(T, ang) if mov else T
        nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        nl = np.linalg.norm(nrm, axis=1, keepdims=True); nl[nl == 0] = 1
        sh = np.clip((nrm / nl) @ light, 0, 1) * 0.55 + 0.45
        base = np.array(matplotlib.colors.to_rgb(col))
        fc = np.clip(base[None, :] * sh[:, None], 0, 1)
        if n == 'table':
            fc = np.concatenate([fc, np.full((len(fc), 1), 0.35)], axis=1)
        pc = Poly3DCollection(P, facecolors=fc, edgecolors='none', linewidths=0)
        ax.add_collection3d(pc)
    x0, x1, y0, y1, z0, z1 = -150, 0, -90, 90, -35, 0
    v = np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]])
    faces = [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[1,2,6,5],[0,3,7,4]]
    ax.add_collection3d(Poly3DCollection([v[f] for f in faces], facecolors=(0.79, 0.64, 0.48, 0.55), edgecolors=(0.5, 0.4, 0.3, 0.6), linewidths=0.6))
    ax.set_xlim(-150, 110); ax.set_ylim(-90, 90); ax.set_zlim(-265, 45)
    ax.set_box_aspect((260, 180, 310), zoom=1.45)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title, fontsize=11)


fig = plt.figure(figsize=(15, 9), dpi=110)
views = [(0, 12, -55, 'Hanging (arm 0 deg)'), (180, 12, -55, 'Inverted (arm 180 deg), the balance pose'),
         (0, 0, -90, 'Side view along the table edge, hanging')]
for i, (ang, el, az, t) in enumerate(views):
    ax = fig.add_subplot(1, 3, i + 1, projection='3d')
    draw(ax, ang, el, az, t)
fig.suptitle('Table-edge swing-up reaction-wheel pendulum (2804 motor), clipped to a 35 mm table (brown = table, left of the clip)', fontsize=12)
fig.subplots_adjust(left=0, right=1, bottom=0, top=0.93, wspace=0)
out = PROJ / 'preview'
out.mkdir(exist_ok=True)
fig.savefig(out / 'swingup_preview.png')
print('wrote', out / 'swingup_preview.png')
