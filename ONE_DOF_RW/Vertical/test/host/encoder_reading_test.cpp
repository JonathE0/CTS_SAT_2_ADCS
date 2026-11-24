#include "EncoderReading.h"
#include <cmath>
#include <cstdlib>
#include <iostream>

static void check(bool condition, const char* message) {
    if (!condition) { std::cerr << "FAIL: " << message << '\n'; std::exit(1); }
}

int main() {
    const auto healthy = decodeEncoderReading(0x20, 0xA8, 0x00);
    check(healthy.raw == 2048, "mask unused high angle bits");
    check(std::fabs(healthy.angleDegrees() - 180.0f) < 0.001f, "half revolution in degrees");
    check(healthy.detected() && healthy.healthy(), "normal field is healthy");
    const auto weak = decodeEncoderReading(0x33, 0x01, 0x23);
    check(weak.raw == 291 && weak.angleDegrees() > 25, "weak field must not hide raw readings");
    check(weak.detected() && weak.weak() && !weak.strong() && !weak.healthy(), "decode observed 0x33 warning");
    check(decodeEncoderReading(0x28, 0, 0).strong(), "strong field warning");
    check(!decodeEncoderReading(0, 0, 0).healthy(), "missing magnet is unhealthy");
    check(decodeEncoderReading(0x20, 0, 0).angleDegrees() == 0, "zero angle");
    check(decodeEncoderReading(0x20, 0x0F, 0xFF).angleDegrees() < 360, "maximum angle below one revolution");
    std::cout << "PASS: encoder angle and diagnostic status, including weak-field readings\n";
}
