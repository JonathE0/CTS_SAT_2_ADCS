#pragma once

#include <cstdint>

constexpr uint8_t GYRO_FILTER_REGISTER_VALUE = 4; // DLPF_CFG=4 selects 21 Hz.

struct GyroSettings {
    int rangeDps;
    uint8_t registerValue;
    float lsbPerDps;

    float rateDps(int32_t rawCounts) const {
        return static_cast<float>(rawCounts) / lsbPerDps;
    }

    bool matchesRegisters(uint8_t gyroConfig, uint8_t filterConfig) const {
        // FS_SEL is bits 4:3; DLPF_CFG=4 is the fixed 21 Hz gyro filter.
        return rangeDps != 0 && ((gyroConfig >> 3) & 0x03) == registerValue &&
               (filterConfig & 0x07) == GYRO_FILTER_REGISTER_VALUE;
    }
};

// Same ranges and conversion factors used by the Adafruit MPU6050 library.
inline GyroSettings gyroSettings(int rangeDps) {
    switch (rangeDps) {
        case 250: return {250, 0, 131.0f};
        case 500: return {500, 1, 65.5f};
        case 1000: return {1000, 2, 32.8f};
        case 2000: return {2000, 3, 16.4f};
        default: return {0, 0, 0.0f};
    }
}
