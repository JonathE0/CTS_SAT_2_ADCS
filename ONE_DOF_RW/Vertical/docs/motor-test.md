# Low-power wheel direction test

The exact kit's [listing photo](https://m.media-amazon.com/images/I/612-qisRZnL._SL1500_.jpg)
shows a SimpleFOC Mini v1.0 with a DRV8313. Its
[wiring illustration](https://m.media-amazon.com/images/I/81RJOR8xicL._SL1500_.jpg)
labels 8–35 V power and active-high EN. The
[TI datasheet](https://www.ti.com/lit/ds/symlink/drv8313.pdf)
confirms active-high enable and internal input pulldowns. The
[kit listing](https://www.amazon.com/dp/B0FXKN9YMJ) specifies a 12 V motor,
seven pole pairs, 2.3-ohm phase resistance, and an AS5600 encoder.
These identify the supplied kit; they are not measurements of the user's board.

`motor_test` adds wheel commands to the combined MPU6050/AS5600 diagnostics.
It replaces the sensor-only image when uploaded; `sensors` remains the default
build environment and never accepts wheel commands.

```powershell
pio run -e motor_test -t upload --upload-port COM10
pio device monitor -p COM10 -b 115200 --eol LF
```

The motor driver must use the GPIO mapping in `include/Config.h` and share ESP32
ground. Keep the secured wheel clear. Do not change wiring while powered.
The driver's 3.3 V pin is an output; do not connect it to the ESP32 3V3 supply.

- Boot: physical EN held LOW, disarmed, no automatic test.
- `h`: configuration and help.
- `l` + Enter: one negative/left open-loop pulse, automatically disabled after 1 s.
- `r` + Enter: one positive/right open-loop pulse, automatically disabled after 1 s.
- `i` + Enter: reinitialize IMU. In this image `r` means right, not IMU reset.
- `a`: arm for up to five seconds; EN remains LOW.
- `t`: consume arming and run one sequence: negative command for one second,
  disabled coast for one second, positive command for one second, then disable.
- `x`: disable and clear arming immediately when processed.

All commands except stop must be sent as single-letter lines followed by Enter.
Stop `x` is accepted immediately without Enter. Help and irrelevant commands are
ignored during an active test so they cannot delay the output deadline.
The pinned library is fetched from its official Git tag because 2.4.0 was not
available in the PlatformIO registry. Dependencies use a short path under the
user's PlatformIO directory to avoid Windows path-length limits.

The open-loop speed command is +/-1 rad/s, with q-axis voltage ramped up/down
over 200 ms and capped at 0.5 V. The power supply remains 12 V; a 0.5 V command
is PWM modulation, not a separate 0.5 V supply or a measured current limit.
The firmware does not perform current sensing. This deliberately gentle first
test may be insufficient to move the attached wheel; do not automatically
increase power when no motion is observed.

Manual `l`/`r` pulses require fresh AS5600 communication and magnet detection.
Weak/strong field flags are displayed as warnings and do not block these
open-loop pulses. Angle feedback is not used for commutation, and reported
displacement is unverified when a warning is present. The automatic `a`/`t`
sequence still requires a healthy field. I2C failure or lost magnet detection
stops either mode. Scan, calibration, reinitialization, help and new motion
commands are ignored while motion is active; `x` always remains available.
Encoder position is sampled about every 10 ms; no encoder EEPROM is programmed.
Long loop gaps also abort on the next iteration. The timer/stop logic runs on the
ESP32, so serial disconnection does not remove the three-second sequence bound;
this is not an independent hardware emergency stop.

CSV fields are the combined MPU/encoder columns from README.md, followed by
`motor_enabled` (0/1). Encoder angle is single-turn absolute degrees. Internal
pulse displacement is unwrapped across encoder rollover.
Pulse completion logs give measured displacement, which can include initial
rotor alignment. Electrical command sign does not define physical left/right;
viewpoint, phase order, and encoder direction determine that mapping.

Completion must report `EN=0, disarmed`. Restoring sensor diagnostics is done by
uploading `sensors`; that firmware holds physical EN LOW and leaves PWM untouched. Disconnect
motor power before reverting to sensor-only work.

## First live check, 2026-11-23

Firmware uploaded and verified on COM10. The AS5600 repeatedly reported
`STATUS=0x33`: magnet detected (MD), but field too weak (ML). Driver stayed
disabled (`EN=0`), and no arm/start command was sent. The direction test is
initially blocked by the strict automatic-sequence check. This alone does not
establish a mounting defect; leave the factory assembly unchanged until further
diagnosis. The status-bit interpretation is from the
[ams AS5600 datasheet, pages 18 and 20](https://s3.amazonaws.com/snapeda/datasheet/AS5600_Ams_AG.pdf).
