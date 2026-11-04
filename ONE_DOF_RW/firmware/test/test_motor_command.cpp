#include "motor_command.h"
#include <cassert>
#include <initializer_list>
#include <limits>

int main() {
    assert(motorDutyForRate(0.0f) == 0);
    assert(motorDutyForRate(4.9f) == 0);
    assert(motorDutyForRate(-5.0f) == 0);
    assert(motorDutyForRate(47.5f) == 64);
    assert(motorDutyForRate(-47.5f) == -64);
    assert(motorDutyForRate(90.0f) == 128);
    assert(motorDutyForRate(500.0f) == 128);
    assert(motorDutyForRate(-500.0f) == -128);
    assert(motorDutyForRate(std::numeric_limits<float>::quiet_NaN()) == 0);
    assert(motorDutyForRate(std::numeric_limits<float>::infinity()) == 0);

    // Stopping after rotation in either direction clears the command.
    for (float rate : {47.5f, -47.5f}) {
        assert(motorDutyForRate(rate) != 0);
        assert(motorDutyForRate(0.0f) == 0);
    }
}
