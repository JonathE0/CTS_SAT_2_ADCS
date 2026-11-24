#pragma once
#include <cstdint>

inline bool encoderMagnetHealthy(uint8_t status) {
    return (status & 0x38) == 0x20;  // MD set; ML and MH clear.
}

inline bool encoderAllowsManualPulse(uint8_t status) {
    return (status & 0x20) != 0;  // Open-loop pulse: field warnings remain diagnostic.
}

inline bool encoderAllowsMotion(bool readOk, uint8_t status, bool manual) {
    return readOk && (manual ? encoderAllowsManualPulse(status) : encoderMagnetHealthy(status));
}

inline int encoderDeltaCounts(uint16_t current, uint16_t previous) {
    int delta = static_cast<int>(current) - previous;
    if (delta > 2048) delta -= 4096;
    if (delta < -2048) delta += 4096;
    return delta;
}

class MotorCommandParser {
public:
    char feed(char value, bool inhibited = false) {
        if (value == 'x') { length_ = 2; return 'x'; }
        if (value == '\r') return 0;
        if (inhibited) length_ = 2;  // Discard this line even if Enter arrives after the pulse.
        if (value == '\n') {
            const char command = length_ == 1 ? first_ : 0;
            length_ = 0;
            return command == 'a' || command == 't' || command == 'h' || command == 'l' ||
                   command == 'r' || command == 's' || command == 'i' || command == 'c' ? command : 0;
        }
        if (length_ == 0) first_ = value;
        if (length_ < 2) ++length_;
        return 0;
    }
private:
    unsigned length_ = 0;
    char first_ = 0;
};

class MotionTest {
public:
    enum class Phase { Idle, Negative, Pause, Positive };
    bool arm() {
        if (running()) return false;
        armed_ = true;
        return true;
    }
    bool start(uint32_t now) {
        if (!armed_ || running()) return false;
        armed_ = false;
        started_ = now;
        singlePulse_ = false;
        phase_ = Phase::Negative;
        return true;
    }
    bool startPulse(uint32_t now, bool positive) {
        if (running()) return false;
        armed_ = false;
        started_ = now;
        singlePulse_ = true;
        phase_ = positive ? Phase::Positive : Phase::Negative;
        return true;
    }
    void update(uint32_t now) {
        if (!running()) return;
        const uint32_t elapsed = now - started_;
        if (singlePulse_) {
            if (elapsed >= 1000) stop();
            return;
        }
        if (elapsed >= 3000) stop();
        else if (elapsed >= 2000) phase_ = Phase::Positive;
        else if (elapsed >= 1000) phase_ = Phase::Pause;
    }
    void stop() { phase_ = Phase::Idle; armed_ = false; }
    bool armed() const { return armed_; }
    bool running() const { return phase_ != Phase::Idle; }
    Phase phase() const { return phase_; }
    uint32_t elapsed(uint32_t now) const { return now - started_; }
    uint32_t pulseElapsed(uint32_t now) const {
        return elapsed(now) - (!singlePulse_ && phase_ == Phase::Positive ? 2000 : 0);
    }

private:
    bool armed_ = false;
    bool singlePulse_ = false;
    uint32_t started_ = 0;
    Phase phase_ = Phase::Idle;
};
