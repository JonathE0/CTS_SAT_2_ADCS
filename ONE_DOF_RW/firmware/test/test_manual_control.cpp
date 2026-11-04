#include "control_state.h"
#include <cassert>
#include <cstring>
#include <initializer_list>

int main() {
    ControlState state;
    assert(!state.manual);
    assert(state.enable(0, 42));
    assert(state.setManual(-1, 50, 100, 42));
    assert(state.manual && !state.enabled);
    assert(state.duty(0.0f, 100) == -128);
    assert(state.duty(500.0f, 100) == -128); // Manual output ignores platform rate.
    assert(state.setManual(1, 100, 200, 42));
    assert(state.duty(-500.0f, 200) == 255);
    assert(!state.setManual(0, 50, 200, 42));
    assert(!state.setManual(2, 50, 200, 42));
    assert(!state.setManual(1, -1, 200, 42));
    assert(!state.setManual(1, 101, 200, 42));
    assert(!state.setManual(1, 50, 200, 0));
    assert(state.duty(0.0f, 200) == 255); // Invalid request leaves state intact.
    assert(state.setManual(-1, 100, 200, 42));
    assert(state.duty(0.0f, 200) == -255);
    assert(state.setManual(1, 0, 200, 42));
    assert(state.manual && state.duty(0.0f, 200) == 0);
    assert(state.setManual(1, 1, 200, 42));
    assert(state.duty(0.0f, 200) == 3);
    assert(!state.heartbeat(500, 43));
    assert(state.heartbeat(500, 42));
    assert(state.duty(0.0f, 2499) == 3);
    assert(state.duty(0.0f, 2500) == 0 && !state.manual);
    assert(!state.heartbeat(2501, 42));
    assert(state.setManual(1, 50, 3000, 42));
    assert(state.enable(3001, 42));
    assert(!state.manual && state.enabled && state.throttlePercent == 0);
    assert(state.duty(12.0f, 3001) == 20);
    assert(state.setManual(1, 50, 3002, 42));
    state.disable();
    assert(!state.manual && !state.enabled && state.duty(500.0f, 3002) == 0);
    assert(state.setManual(1, 50, 3003, 42));
    assert(state.requestGyroRange(250));
    assert(!state.manual && !state.setManual(1, 50, 3003, 42));
    state.finishGyroCalibration();
    assert(!state.manual && !state.enabled);
    assert(state.setManual(1, 50, 6000, 42));
    state.latchFault();
    assert(!state.manual && state.duty(0.0f, 6000) == 0);
    assert(!state.setManual(1, 50, 6001, 42));

    int throttle = 99;
    for (const char *value : {"0", "50", "100"}) {
        assert(parseThrottlePercent(value, std::strlen(value), throttle));
    }
    assert(throttle == 100);
    for (const char *bad : {"", "-1", "101", "1.5", " 50", "50 ", "1e2", "nan", "9999"}) {
        assert(!parseThrottlePercent(bad, std::strlen(bad), throttle));
        assert(throttle == 100);
    }
    assert(!parseThrottlePercent("5\0x", 3, throttle));

    assert(parseManualDirection("left", 4) == -1);
    assert(parseManualDirection("right", 5) == 1);
    assert(parseManualDirection("left\0junk", 9) == 0);
    assert(parseManualDirection("right\0junk", 10) == 0);
    assert(parseManualDirection("Left", 4) == 0);
    assert(!exactText("1\0junk", 6, "1"));
    assert(!exactText("250\0junk", 8, "250"));

    ControlState update;
    assert(!update.updateManualThrottle(50, 0, 42)); // Cannot start via throttle.
    assert(update.setManual(-1, 25, 0, 42));
    assert(!update.updateManualThrottle(50, 1, 43)); // Cannot take another page's session.
    assert(update.updateManualThrottle(50, 1, 42));
    assert(update.manualDirection == -1 && update.duty(0, 1) == -128);
    assert(!update.updateManualThrottle(101, 2, 42));
    update.disable();
    assert(!update.updateManualThrottle(75, 3, 42));
    assert(update.enable(4, 42));
    assert(!update.updateManualThrottle(75, 5, 42));
    assert(update.enabled && !update.manual); // Stale update cannot replace auto.
    assert(update.setManual(1, 25, 10, 42));
    assert(!update.updateManualThrottle(50, 2010, 42)); // Cannot revive expired lease.
    assert(!update.manual && !update.enabled);
}
