# 1-DOF reaction-wheel testbed

The current ESP32 firmware is the complete [PlatformIO project in firmware/](firmware/README.md).
Start with [firmware/src/main.cpp](firmware/src/main.cpp).

It includes L298N motor control, the Wi-Fi control page, adjustable proportional
and integral gains, a motor-direction toggle, manual control, and timed ramp tests.
The firmware starts with automatic control OFF and Ki = 0.

Motor connections: GPIO14 to ENA (remove the ENA jumper), GPIO13 to IN1,
GPIO27 to IN2, common GND, and the motor to OUT1/OUT2. MPU6050 uses SDA21/SCL22.
See the firmware README for the complete wiring and test instructions.

The standalone `main.cpp` in this directory is a legacy example with older pins;
use the project in `firmware/` for the current assembly.
