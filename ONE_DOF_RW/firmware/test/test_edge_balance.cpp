#include "edge_balance.h"
#include <cassert>
#include <cmath>
#include <limits>

static void checkRecovery(float lean, float rate, float wheelRate) {
    const EdgeBalance controller;
    // Hold each controller command for 5 ms. Integrate the nonlinear plant
    // at 0.1 ms to keep plant integration separate from controller timing.
    constexpr float dt = 0.0001f;
    for (int sample = 0; sample < 800; ++sample) {
        const float torque = controller.torque(lean, rate, wheelRate);
        assert(std::fabs(torque) <= EdgeBalance::stallTorque);
        for (int step = 0; step < 50; ++step) {
            const float acceleration =
                (EdgeBalance::gravityTorque * std::sin(lean) - torque) / EdgeBalance::bodyInertia;
            rate += dt * acceleration;
            lean += dt * rate;
            wheelRate += dt * (torque / EdgeBalance::wheelInertia - acceleration);
        }
        assert(std::fabs(lean) < 0.6f);
        assert(std::fabs(wheelRate) < EdgeBalance::noLoadRate);
    }
    assert(std::fabs(lean) < 0.001f);
    assert(std::fabs(rate) < 0.01f);
    assert(std::fabs(wheelRate) < 0.1f);
}

int main() {
    const EdgeBalance controller;
    assert(controller.torque(0, 0, 0) == 0);
    assert(controller.torque(0.1f, 0, 0) == EdgeBalance::stallTorque);
    assert(controller.torque(0.1f, 0, EdgeBalance::noLoadRate) == 0);
    assert(controller.torque(-1, 0, EdgeBalance::noLoadRate) < 0);
    assert(controller.torque(std::numeric_limits<float>::quiet_NaN(), 0, 0) == 0);
    checkRecovery(0.17f, 0, 0);   // About +10 degrees.
    checkRecovery(-0.17f, 0, 0);
    checkRecovery(0, 0.5f, 0);
    checkRecovery(0, 0, 50);
}
