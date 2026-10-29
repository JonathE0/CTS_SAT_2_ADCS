# Reaction-wheel frame — revision 2

## File categories

| Folder | Contents |
| --- | --- |
| `mechanical/frame_parts/` | Frame geometry generator, individual STL parts, assembly meshes, and print-plate layouts. |
| `printing/print_ready/` | Prepared print snapshot: G-code, PrusaSlicer 3MF projects, STL parts/plates, and Fusion import meshes. Read its README before printing. |
| `visualization/` | Interactive frame viewer. Open `frame_viewer.html` in a browser. |

`mechanical/frame_parts/gcode/` contains the slicer's working outputs; `printing/print_ready/` is the prepared distribution snapshot. Both are retained.

Run `make_frame_parts.py` from `mechanical/frame_parts/` to regenerate geometry, then run `slice_plates.ps1` to slice the plates. Refresh the print-ready snapshot after regeneration.

The older truss-frame generator and drawings are in `../archive/rev1/frame_parts/`. Existing firmware (`../ESP_RW1DOF/`), simulation files, testbed guide, and Fusion scripts remain in the parent reaction-wheel directory; they have not been designated revision 2.
