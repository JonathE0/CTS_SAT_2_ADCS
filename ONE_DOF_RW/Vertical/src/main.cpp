#include <Arduino.h>
#include <Wire.h>

#include "Config.h"
#include "EncoderReading.h"
#include "SensorMath.h"
#ifdef ENABLE_WHEEL_COMMANDS
#include "MotionTest.h"
#include "WheelControl.h"
#endif

namespace {
#ifdef ENABLE_WHEEL_COMMANDS
MotorCommandParser commandParser;

void serviceWheel() {
    const bool wasBusy = WheelControl::busy();
    WheelControl::tick();
    if (wasBusy && !WheelControl::busy()) {
        // Input queued before completion cannot become a new motion command afterwards.
        const int queued = Serial.available();
        for (int i = 0; i < queued; ++i) commandParser.feed(static_cast<char>(Serial.read()), true);
    }
}
#endif
struct Sample {
    float ax, ay, az;
    float gx, gy, gz;
};

uint8_t imuAddress = 0;
bool imuReady = false;
bool busReady = false;
bool calibrated = false;
float gyroBias[3] = {};
uint32_t lastSample = 0;
uint32_t lastTelemetry = 0;

bool readRegisters(uint8_t address, uint8_t reg, uint8_t* bytes, size_t count) {
    if (!busReady) return false;
    Wire.beginTransmission(address);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) return false;
    if (Wire.requestFrom(address, count, true) != count) return false;
    for (size_t i = 0; i < count; ++i) bytes[i] = Wire.read();
    return true;
}

bool writeRegister(uint8_t reg, uint8_t value) {
    Wire.beginTransmission(imuAddress);
    Wire.write(reg);
    Wire.write(value);
    return Wire.endTransmission() == 0;
}

void printHeader() {
    Serial.println("# tilt is accelerometer-only, in the sensor frame; not a balance estimate");
    Serial.print("ms,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,roll_deg,pitch_deg,gyro_calibrated,encoder_raw,encoder_deg,encoder_status,magnet_detected,magnet_weak,magnet_strong,encoder_ok,imu_ok");
#ifdef ENABLE_WHEEL_COMMANDS
    Serial.print(",motor_enabled");
#endif
    Serial.println();
}

void help() {
#ifdef ENABLE_WHEEL_COMMANDS
    Serial.println("# SENSOR + MANUAL WHEEL: outputs disabled until an explicit motion command.");
    WheelControl::printHelp();
#else
    Serial.println("# SENSOR-ONLY: motor EN held LOW; no motor commands. r: alias for i.");
#endif
    Serial.println("# h: help; s: I2C scan; i: reinitialize IMU; c: stationary gyro calibration");
    Serial.println("# AS5600 raw angle is shown even with a magnet warning. encoder_ok=I2C read success.");
    Serial.println("# Healthy magnet: detected=1, weak=0, strong=0. nan means unavailable, not zero.");
}

void scanBus() {
    Serial.println("# I2C scan: SDA=33, SCL=32, 100 kHz");
    unsigned found = 0;
    for (uint8_t address = 0x08; address <= 0x77; ++address) {
        Wire.beginTransmission(address);
        const uint8_t status = Wire.endTransmission();
        if (status == 0) {
            Serial.printf("# ACK at 0x%02X%s\n", address,
                          address == 0x36 ? " (AS5600 encoder from identified kit)" : "");
            ++found;
        } else if (status != 2) {
            Serial.printf("# Bus error %u at 0x%02X; check wiring/pull-ups\n", status, address);
            break;
        }
    }
    Serial.printf("# %u device(s) acknowledged\n", found);
}

void initializeImu() {
    imuReady = false;
    calibrated = false;
    for (float& bias : gyroBias) bias = 0;
    imuAddress = 0;
    for (uint8_t address : {uint8_t{0x68}, uint8_t{0x69}}) {
        uint8_t identity = 0;
        if (readRegisters(address, 0x75, &identity, 1)) {
            Serial.printf("# IMU candidate 0x%02X WHO_AM_I=0x%02X\n", address, identity);
            if (identity == 0x68) {
                imuAddress = address;
                break;
            }
        }
    }
    if (!imuAddress) {
        Serial.println("# MPU6050 not identified at 0x68/0x69. Check wiring, then send i.");
        return;
    }
    if (!writeRegister(0x6B, 0x01)) {  // Wake, use X gyro PLL.
        Serial.println("# IMU wake failed. Check wiring, then send i.");
        return;
    }
    delay(100);
    // 44 Hz gyro DLPF, 100 Hz output, +/-250 deg/s, +/-2 g.
    imuReady = writeRegister(0x1A, 0x03) && writeRegister(0x19, 0x09) &&
               writeRegister(0x1B, 0x00) && writeRegister(0x1C, 0x00);
    Serial.println(imuReady ? "# MPU6050 ready; gyro is uncalibrated (send c while stationary)."
                            : "# IMU configuration failed. Check wiring, then send i.");
    printHeader();
}

bool readSample(Sample& sample) {
    uint8_t bytes[14];
    // One retry rides through a transient NACK (motor noise) before declaring the IMU lost.
    if (!readRegisters(imuAddress, 0x3B, bytes, sizeof(bytes)) &&
        !readRegisters(imuAddress, 0x3B, bytes, sizeof(bytes))) {
        imuReady = false;
        calibrated = false;
        Serial.println("# IMU read failed; IMU columns become nan, calibration invalidated. Encoder continues. Send i.");
        return false;
    }
    sample.ax = decodeSigned16(bytes[0], bytes[1]) / 16384.0f;
    sample.ay = decodeSigned16(bytes[2], bytes[3]) / 16384.0f;
    sample.az = decodeSigned16(bytes[4], bytes[5]) / 16384.0f;
    sample.gx = decodeSigned16(bytes[8], bytes[9]) / 131.0f;
    sample.gy = decodeSigned16(bytes[10], bytes[11]) / 131.0f;
    sample.gz = decodeSigned16(bytes[12], bytes[13]) / 131.0f;
    return true;
}

void calibrateGyro() {
    calibrated = false;
    for (float& bias : gyroBias) bias = 0;
    if (!imuReady) {
        Serial.println("# Initialize the IMU with i before calibration.");
        return;
    }
    Serial.println("# Hold the assembly stationary on a support; sampling starts in 1 second.");
    delay(1000);
    GyroCalibration calibration;
    for (unsigned i = 0; i < GyroCalibration::sampleCount; ++i) {
        Sample sample;
        if (!readSample(sample)) return;
        calibration.add(sample.ax, sample.ay, sample.az, sample.gx, sample.gy, sample.gz);
        delay(Config::samplePeriodMs);
    }
    if (calibration.valid()) {
        for (size_t axis = 0; axis < 3; ++axis) gyroBias[axis] = calibration.bias(axis);
        calibrated = true;
        Serial.printf("# Gyro bias (deg/s): %.4f, %.4f, %.4f\n",
                      gyroBias[0], gyroBias[1], gyroBias[2]);
    } else {
        Serial.println("# Calibration rejected (motion or abnormal readings); secure assembly and retry c.");
    }
    printHeader();
}
}  // namespace

void setup() {
    digitalWrite(Config::driverEnable, LOW);
    pinMode(Config::driverEnable, OUTPUT);
    Serial.begin(Config::serialBaud);
    delay(1000);
    help();
    busReady = Wire.begin(Config::sda, Config::scl, Config::i2cHz);
    if (!busReady) {
        Serial.println("# I2C initialization failed; reset after checking wiring.");
        return;
    }
    Wire.setTimeOut(Config::i2cTimeoutMs);
    scanBus();
    initializeImu();
#ifdef ENABLE_WHEEL_COMMANDS
    WheelControl::begin();
    printHeader();
#endif
    if (!imuReady) printHeader();
}

void loop() {
#ifdef ENABLE_WHEEL_COMMANDS
    serviceWheel();
#endif
    for (unsigned serialCount = 0; serialCount < 64 && Serial.available(); ++serialCount) {
        char command = static_cast<char>(Serial.read());
#ifdef ENABLE_WHEEL_COMMANDS
        command = commandParser.feed(command, WheelControl::busy());
        if (WheelControl::busy() && command != 'x') command = 0;
        if (WheelControl::handle(command)) command = 0;
#endif
        switch (command) {
            case 'h': help(); printHeader(); break;
            case 's': scanBus(); printHeader(); break;
#ifndef ENABLE_WHEEL_COMMANDS
            case 'r':
#endif
            case 'i': initializeImu(); break;
            case 'c': calibrateGyro(); break;
            default: break;
        }
    }
    const uint32_t now = millis();
#ifdef ENABLE_WHEEL_COMMANDS
    static uint32_t lastRetry = 0;
    if (!imuReady && busReady && now - lastRetry > 1000) {  // auto-recover instead of waiting for 'i'
        lastRetry = now;
        initializeImu();
    }
#endif
    if (now - lastSample >= Config::samplePeriodMs) {
        lastSample = now;
        Sample sample{NAN, NAN, NAN, NAN, NAN, NAN};
        const bool imuOk = imuReady && readSample(sample);
#ifdef ENABLE_WHEEL_COMMANDS
        {
            // Complementary filter on tilt about sensor Z (gravity lies in X-Y as mounted; gyro gz).
            static float angle = 0;
            static bool angleInit = false;
            static uint32_t prev = 0;
            const float dt = (now - prev) * 1e-3f;
            prev = now;
            if (imuOk) {
                const float rate = sample.gz - gyroBias[2];
                const float roll = std::atan2(sample.ax, sample.ay) * 57.2957795f;  // tilt in the X-Y plane (Z horizontal)
                angle = (!angleInit || dt > 0.1f) ? roll : 0.98f * (angle + rate * dt) + 0.02f * roll;
                angleInit = true;
                WheelControl::balanceUpdate(angle, rate, dt, true);
            } else {
                angleInit = false;
                WheelControl::balanceUpdate(0, 0, dt, false);
            }
        }
#endif
        if (now - lastTelemetry >= Config::telemetryPeriodMs) {
            lastTelemetry = now;
            uint8_t encoderBytes[3];
            const bool encoderOk = readRegisters(0x36, 0x0B, encoderBytes, sizeof(encoderBytes));
#ifdef ENABLE_WHEEL_COMMANDS
            WheelControl::observeEncoder(encoderOk, encoderOk ? encoderBytes[0] : 0);
#endif
            Serial.printf("%lu,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.2f,%.2f,%u,",
                          static_cast<unsigned long>(now), sample.ax, sample.ay, sample.az,
                          sample.gx - gyroBias[0], sample.gy - gyroBias[1], sample.gz - gyroBias[2],
                          rollDegrees(sample.ax, sample.ay, sample.az),
                          pitchDegrees(sample.ax, sample.ay, sample.az), calibrated ? 1u : 0u);
            if (encoderOk) {
                const auto encoder = decodeEncoderReading(encoderBytes[0], encoderBytes[1], encoderBytes[2]);
                Serial.printf("%u,%.2f,0x%02X,%u,%u,%u,1,%u", encoder.raw, encoder.angleDegrees(),
                              encoder.status, encoder.detected() ? 1u : 0u, encoder.weak() ? 1u : 0u,
                              encoder.strong() ? 1u : 0u, imuOk ? 1u : 0u);
            } else {
                Serial.printf("nan,nan,nan,0,0,0,0,%u", imuOk ? 1u : 0u);
            }
#ifdef ENABLE_WHEEL_COMMANDS
            Serial.printf(",%u", WheelControl::enabled() ? 1u : 0u);
#endif
            Serial.println();
        }
    }
#ifdef ENABLE_WHEEL_COMMANDS
    serviceWheel();
#endif
    delay(1);
}
