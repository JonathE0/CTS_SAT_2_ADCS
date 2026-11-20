#include "control_state.h"
#include <cassert>
#include <cmath>
#include <limits>

int main() {
    ControlState s;
    assert(!s.positionMode);
    s.duty(10, 0);
    for (unsigned t=20; t<=1000; t+=20) s.duty(10, t);
    assert(std::fabs(s.angleDeg-10)<0.001); // Tracks while disabled.
    assert(s.zeroPosition() && s.angleDeg==0);
    assert(!s.configurePosition(true, 0, 0, 10));
    assert(!s.configurePosition(true, INFINITY, 1, 10));
    assert(s.configurePosition(true, 20, 0.5, 5));
    assert(!s.enabled);
    assert(s.enable(1000, 1));
    assert(s.duty(0,1000)==-10); // Positive target requests positive body rate.
    assert(s.duty(0,1020)==-10); // Desired rate limited to 5 deg/s.
    s.angleDeg=20;
    assert(s.duty(0,1040)==0); // At target and stationary.
    assert(s.duty(1,1040)==2); // Braking, without rate-mode deadband.
    s.angleDeg=30;
    assert(s.duty(0,1040)==10); // Overshoot reverses command.
    assert(s.setKi("1"));
    s.duty(0,1060);
    s.duty(0,1080);
    assert(s.integralDuty>0);
    assert(s.zeroPosition() && !s.enabled && s.integralDuty==0);
    assert(s.enable(1100,1));
    s.duty(0,1100);
    assert(s.duty(0,1401)==0 && s.fault); // Unknown motion invalidates hold.

    ControlState wrap;
    wrap.duty(10, UINT32_MAX-49);
    wrap.duty(10, 50);
    assert(std::fabs(wrap.angleDeg-1)<0.001);
    wrap.requestGyroRange(250);
    wrap.finishGyroCalibration();
    assert(wrap.angleDeg==0 && !wrap.hasAngleTime);

    ControlState interrupted;
    interrupted.duty(0, 0);
    interrupted.duty(0, 201);
    assert(!interrupted.angleValid && !interrupted.fault);
    assert(interrupted.configurePosition(true, 10, 0.5, 5));
    assert(!interrupted.enable(201, 1));
    assert(interrupted.zeroPosition() && interrupted.enable(201, 1));

    ControlState invalid;
    assert(invalid.configurePosition(true, 10, 0.5, 5));
    assert(invalid.enable(0,1));
    assert(invalid.duty(NAN,0)==0 && invalid.fault);
}
