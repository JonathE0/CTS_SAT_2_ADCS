#include "MotionTest.h"
#include <cstdlib>
#include <iostream>

static void check(bool condition, const char* message) {
    if (!condition) { std::cerr << "FAIL: " << message << '\n'; std::exit(1); }
}

int main() {
    MotionTest test;
    check(!test.running() && !test.armed(), "boot must be disabled and disarmed");
    check(!test.start(0), "reject unarmed start");
    check(test.arm() && test.start(100), "armed start");
    check(!test.armed() && test.phase() == MotionTest::Phase::Negative, "consume arming once");
    check(!test.arm() && !test.start(900), "retrigger must not extend motion");
    test.update(1099);
    check(test.phase() == MotionTest::Phase::Negative, "first pulse duration");
    test.update(1100);
    check(test.phase() == MotionTest::Phase::Pause, "disable between directions");
    test.update(2100);
    check(test.phase() == MotionTest::Phase::Positive, "second pulse");
    test.update(3100);
    check(!test.running() && !test.armed(), "automatic end without rearming");
    check(!test.start(3200), "no automatic repeat");
    test.arm(); test.start(0xfffffff0u); test.update(0x00000ba8u);
    check(!test.running(), "expiry survives millis rollover");
    test.arm(); test.start(1); test.stop();
    check(!test.running() && !test.armed(), "stop clears run and arming");
    test.arm(); test.stop(); check(!test.start(3), "stop cancels pending arming");
    check(encoderMagnetHealthy(0x20), "magnet detected with normal field");
    check(!encoderMagnetHealthy(0), "missing magnet blocks motion");
    check(!encoderMagnetHealthy(0x30), "weak magnet blocks motion");
    check(!encoderMagnetHealthy(0x28), "strong magnet blocks motion");
    check(encoderDeltaCounts(10, 4090) == 16, "forward encoder wrap");
    check(encoderDeltaCounts(4090, 10) == -16, "reverse encoder wrap");
    MotorCommandParser parser;
    for (char c : {'s', 't', 'a', 't', 'u', 's', '\n'})
        check(parser.feed(c) == 0, "text must not arm or start a test");
    check(parser.feed('a') == 0 && parser.feed('\n') == 'a', "exact arm line");
    check(parser.feed('t') == 0 && parser.feed('\r') == 0 && parser.feed('\n') == 't', "CRLF start line");
    check(parser.feed('h') == 0 && parser.feed('h') == 0 && parser.feed('\n') == 0, "reject multi-command line");
    check(parser.feed('x') == 'x', "stop without waiting for newline");
    parser.feed('\n');
    check(parser.feed('t') == 0 && parser.feed('\n') == 't', "recover parser after stop");
    check(parser.feed('l') == 0 && parser.feed('\n') == 'l', "exact left command line");
    check(parser.feed('r') == 0 && parser.feed('\n') == 'r', "exact right command line");
    check(test.startPulse(100, false), "explicit left pulse does not require separate arming");
    check(test.phase() == MotionTest::Phase::Negative, "left uses negative command");
    check(!test.startPulse(500, true), "reject reversal while pulse is active");
    test.update(1100);
    check(!test.running(), "left pulse expires at one second");
    check(test.startPulse(1200, true), "explicit right pulse");
    test.update(1400);
    check(test.phase() == MotionTest::Phase::Positive && test.pulseElapsed(1400) == 200, "right ramp starts at zero");
    test.update(2200);
    check(!test.running() && !test.armed(), "right pulse expires disarmed");
    check(test.startPulse(0xfffffff0u, false), "pulse starts near rollover");
    test.update(0x000003d8u);
    check(!test.running(), "single pulse timeout survives rollover");
    check(encoderAllowsManualPulse(0x33), "weak field permits open-loop diagnostic pulse");
    check(!encoderAllowsManualPulse(0), "no detected magnet blocks manual pulse");
    check(parser.feed('r', true) == 0 && parser.feed('\n') == 0, "discard command started during a pulse");
    check(parser.feed('x', true) == 'x', "stop remains immediate during a pulse");
    parser.feed('\n', true);
    check(parser.feed('l') == 0 && parser.feed('\n') == 'l', "fresh command after pulse is accepted");
    check(encoderAllowsMotion(true, 0x33, true), "manual pulse permits weak warning");
    check(!encoderAllowsMotion(true, 0x33, false), "automatic sequence keeps strict field check");
    check(!encoderAllowsMotion(false, 0x20, true), "any observed I2C failure stops manual pulse");
    std::cout << "PASS: one-shot motion, stop, rollover, magnet checks, encoder wrap\n";
}
