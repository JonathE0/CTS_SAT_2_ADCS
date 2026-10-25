#include <Arduino.h>
#include <Adafruit_MPU6050.h>
#include <Wire.h>
#include "motor_command.h"

constexpr uint8_t LED_PIN = 2;
constexpr int SDA_PIN = 23;
constexpr int SCL_PIN = 22;
constexpr uint8_t MOTOR_PWM_PIN = 33;
constexpr uint8_t MOTOR_DIR_PIN = 32;
constexpr uint32_t MOTOR_PWM_HZ = 20000;
constexpr uint8_t MOTOR_PWM_BITS = 8;
constexpr bool INVERT_MOTOR_DIRECTION = false;
constexpr uint8_t MPU_ADDRESS = 0x68;
// MPU6050 +/-500 degrees/second range uses 65.5 LSB per degree/second.
constexpr float GYRO_LSB_PER_DPS = 65.5f;

Adafruit_MPU6050 mpu;
float gyroBiasYDps = 0.0f;
bool pwmReady = false;
unsigned long lastSampleUs = 0;

void stopMotor() {
    if (pwmReady) {
        ledcWrite(MOTOR_PWM_PIN, 0);
    } else {
        digitalWrite(MOTOR_PWM_PIN, LOW);
    }
    digitalWrite(LED_PIN, LOW);
}

void haltWithMotorOff(const char *message) {
    stopMotor();
    // Require reset and fresh calibration after a sensor/output fault.
    while (true) {
        Serial.println(message);
        delay(1000);
    }
}

int32_t signedWord(const uint8_t *bytes) {
    const uint16_t raw = (static_cast<uint16_t>(bytes[0]) << 8) | bytes[1];
    return raw >= 0x8000 ? static_cast<int32_t>(raw) - 65536 : raw;
}

bool readGyroYDps(float &rateDps) {
    // Read the Y gyroscope directly so I2C errors are checked. The Adafruit
    // getEvent() implementation always returns true, even if its read fails.
    Wire.beginTransmission(MPU_ADDRESS);
    Wire.write(0x45); // GYRO_YOUT_H/L
    if (Wire.endTransmission(false) != 0 ||
        Wire.requestFrom(MPU_ADDRESS, static_cast<size_t>(2)) != 2) {
        return false;
    }
    uint8_t bytes[2];
    for (uint8_t &byte : bytes) {
        byte = static_cast<uint8_t>(Wire.read());
    }
    rateDps = signedWord(bytes) / GYRO_LSB_PER_DPS;
    return true;
}

void applyMotorDuty(int signedDuty) {
    static bool directionHigh = false;
    if (signedDuty == 0) {
        stopMotor();
        return;
    }
    const bool nextDirectionHigh = (signedDuty > 0) != INVERT_MOTOR_DIRECTION;
    if (nextDirectionHigh != directionHigh) {
        // Remove PWM for at least one full 20 kHz cycle before switching DIR.
        ledcWrite(MOTOR_PWM_PIN, 0);
        delayMicroseconds(100);
        digitalWrite(MOTOR_DIR_PIN, nextDirectionHigh ? HIGH : LOW);
        directionHigh = nextDirectionHigh;
    }
    ledcWrite(MOTOR_PWM_PIN, static_cast<uint32_t>(abs(signedDuty)));
    digitalWrite(LED_PIN, HIGH);
}

void setup() {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
    pinMode(MOTOR_PWM_PIN, OUTPUT);
    digitalWrite(MOTOR_PWM_PIN, LOW);
    pinMode(MOTOR_DIR_PIN, OUTPUT);
    digitalWrite(MOTOR_DIR_PIN, LOW);
    Serial.begin(115200);
    pwmReady = ledcAttach(MOTOR_PWM_PIN, MOTOR_PWM_HZ, MOTOR_PWM_BITS);
    if (!pwmReady) {
        haltWithMotorOff("PWM setup failed. Motor disabled; reset to retry.");
    }
    stopMotor();
    if (!Wire.begin(SDA_PIN, SCL_PIN)) {
        haltWithMotorOff("I2C setup failed. Motor disabled; reset to retry.");
    }
    Wire.setTimeOut(20);

    // AD0 connected to GND selects address 0x68.
    while (!mpu.begin(MPU_ADDRESS, &Wire)) {
        Serial.println("MPU6050 not found. Check power, SDA=23, SCL=22, AD0=GND.");
        delay(1000);
    }

    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    if (mpu.getGyroRange() != MPU6050_RANGE_500_DEG) {
        haltWithMotorOff("MPU6050 range configuration failed. Motor disabled.");
    }

    Serial.println("Keep the MPU6050 still for 2 seconds to calibrate zero rotation rate...");
    delay(1000);
    constexpr int CALIBRATION_SAMPLES = 100;
    for (int i = 0; i < CALIBRATION_SAMPLES; ++i) {
        float rateYDps;
        if (!readGyroYDps(rateYDps)) {
            haltWithMotorOff("MPU6050 calibration read failed. Motor disabled.");
        }
        gyroBiasYDps += rateYDps;
        delay(10);
    }
    gyroBiasYDps /= CALIBRATION_SAMPLES;
    lastSampleUs = micros();
    Serial.println("Ready: Y rotation rate commands wheel PWM; stopping gives zero PWM.");
}

void loop() {
    float rateYDps;
    if (!readGyroYDps(rateYDps)) {
        haltWithMotorOff("MPU6050 read failed. Motor disabled; check wiring and reset.");
    }
    const unsigned long nowUs = micros();
    const float dtSeconds = (nowUs - lastSampleUs) * 1.0e-6f;
    lastSampleUs = nowUs;
    if (dtSeconds > 0.2f) {
        haltWithMotorOff("Sensor sampling stalled. Motor disabled; reset to recalibrate.");
    }
    rateYDps -= gyroBiasYDps;
    const int motorDuty = motorDutyForRate(rateYDps);
    applyMotorDuty(motorDuty);

    static unsigned long lastPrintMs = 0;
    if (millis() - lastPrintMs >= 200) {
        lastPrintMs = millis();
        Serial.printf("Y rate: %.1f deg/s | PWM: %d / 255\n", rateYDps, motorDuty);
    }
    delay(20);
}
