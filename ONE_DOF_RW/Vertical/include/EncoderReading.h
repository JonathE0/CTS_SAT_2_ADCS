#pragma once
#include <cstdint>

struct EncoderReading {
    uint16_t raw;
    uint8_t status;
    float angleDegrees() const { return raw * (360.0f / 4096.0f); }
    bool detected() const { return (status & 0x20) != 0; }
    bool weak() const { return (status & 0x10) != 0; }
    bool strong() const { return (status & 0x08) != 0; }
    bool healthy() const { return detected() && !weak() && !strong(); }
};

inline EncoderReading decodeEncoderReading(uint8_t status, uint8_t high, uint8_t low) {
    return {static_cast<uint16_t>(((high & 0x0F) << 8) | low), status};
}
