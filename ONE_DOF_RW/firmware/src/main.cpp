#include <Arduino.h>
#include <Adafruit_MPU6050.h>
#include <Wire.h>
#include <WiFi.h>
#include <WebServer.h>
#include "control_state.h"
#include "control_page.h"
#include "telemetry.h"
#include "mpu_registers.h"

constexpr uint8_t LED_PIN = 2;
constexpr int SDA_PIN = 21;
constexpr int SCL_PIN = 22;
constexpr uint8_t MOTOR_PWM_PIN = 14;
constexpr uint8_t MOTOR_IN1_PIN = 13;
constexpr uint8_t MOTOR_IN2_PIN = 27;
constexpr uint32_t MOTOR_PWM_HZ = 20000;
constexpr uint8_t MOTOR_PWM_BITS = 8;
constexpr uint8_t MPU_ADDRESS = 0x68;
constexpr int GYRO_FILTER_HZ = 21;
static_assert(static_cast<uint8_t>(MPU6050_BAND_21_HZ) == GYRO_FILTER_REGISTER_VALUE,
              "Gyro filter readback must match the library's 21 Hz setting");
GyroSettings activeGyro = gyroSettings(500); // Accessed only by setup/motor loop.

Adafruit_MPU6050 mpu;
float gyroBiasYDps = 0.0f;
bool pwmReady = false;
unsigned long lastSampleUs = 0;

constexpr char WIFI_SSID[] = "RW1DOF-Control";
constexpr char WIFI_PASSWORD[] = "rw1dof-test";
WebServer server(80);
portMUX_TYPE controlMux = portMUX_INITIALIZER_UNLOCKED;
ControlState control;
float latestRateDps = 0.0f;
int latestDuty = 0;

void stopMotor() {
    if (pwmReady) {
        ledcWrite(MOTOR_PWM_PIN, 0);
    } else {
        digitalWrite(MOTOR_PWM_PIN, LOW);
    }
    portENTER_CRITICAL(&controlMux);
    latestDuty = 0;
    portEXIT_CRITICAL(&controlMux);
}

void haltWithMotorOff(const char *message) {
    portENTER_CRITICAL(&controlMux);
    control.latchFault();
    portEXIT_CRITICAL(&controlMux);
    stopMotor();
    // Require reset and fresh calibration after a sensor/output fault.
    while (true) {
        Serial.print("# FAULT: ");
        Serial.println(message);
        delay(1000);
    }
}

int32_t signedWord(const uint8_t *bytes) {
    const uint16_t raw = (static_cast<uint16_t>(bytes[0]) << 8) | bytes[1];
    return raw >= 0x8000 ? static_cast<int32_t>(raw) - 65536 : raw;
}

bool readGyroYDps(float &rateDps, int32_t *rawCounts = nullptr) {
    // Read the Y gyroscope directly so I2C errors are checked. The Adafruit
    // getEvent() implementation always returns true, even if its read fails.
    uint8_t bytes[2];
    if (!readMpuRegisters(Wire, MPU_ADDRESS, 0x45, bytes, sizeof(bytes))) {
        return false;
    }
    const int32_t raw = signedWord(bytes);
    if (rawCounts != nullptr) *rawCounts = raw;
    rateDps = activeGyro.rateDps(raw);
    return true;
}

void applyMotorDuty(int signedDuty, bool invertDirection) {
    static bool directionHigh = false;
    if (signedDuty == 0) {
        stopMotor();
        return;
    }
    const bool nextDirectionHigh = (signedDuty > 0) != invertDirection;
    if (nextDirectionHigh != directionHigh) {
        // Disable the L298N bridge before changing direction.
        ledcWrite(MOTOR_PWM_PIN, 0);
        delayMicroseconds(100);
        digitalWrite(MOTOR_IN1_PIN, nextDirectionHigh ? HIGH : LOW);
        digitalWrite(MOTOR_IN2_PIN, nextDirectionHigh ? LOW : HIGH);
        directionHigh = nextDirectionHigh;
    }
    ledcWrite(MOTOR_PWM_PIN, static_cast<uint32_t>(abs(signedDuty)));
}

void sendState() {
    portENTER_CRITICAL(&controlMux);
    control.expire(millis());
    const bool enabled = control.enabled;
    const bool manual = control.manual;
    const int direction = control.manualDirection;
    const int throttle = control.throttlePercent;
    const bool fault = control.fault;
    const float kp = control.kp;
    const float ki = control.ki;
    const float integral = control.integralDuty;
    const float rate = latestRateDps;
    const int duty = latestDuty;
    const bool calibrating = control.calibrating;
    const bool inverted = control.invertMotorDirection;
    const bool ramp = control.rampTest;
    const GyroSettings gyro = gyroSettings(control.gyroRangeDps);
    portEXIT_CRITICAL(&controlMux);
    char json[384];
    snprintf(json, sizeof(json),
             "{\"enabled\":%s,\"fault\":%s,\"kp\":%.6g,\"ki\":%.6g,\"integral\":%.4g,\"rate\":%.2f,\"pwm\":%d,"
             "\"calibrating\":%s,\"range\":%d,\"lsb_per_dps\":%.6g,\"filter_hz\":%d,"
             "\"manual\":%s,\"direction\":%d,\"throttle\":%d,\"inverted\":%s,\"ramp\":%s}",
             enabled ? "true" : "false", fault ? "true" : "false", kp, ki, integral, rate, duty,
             calibrating ? "true" : "false", gyro.rangeDps, gyro.lsbPerDps, GYRO_FILTER_HZ,
             manual ? "true" : "false", direction, throttle, inverted ? "true" : "false", ramp ? "true" : "false");
    server.sendHeader("Cache-Control", "no-store");
    server.send(200, "application/json", json);
}

bool validControlRequest() {
    // Custom header prevents ordinary cross-origin forms from changing outputs.
    // Do not add CORS headers: only this hotspot page should issue commands.
    const String header = server.header("X-RW-Control");
    if (!exactText(header.c_str(), header.length(), "1")) {
        server.send(403, "text/plain", "Open the controller page to send commands.");
        return false;
    }
    return true;
}

uint32_t requestOwner() {
    const String text = server.arg("owner");
    if (text.isEmpty() || text.length() > 10) return 0;
    for (size_t i = 0; i < text.length(); ++i) {
        if (text[i] < '0' || text[i] > '9') return 0;
    }
    errno = 0;
    const unsigned long long value = strtoull(text.c_str(), nullptr, 10);
    return errno == 0 && value <= UINT32_MAX ? static_cast<uint32_t>(value) : 0;
}

bool startWifiControl() {
    const IPAddress ip(192, 168, 4, 1);
    if (!WiFi.mode(WIFI_AP) ||
        !WiFi.softAPConfig(ip, ip, IPAddress(255, 255, 255, 0)) ||
        !WiFi.softAP(WIFI_SSID, WIFI_PASSWORD)) {
        return false;
    }
    // Own the onboard LED independently of motor output, calibration and HTTP.
    if (xTaskCreate([](void *) {
        bool on = true;
        for (;;) {
            const bool hotspotActive = (WiFi.getMode() & WIFI_AP) != 0;
            digitalWrite(LED_PIN, hotspotActive && on ? HIGH : LOW);
            on = !on;
            vTaskDelay(pdMS_TO_TICKS(500));
        }
    }, "wifi-led", 2048, nullptr, 1, nullptr) != pdPASS) {
        return false;
    }
    const char *headers[] = {"X-RW-Control"};
    server.collectHeaders(headers, 1);
    server.on("/", HTTP_GET, []() {
        server.sendHeader("Cache-Control", "no-store");
        server.send_P(200, "text/html", CONTROL_PAGE);
    });
    server.on("/status", HTTP_GET, sendState);
    server.on("/motor-direction", HTTP_POST, []() {
        if (!validControlRequest()) return;
        const String text = server.arg("inverted");
        const bool inverted = exactText(text.c_str(), text.length(), "1");
        if (!inverted && !exactText(text.c_str(), text.length(), "0")) {
            server.send(400, "text/plain", "Inverted must be 0 or 1.");
            return;
        }
        portENTER_CRITICAL(&controlMux);
        const bool accepted = control.setMotorDirectionInverted(inverted);
        portEXIT_CRITICAL(&controlMux);
        if (!accepted) {
            server.send(409, "text/plain", "Cannot change direction during calibration or after a fault.");
            return;
        }
        sendState();
    });
    server.on("/control", HTTP_POST, []() {
        if (!validControlRequest()) return;
        const String enabled = server.arg("enabled");
        const bool enableRequest = exactText(enabled.c_str(), enabled.length(), "1");
        if (!enableRequest && !exactText(enabled.c_str(), enabled.length(), "0")) {
            server.send(400, "text/plain", "Enabled must be 0 or 1.");
            return;
        }
        const uint32_t owner = requestOwner();
        portENTER_CRITICAL(&controlMux);
        bool accepted = true;
        if (enableRequest) accepted = control.enable(millis(), owner);
        else control.disable();
        portEXIT_CRITICAL(&controlMux);
        if (!accepted) {
            server.send(409, "text/plain", "Cannot enable: calibrating, fault latched, or invalid page owner. Reset after a fault.");
            return;
        }
        sendState();
    });
    server.on("/kp", HTTP_POST, []() {
        if (!validControlRequest()) return;
        const String text = server.arg("kp");
        ControlState candidate;
        // Parse outside the critical section; only the float assignment is shared.
        if (text.length() > 32 || !candidate.setKp(text.c_str(), text.length())) {
            server.send(400, "text/plain", "Kp must be a finite number from 0 to 20.");
            return;
        }
        portENTER_CRITICAL(&controlMux);
        control.kp = candidate.kp;
        control.resetIntegral();
        portEXIT_CRITICAL(&controlMux);
        sendState();
    });
    server.on("/ki", HTTP_POST, []() {
        if (!validControlRequest()) return;
        const String text = server.arg("ki");
        ControlState candidate;
        if (text.length() > 32 || !candidate.setKi(text.c_str(), text.length())) {
            server.send(400, "text/plain", "Ki must be a finite number from 0 to 20.");
            return;
        }
        portENTER_CRITICAL(&controlMux);
        control.ki = candidate.ki;
        control.resetIntegral();
        portEXIT_CRITICAL(&controlMux);
        sendState();
    });
    server.on("/manual", HTTP_POST, []() {
        if (!validControlRequest()) return;
        const String directionText = server.arg("direction");
        const String throttleText = server.arg("throttle");
        const String action = server.arg("action");
        const bool update = exactText(action.c_str(), action.length(), "update");
        const bool ramp = exactText(action.c_str(), action.length(), "ramp");
        const int direction = parseManualDirection(directionText.c_str(), directionText.length());
        int throttle;
        if ((!update && !ramp && !exactText(action.c_str(), action.length(), "start")) || direction == 0 ||
            !parseThrottlePercent(throttleText.c_str(), throttleText.length(), throttle) || (ramp && throttle == 0)) {
            server.send(400, "text/plain", "Choose left/right and an integer throttle from 0 to 100.");
            return;
        }
        const uint32_t owner = requestOwner();
        portENTER_CRITICAL(&controlMux);
        const bool accepted = update ? control.updateManualThrottle(throttle, millis(), owner)
                                     : ramp ? control.startRamp(direction, throttle, millis(), owner)
                                     : control.setManual(direction, throttle, millis(), owner);
        portEXIT_CRITICAL(&controlMux);
        if (!accepted) {
            server.send(409, "text/plain", "Manual command blocked: calibration/fault, invalid owner, or manual session stopped. Use a direction button to start.");
            return;
        }
        sendState();
    });
    server.on("/heartbeat", HTTP_POST, []() {
        if (!validControlRequest()) return;
        const uint32_t owner = requestOwner();
        portENTER_CRITICAL(&controlMux);
        const bool accepted = control.heartbeat(millis(), owner);
        portEXIT_CRITICAL(&controlMux);
        if (!accepted) {
            server.send(409, "text/plain", "Control disabled or page ownership changed. Enable again.");
            return;
        }
        sendState();
    });
    server.on("/gyro-range", HTTP_POST, []() {
        if (!validControlRequest()) return;
        const String text = server.arg("range");
        int range = 0;
        if (exactText(text.c_str(), text.length(), "250")) range = 250;
        else if (exactText(text.c_str(), text.length(), "500")) range = 500;
        else if (exactText(text.c_str(), text.length(), "1000")) range = 1000;
        else if (exactText(text.c_str(), text.length(), "2000")) range = 2000;
        else {
            server.send(400, "text/plain", "Gyro range must be 250, 500, 1000 or 2000 deg/s.");
            return;
        }
        // HTTP queues configuration only. The motor loop owns all MPU/I2C access.
        portENTER_CRITICAL(&controlMux);
        const bool accepted = control.requestGyroRange(range);
        portEXIT_CRITICAL(&controlMux);
        if (!accepted) {
            server.send(409, "text/plain", "Cannot change range during calibration or after a fault.");
            return;
        }
        sendState();
    });
    // WebServer may wait for a slow HTTP client. Keep that wait off the motor loop.
    if (xTaskCreate([](void *) {
        server.begin();
        for (;;) {
            server.handleClient();
            vTaskDelay(pdMS_TO_TICKS(5));
        }
    }, "wifi-control", 6144, nullptr, 1, nullptr) != pdPASS) {
        return false;
    }
    Serial.println("# ===== WI-FI CONTROL PAGE =====");
    Serial.printf("# Connect to Wi-Fi: %s\n", WIFI_SSID);
    Serial.printf("# Wi-Fi password: %s\n", WIFI_PASSWORD);
    Serial.println("# Open in your browser: http://192.168.4.1");
    Serial.println("# Stay connected if your device reports no Internet.");
    Serial.println("# =============================");
    return true;
}

void configureAndCalibrateGyro(int rangeDps) {
    stopMotor();
    const GyroSettings settings = gyroSettings(rangeDps);
    const auto range = static_cast<mpu6050_gyro_range_t>(settings.registerValue);
    mpu.setGyroRange(range);
    // Read CONFIG and GYRO_CONFIG in one checked transfer. Library enum getters
    // can mask an I2C error into enum 3, which is also a valid +/-2000 range.
    uint8_t config[2];
    if (!readMpuRegisters(Wire, MPU_ADDRESS, 0x1A, config, sizeof(config)) ||
        !settings.matchesRegisters(config[1], config[0])) {
        haltWithMotorOff("MPU6050 range/filter configuration failed. Motor disabled.");
    }
    activeGyro = settings;
    Serial.printf("# Calibrating +/- %d deg/s, %.6g LSB/(deg/s), filter %d Hz. Keep sensor still for 2 seconds.\n",
                  settings.rangeDps, settings.lsbPerDps, GYRO_FILTER_HZ);
    delay(1000); // Let the new range/filter settle, and allow time to hold still.
    float biasSum = 0.0f;
    constexpr int CALIBRATION_SAMPLES = 100;
    for (int i = 0; i < CALIBRATION_SAMPLES; ++i) {
        float rateYDps;
        if (!readGyroYDps(rateYDps)) {
            haltWithMotorOff("MPU6050 calibration read failed. Motor disabled.");
        }
        biasSum += rateYDps;
        delay(10);
    }
    gyroBiasYDps = biasSum / CALIBRATION_SAMPLES;
    portENTER_CRITICAL(&controlMux);
    latestRateDps = 0.0f;
    control.finishGyroCalibration();
    portEXIT_CRITICAL(&controlMux);
    lastSampleUs = micros(); // Calibration delay is intentional, not a sampling fault.
    Serial.printf("# Calibration complete. Y bias %.6g deg/s. Control OFF.\n", gyroBiasYDps);
}

void setup() {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
    pinMode(MOTOR_PWM_PIN, OUTPUT);
    digitalWrite(MOTOR_PWM_PIN, LOW);
    pinMode(MOTOR_IN1_PIN, OUTPUT);
    digitalWrite(MOTOR_IN1_PIN, LOW);
    pinMode(MOTOR_IN2_PIN, OUTPUT);
    digitalWrite(MOTOR_IN2_PIN, HIGH);
    Serial.setTxBufferSize(1024);
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
        Serial.println("# MPU6050 not found. Check power, SDA=21, SCL=22, AD0=GND.");
        delay(1000);
    }

    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    control.requestGyroRange(500);
    configureAndCalibrateGyro(500);
    if (!startWifiControl()) {
        haltWithMotorOff("Wi-Fi setup failed. Motor disabled; reset to retry.");
    }
    lastSampleUs = micros();
    Serial.println("# Ready: control OFF. Open the Wi-Fi page to enable and tune Kp/range.");
    Serial.println(TELEMETRY_CSV_HEADER);
}

void loop() {
    portENTER_CRITICAL(&controlMux);
    const bool calibrating = control.calibrating;
    const int requestedRange = control.requestedGyroRangeDps;
    portEXIT_CRITICAL(&controlMux);
    if (calibrating) {
        configureAndCalibrateGyro(requestedRange);
        return;
    }
    float rateYDps;
    int32_t rawCounts;
    if (!readGyroYDps(rateYDps, &rawCounts)) {
        haltWithMotorOff("MPU6050 read failed. Motor disabled; check wiring and reset.");
    }
    const unsigned long nowUs = micros();
    const float dtSeconds = (nowUs - lastSampleUs) * 1.0e-6f;
    lastSampleUs = nowUs;
    if (dtSeconds > 0.2f) {
        haltWithMotorOff("Sensor sampling stalled. Motor disabled; reset to recalibrate.");
    }
    const float rawRateDps = rateYDps;
    rateYDps -= gyroBiasYDps;
    portENTER_CRITICAL(&controlMux);
    latestRateDps = rateYDps;
    // Sample time after locking: HTTP may have just refreshed the heartbeat.
    const uint32_t timeMs = millis();
    const int motorDuty = control.duty(rateYDps, timeMs);
    const bool invertDirection = control.invertMotorDirection;
    const float kp = control.kp;
    const bool enabled = control.enabled;
    const bool manual = control.manual;
    const int throttle = control.throttlePercent;
    portEXIT_CRITICAL(&controlMux);
    applyMotorDuty(motorDuty, invertDirection);
    portENTER_CRITICAL(&controlMux);
    latestDuty = motorDuty;
    portEXIT_CRITICAL(&controlMux);

    char row[256];
    const TelemetrySample sample{timeMs, rawCounts, rawRateDps, rateYDps, motorDuty,
        kp, enabled, activeGyro.rangeDps, activeGyro.lsbPerDps, GYRO_FILTER_HZ, manual, throttle};
    const int length = formatTelemetryCsv(row, sizeof(row), sample);
    // Skip a row under serial backpressure rather than blocking the motor loop.
    if (length > 0 && length < static_cast<int>(sizeof(row)) &&
        Serial.availableForWrite() >= length) {
        Serial.write(reinterpret_cast<const uint8_t *>(row), static_cast<size_t>(length));
    }
    delay(20);
}
