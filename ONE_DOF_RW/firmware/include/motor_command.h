#pragma once

#include <cmath>

// PWM duty command, not measured wheel RPM. 128/255 limits initial output to 50%.
constexpr float RATE_DEADBAND_DPS = 5.0f;
constexpr float FULL_COMMAND_RATE_DPS = 90.0f;
constexpr int MAX_MOTOR_DUTY = 128;

inline int motorDutyForRate(float rateDps) {
    if (!std::isfinite(rateDps) || std::fabs(rateDps) <= RATE_DEADBAND_DPS) {
        return 0;
    }
    float fraction = (std::fabs(rateDps) - RATE_DEADBAND_DPS) /
                     (FULL_COMMAND_RATE_DPS - RATE_DEADBAND_DPS);
    if (fraction > 1.0f) {
        fraction = 1.0f;
    }
    const int duty = static_cast<int>(std::lround(fraction * MAX_MOTOR_DUTY));
    return rateDps > 0.0f ? duty : -duty;
}
