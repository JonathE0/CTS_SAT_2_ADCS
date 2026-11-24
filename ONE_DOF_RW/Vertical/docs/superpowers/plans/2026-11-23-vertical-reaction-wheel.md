# Vertical Reaction Wheel Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** A buildable ESP32 PlatformIO workspace for sensor-first commissioning.

**Architecture:** Arduino Wire handles MPU6050 register access and bus discovery.
Portable C++ helpers decode readings, calculate accelerometer tilt, and validate
stationary gyro calibration. Motor GPIOs remain untouched.

**Tech Stack:** PlatformIO Core 6, Espressif32 8.0.0, Arduino C++, PowerShell.

**Spec:** `docs/superpowers/specs/2026-11-23-vertical-reaction-wheel-design.md`

## Global Constraints

- Work in the user-selected Vertical folder; preserve sibling projects.
- I2C SDA 33, SCL 32; reserve EN 13 and PWM 27/25/26 without driving them.
- No automatic motor activation or guessed driver/motor parameters.
- No encoder register access until its identity is confirmed.

## Review Focus

- Negative and extreme signed readings: host decode tests.
- Unknown IMU identity / partial I2C reads: reject and report, bench checklist.
- Moving calibration / missing samples: host rejection tests.
- Sensor loss after calibration: invalidate offsets and require reinitialization.
- Unconfirmed mounting: label roll/pitch as sensor-frame, not balance angle.

## Task 1: Sensor diagnostics and workspace

Files: `platformio.ini`, `include/Config.h`, `include/SensorMath.h`,
`src/main.cpp`, `test/host/sensor_math_test.cpp`, `scripts/test.ps1`,
`.vscode/tasks.json`, `.vscode/extensions.json`, `.gitignore`, `README.md`,
`docs/commissioning.md`, `Vertical.code-workspace`.

Interfaces: `decodeSigned16(high, low)`, `rollDegrees(ax, ay, az)`,
`pitchDegrees(ax, ay, az)`, and `GyroCalibration::add/ready/valid/bias`.

- [x] Write host tests for signed extrema, known tilt orientations, accepted
      fixed gyro bias, rejected motion, and insufficient calibration samples.
- [x] Run the tests and observe failure before adding the sensor math helpers.
- [x] Implement helpers, register-based sensor diagnostics, and central config.
- [x] Create pinned PlatformIO configuration, VS Code tasks, and bench docs.
- [x] Run all host tests and the ESP32 build; record actual results.
- [x] Review the complete change and document remaining hardware verification.

## Execution notes

Implement inline in this folder as requested; do not create a separate worktree
or commit unrelated parent-repository files. No upload without an identified
ESP32 USB port. Only Bluetooth serial ports were visible during initial inspection.

Verification: host tests passed; `pio run -e sensors` succeeded with RAM 23,524
bytes and flash 333,188 bytes. PlatformIO/VS Code extensions were already present.
The completed workspace was launched using VS Code's CLI. Hardware upload,
sensor readings, motor operation, and balance remain unverified.

Independent review identified sensor wiring order and a missing IMU wake-error
message. Both were corrected before the final build and host-test rerun.
