#pragma once

#include <cstdint>

namespace Config {
constexpr int sda = 33;
constexpr int scl = 32;
constexpr uint32_t i2cHz = 400000;
constexpr uint16_t i2cTimeoutMs = 20;
constexpr uint32_t serialBaud = 115200;
constexpr uint32_t samplePeriodMs = 5;
constexpr uint32_t telemetryPeriodMs = 100;

// Sensor firmware holds EN LOW. Only motor_test drives the PWM pins.
constexpr int driverEnable = 13;
constexpr int driverIn1 = 27;
constexpr int driverIn2 = 25;
constexpr int driverIn3 = 26;
}  // namespace Config
