#include "control_state.h"
#include <cassert>

int main() {
    ControlState state;
    assert(state.invertMotorDirection); // Preserve the existing wiring mapping.
    assert(state.enable(0, 42));
    assert(state.setMotorDirectionInverted(false));
    assert(!state.invertMotorDirection && !state.active() && state.owner == 0);
    assert(state.duty(12, 1) == 0);
    assert(!state.heartbeat(1, 42)); // A stale session cannot restart the wheel.
    assert(state.setManual(1, 50, 2, 42));
    assert(state.setMotorDirectionInverted(true));
    assert(state.invertMotorDirection && !state.active() && state.throttlePercent == 0);
    assert(state.duty(12, 3) == 0);
    assert(state.enable(4, 42));
    assert(state.duty(12, 4) == 20); // Direction configuration preserves gain mapping.
    assert(state.setMotorDirectionInverted(true)); // Retries also leave outputs off.
    assert(!state.active());
    assert(state.requestGyroRange(250));
    assert(!state.setMotorDirectionInverted(false));
    assert(state.invertMotorDirection);
    state.finishGyroCalibration();
    state.latchFault();
    assert(!state.setMotorDirectionInverted(false));
    assert(state.fault && state.invertMotorDirection && !state.active());
}
