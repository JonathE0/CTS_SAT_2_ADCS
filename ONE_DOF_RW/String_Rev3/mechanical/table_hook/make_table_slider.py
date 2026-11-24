"""Adjustable clamp for the table hook: a slider that rides on the plate, a printed screw and a flat pad for the table underside.

    python make_table_slider.py        # needs numpy + manifold3d; reads make_table_hook.py and ../frame_parts/make_frame_parts.py

Writes Table_Hook_Slider.stl (hook and rider in one print, 0.4 mm apart, rider printed in place on pin hole -25), Slider_Screw.stl, Slider_Pad.stl, Slider_Pin.stl, in assembly position (table face x = 0, table top
z = 0, plate x 0..5). The rider wraps the plate (a U around its two edges and outer face) and carries a shelf that runs under
the table; the printed pin through the rider's outer wall and one of the plate's holes (10 mm apart) sets the height, the
screw (4 mm pitch, 45 degree flanks) takes up the last 10 mm and the pad spreads the load. Stick rubber on the pad's flat face.
Fits tables 5 to 45 mm thick (pin hole z = -15 ... -55, the table underside sits 10 mm below the pin).
"""
import importlib.util
from pathlib import Path

import numpy as np
import manifold3d as m3

HERE = Path(__file__).parent
def load(name, p):
    spec = importlib.util.spec_from_file_location(name, p); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
H = load('hook', HERE / 'make_table_hook.py')
F = H.F
box = F.box

T, CL, WALL = H.T, 0.4, 4.0                      # plate thickness, print-in-place clearance (0.4 mm all round), rider wall
HW = 15.0                                        # plate half width
SX = -25.0                                       # screw axis x (under the table, 25 mm in from the edge)
PITCH, CAM_R, CAM_E, NUT_CL = 6.0, 6.0, 0.9, 0.35


def cyl_z(r, z0, z1, x=SX, y=0.0, seg=64):
    return m3.Manifold.cylinder(z1 - z0, r, r, seg).translate((x, y, z0))


def cyl_x(r, x0, x1, y=0.0, z=0.0, seg=48):
    return m3.Manifold.cylinder(x1 - x0, r, r, seg).rotate((0, 90, 0)).translate((x0, y, z))


def thread(z0, z1, r_cam, x=SX):
    """Single-start thread as an eccentric disc twisted 360 degrees per pitch: radius 5.1..6.9 for r_cam 6; lateral shift per mm of height is 0.94 so the flanks never overhang more than 45 degrees."""
    h = z1 - z0
    cs = m3.CrossSection.circle(r_cam, 48).translate((CAM_E, 0))
    t = m3.Manifold.extrude(cs, h, int(h / PITCH * 24), 360.0 * h / PITCH)
    return t.rotate((0, 0, 360.0 * z0 / PITCH)).translate((x, 0, z0))      # phase fixed to absolute z, so screw and nut are the same helix


def rider(zh=0.0):
    ow = box(T + CL, T + CL + WALL, -HW - CL - WALL, HW + CL + WALL, -20, 10)            # outer wall (x 5.3 to 9.3)
    sw = [box(CL, T + CL + WALL, s * (HW + CL), s * (HW + CL + WALL), -20, 10) if s > 0 else
          box(CL, T + CL + WALL, -(HW + CL + WALL), -(HW + CL), -20, 10) for s in (1, -1)]
    rails = [box(-45, CL, HW + CL, HW + CL + WALL, -20, -12), box(-45, CL, -(HW + CL + WALL), -(HW + CL), -20, -12)]
    shelf = box(-45, -CL, -(HW + CL + WALL), HW + CL + WALL, -20, -12)                  # shelf under the table
    boss = cyl_z(13.0, -32, -12)                                                         # nut for the screw, 20 mm long
    body = ow + sw[0] + sw[1] + rails[0] + rails[1] + shelf + boss
    body = body - cyl_x(2.7, T, T + CL + WALL + 1, 0, 0)                                 # pin hole in the outer wall (5.4)
    body = body - thread(-33, -11, CAM_R + NUT_CL)                                       # threaded hole
    return body.translate((0, 0, zh))


def screw():
    th = thread(-52, -16, CAM_R)
    peg = cyl_z(4.5, -16.5, -12)
    knob = cyl_z(16.0, -61, -52)
    for k in range(10):                                                                  # scallops for grip
        a = 2 * np.pi * k / 10
        knob = knob - cyl_z(3.2, -62, -51, SX + 16.0 * np.cos(a), 16.0 * np.sin(a), 24)
    return th + peg + knob


def pad():
    return cyl_z(14.0, -16, -10) - cyl_z(4.6, -17, -12.0)                                # socket 9.2 mm, 4 deep


def pin():
    shaft = cyl_x(2.5, -0.5, T + CL + WALL + 0.5, 0, 0) - m3.Manifold.cube((1.2, 6, 6), True).translate((-0.5, 0, 0))   # small tip flat
    head = cyl_x(5.0, T + CL + WALL, T + CL + WALL + 2.5, 0, 0)
    return shaft + head


def vol_overlap(a, b):
    return (a ^ b).volume()


def main():
    R, S, P, N = rider(), screw(), pad(), pin()
    hook = H.hook()
    zh = -25.0                                   # the pin goes in the -25 hole: table underside at -35, a 35 mm table
    Rz = R.translate((0, 0, zh)); Sz = S.translate((0, 0, zh)); Pz = P.translate((0, 0, zh)); Nz = N.translate((0, 0, zh))
    table = box(-300, -0.0, -150, 150, -35, 0)                                           # square-edged 35 mm table, top at z = 0
    for name, m in (('rider', R), ('screw', S), ('pad', P), ('pin', N)):
        assert m.status() == m3.Error.NoError and not m.is_empty(), name
        bb = np.asarray(m.bounding_box())
        print(f'{name:6s} {m.volume() / 1000:5.1f} cm3  {m.volume() * 1.24e-3:5.1f} g   x {bb[0]:.0f}..{bb[3]:.0f}  y {bb[1]:.0f}..{bb[4]:.0f}  z {bb[2]:.0f}..{bb[5]:.0f}')
    print('overlaps at the 35 mm table, mm3:',
          f'rider-plate {vol_overlap(Rz, hook):.2f}, rider-table {vol_overlap(Rz, table):.2f}, rider-screw {vol_overlap(Rz, Sz):.2f}, '
          f'pad-table {vol_overlap(Pz, table):.2f}, pad-screw {vol_overlap(Pz, Sz):.2f}, pin-rider {vol_overlap(Nz, Rz):.2f}, pin-plate {vol_overlap(Nz, hook):.2f}, rider-hookarm {vol_overlap(Rz, hook):.2f}')
    # reach of the screw: pad top at -10 + zh = -35 is the table underside; screw can drop 25 mm before the thread leaves the nut
    combo = hook + Rz                                                                    # one print: the rider sits on the plate with a 0.4 mm gap, supports hold it, snap them off and slide it
    assert combo.status() == m3.Error.NoError and (combo.num_vert() > 0)
    gap = (hook ^ Rz).volume()
    print(f'hook + rider as one print: {combo.volume() / 1000:.1f} cm3, {combo.volume() * 1.24e-3:.0f} g, overlap {gap:.2f} mm3')
    for name, m in (('Table_Hook_Slider', combo), ('Slider_Screw', S), ('Slider_Pad', P), ('Slider_Pin', N)):
        F.write_stl(HERE / f'{name}.stl', m)


if __name__ == '__main__':
    main()
