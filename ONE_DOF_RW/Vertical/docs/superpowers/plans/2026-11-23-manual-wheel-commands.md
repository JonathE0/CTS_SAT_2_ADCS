# Manual Wheel Commands Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline.

**Goal:** User can send exact `l`/`r` lines for individual low-power wheel pulses
while continuing to read both sensors in the same terminal.

**Architecture:** Reuse the tested motion sequence and SimpleFOC driver behind
`WheelControl`. The `motor_test` environment links it into the existing sensor
entry point; the default `sensors` environment stays disabled-only.

**Tech Stack:** Existing pinned ESP32/Arduino/SimpleFOC toolchain.
**Spec:** User requested left/right on command after verifying live MPU/encoder readings.

## Constraints and acceptance

- `l` and `r` are exact single-letter lines; each starts one one-second pulse,
  +/-1 rad/s, 0.5 V maximum q-axis command, with existing 200 ms ramps.
- Deliberate l/r command is the manual start authorization; no separate arm.
- Reject commands during motion except immediate `x`; no retrigger extension.
- Disable at boot, on timeout, loop delay, I2C failure, missing detected magnet.
- Field-strength flags are diagnostic for these open-loop pulses; raw angle is
  not used as motor feedback. Existing armed automatic sequence stays strict.
- Preserve MPU and encoder terminal columns; append `motor_enabled` in motor mode.
- Use `i` for IMU reinitialization; motor-mode `r` means right. Sensor-only `r`
  remains an alias for `i`. Do not run scan/calibration/reinit during a pulse.
- Do not automatically increase voltage when a pulse produces no visible motion.

## Execution

- [x] Add failing tests for exact l/r parsing, one-second expiry in both
  directions, no active retrigger, rollover, and warning-only manual status.
- [x] Implement sequence/parser and WheelControl integration; all host tests pass.
- [ ] Build both environments; independent actuation-path review.
- [ ] Upload boot-disabled motor firmware and verify combined telemetry/stop.
- [ ] Exercise one requested left pulse and one right pulse, verify final EN=0,
  and report actual encoder displacement without claiming verified angle accuracy.
