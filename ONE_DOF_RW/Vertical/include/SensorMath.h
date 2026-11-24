#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>

inline int16_t decodeSigned16(uint8_t high, uint8_t low) {
    const int32_t value = (static_cast<int32_t>(high) << 8) | low;
    return static_cast<int16_t>(value >= 32768 ? value - 65536 : value);
}

inline float rollDegrees(float /*ax*/, float ay, float az) {
    return std::atan2(ay, az) * 57.2957795f;
}

inline float pitchDegrees(float ax, float ay, float az) {
    return std::atan2(-ax, std::sqrt(ay * ay + az * az)) * 57.2957795f;
}

class GyroCalibration {
public:
    static constexpr unsigned sampleCount = 200;

    void add(float ax, float ay, float az, float gx, float gy, float gz) {
        const float gravity = std::sqrt(ax * ax + ay * ay + az * az);
        stationary_ = stationary_ && gravity >= 0.9f && gravity <= 1.1f;
        const float gyro[] = {gx, gy, gz};
        for (size_t axis = 0; axis < 3; ++axis) {
            stationary_ = stationary_ && std::isfinite(gyro[axis]);
            sum_[axis] += gyro[axis];
            squares_[axis] += gyro[axis] * gyro[axis];
        }
        ++count_;
    }

    bool ready() const { return count_ >= sampleCount; }

    bool valid() const {
        if (!ready() || !stationary_) return false;
        for (size_t axis = 0; axis < 3; ++axis) {
            const float mean = bias(axis);
            const float variance = squares_[axis] / count_ - mean * mean;
            if (std::fabs(mean) > 5.0f || variance > 1.0f) return false;
        }
        return true;
    }

    float bias(size_t axis) const { return count_ ? sum_[axis] / count_ : 0; }

private:
    unsigned count_ = 0;
    bool stationary_ = true;
    float sum_[3] = {};
    float squares_[3] = {};
};
