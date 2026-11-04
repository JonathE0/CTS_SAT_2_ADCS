#include "control_state.h"
#include <cassert>
#include <cstdint>

int main() {
    ControlState state;
    assert(state.enable(0, 42));
    assert(state.startRamp(1, 50, 0, 42));
    assert(state.manual && state.rampTest && !state.enabled);
    assert(state.duty(100, 0) == 0);
    for (uint32_t t = 500; t < 7000; t += 500) {
        assert(state.heartbeat(t, 42));
        const int expected = t < 5000 ? static_cast<int>(128 * t / 5000) : 128;
        assert(state.duty(-100, t) == expected);
    }
    assert(state.duty(100, 7000) == 0);
    assert(!state.active() && !state.rampTest && state.owner == 0);
    assert(!state.heartbeat(7001, 42));

    assert(state.startRamp(-1, 100, 8000, 42));
    assert(!state.updateManualThrottle(75, 8001, 42));
    assert(state.heartbeat(9000, 42));
    assert(state.duty(0, 9000) == -51);
    assert(state.duty(0, 11000) == 0); // Heartbeat loss cancels the test.
    assert(!state.rampTest);
    assert(!state.startRamp(0, 50, 11001, 42));
    assert(!state.startRamp(1, 0, 11001, 42));
    assert(!state.startRamp(1, 101, 11001, 42));
    assert(!state.startRamp(1, 50, 11001, 0));

    assert(state.startRamp(1, 50, 12000, 42));
    state.disable();
    assert(!state.rampTest && state.duty(0, 12001) == 0);
    assert(state.startRamp(1, 50, 13000, 42));
    assert(state.setMotorDirectionInverted(false));
    assert(!state.rampTest && !state.active());
    assert(state.startRamp(1, 50, 14000, 42));
    assert(state.enable(14001, 42));
    assert(!state.rampTest && !state.manual);
    assert(state.startRamp(1, 50, 15000, 42));
    assert(state.requestGyroRange(250));
    assert(!state.rampTest && !state.startRamp(1, 50, 15001, 42));
    state.finishGyroCalibration();
    assert(state.startRamp(1, 50, 16000, 42));
    state.latchFault();
    assert(!state.rampTest && !state.startRamp(1, 50, 16001, 42));

    ControlState wrap;
    const uint32_t start = UINT32_MAX - 1000;
    assert(wrap.startRamp(1, 100, start, 42));
    assert(wrap.heartbeat(start + 1500, 42));
    assert(wrap.duty(0, start + 1500) == 76); // Unsigned timer wrap is safe.
}
