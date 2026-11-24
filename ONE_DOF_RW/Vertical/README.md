# Vertical 1-DOF reaction wheel

PlatformIO / VS Code workspace for the ESP32 DevKit V1 described in
[the wiring guide](cube_balancing_wiring.md).

The default `sensors` firmware is **sensor diagnostics only**. It scans I2C, identifies an
MPU6050 at `0x68` or `0x69`, and streams acceleration/gyro/tilt together with
AS5600 encoder angle and magnet status at `0x36`. It supports stationary gyro
calibration and holds motor EN LOW. It does not implement balancing.

A separate `motor_test` image adds exact `l`/`r` commands for one-second,
low-voltage pulses while preserving both sensor streams. It also retains the
manually armed automatic direction test for the identified SimpleFOC Mini v1.0 kit. See
[motor test controls and limits](docs/motor-test.md). It does not run at boot.

## Open, build, upload

1. Open `Vertical.code-workspace` in VS Code. PlatformIO IDE is already installed
   on this computer. Allow project indexing to finish.
2. Press **Ctrl+Shift+B** to build `sensors`. Alternatively use PlatformIO's
   **Project Tasks > sensors > General > Build**.
3. With USB and motor power disconnected, connect the MPU6050 and encoder as
   listed below. Then connect the ESP32 using a USB data cable; leave motor
   power disconnected.
4. Run **Terminal > Run Task > PlatformIO: List serial ports**. Identify the ESP32
   USB port; do not use Bluetooth COM5/COM6. If needed, set `upload_port = COMx`
   and `monitor_port = COMx` in `platformio.ini` using the actual port.
5. Run **PlatformIO: Upload sensors**, then **PlatformIO: Serial monitor** at
   **115200 baud**. Close the monitor before uploading again. If upload stalls at
   Connecting, hold BOOT while connecting, then release once uploading begins.
6. Follow [the bench checklist](docs/commissioning.md) before any motor work.

The selected board is `esp32doit-devkit-v1` (classic ESP32, assumed 4 MB flash).
Check the module marking if your board is an ESP32-S3/C3 or another variant;
those need a different board target and reviewed pin assignments.

## Wiring

| Connection | ESP32 |
| --- | --- |
| MPU6050 + encoder SDA | GPIO33 |
| MPU6050 + encoder SCL | GPIO32 |
| Sensor VCC | 3V3 |
| Sensor GND | GND |
| Driver EN, reserved | GPIO13 |
| Driver IN1 / IN2 / IN3, reserved | GPIO27 / GPIO25 / GPIO26 |

The `sensors` firmware holds driver EN LOW and does not initialize PWM.
Sensor readings need only USB power; keep motor power disconnected for sensor work.
Do not power the motor from the ESP32. See the wiring guide for common ground,
I2C pull-ups, and the still-unverified driver requirements.

## Serial commands

| Command | Action |
| --- | --- |
| `h` | Help and telemetry column names |
| `s` | Scan I2C addresses (discovery interrupts telemetry briefly) |
| `i` | Identify/reconfigure MPU6050; clear gyro calibration (`r` also works in sensor-only mode) |
| `c` | Calibrate gyro: one-second settling delay, then about two seconds of samples |

Support the mechanism so it remains stationary before sending `c`. Calibration
rejects abnormal gravity magnitude, large mean angular rates, or noisy rotation.
These checks cannot prove the assembly is stationary; slow motion can still bias
calibration. Offsets are kept in RAM and are lost on reset.

CSV telemetry is emitted at approximately 10 Hz; lines beginning `#` are status:

```text
ms,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,roll_deg,pitch_deg,gyro_calibrated,encoder_raw,encoder_deg,encoder_status,magnet_detected,magnet_weak,magnet_strong,encoder_ok,imu_ok
```

Acceleration is in g; gyro rates are in degrees/second. Gyro offsets are subtracted
only after accepted calibration (`gyro_calibrated=1`). Roll and pitch use gravity
in the **sensor frame**, with zero roll/pitch when +Z points up. They are not
filtered balance angles and become unreliable during acceleration. Establish
mounting orientation and pivot axis before choosing a balance signal.

Encoder angle is a single-turn absolute angle from 0 to just below 360 degrees;
`encoder_raw` is 0–4095. `encoder_status` is hexadecimal. A healthy magnet has
`magnet_detected=1`, `magnet_weak=0`, and `magnet_strong=0`. Angle readings remain
visible with a field warning so you can diagnose alignment; they may be unreliable.
`encoder_ok=1` means the I2C read succeeded, not that the magnet field is healthy.

Each sensor's stream continues if the other sensor fails. Unavailable readings
are `nan`, with the corresponding `encoder_ok` or `imu_ok` flag set to zero.
An MPU read failure invalidates calibration; send `i` after correcting the issue.
Encoder reads retry automatically. No stale samples are emitted as fresh data.
Gyro calibration briefly pauses the combined stream.

## Files and checks

- `platformio.ini`: board, pinned platform/framework, upload and monitor settings.
- `include/Config.h`: central wiring and acquisition timing.
- `src/main.cpp`: I2C diagnostics and serial interface.
- `include/SensorMath.h`: signed decoding, tilt, and calibration validation.
- `test/host/sensor_math_test.cpp`: hardware-independent C++ checks.
- `docs/commissioning.md`: staged hardware bring-up and remaining parameters.

From a PlatformIO terminal:

```powershell
pio run -e sensors
pio device list
pio run -e sensors -t upload --upload-port COMx
pio device monitor -p COMx -b 115200
```

If `pio` is unavailable in a normal PowerShell terminal, use the installed core:

```powershell
& "$env:USERPROFILE/.platformio/penv/Scripts/platformio.exe" run -e sensors
```

Host tests use the existing MSYS2 GCC on this computer:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test.ps1
# Elsewhere, provide a Windows g++ compiler with -Compiler 'path/to/g++.exe'.
```

These tests and the firmware build do not prove physical wiring or balancing.

References: [PlatformIO board target](https://docs.platformio.org/en/latest/boards/espressif32/esp32doit-devkit-v1.html),
[TDK MPU6050 register map](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Register-Map.pdf).
