# RW1DOF testbed, rev 3

Rev 2 frame with four changes: a **100 mm flywheel** (was 80 mm), its ten rim weight-bolt holes now **threaded M4**, the **electronics moved to the outside** of the left wall, and a **battery tray that snaps** into the baseplate's existing slits instead of being screwed on. Only one printed frame part changed, the pack tray; the baseplate, walls, lid, lock rods and cotters are as in rev 2, so use those STLs, G-code and the slicer script from `../rev2`.

## Battery tray snap fit

The tray snaps onto the rev 2 baseplate without screws, and **the baseplate is unchanged** (`rev2/.../base_pillars.stl`, byte for byte). It uses the plate's four existing plain slits (33.4 x 6.4 mm, at x = +-28 + 0 to 30, y = +-39).

- **Put it on:** load the pack, hold the tray under the plate and push it straight up. The four spring leaves flex in, pass through the slits and click out over the slit edges. Nothing to line up in y.
- **Take it off:** pull the tray down firmly, or press the four barbs in from above (they stand 2.6 mm above the plate) and lower it. It snaps off the same way it went on.
- **Trim:** it slides along the slits between tray x = 5 and 25 mm.
- **The leaves:** each is 8 mm wide and 2 mm thick, about 22.6 mm free length, with a 1.1 mm barb that has 45 degree ramps on both sides. The barb reaches 0.9 mm over the plate. Pushing on or pulling off bends a leaf 1.2 mm, about 0.7 % strain, about 4 N per leaf, 17 N for all four, roughly the pull of a 1.7 kg weight. The tray plus pack weighs about 180 g (1.8 N), so it stays put, even in a bump. Those figures are an estimate with E = 2.5 GPa; the first print tells the truth. If it is too stiff or too loose, change `LEAF_T` (1.6 softer, 2.4 stiffer) or `BARB` in the script.
- **Printing:** floor on the bed, no supports. The leaves stand up from a root block with 45 degree fillets, the barbs have 45 degree ramps, and I checked the whole tray: 0.02 mm2 of overhang steeper than 45 degrees, that is nothing. PETG is the better material for the leaves; they bend across the layers, which is PLA's weak direction, but only 0.7 % strain, so PLA works too.
- **Tray changes after the first print:** all outer corners and the closed-end inside corners are filleted (3 mm). The low stopper sits at the very edge of the porch, so the pack can sit out to it (room for about 74 mm). The zip-tie holes are gone. A **wire hole** through the -y side wall, centred 27 mm from the closed end between the two leaves: an oval 24 mm wide and 16 mm tall, sitting on the floor, so the plug and wires have room to slide along the wall. The crown of an oval has no 45 degree roof: it bridges about 20 mm, which PLA usually manages with good cooling but may sag a little; if it does, print the tray with supports under the crown or make the oval narrower (`WIRE_W`) or lower (`WIRE_H`). `WIRE_SIDE = 1` puts it on the +y wall; `WIRE_X` moves it.
- The tray keeps its 6 mm of extra width: the pack shifts 3 mm each way inside it.
- Written for the rev 2 slits. If your printed plate has different slit sizes (an older version had them 8.4 mm wide), the leaves still pass but the barb overlap changes, so measure your slits.
- Changed file: `printing/print_ready/stl/plates/plate5_pack_tray.stl` (and the single part in `stl/parts/`). Nothing else on the plates changed from rev 2.

## Weight basket

`mechanical/weight_basket/make_weight_basket.py` makes `Weight_Basket.stl` (also in `printing/print_ready/stl/`): two J-hooks hang over the rib under the two top-middle windows and carry a wide open basket on the outside, below the windows.

- **Hooks:** each is a J. An arm lies on the sill of a window (y = +-15, z = 55), a 3 mm lip on the inside drops 12 mm behind the 7 mm rib (it wraps the whole rib and ends 5 mm below it), and a 16 mm strap on the outside runs down from the arm to the basket. The rib sits in the pocket, so the weight cannot pull it off outward. 0.3 mm clearance, 0 mm3 overlap with the wall in the CAD.
- **On and off:** lift it about 12 mm, push the lips through the windows, lower it. Reverse to remove.
- **Basket:** 90 mm wide, 18 mm deep, 25.5 mm tall (z 18 to 43.5), 2 mm walls, 2.5 mm floor, about 26 g empty.
- **Print:** upright as it sits (basket floor on the bed), with auto supports under the hooks' arms and lips (the hooks stick out behind the back face, so it cannot lie on its back). Hook edges, the basket corners and the floor-to-wall joints are filleted (45 degree fillets at the floor).
- **Balance:** the viewer counts the empty basket in (about 26 g at x = 86). Untick "Weight basket" to see the plain wall.

## Table hook and slider clamp

`mechanical/table_hook/make_table_hook.py` makes `Table_Hook.stl` (hook alone); `make_table_slider.py` makes `Table_Hook_Slider.stl` (the hook with the slider printed in place on it), `Slider_Screw.stl`, `Slider_Pad.stl` and `Slider_Pin.stl`. All are also in `printing/print_ready/stl/`. The far end of the string hangs from a square table edge. Replaces the C-clamp from earlier in rev 3.

- **Hook:** an L-bracket. A 45 mm tab lies on the table top, a 90 degree bend (5 mm plate, 30 mm wide) carries it down the face for 96.5 mm, and a short stub at the bottom (16 mm wide, 10 mm thick, round end, flared into the plate like the lid's eye) has a 7 mm pinhole along the table edge. The string leaves the hole 102 mm below the table top and 2.5 mm out from the face. Nothing depends on the table thickness. About 28 g.
- **Holding it:** the weight hangs from the bend, and the string hangs almost straight below the plate (2.5 mm offset), so little pushes the plate sideways and friction is hardly needed. Use the slider, or stick rubber or felt on the tab and plate. The rig is about 0.5 kg, so the load is about 5 N.
- **Slider clamp:** the rider wraps the plate and runs a shelf under the table. A printed pin through the rider and one of the plate's five 5.4 mm holes (10 mm apart) sets the height; the screw (6 mm pitch, one start, cam-shaped so the flanks never overhang more than 45 degrees and it prints without supports) takes up the last 10 mm; the pad (28 mm, with a 9.2 mm socket that fits the screw's 9 mm peg) spreads the load. Stick rubber on the pad's flat face and put a drop of glue in its socket. Fits tables 5 to 45 mm thick.
- **One print:** `Table_Hook_Slider.stl` has the rider already around the plate with a 0.4 mm gap all round (0 mm3 overlap in the CAD). Print it on its side with supports (the upper side wall and the nut boss hang over the plate), snap the supports off, and slide the rider up and down to free it. If a layer or two have fused, twist it with a flat screwdriver; if the gap fuses a lot, raise `CL` in `make_table_slider.py` to 0.5.
- **Separate prints:** screw knob down, no supports; pad flat; pin lying down. Weights: hook and rider 57 g, screw 13 g, pad 4 g, pin 0.5 g.
- **Checks:** in the CAD at a 35 mm table nothing overlaps (hook, rider, table, screw, pad, pin), and the threads mesh with 0.35 mm clearance. Nothing printed or load-tested; printed threads often need a first turn with force, and PLA creeps, so recheck the clamp after a day. The string must hang straight down.

## One build plate

`mechanical/plate_rev3/make_plate.py` orients every new or changed part for printing and lays them out on one plate (`printing/print_ready/stl/Rev3_plate.stl`); `slice_plate.ps1` slices it on the stock CORE One presets (0.20 mm BALANCED, Prusament PLA) to `printing/print_ready/gcode/Rev3_all_parts.gcode` and `3mf/Rev3_all_parts.3mf`. 4 h 04 min, 114 g, all inside 220 x 162 mm of the 250 x 220 bed, two rows (wheel, tray, basket; then hook, screw, pad, pin) 6 mm apart (PrusaSlicer's own arranger crashed on this set, so the layout is by script).

- **On the plate:** wheel (100 mm), pack tray, weight basket, hook with the slider, screw, pad and pin. Not on it: the unchanged rev 2 parts, and the hook without the slider (`Table_Hook.stl`).
- **Orientation:** hook and slider on their side, basket upright, tray floor down, wheel face down, screw knob down, pad flat, pin head down.
- **Supports:** automatic, only where an overhang is shallower than 35 degrees from horizontal. They land under the basket's hooks and the slider (about 8,500 moves under the hook, 4,400 under the basket), and almost nothing under the screw, wheel or tray. Check the preview before printing.
- **Orientations tried alone:** basket upright 39 min and 20 g (best; lying down 51 min to 1 h 15 min and 26 to 29 g); hook with slider on its side 1 h 12 min and 31 g (best; standing as assembled 2 h 23 min and 68 g). The layout is a hand-placed grid, about half the bed area covered, not a true packing.
- **Print order:** nothing to change. If the plate is too tall for your comfort, delete parts in PrusaSlicer; the time is mostly the wheel and the hook.

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
