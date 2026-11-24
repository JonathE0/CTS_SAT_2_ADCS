# Vertical 1-DOF reaction-wheel workspace

Status: accepted for implementation following the user's PlatformIO selection.

## Intent

Prepare this folder for an ESP32 DevKit V1 controlling a vertical, single-axis
balancing mechanism with a reaction wheel. Follow `cube_balancing_wiring.md`.
The intended balance point is upright about a constrained pivot; the wheel axis
must be parallel to that pivot. The exact mechanism and IMU orientation remain
to be confirmed on the bench.

## Approaches

1. PlatformIO with Arduino C++: recommended. Provides a reproducible project,
   pinned dependencies, serial monitoring, and VS Code integration. PlatformIO
   is already installed on this computer. The user selected this approach.
2. Arduino IDE sketch: suitable if this is the user's existing workflow;
   dependency and board setup require more manual steps.

## Proposed initial deliverable

- A PlatformIO project for the classic ESP32 DevKit V1, with build/upload/monitor
  instructions, central pin configuration, and VS Code tasks.
- Sensor-only firmware: I2C scan, MPU6050 identification and raw readings,
  stationary gyro calibration, and serial telemetry for checking tilt direction.
- Encoder detection on the shared bus. Decode wheel angle only after its model
  is confirmed; an ACK at address 0x36 alone does not establish its identity.
- A staged bench checklist and a record of hardware parameters still needed.
- A successful local firmware build, or explicit diagnostics if setup is blocked.

Initial success means the project builds and is ready for sensor verification.
Physical upload and readings require the connected hardware and remain unverified
until observed. Successful balancing is a later commissioning milestone.

## Wiring

| Signal | ESP32 GPIO |
| --- | --- |
| I2C SDA | 33 |
| I2C SCL | 32 |
| Driver EN | 13 |
| Driver IN1 / IN2 / IN3 | 27 / 25 / 26 |

Sensors use 3.3 V logic and a common ground. Motor power comes from a separately
appropriate supply. The initial firmware does not initialize PWM, drive EN, or
offer motor-arming commands. Keep motor power disconnected during sensor tests;
an input/high-impedance EN pin is not a guaranteed disabled driver.

## Later motor and balance commissioning

Confirm driver model, 3PWM compatibility, EN polarity, logic levels, supply range,
current limit, motor pole pairs, encoder model, magnet installation, and wheel
attachment before implementing powered motor tests. SimpleFOC is a candidate
only after compatibility is established; do not assume a 2804 motor's pole count
from its size.

Commission in order: sensors, secured low-power motor direction/encoder test,
angle estimation, bounded control with manual arming and shutdown conditions,
then supported balance tuning. Determine control signs from physical tests.
Choose gains and operating limits from measured mechanics and hardware ratings.
Record wheel speed so saturation can be detected during balance experiments.

## Scope and constraints

No guessed power ratings, balance gains, or motor-enable polarity. No automatic
motor activation, jump-up behavior, mechanical redesign, or changes to sibling
projects. Hardware-independent setup can proceed before hardware details are
known; powered operation cannot.

## References

- [ESP32 GPIO reference](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/gpio.html)
- [SimpleFOC 3PWM interface](https://docs.simplefoc.com/bldcdriver3pwm)
- [SimpleFOC I2C encoders](https://docs.simplefoc.com/magnetic_sensor_i2c)
