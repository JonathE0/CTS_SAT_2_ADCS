# RW1DOF testbed, rev 3

Rev 2 frame with four changes: a **100 mm flywheel** (was 80 mm), its ten rim weight-bolt holes now **threaded M4**, the **electronics moved to the outside** of the left wall, and a **battery tray that snaps** into the baseplate's existing slits instead of being screwed on. Only one printed frame part changed, the pack tray; the baseplate, walls, lid, lock rods and cotters are as in rev 2, so use those STLs, G-code and the slicer script from `../rev2`.

## Battery tray snap fit

The tray snaps onto the rev 2 baseplate without screws, and **the baseplate is unchanged** (`rev2/.../base_pillars.stl`, byte for byte). It uses the plate's four existing plain slits (33.4 x 6.4 mm, at x = +-28 + 0 to 30, y = +-39).

- **Put it on:** load the pack, hold the tray under the plate and push it straight up. The four spring leaves flex in, pass through the slits and click out over the slit edges. Nothing to line up in y.
- **Take it off:** pull the tray down firmly, or press the four barbs in from above (they stand 2.6 mm above the plate) and lower it. It snaps off the same way it went on.
- **Trim:** it slides along the slits between tray x = 5 and 25 mm.
- **The leaves:** each is 8 mm wide and 2 mm thick, about 22.6 mm free length, with a 1.1 mm barb that has 45 degree ramps on both sides. The barb reaches 0.9 mm over the plate. Pushing on or pulling off bends a leaf 1.2 mm, about 0.7 % strain, about 4 N per leaf, 17 N for all four, roughly the pull of a 1.7 kg weight. The tray plus pack weighs about 180 g (1.8 N), so it stays put, even in a bump. Those figures are an estimate with E = 2.5 GPa; the first print tells the truth. If it is too stiff or too loose, change `LEAF_T` (1.6 softer, 2.4 stiffer) or `BARB` in the script.
- **Printing:** floor on the bed, no supports. The leaves stand up from a root block with 45 degree fillets, the barbs have 45 degree ramps, and I checked the whole tray: 0.02 mm2 of overhang steeper than 45 degrees, that is nothing. PETG is the better material for the leaves; they bend across the layers, which is PLA's weak direction, but only 0.7 % strain, so PLA works too.
- **Tray changes after the first print:** all outer corners and the closed-end inside corners are filleted (3 mm). The low stopper sits at the very edge of the porch, so the pack can sit out to it (room for about 74 mm). The zip-tie holes are gone. A **wire hole** through the -y side wall, 25 mm from the closed end between the two leaves: a capsule 13 mm wide and 18 mm tall (the DC plug passes), round at the bottom and with a 45 degree roof so it prints without support. `WIRE_SIDE = 1` puts it on the +y wall, `WIRE_X`, `WIRE_D`, `WIRE_EXT` move and size it.
- The tray keeps its 6 mm of extra width: the pack shifts 3 mm each way inside it.
- Written for the rev 2 slits. If your printed plate has different slit sizes (an older version had them 8.4 mm wide), the leaves still pass but the barb overlap changes, so measure your slits.
- Changed file: `printing/print_ready/stl/plates/plate5_pack_tray.stl` (and the single part in `stl/parts/`). Nothing else on the plates changed from rev 2.

## Weight basket

`mechanical/weight_basket/make_weight_basket.py` makes `Weight_Basket.stl` (also in `printing/print_ready/stl/`): two hooks go into the right wall and a small open basket on the outside holds trim weights.

- **Hooks:** two 22.2 mm square plug-hooks go into the two top-middle windows (23 mm, y = +-15, z = 55). Eight 0.5 mm crush ribs give a light press fit (0.1 mm interference, 2.8 mm3 overlap in the CAD). Pull it straight out to remove.
- **Basket:** 60 mm wide, 16 mm deep, 29 mm tall, 2 mm walls, 2.5 mm floor, about 20 cm3 inside, 3 mm corner fillets. Drop in washers, nuts or lead shot. About 18 g empty.
- **Print:** upright as it sits (basket floor on the bed), no supports. The only overhang is the 1.5 mm flat under each plug.
- **Balance:** the viewer counts the empty basket in (about 18 g at x = 86). Untick "Weight basket" to see the plain wall.
- Replaces the earlier plug-and-arm hook (removed).

## Table mount

`mechanical/table_mount/make_table_mount.py` makes `Table_Mount.stl`: a C-clamp for the far end of the string.

- **Clamp:** fits a table top up to 40 mm thick (42 mm gap), 30 mm wide, 45 mm deep. An M8 bolt through the bottom jaw (hex nut pocket, 13.6 mm across flats) pushes up on the underside of the table. You need one M8 x 40 bolt and nut; add a rubber or felt pad under the table to protect the surface.
- **Eye:** the same eye as the lid (18 mm wide, 10 mm thick, 7 mm hole) on the top jaw, 20 mm up, with a 45 degree flared foot.
- **Print:** lie it on its side (the C flat on the bed), no supports, so the layers run along the clamp's bending direction. About 64 g.
- Unchecked: not tested under load. The clamp's bolt, not the plastic, holds the string tension; keep the string pull small and mostly vertical.

## What changed

Wheel masses are PrusaSlicer on the stock CORE One presets (0.20 mm BALANCED, Prusament PLA). J_w "printed" scales the solid-model inertia by the sliced mass fraction, so it is an estimate: weigh the print.

| | rev 2 wheel (80 mm) | rev 3 wheel (100 mm) |
|---|---|---|
| Solid volume / solid PLA | 32.8 cm³ / 40.7 g | 43.4 cm³ / 53.9 g |
| Sliced mass, stock presets | 20.2 g | 25.8 g |
| J_w, solid model | 4.17e-5 kg·m² | 9.27e-5 kg·m² (x2.2) |
| J_w, printed (estimate) | about 2.1e-5 | about 4.6e-5 |
| Momentum at 250 rpm | about 5.5e-4 N·m·s | about 1.2e-3 N·m·s |
| Weight-bolt holes (10, on the rim) | smooth 4.4 mm, M4 bolt + nut | threaded M4 x 0.7, drawn 0.2 mm under nominal, the bolt cuts its own thread |

| Whole rig (viewer) | rev 2 | rev 3 |
|---|---|---|
| Boards (ESP32 + IMU perf board, L298N) | inside the left wall | outside the left wall, 5 mm standoffs |
| Trim weight | 0 g | 14 g (boards sit 23 mm further out) |
| J_b, platform without the wheel | 1.96e-3 kg·m² | 2.27e-3 kg·m² |
| Max platform rate the wheel can absorb | about 16 °/s | about 30 °/s |

## Flywheel

`mechanical/flywheel/make_flywheel_d100.py` rebuilds the wheel from its parameters (the `tt_flywheel.py` design: hub, double-D shaft socket, three slotted spokes, ten rim holes) instead of stretching the old mesh, which would have distorted the holes. As a check it first rebuilds the 80 mm wheel and compares it with `Flywheel_D80.stl`: volume -0.1 %, Izz -0.1 %.

- **Threads:** a right-handed M4 x 0.7 internal thread is modelled as a helix on each of the ten holes, 7.8 mm long (from the bottom face to the counterbore floor). Drawn 0.2 mm under nominal: root 3.8 mm, crest 3.04 mm, so M4 x 12 bolts bite in and cut their own thread. No nut. The Ø7.6 x 4.2 counterbore for the heads on the +Z face is unchanged.
- **Print:** z = 0 face down, no supports, no brim. The thread is 0.38 mm deep with a 0.7 mm pitch, about one line width, so expect a rough thread rather than a crisp one. If the bolts bind or strip, change `UNDERSIZE` in the script (0.1 is looser) and rerun.
- **Slice:** `mechanical/flywheel/slice_flywheel.ps1` writes `printing/print_ready/gcode/Flywheel_D100.gcode` and `3mf/Flywheel_D100.3mf`: 58 min, 25.8 g, 2 perimeters, 15 % grid infill, centred on the 250 x 220 bed, 16 mm tall.
- **More inertia:** the stock preset leaves the rim about half hollow. From the toolpaths (same presets, only perimeters changed; 4 perimeters about 34 g and 5.7e-5, 6 perimeters about 41 g and 6.8e-5, 1 h 27 min), more perimeters raise J_w toward the 9.3e-5 solid figure at the cost of mass. Slicing yourself: 6 perimeters is a good default for this wheel. `printing/print_ready/stl/Flywheel_D100.stl` is the file to load; the G-code there is the stock-preset slice.
- **Worth checking:** the double-D shaft socket is 3.98 mm flat to flat, not the 3.7 mm of the TT shaft. It comes from the original script (chord half-length used as the flat distance), and I kept it so the wheel matches rev 2. Tighten it if the wheel slips on the shaft.
- **Mesh:** 139,826 triangles, about 7 MB.

## Fit

- Radial: the rim reaches R50. With the boards outside, nothing inside is within 4 mm of it: motor terminals about 54 mm from the axis, the walls 73 mm.
- Vertical: the motor case tops out at z = 28.0, the wheel hub bottom sits at 28.6 and the rim bottom at 31.6.
- Boards outside: the perf board is 15 to 85 mm high, below the lock rods (z 90.5 to 95.5) and the lid blocks (from 85). Leads from the motor and the pack pass through the wall's lattice windows.

## Folders

- `mechanical/flywheel/`: `Flywheel_D80.stl` (rev 2 wheel), `Flywheel_D100.stl` (print this), the build script and the slice script.
- `printing/print_ready/`: `gcode/Flywheel_D100.gcode`, `3mf/Flywheel_D100.3mf`.
- `visualization/`: `frame_viewer.html` with `flywheel.json` (new wheel, hub end down) and `tt_case.json`. Published as a separate page from rev 2.

## Still to do

- `p.Jw = 1.08e-5` in `rw1dof_params.m` ("disc, weighed"): weigh the printed D100 wheel and update `p.Jw`, and update `p.Jb` for the heavier, wider platform, before using the controller or the string-test model.
- The firmware's 50% duty cap on the motor was set for the old wheel. A heavier wheel spins up slower at the same duty.
