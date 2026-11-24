# Vertical 1-DOF reaction wheel: session context

Hand-off notes so a new Claude Code session can continue. Last updated 2026-11-24.

## Goal
Balance a cube on one edge using a reaction wheel. ESP32 DevKit V1, PlatformIO + Arduino, SimpleFOC v2.4.0.
Control the wheel from a phone over Wi-Fi.

## Hardware
- ESP32 DevKit V1 (upload/monitor port **COM10**, 115200 baud). If COM10 disappears, replug USB / press EN.
- SimpleFOC Mini v1.0 (DRV8313): EN=GPIO13 (active high), IN1/2/3 = GPIO27/25/26. Peak 2.5 A, continuous ~1.75 A.
- 2804 gimbal motor, 7 pole pairs (measured 7.0), 2.3 ohm phase resistance, 12 V supply.
- MPU6050 (0x68) + AS5600 encoder (0x36) on shared I2C: SDA=GPIO33, SCL=GPIO32, 400 kHz.
- AS5600 reports a weak-magnet flag (STATUS 0x33) but angle reads work.
- Onboard blue LED (GPIO2) turns on when the Wi-Fi AP is up.

## Build / upload
PlatformIO is not on PATH. Use `%USERPROFILE%\.platformio\penv\Scripts\pio.exe`.
- `pio run -e motor_test -t upload --upload-port COM10` (about 80 s)
- `sensors` env is sensor-only and holds EN low. `motor_test` is the real firmware (src/motor_test.cpp + src/main.cpp).
- Close any serial monitor before uploading.

## Phone UI
Join Wi-Fi **Wheel**, password **12345678** (WPA2 needs 8+ chars), open `http://192.168.4.1`.
Buttons: LEFT, RIGHT, STOP, Balance ON/OFF (default OFF), Reset to zero, Mode (open-loop / closed-loop), Direction (flip sign), Export to log, Clear graph.
Sliders (live): Kp, Ki, Kd, Volts (0.5-6), Max wheel rad/s (5-120), wheel-speed damping, back-EMF feed-forward, LEFT/RIGHT acceleration throttle.
Graph: tilt error (green) and wheel speed (orange).

## Firmware design (src/motor_test.cpp, src/main.cpp)
- Tilt = complementary filter on `atan2(ax, ay)` with gyro **gz** (gravity lies in the sensor X-Y plane as mounted). Not roll about X.
- Balance gate: needs fresh IMU + encoder, no pulse running. IMU auto-reinitializes every 1 s after a failure; one retry per read.
- Controller runs in `WheelControl::balanceUpdate` at about 200 Hz (5 ms sample period).
- Open loop: PID gives wheel acceleration, integrated to a velocity_openloop target, with 2/s decay.
- Closed loop (Mode button): custom `AS5600Sensor` for SimpleFOC, torque control in voltage mode.
  - Torque term: `kSign*0.025*(Kp*err + Ki*integ + Kd*rate) - gK*vel`, capped at +/-3.5 V, plus a 0.05 V friction kick.
  - **Back-EMF feed-forward:** `u = torque_term + gB*wheel_speed`, so a given error always means the same torque regardless of wheel speed. gB default 0.05 V per rad/s (about 190 rpm/V).
  - Alignment on first Mode press: slow 3-rev pole-pair measurement at 3 V, then `initFOC`. Rotor turns about half a revolution. **Do it with the cube lying down.** No torque pulse any more (it tipped the cube).
- Reset to zero: sets setpoint to current tilt, clears integral, rate filter, command; in closed loop makes current wheel speed the zero reference.
- Out of range (>25 deg from setpoint) or overspeed (>1.25x Max wheel): controller stays on and brakes the wheel. Stops only on STOP, or if IMU/encoder data is stale >50 ms.
- LEFT/RIGHT: 1 s open-loop pulses. Speed ramps at the acceleration throttle (rad/s^2) up to Max wheel; voltage follows the Volts slider.
- Export to log: page POSTs graph data + gains to `/log`; ESP prints it to serial as `# LOG ...`. Balance also prints `# B,ms,err,rate,wheel,cmd` at about 50 Hz.

## Key findings (from logs)
- Wheel tracks commands; sign was correct (corr err vs wheel accel positive, cube accel negative).
- Original open-loop authority was tiny (about 0.36 deg/s^2 cube accel per rad/s^2 wheel accel), and the wheel saturated at the speed cap.
- Voltage-mode drive acts like a velocity command: at about 0.8 V the wheel reached about 16 rad/s and stopped accelerating, so steady errors produced no torque. Fixed with back-EMF feed-forward.
- Gyro noise from motor vibration caused self-excited oscillation at rest. Fixed with rate low-pass, 0.2 deg deadband, softer gains.
- Pole pairs = 7 (slow sweep gives 7.0). Fast sweeps gave garbage (5.9-7.5).
- Last log (back-EMF firmware): recovers from 14 deg errors in about 0.5 s, holds +/-3 deg for 30-100 s. Remaining problems: slow +/-17 deg swings (about 14 s period) with Ki 0.4; steady 2-4 deg offset when the setpoint is not the true balance point.
- Physical limit: peak torque is motor-limited (about 1.3 A at 3 V). A heavier wheel does not raise peak torque; geometry (lower centre of mass) and a stronger motor do.

## Suggested next settings
Ki 0, Kp 6-8, Kd about 1.0, damping 0.02, back-EMF 0.035-0.05, Max wheel 60-100, Volts 4-6 (6 V stall is about 2.6 A, short bursts only).
Press Reset to zero with the cube at its real balance point. Press Clear graph before a run, Export to log after.

## Workflow used with Claude
A background serial logger writes `COM10` to `serial.log` in the Claude scratchpad; user presses Export to log, then Claude analyses the `# B` and `# LOG` lines.
The logger exits if COM10 vanishes (it did at the end of this session). Restart it after the board reconnects.

## Docs already in repo
README.md, cube_balancing_wiring.md, docs/commissioning.md, docs/motor-test.md, docs/superpowers/specs and plans (older notes; they predate the Wi-Fi/balance work).
