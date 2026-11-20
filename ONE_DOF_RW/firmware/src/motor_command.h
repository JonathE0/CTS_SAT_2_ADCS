#pragma once

#include <cmath>

// Starting values for the rate-to-PWM test; tune for your motor and driver.
constexpr float MOTOR_RATE_DEADBAND_DPS = 2.0f;
constexpr float MOTOR_PWM_PER_DPS = 2.0f;
constexpr int MOTOR_MAX_DUTY = 255; // Matches the 8-bit PWM in main.cpp.

inline float limitMagnitude(float value, float limit) {
    return std::fmax(-limit, std::fmin(limit, value));
}

inline float rateErrorOutsideDeadband(float rateDps) {
    const float magnitude = std::fmax(0.0f, std::fabs(rateDps) - MOTOR_RATE_DEADBAND_DPS);
    return std::copysign(magnitude, rateDps);
}

inline int motorDutyForRate(float rateDps, float kp = MOTOR_PWM_PER_DPS) {
    if (!std::isfinite(rateDps) || !std::isfinite(kp) || kp < 0.0f) return 0;
    return std::lround(limitMagnitude(rateErrorOutsideDeadband(rateDps) * kp, MOTOR_MAX_DUTY));
}
