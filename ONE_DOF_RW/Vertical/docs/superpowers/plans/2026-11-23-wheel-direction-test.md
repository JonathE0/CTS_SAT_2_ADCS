# Wheel Direction Test Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. The user requested a secured left/right test and supplied the exact motor kit listing.

**Goal:** Execute one bounded, low-voltage direction test, then disable outputs.

**Architecture:** Separate `motor_test` environment preserves sensor firmware.
SimpleFOC generates open-loop commutation for seven pole pairs. A separately
controlled active-high EN stays LOW through initialization; serial arming is
required. AS5600 read errors or invalid magnet status prevent/abort motion.

**Spec:** User-requested left, stop, right, stop test; secured assembly, 12 V supply.
**Tech Stack:** Existing ESP32 Arduino toolchain, SimpleFOC 2.4.0, host C++ tests.

## Evidence and constraints

- Exact listing photos show SimpleFOC Mini v1.0 and DRV8313, 8–35 V supply.
- TI DRV8313 datasheet confirms EN is active-high with internal pulldown.
- Listing specifies 12 V motor, seven pole pairs, 2.3-ohm phase resistance,
  AS5600 encoder. These are seller specifications, not bench measurements.
- Use 0.5 V maximum commanded q-axis voltage; no current sensing or closed-loop
  current limit is claimed. Driver supply remains 12 V.
- One second negative command, one second disabled coast, one second positive
  command, then disabled. This is a direction check, not position control or balance.
- Physical left/right depends on viewpoint and phase wiring; measure encoder
  displacement and do not claim rotation from command acknowledgement alone.
- Never run automatically on boot; `a` arms, `t` consumes arming once, `x` stops.

## Task and review focus

- [x] Test sequence idle boot, arming, one-shot expiry, no retrigger extension,
  abort, elapsed-time rollover, magnetic-status rejection, and encoder wrap.
- [x] Observe failing test; implement `MotionTest.h` and pass all host tests.
- [x] Add `motor_test.cpp`, separate build filters and dependency; document controls.
- [x] Build both environments and obtain independent review before powered motion.
- [x] Upload disabled-by-default firmware; read encoder health before arming.
- [ ] Execute one requested test only if health checks pass; capture actual
  displacement and final disabled state. Report any lack of movement directly.

Review fixes: exact command-line parser with regression checks, suppress help
during motion, refresh timestamp after I2C, and invoke SimpleFOC 2.4 loopFOC after
move. Reviewer verified fixes with no remaining blocker. All host tests pass.
Sensor build passed. Motor-test build passed (24,612 bytes RAM; 381,248 flash)
with warnings in upstream SimpleFOC sources. No local-source build errors.

Dependency setup: registry had no 2.4.0 package, so use official v2.4.0 Git tag,
resolved commit `4f072b365f6e0185adca544071e595834405babc`. Shorten PlatformIO's
dependency cache path to avoid Windows MAX_PATH failures in upstream examples.

Live result: upload and flash verification succeeded on COM10. Help/stop
handshake confirmed the motor-test image. Thirty consecutive status rows showed
phase=0, STATUS=0x33, healthy=0, EN=0. Per the ams AS5600 datasheet, MD and ML
are set: magnet detected but field too weak. No arm/start commands were sent.
Direction test remains pending physical magnet alignment/gap correction.
