#pragma once

#include "motor_command.h"
#include "gyro_settings.h"
#include <cerrno>
#include <cstdint>
#include <cstdlib>
#include <cstring>

inline bool exactText(const char *text, size_t length, const char *expected) {
    return length == std::strlen(expected) && std::memcmp(text, expected, length) == 0;
}

inline int parseManualDirection(const char *text, size_t length) {
    if (exactText(text, length, "left")) return -1;
    if (exactText(text, length, "right")) return 1;
    return 0;
}

inline bool parseThrottlePercent(const char *text, size_t length, int &result) {
    if (length == 0 || length > 3) return false;
    int value = 0;
    for (size_t i = 0; i < length; ++i) {
        if (text[i] < '0' || text[i] > '9') return false;
        value = value * 10 + (text[i] - '0');
    }
    if (value > 100) return false;
    result = value;
    return true;
}

// Hardware-independent state. Callers must lock when sharing between tasks.
struct ControlState {
    static constexpr uint32_t TIMEOUT_MS = 2000;
    static constexpr float MAX_KP = 20.0f;
    static constexpr float MAX_KI = 20.0f;
    bool enabled = false;
    bool manual = false;
    int manualDirection = 0;
    int throttlePercent = 0;
    bool fault = false;
    float kp = MOTOR_PWM_PER_DPS;
    float ki = 0.0f;
    float integralDuty = 0.0f;
    uint32_t lastPiMs = 0;
    bool hasPiTime = false;
    uint32_t lastHeartbeatMs = 0;
    uint32_t owner = 0;
    int gyroRangeDps = 500;
    int requestedGyroRangeDps = 500;
    bool calibrating = false;
    bool invertMotorDirection = true;
    static constexpr uint32_t RAMP_UP_MS = 5000;
    static constexpr uint32_t RAMP_HOLD_MS = 2000;
    bool rampTest = false;
    uint32_t rampStartedMs = 0;

    bool setKp(const char *text) {
        return setKp(text, std::strlen(text));
    }

    bool setKp(const char *text, size_t length) {
        char *end;
        errno = 0;
        const float value = std::strtof(text, &end);
        if (end == text || end != text + length || *end != '\0' || errno == ERANGE ||
            !std::isfinite(value) || value < 0.0f || value > MAX_KP) {
            return false;
        }
        kp = value;
        resetIntegral();
        return true;
    }

    void resetIntegral() {
        integralDuty = 0.0f;
        hasPiTime = false;
    }

    bool setKi(const char *text) { return setKi(text, std::strlen(text)); }

    bool setKi(const char *text, size_t length) {
        char *end;
        errno = 0;
        const float value = std::strtof(text, &end);
        if (end == text || end != text + length || *end != '\0' || errno == ERANGE ||
            !std::isfinite(value) || value < 0.0f || value > MAX_KI) return false;
        ki = value;
        resetIntegral();
        return true;
    }

    bool enable(uint32_t now, uint32_t client) {
        if (fault || calibrating || client == 0) {
            return false;
        }
        disable();
        owner = client;
        lastHeartbeatMs = now;
        enabled = true;
        lastPiMs = now;
        hasPiTime = true;
        return true;
    }

    bool setManual(int direction, int throttle, uint32_t now, uint32_t client) {
        if (fault || calibrating || client == 0 ||
            (direction != -1 && direction != 1) || throttle < 0 || throttle > 100) {
            return false;
        }
        disable();
        manual = true;
        manualDirection = direction;
        throttlePercent = throttle;
        owner = client;
        lastHeartbeatMs = now;
        return true;
    }

    bool active() const { return enabled || manual; }

    bool startRamp(int direction, int throttle, uint32_t now, uint32_t client) {
        if (throttle < 1 || !setManual(direction, throttle, now, client)) return false;
        rampTest = true;
        rampStartedMs = now;
        return true;
    }

    bool updateManualThrottle(int throttle, uint32_t now, uint32_t client) {
        expire(now);
        if (!manual || rampTest || fault || calibrating || client == 0 || client != owner ||
            throttle < 0 || throttle > 100) return false;
        throttlePercent = throttle;
        lastHeartbeatMs = now;
        return true;
    }

    void disable() {
        resetIntegral();
        enabled = false;
        manual = false;
        rampTest = false;
        manualDirection = 0;
        throttlePercent = 0;
        owner = 0;
    }
    void latchFault() { fault = true; disable(); }

    bool setMotorDirectionInverted(bool inverted) {
        if (fault || calibrating) return false;
        disable();
        invertMotorDirection = inverted;
        return true;
    }

    bool requestGyroRange(int rangeDps) {
        if (fault || calibrating || gyroSettings(rangeDps).rangeDps == 0) {
            return false;
        }
        disable();
        requestedGyroRangeDps = rangeDps;
        calibrating = true;
        return true;
    }

    void finishGyroCalibration() {
        gyroRangeDps = requestedGyroRangeDps;
        calibrating = false;
        // Never resume a previous control session after reconfiguration.
        disable();
    }

    void expire(uint32_t now) {
        if (rampTest && static_cast<uint32_t>(now - rampStartedMs) >= RAMP_UP_MS + RAMP_HOLD_MS) {
            disable();
        }
        if (active() && static_cast<uint32_t>(now - lastHeartbeatMs) >= TIMEOUT_MS) {
            disable();
        }
    }

    bool heartbeat(uint32_t now, uint32_t client) {
        expire(now);
        if (!active() || client != owner) {
            return false;
        }
        lastHeartbeatMs = now;
        return true;
    }

    int duty(float rateDps, uint32_t now) {
        expire(now);
        if (fault || calibrating) return 0;
        if (manual) {
            const int target = (throttlePercent * MOTOR_MAX_DUTY + 50) / 100;
            const uint32_t elapsed = now - rampStartedMs;
            const int magnitude = rampTest && elapsed < RAMP_UP_MS
                ? static_cast<int>(target * elapsed / RAMP_UP_MS) : target;
            return manualDirection * magnitude;
        }
        if (!enabled || !std::isfinite(rateDps)) {
            resetIntegral();
            return 0;
        }
        if (ki == 0.0f) {
            resetIntegral();
            return motorDutyForRate(rateDps, kp);
        }
        uint32_t elapsedMs = hasPiTime ? now - lastPiMs : 0;
        lastPiMs = now;
        hasPiTime = true;
        // Never integrate across a sampling interruption. The motor loop also
        // latches a fault for stalls longer than 200 ms.
        if (elapsedMs > 200) {
            integralDuty = 0.0f;
            elapsedMs = 0;
        }
        const float magnitude = std::fmax(0.0f, std::fabs(rateDps) - MOTOR_RATE_DEADBAND_DPS);
        const float error = rateDps < 0.0f ? -magnitude : magnitude;
        const float proportional = kp * error;
        const float delta = ki * error * (elapsedMs * 0.001f);
        const float candidate = std::fmax(-float(MOTOR_MAX_DUTY),
            std::fmin(float(MOTOR_MAX_DUTY), integralDuty + delta));
        const float requested = proportional + candidate;
        // Conditional integration: allow unwinding, but do not accumulate
        // correction that pushes an already saturated output further out.
        if (!((requested > MOTOR_MAX_DUTY && delta > 0) ||
              (requested < -MOTOR_MAX_DUTY && delta < 0))) integralDuty = candidate;
        const float output = std::fmax(-float(MOTOR_MAX_DUTY),
            std::fmin(float(MOTOR_MAX_DUTY), proportional + integralDuty));
        return static_cast<int>(std::lround(output));
    }
};
