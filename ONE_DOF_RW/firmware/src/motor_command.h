#pragma once

#include <cmath>

// Starting values for the rate-to-PWM test; tune for your motor and driver.
constexpr float MOTOR_RATE_DEADBAND_DPS = 2.0f;
constexpr float MOTOR_PWM_PER_DPS = 2.0f;
constexpr int MOTOR_MAX_DUTY = 255; // Matches the 8-bit PWM in main.cpp.

inline int motorDutyForRate(float rateDps, float kp = MOTOR_PWM_PER_DPS) {
    if (!std::isfinite(rateDps) || !std::isfinite(kp) || kp < 0.0f) {
        return 0;
    }
    const float magnitude = std::fabs(rateDps);
    if (magnitude <= MOTOR_RATE_DEADBAND_DPS) {
        return 0;
    }
    const float requestedDuty =
        (magnitude - MOTOR_RATE_DEADBAND_DPS) * kp;
    const int duty = requestedDuty >= MOTOR_MAX_DUTY
        ? MOTOR_MAX_DUTY
        : static_cast<int>(requestedDuty + 0.5f);
    return rateDps < 0.0f ? -duty : duty;
}
