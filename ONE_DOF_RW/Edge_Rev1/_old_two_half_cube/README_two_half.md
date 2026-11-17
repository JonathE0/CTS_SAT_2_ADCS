# Edge cube, 90 mm (one 2804 motor)

A cube that stands on one edge and balances itself with a reaction wheel inside. One motor, one axis, battery and electronics on board. Design status: **CAD checked, nothing printed, nothing run on hardware.** The interactive page that explains the physics is the Artifact "Edge Cube Balancer".

![standing](preview/cube_standing.png)
![exploded](preview/cube_exploded.png)

## What it is

- **Frame:** twelve 5 x 5 mm bars, 90 mm outer side, every outer edge rounded to R1.5 so it rolls on any edge. Printed in two halves joined at the middle by four glued tenons.
- **Motor and wheel:** the 2804 sits on the cube's axis (parallel to the pivot edge), bolted through its **stator-back M2.5 holes** to a motor plate carried on two diagonal ribs. The D74 wheel screws onto the rotor with the **rotor-face M2.5 holes**. Dimensions are from the drawing in the Amazon.ca listing (see `../SWINGUP_RWP`).
- **Electronics end:** a 16 mm lattice for zip-tying the battery, ESP32, driver and IMU.
- **Pivot edge:** the edge at (y, z) = (-45, +45). The IMU sits near it, because the accelerometer sees less sway close to the pivot.

Stack along x (the wheel axis), in mm:

| x | what |
|---|---|
| -45 to -42.6 | electronics lattice, flush with the end face |
| -42.6 to -25.6 | battery; ESP32, driver and IMU beside it on the lattice |
| 3 to 15 | wheel rim (D74) |
| 15 to 30 | motor body; rear hub D12 x 4.5 goes into the plate's window |
| 30 to 38 | motor plate (40 x 40) |
| 36 to 37.6 | the kit's AS5600 board in a recess on the plate's outboard face, chip towards the hub; its headers reach x = 44.6 |
| 40 to 45 | end ring |

Nothing leaves the 90 mm envelope (checked), so the cube can fall on any face or edge without the board or wheel touching the table. Lying on a face, the wheel's rim stays 8 mm above the table.

## Parts

Print in PLA or PETG. Print the cube halves ring-face down.

| file | notes |
|---|---|
| `Cube_Half_Motor.stl` | ring face (x = 45) down. **Needs supports** under the motor plate and its ribs (7 to 9 mm tall). The board recess faces the bed side, so the supports will fill it; clear it out. |
| `Cube_Half_Electronics.stl` | ring face (x = -45) down, no supports. Its four tenons point up. |
| `Wheel_D74_2804.stl` | face down, no supports. Threaded M4 holes as rev3, so the bolts cut their own thread. |

Buy: the 2804 motor kit; a 3S LiPo of about 450 mAh (the model assumes 58 x 21 x 17 mm, 38 g with its lead); an ESP32 dev board; a SimpleFOC-compatible three-phase driver (the listing's wiring picture uses the SimpleFOC mini); an MPU6050 breakout; 4 x M2.5 x 10 pan-head screws for the motor plate and 4 x M2.5 x 6 socket cap screws for the wheel (plus spares and thread-lock); 8 x M4 x 12 socket cap screws as wheel weights; two-part epoxy for the joints; small zip ties and a Velcro strap.

## Assembly

1. Test-fit the four tenons on the electronics half into the sockets on the motor half, dry. They have 0.2 mm clearance per side. Sand or drill if your printer runs tight.
2. Mount the motor on the plate from inside: its stator back against the plate's inner face, the hub through the window, turned so the notch in the stator plate where the leads leave points up the +y channels (the channels run towards +y on the plate's inner face).
3. Drop the AS5600 board into the recess on the outboard face, chip side down. Four M2.5 x 10 screws go through the board's slots, the plate and into the motor. Use thread-lock. That engages about 2.4 mm of thread, under the drawing's 4 mm limit; a 12 mm screw would reach 4.4 mm and bottom out.
4. Screw the wheel to the rotor with four M2.5 x 6 screws (about 2.5 mm of engagement, under the 3 mm limit). Add the eight M4 bolts. Spin it by hand; shuffle bolts or add washers until it runs without a wobble.
5. Zip-tie the motor leads to the diagonal rib and along one corner stub to the electronics end (about 80 mm). Keep the phase leads away from the encoder's I2C wires.
6. Fix the battery, ESP32, driver and IMU to the lattice with zip ties and the Velcro strap.
7. Epoxy the tenons and join the halves, square.
8. Balance it (next sections).

## Numbers from the CAD

| | |
|---|---|
| Mass | 194 g: printed frame 49 g, printed wheel 19 g, 8 bolts 18 g, motor 40 g, board 5 g, battery 38 g, ESP32 10 g, driver 6 g, IMU 3 g, wiring 6 g |
| Centre of mass above the edge | 63.8 mm; Mgl = 0.122 N·m |
| Inertia about the edge (without the wheel's own spin) | 9.3e-4 kg·m² |
| Wheel spin inertia | 3.85e-5 kg·m² (wheel 1.6e-5, bolts 1.8e-5, rotor 0.5e-5) |

Printed masses use sliced-mass fractions (frame 0.85, wheel 0.48). **Weigh the printed parts and the real battery and boards and update `FILL_*` and the placeholders.**

Simulated recovery, with ideal sensing and the torque limit and back-EMF derating at 12 V (`analysis/check_cube.py`):

| torque limit | torque / Mgl | recovers from | wheel peak speed |
|---|---|---|---|
| 0.015 N·m | 0.12 | 6.0 deg | 101 rad/s |
| 0.020 | 0.16 | 7.9 deg | 134 rad/s |
| 0.030 | 0.25 | 11.3 deg | 201 rad/s |
| 0.045 | 0.37 | 15.5 deg | 265 rad/s |

At plus or minus 20 % on mass and inertia and plus or minus 5 mm on the centre of mass, all 27 combinations still recover from more than 4 degrees at 0.030 N·m. **This is a feasibility study, not a guarantee:** no sensor noise, delay, friction or quantisation, and SimpleFOC without current sensing makes torque a voltage command. The web page's 13 degrees at 90 mm assumed a 27 g bar frame; the real frame with its plate, ribs, collars and lattice is 49 g, which is why this reads lower.

## Balance and trim

The model puts the centre of mass 0.05 mm off the diagonal, but that only reflects where I placed the battery and boards. On the bench it will differ. Each millimetre of sideways offset moves the balance point by 0.9 degrees, and a real offset makes the wheel run away while it tries to hold. Plan to:

- weigh and place the battery and boards symmetrically,
- add trim weight (small steel or lead on a zip tie) until the cube sits still on the edge by hand,
- let the controller learn the equilibrium angle.

## Checks run

All in `analysis/check_cube.py`. Each probe has a control that must read above zero.

- Static fits between frame, motor, board, wheel and placed boards: all 0 mm³; everything inside the 90 mm envelope.
- Wheel spin: a solid disc over the rim's x range clears both halves. The wheel could grow to about D105 before touching the joint collars. D74 is chosen to stay inside the envelope, not for clearance. A D108 control disc hits the collars (66 mm³).
- Screw paths (stator back, wheel), lead channels, joint tenons (0.2 mm clearance) and edge rounding (stub cross-section 24.51 mm², expected 24.52).

## Not verified, or not done

- **Assumed sizes:** battery, ESP32, driver and IMU are placeholder envelopes. The board's recess assumes its chip plane is 6 mm from the stator back (hub 4.5 mm plus 1.5 mm gap), and the kit's slots must pass M2.5 screws at the D19 holes. Check both on the real parts.
- **Print and glue:** the 3.2 mm tenons and the thin outer walls beside the sockets (2.2 mm) are untested. PLA creeps, and a glued joint is a weak point if the cube lands hard.
- **Only one axis:** no mounts for a second or third wheel, and no brake for jumping up. Both are separate designs.
- **No firmware:** the SimpleFOC torque loop and the lean controller (the page uses three-state pole placement) are not written.
- **Pivot edge:** it stands on the marked edge only. Standing it on another edge moves the IMU away from the pivot and changes the IMU axes.

## Regenerate

```powershell
python mechanical\make_cube_parts.py     # numpy + manifold3d; writes the STLs, cad_numbers.json, viewer_data.json
python analysis\check_cube.py            # clearance, screw and wire paths, balance numbers, simulated recovery
python analysis\render_cube.py           # numpy + matplotlib; rewrites the two preview images
```
