#include "control_state.h"
#include <cassert>
#include <cstdint>
#include <initializer_list>
#include <limits>

int main() {
    ControlState state;
    assert(!state.enabled && state.kp == 2.0f);
    assert(state.duty(20.0f, 0) == 0);
    assert(state.enable(100, 42));
    assert(state.duty(12.0f, 100) == 20);
    assert(state.setKp("4.5"));
    assert(!state.setKp("2\0junk", 6));
    assert(state.duty(12.0f, 100) == 45);
    assert(state.duty(-12.0f, 100) == -45);
    assert(state.duty(500.0f, 100) == 255);
    assert(state.duty(-500.0f, 100) == -255);
    assert(state.duty(2.0f, 100) == 0);
    assert(state.duty(std::numeric_limits<float>::quiet_NaN(), 100) == 0);
    for (const char *bad : {"", " ", "nan", "inf", "-1", "20.01", "2junk", "1e999", "1e-999"}) {
        assert(!state.setKp(bad));
        assert(state.kp == 4.5f);
    }
    assert(state.setKp("0"));
    assert(state.duty(500.0f, 100) == 0);
    assert(state.setKp("20"));
    assert(state.setKp("2"));
    assert(!state.heartbeat(500, 43));
    assert(state.heartbeat(500, 42));
    assert(state.duty(12.0f, 2499) == 20);
    assert(state.duty(12.0f, 2500) == 0);
    assert(!state.enabled);
    assert(!state.heartbeat(2501, 42)); // Heartbeat cannot re-enable.
    assert(state.enable(3000, 43));
    state.disable();
    assert(state.duty(12.0f, 3001) == 0);
    assert(state.enable(UINT32_MAX - 1000, 42));
    assert(state.duty(12.0f, 998) == 20);
    assert(state.duty(12.0f, 999) == 0);
    assert(state.enable(4000, 42));
    assert(!state.heartbeat(6000, 42)); // Late heartbeat cannot revive a lease.
    assert(!state.enabled);
    state.latchFault();
    assert(!state.enable(6001, 42));
    assert(state.duty(500.0f, 6001) == 0);
    assert(!state.enable(6001, 0));
}
