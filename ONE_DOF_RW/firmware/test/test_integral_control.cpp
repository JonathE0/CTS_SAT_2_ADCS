#include "control_state.h"
#include <cassert>
#include <cmath>
#include <limits>
#include <initializer_list>

int main() {
    ControlState s;
    assert(s.ki == 0 && s.integralDuty == 0);
    assert(s.setKi("1"));
    assert(!s.setKi("1\0junk", 6));
    for (const char *bad : {"", "-1", "21", "nan", "inf", "1x"}) {
        assert(!s.setKi(bad) && s.ki == 1);
    }
    assert(s.enable(0, 42));
    assert(s.duty(12, 0) == 20);
    for (uint32_t t = 100; t <= 1000; t += 100) {
        assert(s.heartbeat(t, 42));
        s.duty(12, t);
    }
    assert(std::fabs(s.integralDuty - 10) < 0.001);
    assert(s.duty(12, 1000) == 30); // Repeated timestamp cannot integrate again.
    s.duty(0, 1100);
    assert(std::fabs(s.integralDuty - 10) < 0.001); // Deadband adds no drift.
    assert(s.setKi("0") && s.integralDuty == 0);
    assert(s.duty(12, 1200) == 20);

    assert(s.setKi("20"));
    s.disable(); assert(s.integralDuty == 0);
    assert(s.enable(2000, 42));
    for (uint32_t t = 2000; t <= 5000; t += 20) {
        assert(s.heartbeat(t, 42));
        assert(s.duty(1000, t) == 255);
    }
    assert(s.integralDuty == 0); // Saturated P must not wind up the integrator.
    assert(s.setKp("0"));
    s.resetIntegral();
    for (uint32_t t = 5020; t <= 6020; t += 20) {
        assert(s.heartbeat(t, 42));
        s.duty(12, t);
    }
    const float before = s.integralDuty;
    assert(before > 0 && before <= 255);
    s.duty(-12, 6040);
    assert(s.integralDuty < before); // Reversed error unwinds the correction.
    assert(s.setManual(1, 50, 6050, 42));
    assert(s.integralDuty == 0 && s.duty(1000, 6051) == 128);
    assert(s.enable(6060, 42));
    s.duty(12, 6080);
    assert(s.setMotorDirectionInverted(false) && s.integralDuty == 0);
    assert(s.enable(6100, 42));
    s.duty(12, 6120);
    assert(s.integralDuty > 0);
    assert(s.duty(std::numeric_limits<float>::quiet_NaN(), 6140) == 0);
    assert(s.integralDuty == 0);
    s.duty(12, 6160);
    assert(s.duty(12, 8100) == 0 && s.integralDuty == 0); // Lost heartbeat.
    assert(s.enable(8200, 42));
    s.duty(12, 8220);
    s.latchFault(); assert(s.integralDuty == 0 && s.duty(12, 8240) == 0);

    // Equivalent elapsed time gives the same correction at different sample rates.
    ControlState fast, slow;
    assert(fast.setKi("1") && slow.setKi("1"));
    assert(fast.enable(0, 42) && slow.enable(0, 42));
    for (uint32_t t = 20; t <= 1000; t += 20) fast.duty(-12, t);
    for (uint32_t t = 100; t <= 1000; t += 100) slow.duty(-12, t);
    assert(std::fabs(fast.integralDuty - slow.integralDuty) < 0.001);
    assert(std::fabs(fast.integralDuty + 10) < 0.001);
    fast.duty(-12, 1500); // Sampling interruption clears stored correction.
    assert(fast.integralDuty == 0);

    ControlState limited;
    assert(limited.setKp("0") && limited.setKi("20") && limited.enable(0, 42));
    for (uint32_t t = 0; t <= 4000; t += 20) {
        assert(limited.heartbeat(t, 42));
        const int output = limited.duty(-12, t);
        assert(output >= -255 && output <= 0);
    }
    assert(limited.integralDuty == -255);
    limited.duty(12, 4020);
    assert(limited.integralDuty > -255);
    assert(limited.setKp("2") && limited.integralDuty == 0);

    ControlState wrap;
    assert(wrap.setKi("1") && wrap.enable(UINT32_MAX - 50, 42));
    assert(wrap.duty(12, 49) == 21);
    assert(std::fabs(wrap.integralDuty - 1) < 0.001);
}
