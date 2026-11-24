# RW1DOF testbed frame, rev 2: print-ready files

Everything here is generated from `../../mechanical/frame_parts/make_frame_parts.py` (geometry) and `../../mechanical/frame_parts/slice_plates.ps1` (slicing). Edit the script, rerun both, and recopy; this folder is a snapshot.

## Print order

| # | G-code | What | Time | PLA | Notes |
|---|---|---|---|---|---|
| 1 | `gcode/plate1_frame.gcode` | base with pillars, 2 lock rods, 4 cotters (2 spare) | 3 h 58 m | 92 g | 4 mm brim |
| 2 | `gcode/plate2_walls.gcode` | left and right wall panels | 1 h 46 m | 42 g | |
| 3 | `gcode/plate4_lid.gcode` | one-piece X lid with eye | 3 h 00 m | 55 g | organic supports under the X arms |
| 4 | `gcode/plate5_pack_tray.gcode` | tray for the 12.6 V pack | 0 h 48 m | 27 g | sized for an assumed 70 x 58 x 21 mm pack |
| opt | `gcode/plate3_walls.gcode` | back and front panels, 2 spare rods | 2 h 04 m | 50 g | only if you want those walls |

Slicer: PrusaSlicer 2.9.6, stock presets `Prusa CORE One HF0.4 nozzle`, `0.20mm BALANCED @COREONE HF0.4`, `Prusament PLA @COREONE HF0.4`. Plain-text G-code. Each `.3mf` in `3mf/` opens in PrusaSlicer with the same settings.

## Folders

- `gcode/`, `3mf/`: one per plate, ready to send to the printer or to inspect.
- `stl/plates/`: the five bed layouts (bed coordinates, mm).
- `stl/parts/`: each part alone, in print orientation.
- `fusion_import/`: each part in assembly position plus `assembly_all_in_one.stl`, for Fusion's Insert > Insert Mesh (units: mm). They are meshes, not solids: use Mesh > Convert Mesh in Fusion if you want to edit them. Assembly frame: origin on the spin axis at the baseplate top, +Z up, -X is the driver wall.

## Assembly notes

- Lock rods: printed lying flat, head on one end, a printed cotter through the cross-hole at the other. Two rods, one per side wall, pillar to pillar through the lid blocks.
- Pack tray: four M3 self-tapping screws from the top of the plate through the slotted holes into the tray tabs. A zip tie through the two porch holes closes the open end.
- Lid: prints right way up with supports; remove them from under the X arms.
