# ESP_RW1DOF ESP32 C++ workspace

Uses PlatformIO with the Arduino C++ framework and pinned Espressif32 platform
8.0.0. The initial target is a generic
**ESP32 Dev Module / WROOM-32** (`esp32dev`). Confirm the board before uploading;
ESP32-S3, C3, and other variants need their corresponding PlatformIO board ID.

## VS Code

1. Open this **ESP_RW1DOF** folder in VS Code. Reload the window if PlatformIO was
   just installed, and allow its first-run setup to finish.
2. Edit `src/main.cpp`. PlatformIO supplies the ESP32 compiler and IntelliSense
   configuration; a desktop C++ compiler is not used for this firmware.
3. Press **Ctrl+Shift+B** to build using the project virtual environment.
4. Connect the confirmed board with a USB data cable. Run **Terminal > Run Task >
   ESP32: List Ports**, then **ESP32: Upload**.
5. Keep the MPU6050 still for about two seconds after startup to calibrate its
   zero rotation rate. Rotate around its marked Y axis: faster rotation commands
   more wheel PWM after enabling control on the Wi-Fi page, and opposite rotation reverses direction. Stopping rotation,
   including holding a fixed tilt, returns the command to zero. The onboard blue
   GPIO 2 LED blinks while the Wi-Fi hotspot is active (500 ms on, 500 ms off),
   including during runtime calibration or a motor fault while Wi-Fi remains on.
6. Run **ESP32: Serial Monitor** at 115200 baud to see timestamped CSV readings,
   including Y rotation rate and signed PWM. Use **ESP32: Log Telemetry** to also
   record them to disk. Close the monitor before uploading again.

## MPU6050 wiring

Disconnect USB while wiring a typical MPU6050 breakout (such as a GY-521).

| MPU6050 | ESP32 |
|---|---|
| VCC / VIN | 3V3 |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |
| AD0 | GND (I2C address 0x68) |
| INT, XDA, XCL | Unconnected |

Startup calibration requires a stationary sensor. If the sensor was moving during
calibration, reset the ESP32 with the sensor still. PWM remains zero during
startup/calibration. The Y gyroscope bias is measured on every reset. The controller
uses angular velocity in degrees/second directly; it does not integrate an angle
or set a zero pose. Startup orientation can be arbitrary as long as it is still.

A failed runtime sensor read or a sampling stall sets PWM to zero and requires a
reset. Serial Monitor repeats the fault message once per second so a late-opened
monitor can still show why output stopped.

## Automatic PI rate controller

Automatic control targets zero Y-axis rotation rate. The existing Kp mapping
is supplemented by an adjustable Ki (0 to 20 PWM per degree of accumulated rate
error) and a live Integral correction display. Ki defaults to 0, preserving the
previous proportional-only response. Choose a small positive Ki to enable it.
The selected Motor direction mapping applies to the combined P + I output.

Both terms use rate beyond the +/-2 deg/s deadband. Integration uses actual
elapsed milliseconds, with conditional anti-windup and a +/-255 PWM integral
limit; total PWM is also limited to +/-255. Within the deadband, the stored
integral holds its correction. This can keep the wheel driven at zero body rate.
The controller regulates body rate, not wheel RPM or absolute attitude.

Changing either gain clears the accumulated integral. Stop, timeout, manual/ramp
mode, direction changes, calibration and faults clear it too. Sampling gaps over
200 ms do not accumulate correction (the firmware also latches sampling faults).
Reboot restores Kp = 2, Ki = 0, integral = 0 and control OFF. The app shows Ki and
the integral contribution; the existing CSV format is unchanged.

## Wheel ramp test

Set the manual throttle slider to a nonzero limit, then choose **Ramp left** or
**Ramp right**. PWM rises from zero to that limit over 5 seconds, holds for
2 seconds, then turns OFF. The wheel coasts after PWM is removed; this is a
PWM test, not closed-loop RPM control. The selected Motor direction mapping
also applies to ramp tests.

Keep the page open for its heartbeat. Stop wheel, Disable control, a lost
connection, a direction-setting change, calibration, or a sensor fault cancels
the test. Starting automatic control or a new manual command replaces the test.
Apply throttle is blocked during a ramp; select a limit and start a new test
instead. The existing CSV PWM column records the ramp output (mode is manual).

## L298N motor driver

This firmware uses L298N channel A: 20 kHz, 8-bit PWM on ENA and complementary
direction signals on IN1/IN2. Remove the ENA jumper before connecting GPIO 14.

| ESP32 | Motor driver |
|---|---|
| GPIO 14 (D14) | ENA (remove ENA jumper) |
| GPIO 13 (D13) | IN1 |
| GPIO 27 (D27) | IN2 |
| GND | Signal GND / common ground |

Connect the motor to OUT1 and OUT2 and power the driver from a supply
appropriate for the motor. The ESP32 GPIOs only carry control signals.
The ESP32 is USB-powered; its 3V3 pin powers the MPU6050. The motor driver uses its
separate motor supply, with signal ground connected to ESP32 GND.

The active mapping settings are in `src/motor_command.h` (the older
`include/motor_command.h` is not used by the firmware):

- `MOTOR_RATE_DEADBAND_DPS = 2`: zero PWM within +/-2 degrees/second.
- `MOTOR_PWM_PER_DPS = 2`: default Kp, adjustable on the Wi-Fi page.
- `MOTOR_MAX_DUTY = 255`: 8-bit PWM cap.

At Kp = 2, +/-12 degrees/second commands +/-20/255 duty. Direction depends on
motor wiring and sensor orientation. Use the **Motor direction** button on the
Wi-Fi page to switch between NORMAL and INVERTED. A change turns automatic and
manual control OFF; explicitly enable again to test. Reboot restores INVERTED.
ENA PWM is cleared before switching IN1/IN2.
This is an open-loop duty command: actual wheel RPM depends on supply, load, and
motor characteristics. There is no wheel speed feedback or balancing controller.

For the first powered test, secure the assembly, keep the wheel clear, and make
small rotations. PWM does not limit motor current or wheel RPM. Zero PWM
on ENA disables the L298N bridge, allowing the motor to coast.

### Rotation-rate motor mapping checks (Windows with MSYS2 UCRT64)

The original test below covers the legacy `include/` mapping. The Wi-Fi test
covers the active `src/` mapping, gain validation, enable/disable, heartbeat
ownership/timeout (including clock wrap), and fault latching.

```powershell
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
g++ -std=c++17 -Wall -Wextra -Werror -Iinclude test/test_motor_command.cpp -o .pio/test_motor_command.exe
.\.pio\test_motor_command.exe
g++ -std=c++17 -Wall -Wextra -Werror -Isrc test/test_wifi_control.cpp -o .pio/test_wifi_control.exe
.\.pio\test_wifi_control.exe
g++ -std=c++17 -Wall -Wextra -Werror -Isrc test/test_gyro_telemetry.cpp -o .pio/test_gyro_telemetry.exe
.\.pio\test_gyro_telemetry.exe
g++ -std=c++17 -Wall -Wextra -Werror -Isrc test/test_manual_control.cpp -o .pio/test_manual_control.exe
.\.pio\test_manual_control.exe
node test/test_control_page.cjs
```

The Node.js check runs the actual embedded page script with simulated HTTP
responses to verify button ordering, heartbeat behavior, and invalid gain input.
It also verifies range selection, calibration status and the enable lockout.
The gyro/telemetry test checks all four range conversions and CSV formatting.
The manual-control test covers direction/PWM, automatic/manual handoff, stop,
heartbeat timeout/ownership, invalid throttle and calibration/fault lockout.

## Wi-Fi control and Kp tuning

1. Upload the firmware. Keep the sensor still during startup calibration.
2. Connect your phone or computer to **RW1DOF-Control**, password **rw1dof-test**.
   Choose to stay connected if it reports that this network has no Internet.
3. Open **http://192.168.4.1** in a current browser. No app or router is needed.
4. Press **Enable control** to run the controller; **Disable control** sets PWM
   to zero. The page shows measured Y angular velocity, signed PWM, and active Kp.
5. Enter Kp and press **Apply Kp**. It accepts finite values from **0 to 20**;
   Kp is PWM counts per degree/second beyond the 2 deg/s deadband. Start at the
   default **2**. Changes apply immediately, including while enabled.

Control starts **OFF** after every reset. Kp resets to **2**; settings are not
saved to flash. Keep the enabling page open and your phone awake: it sends a
heartbeat every 500 ms. A missing heartbeat for 2 seconds disables control at
the next motor-loop iteration. Reconnecting does not automatically re-enable.
Only the page that enabled control can refresh that heartbeat; other pages can
disable it. Browser background/screen-lock throttling can therefore stop control.
Zero PWM uses the existing driver stop behavior and may brake the motor; it does
not guarantee an instant physical stop.

HTTP runs in a separate task so slow HTTP requests do not block sensor sampling.
Sensor faults still latch output off until reset; the page reports a fault when
the web server has started. If initial sensor calibration fails, the hotspot may
not start; check Serial Monitor. Wi-Fi credentials are near the top of
`src/main.cpp`; anyone with those credentials can access this local controller.
The hotspot uses the ESP32 [Soft-AP API](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/wifi.html).

Bench verification after upload: confirm output remains off at startup, compare
enable/disable behavior, adjust Kp, then close the enabling page or disconnect
Wi-Fi and confirm zero PWM after the timeout. Hardware timing, RF connectivity,
and physical stopping must be checked on the actual assembly.

## Manual left/right and throttle

1. On the Wi-Fi page, set the **Throttle** slider (0..100% PWM; starts at 0).
2. Press **Turn left** or **Turn right**. This switches automatic control OFF
   and continuously commands that wheel direction at the selected PWM duty.
3. To change a running manual command, move the slider and press **Apply throttle**.
   Moving the slider alone stages a value; **Applied manual throttle** shows the
   value accepted by the ESP32. An update requires the same page's still-active
   manual session; it cannot restart a stopped/expired command or replace auto.
4. Press **Stop wheel** or **Disable control** to clear PWM in either mode.
   **Enable automatic control** explicitly switches back to the rate controller.

Left/right labels refer to wheel command direction; actual observed direction
depends on mounting and wiring. The selected Motor direction mapping is
preserved. Manual throttle is open-loop PWM, not measured RPM, power, or current.
At 50% it commands 128/255; at 100% it commands 255/255. Zero may brake the wheel
and does not guarantee an immediate physical stop.

Manual mode uses the same page-owned heartbeat: keep the enabling page open and
phone awake, or output clears after two seconds without contact. Startup, Stop,
range changes/calibration, and sensor faults leave manual output off. A fault or
calibration blocks manual commands. Neither automatic nor manual mode resumes
after calibration/reset without an explicit command. Bench-check direction and
stop behavior at low throttle before larger commands.

## MPU sensitivity and terminal plots

On the Wi-Fi page, select **MPU6050 gyro range** and press **Apply range & calibrate**.
Control turns OFF. Hold the sensor still for about two seconds until calibration
finishes, then explicitly enable control again. Changes during calibration or
after a latched fault are rejected. Reboot restores **+/-500 deg/s**.

| Range (deg/s) | Sensitivity (LSB per deg/s) |
|---|---|
| +/-250 | 131 |
| +/-500 | 65.5 |
| +/-1000 | 32.8 |
| +/-2000 | 16.4 |

The page displays the active range, sensitivity, and fixed **21 Hz** filter.
A lower range resolves smaller changes but clips at a lower rotation speed.
The conversion to deg/s follows the selected range, so switching ranges does not
multiply the physical rate or Kp. The controller still has a 2 deg/s deadband.
Only the Y gyroscope is logged; there is no wheel-speed measurement.

Serial output is CSV at roughly 50 samples/s, with actual timestamps:

```text
time_ms,gyro_y_raw_counts,gyro_y_raw_dps,gyro_y_corrected_dps,pwm,kp,enabled,gyro_range_dps,gyro_lsb_per_dps,filter_hz,mode,throttle_pct
1234,-1310,-10.0000,-9.5000,-15,2,1,250,131,21,auto,0
```

`raw_counts` is the signed sensor register value, `raw_dps` is converted before
bias subtraction, and `corrected_dps` is the calibrated rate used by control.
PWM is signed -255..255; `enabled` is 1 only for automatic control. `mode` is
`off`, `auto`, or `manual`; `throttle_pct` is the applied manual throttle (0 in
other modes). These two columns are appended to the previous CSV layout.
`time_ms` is milliseconds since boot.
Calibration creates an intentional gap in samples. Buffered serial skips a row
under backpressure rather than waiting and delaying the motor loop.
Diagnostic messages start with `#`; the ESP32 ROM may also print boot messages.

To display and record readings in the VS Code terminal, run **Tasks: Run Task >
ESP32: Log Telemetry**, or use:

```powershell
cd "C:\Users\jonat\Desktop\CTS-SAT-2\rw1dof\ESP_RW1DOF"
.\.venv\Scripts\python.exe -m platformio device monitor --filter log2file
```

Press EN/reset with the sensor still to capture the CSV header. The terminal
prints the log filename under `logs/device-monitor-*.log`. Stop with **Ctrl+C**
before uploading or opening another serial application. Reset also turns control
off and restores the default Kp/range, so select settings again after reset.

To extract the latest log into a clean CSV, keeping only one header and numeric
rows (one boot/session per recording), run:

```powershell
$telemetryLog = Get-ChildItem .\logs\device-monitor-*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$telemetryLines = Get-Content -LiteralPath $telemetryLog.FullName
$telemetryHeader = $telemetryLines | Where-Object { $_ -like 'time_ms,*' } | Select-Object -First 1
if (-not $telemetryHeader) { throw 'No CSV header: record again and press EN/reset after opening the monitor.' }
$telemetryCsv = @($telemetryHeader) + @($telemetryLines | Where-Object { $_ -match '^\d+,-?\d+,' })
$telemetryCsv | Set-Content -Encoding ascii .\telemetry.csv
```

Import `telemetry.csv` into Excel, MATLAB, or your plotting tool. Plot `time_ms`
against `gyro_y_corrected_dps`; use a separate axis/panel for `pwm`. Filter by
`gyro_range_dps` or `kp` to compare settings. Verify on hardware that all four
ranges report plausible rates, control stays off through recalibration, and
timestamps continue after the calibration gap before running motor experiments.

PlatformIO's sidebar also provides Build, Upload, and Monitor tasks. Its extension
manages its own Python environment; the supplied VS Code tasks use `.venv`.

Windows reported a Silicon Labs USB UART on **COM10** during setup. This is a
candidate port, not proof of the board model. Ports are detected automatically;
if multiple serial devices are connected, uncomment and set `upload_port` and
`monitor_port` in `platformio.ini`.

## PowerShell commands

```powershell
# Recreate the local CLI environment if needed:
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

# Build, inspect ports, upload, and monitor:
.\.venv\Scripts\python.exe -m platformio run
.\.venv\Scripts\python.exe -m platformio device list
.\.venv\Scripts\python.exe -m platformio run --target upload
.\.venv\Scripts\python.exe -m platformio device monitor
```

## Connection troubleshooting

- `MPU6050 range/filter configuration failed` on older firmware: the 21 Hz
  filter uses register value **4**, not 3 (44 Hz). Current firmware checks the
  correct value and has a compile-time check against the Adafruit enum. This
  startup fault prevents the hotspot and Wi-Fi LED from starting; upload the
  corrected firmware before diagnosing the LED pin or sensor wiring.

- No USB UART: try a data cable and another USB port; inspect Windows Device
  Manager for the board's USB bridge and install its manufacturer's driver if
  missing. The Silicon Labs device was already enumerated during setup.
- Connection timeout: hold BOOT while the uploader says `Connecting`, then release
  once writing begins. Some boards also require a tap on EN/reset.
- Port busy: close other serial monitors, including Arduino IDE and MATLAB.
- Upload stops partway through: upload baud is reduced to 57600 after an
  interrupted transfer. Disconnect the motor supply while flashing, close serial
  monitors, and retry with the ESP32 on a direct USB connection. If it repeats,
  try another short USB data cable and USB port. Serial Monitor stays at 115200.
- `Failed to start stub flasher`: `upload_flags = --no-stub` bypasses the temporary
  RAM flasher and uses the ESP32 ROM loader. This is an upload workaround, not a
  confirmed fix for USB/power instability. Remove this option after the connection
  is reliable if you want to return to the default flasher.
- Hardware breakpoints require a compatible debug probe or supported onboard
  USB JTAG interface; the basic serial workflow does not configure a debugger.

The program uses the MPU6050 Y-axis angular velocity to command motor
PWM on GPIO 14 (ENA) and direction on GPIO 13/27 (IN1/IN2), with a Wi-Fi status LED on GPIO 2.
Uploading replaces the firmware currently stored on the selected board.

References: [PlatformIO VS Code integration](https://docs.platformio.org/en/stable/integration/ide/vscode.html)
and [ESP32 Dev Module board definition](https://docs.platformio.org/en/stable/boards/espressif32/esp32dev.html).
MPU6050 readings follow the [Adafruit library example](https://github.com/adafruit/Adafruit_MPU6050/blob/master/examples/basic_readings/basic_readings.ino).
Motor interface: [ST L298 datasheet](https://www.st.com/resource/en/datasheet/l298.pdf).
PWM API: [Espressif LEDC](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/ledc.html).
