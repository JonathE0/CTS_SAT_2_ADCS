#pragma once

#include <cmath>

// Edge Rev1 model. All angles are in radians, rates in rad/s, torque in N·m.
class EdgeBalance {
public:
    static constexpr float gravityTorque = 0.080f; // m*g*l
    static constexpr float bodyInertia = 5.9e-4f;   // About pivot, excludes wheel spin.
    static constexpr float wheelInertia = 4.19e-5f;
    static constexpr float stallTorque = 0.030f;    // Modeled torque limit at zero speed.
    static constexpr float noLoadRate = 272.0f;

    EdgeBalance() {
        const float a = gravityTorque / bodyInertia;
        const float s = std::sqrt(a);
        const float p1 = 1.5f * s, p2 = 1.9f * s, p3 = 0.6f * s;
        // Match the linearized closed-loop polynomial to (λ+p1)(λ+p2)(λ+p3).
        wheelGain = p1 * p2 * p3 * wheelInertia / a;
        leanGain = gravityTorque + bodyInertia * (p1*p2 + p1*p3 + p2*p3);
        rateGain = bodyInertia * (p1 + p2 + p3)
                 + (1.0f + bodyInertia / wheelInertia) * wheelGain;
    }

    // Lean is measured from gravity upright. Wheel rate is relative to the
    // body, with both rates positive about the same axis. Positive torque
    // accelerates the wheel positively and pushes the body negatively.
    float torque(float lean, float bodyRate, float wheelRate) const {
        if (!std::isfinite(lean) || !std::isfinite(bodyRate) || !std::isfinite(wheelRate))
            return 0.0f;

        const float requested = leanGain * lean + rateGain * bodyRate + wheelGain * wheelRate;
        float limited = std::fmax(-stallTorque, std::fmin(stallTorque, requested));
        // Approximate loss of torque while driving the wheel faster. Keep
        // braking authority in the opposite direction, as in the simulator.
        if (limited * wheelRate > 0.0f)
            limited *= std::fmax(0.0f, 1.0f - std::fabs(wheelRate) / noLoadRate);
        return limited;
    }

private:
    float leanGain;
    float rateGain;
    float wheelGain;
};
