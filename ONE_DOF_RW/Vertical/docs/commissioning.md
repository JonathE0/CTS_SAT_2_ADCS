# Bench commissioning

## 1. Sensors with motor power disconnected

- Confirm a classic ESP32 DevKit V1 and the sensor pin markings.
- Connect shared SDA GPIO33, SCL GPIO32, 3.3 V logic, and common ground.
- Check existing pull-ups; do not add parallel resistors blindly. Both bus lines
  should idle near 3.3 V, never 5 V.
- Upload `sensors`; open the 115200-baud monitor. Reset the board to see startup.
- Expect MPU6050 at 0x68 or 0x69 with WHO_AM_I 0x68. An encoder at 0x36 is only a
  candidate AS5600; record its actual part marking before reading its registers.
- No ACKs: check power, swapped SDA/SCL, ground, and pull-ups; send `s`.
- Bus error: fix wiring/power before retrying. Unknown WHO_AM_I: confirm the
  sensor model instead of bypassing identification.
- At rest, acceleration magnitude should be approximately 1 g. Gently tilt about
  each axis and record which roll/pitch signal follows the pivot and its sign.
- Support the mechanism, send `c`, and confirm gyro rates become near zero.
- Disconnect a sensor only with power removed. On a subsequent failed read,
  firmware should stop telemetry and require `r`, then another calibration.

Record the IMU orientation relative to the pivot. The wheel rotation axis must
be parallel to the single allowed body rotation axis. Accelerometer-only tilt
cannot be used directly as a robust balance controller under wheel acceleration.

## 2. Resolve hardware parameters before motor tests

| Parameter | Current status |
| --- | --- |
| MiniFOC exact model / schematic | Listing photo: SimpleFOC Mini v1.0, DRV8313; see motor-test.md |
| Driver motor supply range / chosen supply | Board marked 8–35 V; user supplied 12 V |
| Driver continuous/peak phase current | Unknown |
| EN polarity, reset state, required pull resistor | DRV8313 active-high EN, internal pulldown per TI datasheet |
| 3.3 V input compatibility / 3PWM mode and polarity | DRV8313 logic-compatible, standard 3PWM input |
| Fault/brake pin requirements | Unknown |
| Motor 2804 exact model, KV, pole pairs, current rating | Listing: 220 KV, 7 pole pairs, 0.5 A rated / 2 A maximum; not measured |
| Encoder model, resolution, magnet placement | Listing: AS5600, 12-bit; live magnet health must be checked |
| Wheel mass/inertia, attachment, allowable speed | Unknown |
| Body mass, pivot-to-COM distance, pivot friction | Not measured |
| IMU mounting, balance axis, angle and torque signs | To establish on bench |
| Fuse, supply current limit, bulk capacitor ratings | Select from confirmed specifications |

Use the existing Amazon link as a lead, not a confirmed driver specification.
GPIO13 is not a classic ESP32 strapping pin; the driver still needs a verified
inactive state during reset and power sequencing.

## 3. Later firmware milestones

1. After driver compatibility is confirmed, add a separately selected motor test
   environment. Secure the assembly and verify low-power rotation, phase/encoder
   direction, pole pairs, and enable/disable behavior. A SimpleFOC 3PWM driver is
   a candidate, not yet an established match.
2. Establish a fused tilt estimate and gyro rate for the actual pivot axis.
   Measure timing and shared-I2C throughput with encoder feedback before choosing
   control-loop rates.
3. Add manual arming, explicit stop, sensor-loss shutdown, excessive-tilt shutdown,
   command timeout where applicable, and motor voltage/current/speed limits before
   tuning balance gains. Verify shutdown behavior with the mechanism restrained.
4. Measure mechanics, derive initial gains, and tune with support near upright.
   Watch wheel speed: a reaction wheel has finite momentum capacity and saturates
   under persistent torque. Plan for re-centering or stopping safely.

There are no powered motor or balance commands in the current firmware.
