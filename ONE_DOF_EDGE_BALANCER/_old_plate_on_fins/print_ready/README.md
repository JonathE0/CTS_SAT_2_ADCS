# Print-ready STLs, balancing wheel module

Every file is already turned into its print orientation and stands on z = 0, centred on the bed. Do not rotate them. Units are mm. Each file was re-read after writing and checked: closed mesh with no open edges, volume equal to the CAD, lowest point at z = 0.

**No part needs supports.** The design limit is that every downward-facing surface leans no more than 38 degrees from vertical (you asked for 40 or less; a flat ceiling is 90). Supports are optional, not required: see "Do you need the 40 degree limit?" below.

| file | size (mm) | sits on the bed on | worst overhang |
|---|---|---|---|
| `stl/Frame_Base.stl` | 90 x 90 x 36.5 | the end ring's outer face; stubs, tenons and the four fins with their pegs pointing up | none (0 mm² over 40 degrees) |
| `stl/Motor_Plate.stl` | 88 x 88 x 5.4 | its front face, where the motor unit's feet land; the ribs and the peg holes' lead-ins face up | none |
| `stl/Frame_Cap.stl` | 90 x 90 x 14 | the end ring's outer face, collars and sockets pointing up | 35 degrees (the collar taper) |
| `stl/Wheel_D74_2804.stl` | 74 x 74 x 26 | the outside of the floor; the cup opens up, and the weight-bolt holes open up in the rim's end | threads only, see below |
| `stl/Joint_Test.stl` | 45 x 17 x 36.5 | one corner of the base and one of the cap, side by side | none |
| `stl/Fit_Test_Sockets.stl` | 65 x 22 x 9 | flat: the board of five square sockets | none |
| `stl/Fit_Test_Peg.stl` | 40 x 12 x 10 | flat on its handle, the tenon peg pointing up | none |
| `stl/Fit_Test_Pins.stl` | 60 x 12 x 15 | four pins, each standing on its round head | none |
| `stl/Fit_Test.stl` | 65 x 58 x 15 | all three of the above in one file | none |

## What changed in this version

- **The wheel is a cup that covers the motor.** It screws to the rotor end (4 x M2.5 on the 16 mm circle, the 3 mm-deep rotor holes in the motor drawing). A thin inner wall slides over the spinning can, and the rim runs back along the motor with the eight M4 weight bolts in its far end. It prints floor down as one piece with no supports, 26 mm tall.
- **The motor is held by the encoder board's feet, as the kit comes.** The plate no longer uses the motor's own holes. The four brass standoffs on the back of the board stand on the plate, and four M2.5 x 8 screws go in from behind into them. The plate is now a flat cross with an open middle, 8.5 g instead of 13.8 g.
- **The plate glues to four fins on the base ring's bars** (on the frame's axes, no longer the diagonals). A peg on each fin, the same 3.4 mm tenon, goes through a square hole in the arm end.

## How the 40 degree limit is met

- **The motor plate is its own flat part**, printed face down, instead of hanging inside the base. Every hole in it is straight through.
- **The wheel prints floor down.** Its walls are vertical and every hole opens upward or goes straight through, so nothing hangs.
- **Collars taper** at 38 degrees where they widen, instead of stepping out 3 mm.
- **The tenons sit flush** with their stubs, so they add no overhang.
- **Only the four edges parallel to the wheel axis are rounded.** They print vertical. The end-face edges are left sharp so the first layers have nothing to overhang.

## What the check measures, and the one place it is not zero

The check does what a slicer does: it compares every 0.2 mm layer with the one below it, grown by 0.2 x tan(40 degrees) = 0.17 mm. Anything left over is an overhang steeper than 40 degrees. Results: base, plate, cap and joint test all read **0.0 mm²** in every layer. The wheel's worst layer is **0.3 mm²** (about the area of a pencil dot) and is the M4 thread flank. The threads are drawn 0.25 mm deep, which is 35 degrees. As a control, the base with the plate fused onto it overhangs **1267 mm²** in a single layer, so the check does detect a real problem.

A plain count of mesh faces would report about 1,800 mm² for the wheel. That is the triangle facets of the thread helix, not a real overhang, so the layer check is the one to trust.

## Do you need the 40 degree limit?

No. You can print any of these with supports and it will work. The limit was a design goal, not a requirement of the printer. Bambu printers handle 45 degree overhangs cleanly, so 40 degrees is a conservative target. Supports leave a rough surface wherever they touch and take time, filament and cleanup, and in this design none are needed.

## Print the test coupons first

**`Joint_Test`** is a corner of the base (stub and tenon) and a corner of the cap (tapered collar and socket), cut from the real geometry. The tenon is 3.4 mm in a 3.5 mm socket, 0.05 mm clearance per side, the value you measured with `Fit_Test_Sockets`, with a 0.4 mm lead-in on the tip and the mouth. It should slide in with light pressure. The plate's pegs and their square holes are the same size and fit.

The sockets and pins are already measured (socket 2, 0.05 mm per side, and the D6.4 pin), so you do not need to print the fit test again. `Fit_Test` is all three coupons in one file if you ever want to repeat it. Details and the setting names are in `../README.md` under "Fits and tolerances".

## Settings to start from

- **Frame parts:** 0.20 mm layers, 4 perimeters (the 5 mm bars then print almost solid), 20 to 30 % infill, PLA or PETG. The mass model assumes the printed frame is 85 % of the solid CAD volume. Turn supports off.
- **Wheel:** the stock 0.20 mm profile (2 perimeters, 15 % infill) matches the model, about 27 g. More perimeters make it heavier with more inertia: weigh it and tell me so I can update the numbers.
- **Threads:** the M4 holes are drawn 3.3 mm, the M4 tap drill size, so the M4 x 12 bolts cut their own thread. Run each bolt in and out once before the final fit.
- **Wheel to motor:** the inner wall is 0.15 mm per side over the motor's 34.5 mm can. If it is tight, sand the bore; do not force it, and do not let it touch the stator base (the last 4 mm of the motor, where the leads leave), which does not turn.
- **Alignment pin (optional, not printed):** the floor's centre hole is 6.5 mm, for the headed D6.4 pin from `Fit_Test_Pins`. It is a removable jig that centres the wheel on the shaft while the four M2.5 screws are tightened.
- **Brim:** the base and cap stand on rings of 5 mm bars, so a brim helps against lifting at the corners. The plate is thin and wide, so a brim helps there too.

## Hardware

- 4 x M2.5 x 5 button-head screws (ISO 7380): wheel floor to the rotor. They engage 2.5 mm, under the motor drawing's 3 mm. Do not go longer.
- 4 x M2.5 x 8 button-head screws: from behind the plate into the four brass feet.
- 8 x M4 x 12 socket cap screws: weight bolts in the wheel's rim.
- The kit's own board, six brass standoffs, four nuts and two screws, left as they come.

## After printing

1. Glue the plate in, then fit the wheel to the motor and the motor unit to the plate (see `../README.md`).
2. Spin the wheel by hand before gluing the cap on. It should clear the ring by about 3 mm all round and the plate by about 3 mm.
3. Measure the motor unit from the rotor face to the ends of the brass feet. The model has 30.6 mm. If yours is longer, the wheel's screw heads have only 1 mm to spare at the -x face, so tell me the number.
4. Weigh the finished parts and the module. The CAD predicts 138 g in all, with the trim pads empty.
