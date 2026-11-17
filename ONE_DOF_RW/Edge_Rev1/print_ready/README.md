# Print-ready STLs, balancing wheel module

Every file is already turned into its print orientation and stands on z = 0, centred on the bed. Do not rotate them. Units are mm. Each file was re-read after writing and checked: closed mesh with no open edges, volume equal to the CAD, lowest point at z = 0.

**No part needs supports.** The design limit is that every downward-facing surface leans no more than 38 degrees from vertical (you asked for 40 or less; a flat ceiling is 90). Supports are optional, not required: see "Do you need the 40 degree limit?" below.

| file | size (mm) | sits on the bed on | worst overhang |
|---|---|---|---|
| `stl/Frame_Base.stl` | 90 x 90 x 36.5 | its outside face: the end ring and the motor mount lie flat on the bed; the four foot pads, the stubs and the tenons point up | 38 degrees (the roofs of the four screw-head pockets) |
| `stl/Frame_Cap.stl` | 90 x 90 x 14 | the end ring's outer face, collars and sockets pointing up | 35 degrees (the collar taper) |
| `stl/Wheel_D74_2804.stl` | 74 x 74 x 16.3 | the outside of the floor; the cup opens up, and the eight bolt counterbores open up in the rim's end | none: every wall is vertical |
| `stl/Joint_Test.stl` | 45 x 17 x 36.5 | one corner of the base and one of the cap, side by side | none |
| `stl/Fit_Test_Sockets.stl` | 65 x 22 x 9 | flat: the board of five square sockets | none |
| `stl/Fit_Test_Peg.stl` | 40 x 12 x 10 | flat on its handle, the tenon peg pointing up | none |
| `stl/Fit_Test_Pins.stl` | 60 x 12 x 15 | four pins, each standing on its round head | none |
| `stl/Fit_Test.stl` | 65 x 58 x 15 | all three of the above in one file | none |

**`Motor_Plate.stl` is gone.** If you still have a copy from the last version, do not print it: the motor mount is now part of `Frame_Base`. `Frame_Base` and `Wheel_D74_2804` both changed, so old prints of those two do not fit this version either. `Frame_Cap` and the test coupons are unchanged.

## What changed in this version

- **The motor mount is part of the base.** A hub ring on four arms, in the same 5 mm slab as the end ring, so it lies flat on the bed. Four pads on it take the kit's four brass feet, and four M2.5 x 8 screws go in from the outside face. No separate plate, no glue for the mount.
- **The screw-head pockets print without supports.** They are on the bed face, so a flat-roofed counterbore would have been a ceiling. Each pocket is 2 mm deep with straight walls, then its roof narrows to the screw slot at 38 degrees. The screw's head stops on that taper.
- **The wheel's rim is shorter and thicker.** It lies beside the motor only (r 27 to 37, 16.3 mm long) and no longer wraps round the motor's wires and the encoder's plugs. The eight M4 bolts go in from the rim's back end into plain 3.5 mm holes, with their heads in counterbores.
- **No modelled threads.** The wheel file is 0.5 MB instead of 8.5 MB.

## How the 40 degree limit is met

- **Everything on the base rises straight from the bed**: ring, mount, pads, stubs. The only sloping surfaces are the four pocket roofs, at 38 degrees.
- **The wheel prints floor down.** Its walls are vertical and every hole opens upward or goes straight through, so nothing hangs.
- **Collars taper** at 38 degrees where they widen, instead of stepping out 3 mm.
- **The tenons sit flush** with their stubs, so they add no overhang.
- **Only the four edges parallel to the wheel axis are rounded.** They print vertical. The end-face edges are left sharp so the first layers have nothing to overhang.

## What the check measures

The check does what a slicer does: it compares every 0.2 mm layer with the one below it, grown by 0.2 x tan(40 degrees) = 0.17 mm. Anything left over is an overhang steeper than 40 degrees. Results: base, cap, wheel and joint test all read **0.0 mm²** in every layer. As a control, the same base with plain flat-roofed pockets for the screw heads overhangs **73.8 mm²** in one layer, so the check does detect a real problem.

## Do you need the 40 degree limit?

No. You can print any of these with supports and it will work. The limit was a design goal, not a requirement of the printer. Bambu printers handle 45 degree overhangs cleanly, so 40 degrees is a conservative target. Supports leave a rough surface wherever they touch and take time, filament and cleanup, and in this design none are needed.

## Test coupons

**`Joint_Test`** is a corner of the base (stub and tenon) and a corner of the cap (tapered collar and socket), cut from the real geometry. The tenon is 3.4 mm in a 3.5 mm socket, 0.05 mm clearance per side, the value you measured with `Fit_Test_Sockets`, with a 0.4 mm lead-in on the tip and the mouth. It should slide in with light pressure.

The sockets and pins are already measured (socket 2, 0.05 mm per side, and the D6.4 pin), so you do not need to print the fit test again. `Fit_Test` is all three coupons in one file if you ever want to repeat it. Details and the setting names are in `../README.md` under "Fits and tolerances".

## Settings to start from

- **Frame parts:** 0.20 mm layers, 4 perimeters (the 5 mm bars then print almost solid), 20 to 30 % infill, PLA or PETG. The mass model assumes the printed frame is 85 % of the solid CAD volume. Turn supports off.
- **Wheel:** the stock 0.20 mm profile (2 perimeters, 15 % infill) matches the model, about 22 g. More perimeters or infill make it heavier with more spin inertia, which this shorter rim can use: weigh it and tell me so I can update the numbers.
- **Weight-bolt holes:** drawn 3.5 mm, plain. The M4 x 12 bolts cut their own thread. Drive each one in from the counterbored end until its head is just under the surface; the tip then comes level with the wheel's front face.
- **Wheel to motor:** the inner wall is 0.15 mm per side over the motor's 34.5 mm can. If it is tight, sand the bore; do not force it, and do not let it touch the stator base (the last 4 mm of the motor, where the leads leave), which does not turn.
- **Alignment pin (optional, not printed):** the floor's centre hole is 6.5 mm, for the headed D6.4 pin from `Fit_Test_Pins`. It is a removable jig that centres the wheel on the shaft while the four M2.5 screws are tightened.
- **Brim:** the base and cap stand on rings of 5 mm bars, so a brim helps against lifting at the corners.
- **First layer on the base:** the four screw-head pockets and the slots are open on the bed face. If the first layer squashes out a lot, the slots (2.8 mm for an M2.5 screw) close up slightly; clear them with the screw or a 2.5 mm drill.

## Hardware

The same list as the last version.

- 4 x M2.5 x 5 button-head screws (ISO 7380): wheel floor to the rotor. They engage 2.5 mm, under the motor drawing's 3 mm. Do not go longer.
- 4 x M2.5 x 8 button-head screws: from the outside face of the base into the four brass feet (3.9 mm in the base, 4.1 mm in each foot). Tighten snug, not hard.
- 8 x M4 x 12 socket cap screws: weight bolts in the wheel's rim.
- The kit's own board, six brass standoffs, four nuts and two screws, left as they come.

## After printing

1. Glue the cap to the base, tie the IMU on, fit the wheel to the motor and the motor unit to its pads (see `../README.md`).
2. Spin the wheel by hand. It should clear the cap ring by about 3 mm all round, and no wire should be near it: the rim ends just before the motor's back face.
3. Measure the motor unit from the rotor face to the ends of the brass feet. The model has 30.6 mm, and anything up to 33.5 mm stays inside the 44 mm depth.
4. Weigh the finished parts, one M4 bolt and the module. The CAD predicts 133 g in all, with the trim pads empty.
