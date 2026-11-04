#pragma once

#include <cstddef>
#include <cstdint>

// Check transfer status before interpreting register bytes. In particular, an
// I2C failure must not become 0xFF masked into a valid gyro-range enum.
template <typename I2cBus>
bool readMpuRegisters(I2cBus &bus, uint8_t address, uint8_t reg,
                      uint8_t *bytes, size_t length) {
    bus.beginTransmission(address);
    const bool queued = bus.write(reg) == 1;
    const int status = bus.endTransmission(false);
    if (!queued || status != 0 || bus.requestFrom(address, length) != length) {
        return false;
    }
    for (size_t i = 0; i < length; ++i) {
        const int value = bus.read();
        if (value < 0) return false;
        bytes[i] = static_cast<uint8_t>(value);
    }
    return true;
}
