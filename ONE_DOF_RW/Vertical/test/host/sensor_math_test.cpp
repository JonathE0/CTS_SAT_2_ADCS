#include "SensorMath.h"
#include <cmath>
#include <cstdlib>
#include <iostream>

static void check(bool condition, const char* message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(1);
    }
}

int main() {
    check(decodeSigned16(0x00, 0x00) == 0, "decode zero");
    check(decodeSigned16(0x7f, 0xff) == 32767, "decode positive maximum");
    check(decodeSigned16(0x80, 0x00) == -32768, "decode negative minimum");
    check(decodeSigned16(0xff, 0xff) == -1, "decode negative one");
    check(std::fabs(rollDegrees(0, 0, 1)) < 0.01f, "flat roll");
    check(std::fabs(rollDegrees(0, 1, 0) - 90) < 0.01f, "positive roll");
    check(std::fabs(rollDegrees(0, -1, 0) + 90) < 0.01f, "negative roll");
    check(std::fabs(pitchDegrees(-1, 0, 0) - 90) < 0.01f, "positive pitch");
    check(std::fabs(pitchDegrees(1, 0, 0) + 90) < 0.01f, "negative pitch");

    GyroCalibration stationary;
    for (int i = 0; i < 200; ++i) stationary.add(0, 0, 1, 1.5f, -2, 0.5f);
    check(stationary.ready() && stationary.valid(), "accept stationary bias");
    check(std::fabs(stationary.bias(0) - 1.5f) < 0.01f, "X gyro bias");
    check(std::fabs(stationary.bias(1) + 2) < 0.01f, "Y gyro bias");
    check(std::fabs(stationary.bias(2) - 0.5f) < 0.01f, "Z gyro bias");

    GyroCalibration incomplete;
    incomplete.add(0, 0, 1, 0, 0, 0);
    check(!incomplete.ready() && !incomplete.valid(), "reject incomplete window");
    GyroCalibration moving;
    GyroCalibration accelerating;
    GyroCalibration spinning;
    for (int i = 0; i < 200; ++i) {
        moving.add(0, 0, 1, i % 2 ? 3 : -3, 0, 0);
        accelerating.add(0, 0, 1.3f, 0, 0, 0);
        spinning.add(0, 0, 1, 8, 0, 0);
    }
    check(!moving.valid(), "reject gyro variance from motion");
    check(!accelerating.valid(), "reject acceleration inconsistent with gravity");
    check(!spinning.valid(), "reject steady rotation");
    std::cout << "PASS: signed decoding, sensor-frame tilt, and gyro calibration\n";
}
