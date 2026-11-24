#include <Arduino.h>
#include <SimpleFOC.h>
#include <Wire.h>
#include <WebServer.h>
#include <WiFi.h>
#include "Config.h"
#include "MotionTest.h"
#include "WheelControl.h"

namespace {
// Open-loop drive: current ~= volts / 2.3 ohm. 2 V ~ 0.9 A; DRV8313 peak is 2.5 A.
constexpr float kVolts = 2.0f;  // initial driver limit only
float gA = 10.0f;               // l/r pulse acceleration throttle, rad/s^2 (speed ramps up to Max wheel)
// Balance PID (UNTUNED). Output is wheel acceleration (rad/s^2); integrated to a wheel speed.
// kSign: flip to -1 if the wheel pushes the wrong way.
float kSign = 1.0f;  // flipped from the phone page
// Live-adjustable from the phone page.
float gP = 12.0f, gI = 0.0f, gD = 0.4f, gV = 6.0f, gW = 60.0f;  // per deg, per deg*s, per deg/s, V, rad/s
constexpr float kIntMax = 20.0f, kFallDeg = 25.0f;
// AS5600 raw angle for SimpleFOC; reads on the already-started shared Wire bus.
class AS5600Sensor : public Sensor {
public:
    void begin() { Sensor::init(); }
    float getSensorAngle() override {
        Wire.beginTransmission(0x36);
        Wire.write(0x0C);
        if (Wire.endTransmission(false) != 0 || Wire.requestFrom(uint8_t{0x36}, size_t{2}, true) != 2) return last;
        const uint8_t hi = Wire.read();
        const uint8_t lo = Wire.read();
        last = static_cast<float>(((hi & 0x0F) << 8) | lo) * (6.2831853f / 4096.0f);
        return last;
    }
private:
    float last = 0;
};
AS5600Sensor wheelSensor;
bool clMode = false, clReady = false;  // closed-loop torque mode / alignment done
constexpr float kCl = 0.025f;          // volts per unit of the P/I/D sum (Kp 6 -> 0.15 V/deg)
float gB = 0.05f;                      // back-EMF constant, V per rad/s (~190 rpm/V estimated from logs)
float gK = 0.02f;                      // wheel-speed damping, V per rad/s
float clCmd = 0;
float velOffset = 0;                  // wheel speed treated as "zero" (set by Reset to zero)
float rateLp = 0;                     // filtered gyro rate
float clVelSign = 1;                  // +1 if positive q-voltage gives positive measured speed                       // last q-axis voltage command
bool balancing_ = false;
float setpoint = 0, tilt = 0, integ = 0, wheelTarget = 0;
bool tiltOk = false;
uint32_t tiltTime = 0;
// Physical EN is controlled separately so library initialization cannot enable it.
BLDCDriver3PWM driver(Config::driverIn1, Config::driverIn2, Config::driverIn3);
BLDCMotor motor(7);
MotionTest sequence;
MotionTest::Phase previousPhase = MotionTest::Phase::Idle;
bool initialized = false;
bool encoderHealthy = false;
bool encoderPresent = false;
bool manualPulse = false;
bool haveAngle = false;
bool outputEnabled = false;
uint16_t angleRaw = 0;
uint8_t magnetStatus = 0;
int32_t positionCounts = 0;
int32_t pulseStartCounts = 0;
uint32_t encoderTime = 0;
uint32_t pollTime = 0;
uint32_t loopTime = 0;
uint32_t armedTime = 0;

void disableOutput() {
    // Remove physical enable before library calls.
    digitalWrite(Config::driverEnable, LOW);
    outputEnabled = false;
    balancing_ = false;
    if (initialized) motor.disable();
}

void stop(const char* reason) {
    disableOutput();
    sequence.stop();
    previousPhase = MotionTest::Phase::Idle;
    Serial.printf("# STOP: %s; EN=0, disarmed\n", reason);
}

bool readEncoder() {
    uint8_t bytes[3];
    Wire.beginTransmission(0x36);
    Wire.write(0x0B);  // STATUS, RAW_ANGLE high, RAW_ANGLE low. No config writes.
    if (Wire.endTransmission(false) != 0 || Wire.requestFrom(uint8_t{0x36}, size_t{3}, true) != 3) {
        encoderHealthy = false;
        encoderPresent = false;
        haveAngle = false;
        return false;
    }
    for (uint8_t& value : bytes) value = Wire.read();
    magnetStatus = bytes[0];
    const uint16_t next = ((bytes[1] & 0x0F) << 8) | bytes[2];
    encoderHealthy = encoderMagnetHealthy(magnetStatus);
    encoderPresent = encoderAllowsManualPulse(magnetStatus);
    if (encoderPresent) {
        if (haveAngle) positionCounts += encoderDeltaCounts(next, angleRaw);
        angleRaw = next;
        encoderTime = millis();
    }
    haveAngle = encoderPresent;
    return encoderPresent;
}

}  // namespace

namespace WheelControl {
bool handle(char command);
}

namespace {
WebServer web(80);
const char page[] = R"HTML(<meta name=viewport content='width=device-width'>
<style>body{font-family:sans-serif;margin:8px}button{width:100%;height:9vh;font-size:1.5em;margin:.4vh 0}
.r{display:flex;gap:6px}input{width:100%}canvas{width:100%;height:32vh;background:#111}label{display:block;margin-top:6px}</style>
<div class=r><button onclick="fetch('/l')">&larr; LEFT</button><button onclick="fetch('/r')">RIGHT &rarr;</button></div>
<button onclick="fetch('/x')" style="background:#e55">STOP</button>
<button id=b onclick="fetch('/b').then(poll)">Balance: OFF</button>
<button onclick="fetch('/z')">Reset to zero (set balance point)</button>
<button id=f onclick="flip()">Direction: normal</button>
<button onclick="exp()">Export to log</button>
<button onclick="E.length=0;W.length=0">Clear graph</button>
<button id=m onclick="fetch('/m').then(poll)">Mode: open-loop</button>
<div id=g></div>
<canvas id=c width=700 height=300></canvas>
<div id=t></div>
<script>
const K=[['p','Kp (accel per deg)',0,100,0.5],['i','Ki',0,20,0.1],['d','Kd (per deg/s)',0,10,0.05],['v','Volts (power)',0.5,6,0.1],['w','Max wheel rad/s',5,120,1],['k','Wheel-speed damping (closed-loop, V per rad/s)',0,0.3,0.005],['b','Back-EMF feed-forward (V per rad/s)',0,0.2,0.005],['a','LEFT/RIGHT acceleration throttle (rad/s&sup2;)',1,200,1]];
const g=document.getElementById('g');
let sg=1;function flip(){sg=-sg;fetch('/g?s='+sg);f.textContent='Direction: '+(sg<0?'FLIPPED':'normal')}
fetch('/g').then(r=>r.text()).then(t=>{const v=t.split(',');sg=+v[8]||1;f.textContent='Direction: '+(sg<0?'FLIPPED':'normal');K.forEach((k,n)=>{
 g.insertAdjacentHTML('beforeend',`<label>${k[1]}: <b id=o${k[0]}>${v[n]}</b><input type=range id=s${k[0]} min=${k[2]} max=${k[3]} step=${k[4]} value=${v[n]}></label>`);});
 K.forEach(k=>{const s=document.getElementById('s'+k[0]);
  s.oninput=()=>document.getElementById('o'+k[0]).textContent=s.value;
  s.onchange=()=>fetch('/g?'+k[0]+'='+s.value);});});
function exp(){const q=K.map(k=>k[0]+'='+document.getElementById('s'+k[0]).value).join(' ')+' s='+sg;
 fetch('/log',{method:'POST',body:'gains '+q+'\nerr_deg '+E.join(' ')+'\nwheel_rads '+W.join(' ')})}
function poll(){fetch('/s').then(r=>r.text()).then(t=>{const a=t.split('|');b.textContent='Balance: '+a[0];m.textContent='Mode: '+(a[1]=='CL'?'closed-loop torque (encoder)':'open-loop')})}
const E=[],W=[],N=200,cx=c.getContext('2d');
function line(a,col){const m=Math.max(1,...a.map(Math.abs));cx.strokeStyle=col;cx.beginPath();
 a.forEach((y,i)=>{const X=i*c.width/N,Y=c.height/2-y/m*c.height/2*.9;i?cx.lineTo(X,Y):cx.moveTo(X,Y)});cx.stroke();return m}
setInterval(()=>{fetch('/d').then(r=>r.text()).then(t=>{const v=t.split(',');E.push(+v[0]);W.push(+v[1]);
 if(E.length>N){E.shift();W.shift()}
 cx.clearRect(0,0,c.width,c.height);cx.strokeStyle='#444';cx.beginPath();cx.moveTo(0,c.height/2);cx.lineTo(c.width,c.height/2);cx.stroke();
 const a=line(E,'#4f4'),w=line(W,'#fa0');
 document.getElementById('t').innerHTML=`<span style=color:#4a4>error ${(+v[0]).toFixed(2)} deg (scale &plusmn;${a.toFixed(1)})</span> | <span style=color:#c80>wheel ${(+v[1]).toFixed(1)} rad/s (scale &plusmn;${w.toFixed(1)})</span>`;
 poll()}).catch(()=>{})},100);
</script>)HTML";

void webCommand(char c) {
    WheelControl::handle(c);  // Same guarded 1 s pulse as serial l/r/x.
    web.send(200, "text/plain", "ok");
}

void webBegin() {
    // WPA2 requires >= 8 chars, so "123" is not accepted by the ESP32 AP.
    if (WiFi.softAP("Wheel", "12345678")) {
        pinMode(2, OUTPUT);  // Onboard blue LED on DevKit V1: on once the AP is up.
        digitalWrite(2, HIGH);
    }
    web.on("/", [] { web.send(200, "text/html", page); });
    web.on("/l", [] { webCommand('l'); });
    web.on("/r", [] { webCommand('r'); });
    web.on("/x", [] { webCommand('x'); });
    web.on("/b", [] { WheelControl::toggleBalance(); web.send(200, "text/plain", "ok"); });
    web.on("/m", [] { WheelControl::toggleClosedLoop(); web.send(200, "text/plain", "ok"); });  // blocks ~3 s while aligning
    web.on("/z", [] { WheelControl::zeroBalance(); web.send(200, "text/plain", "ok"); });
    web.on("/g", [] {
        for (const char k : {'p', 'i', 'd', 'v', 'w', 'k', 'b', 'a', 's'})
            if (web.hasArg(String(k))) WheelControl::setGain(k, web.arg(String(k)).toFloat());
        String out;
        for (const char k : {'p', 'i', 'd', 'v', 'w', 'k', 'b', 'a', 's'}) { if (out.length()) out += ','; out += String(WheelControl::gainValue(k), 2); }
        web.send(200, "text/plain", out);
    });
    web.on("/log", HTTP_POST, [] {
        Serial.print("# LOG ");
        Serial.println(web.arg("plain"));
        Serial.println("# LOG END");
        web.send(200, "text/plain", "ok");
    });
    web.on("/d", [] {
        web.send(200, "text/plain", String(WheelControl::balanceError(), 2) + "," + String(WheelControl::balanceWheel(), 2));
    });
    web.on("/s", [] { web.send(200, "text/plain", String(WheelControl::balancing() ? "ON" : "OFF") + (WheelControl::closedLoop() ? "|CL" : "|OL")); });
    web.begin();
    Serial.printf("# WIFI: SSID Wheel, password 12345678, open http://%s\n", WiFi.softAPIP().toString().c_str());
}
}  // namespace

namespace WheelControl {
void printHelp() {
    Serial.println("# MOTOR_TEST: 12V supply, 7 pole pairs, 0.5V q-axis maximum, 1rad/s command.");
    Serial.println("# a: arm for 5s; t: negative 1s / coast 1s / positive 1s / disable; x: stop; h: help");
    Serial.println("# l + Enter: one left pulse; r + Enter: one right pulse. Each stops after 1s.");
    Serial.println("# l/r use open loop; weak/strong magnet flags warn but do not block these pulses.");
    Serial.println("# Open loop: actual direction/speed must be verified from encoder; not balance control.");
}

void begin() {
    digitalWrite(Config::driverEnable, LOW);
    pinMode(Config::driverEnable, OUTPUT);
    Wire.setTimeOut(5);
    driver.voltage_power_supply = 12;
    driver.voltage_limit = 12;
    driver.pwm_frequency = 25000;
    if (!driver.init()) {
        Serial.println("# FATAL: PWM init failed; motor remains disabled.");
        return;
    }
    motor.linkDriver(&driver);
    motor.controller = MotionControlType::velocity_openloop;
    motor.voltage_limit = kVolts;
    motor.velocity_limit = 120.0f;  // hard ceiling; gW sets the working limit
    if (!motor.init()) {
        Serial.println("# FATAL: motor init failed; physical EN remains LOW.");
        return;
    }
    initialized = true;
    disableOutput();
    readEncoder();
    while (Serial.available()) Serial.read();
    printHelp();
    Serial.println("# READY: EN=0, disarmed. l/r require encoder communication and detected magnet.");
    loopTime = millis();
    webBegin();
}

bool busy() { return sequence.running(); }
bool balancing() { return balancing_; }
bool closedLoop() { return clMode; }

void balanceUpdate(float angleDeg, float rateDps, float dt, bool ok) {
    tilt = angleDeg;
    tiltOk = ok;
    tiltTime = millis();
    if (!balancing_) return;
    rateLp += 0.2f * (rateDps - rateLp);  // motor vibration swamps raw gyro; filter the D term
    float err = tilt - setpoint;
    if (fabsf(err) < 0.2f) err = 0;       // deadband: don't chase sensor noise at rest
    if (!ok) { stop("IMU lost"); return; }
    const bool fallen = fabsf(err) > kFallDeg;  // stay enabled; just stop pushing until it is back in range
    static uint8_t n = 0;
    if (++n >= 4) {  // ~50 Hz: ms, tilt error, filtered gyro, wheel target
        n = 0;
        Serial.printf("# B,%lu,%.2f,%.1f,%.2f,%.2f\n", static_cast<unsigned long>(millis()), tilt - setpoint, rateLp, wheelTarget, clCmd);
    }
    if (fallen) integ = 0; else integ = constrain(integ + err * dt, -kIntMax, kIntMax);
    if (clMode) {
        const float raw = motor.shaft_velocity * clVelSign;  // wheel speed in the torque-command direction, rad/s
        const float vel = raw - velOffset;
        if (fallen || fabsf(raw) > gW * 1.25f) {  // out of range or overspeed: brake the wheel, keep the controller on
            clCmd = constrain(-0.1f * vel, -gV, gV);
            wheelTarget = vel;
            return;
        }
        // Voltage-mode "torque" is (V - back-EMF)/R, so add the back-EMF back in: the P/D term is then a
        // true torque request that does not fade as the wheel speeds up.
        float t = kSign * kCl * (gP * err + gI * integ + gD * rateLp) - gK * vel;
        if ((vel > gW && t > 0) || (vel < -gW && t < 0)) t = 0;  // wheel speed limit
        if (fabsf(t) > 0.03f) t += copysignf(0.05f, t);           // small friction kick
        t = constrain(t, -3.5f, 3.5f);                            // torque term cap (~1.5 A)
        const float u = t + gB * raw;
        clCmd = constrain(u, -gV, gV);
        wheelTarget = vel;
        return;
    }
    if (fallen) { wheelTarget -= wheelTarget * 5.0f * dt; return; }
    wheelTarget += kSign * (gP * err + gI * integ + gD * rateLp) * dt;
    wheelTarget -= wheelTarget * 2.0f * dt;  // speed damping (0.5 s): a steady small error settles at Kp*err/2 rad/s instead of ramping to the limit
    wheelTarget = constrain(wheelTarget, -gW, gW);
}

// Switch open-loop <-> encoder closed-loop torque. First use aligns the rotor (it moves ~1/7 turn).
bool toggleClosedLoop() {
    if (balancing_ || sequence.running() || sequence.armed()) return clMode;
    if (clMode) { clMode = false; return false; }
    if (!clReady) {
        if (!initialized || !encoderPresent) { Serial.println("# CL rejected: encoder not reading."); return false; }
        motor.linkSensor(&wheelSensor);
        wheelSensor.begin();
        motor.torque_controller = TorqueControlType::voltage;
        motor.controller = MotionControlType::torque;
        motor.voltage_sensor_align = 2.0f;
        motor.voltage_limit = 2.0f;
        digitalWrite(Config::driverEnable, HIGH);
        // Measure pole pairs slowly (rotor must keep up): per electrical revolution it moves 2*pi/pp.
        wheelSensor.update();
        float prev = wheelSensor.getAngle(), total = 0;
        for (int rev = 0; rev < 3; rev++) {
            for (int i = 0; i < 100; i++) {
                motor.setPhaseVoltage(3.0f, 0, _3PI_2 + _2PI * i / 100.0f);
                for (int k = 0; k < 5; k++) { delay(5); wheelSensor.update(); }
            }
            const float a = wheelSensor.getAngle();
            Serial.printf("# CL rev %d moved %.3f rad (pp %.2f)\n", rev, a - prev, _2PI / fabsf(a - prev + 1e-6f));
            if (rev > 0) total += a - prev;  // rev 0 includes initial settling
            prev = a;
        }
        const float ppEst = fabsf(total) > 0.05f ? 2 * _2PI / fabsf(total) : 0;
        Serial.printf("# CL pole pairs: configured %u, measured %.2f\n", motor.pole_pairs, ppEst);
        if (ppEst >= 2 && ppEst <= 20 && fabsf(ppEst - roundf(ppEst)) < 0.2f) motor.pole_pairs = static_cast<int>(roundf(ppEst));
        const int ok = motor.initFOC();
        // initFOC picked sensor_direction so +Uq gives +speed (measured: sign was +1 on every run),
        // so the old +1.2 V torque test and brake pulse are gone: that impulse tipped the cube over.
        float velSign = 1;
        clVelSign = velSign;
        digitalWrite(Config::driverEnable, LOW);
        motor.disable();
        Serial.printf("# CL align %s, sensor_dir=%d, zero_elec=%.2f, pp_check=%d%s", ok ? "OK" : "FAILED",
                      static_cast<int>(motor.sensor_direction), motor.zero_electric_angle, motor.pp_check_result, "\n");
        clReady = ok == 1;
        if (!clReady) return false;
    }
    clMode = true;
    return true;
}

bool toggleBalance() {
    if (balancing_) { stop("balance off"); return false; }
    if (!initialized || !encoderPresent || sequence.running() || sequence.armed() ||
        !tiltOk || millis() - tiltTime > 50) {
        Serial.println("# BALANCE rejected: need IMU + encoder reading and no pulse active.");
        return false;
    }
    if (clMode && !clReady) { Serial.println("# BALANCE rejected: closed-loop not calibrated."); return false; }
    integ = 0;
    wheelTarget = 0;
    clCmd = 0;
    velOffset = 0;
    motor.controller = clMode ? MotionControlType::torque : MotionControlType::velocity_openloop;
    manualPulse = true;
    motor.voltage_limit = gV;
    motor.enable();
    digitalWrite(Config::driverEnable, HIGH);
    outputEnabled = true;
    balancing_ = true;
    Serial.printf("# BALANCE on, setpoint %.2f deg\n", setpoint);
    return true;
}

float gainValue(char key) {
    switch (key) { case 'p': return gP; case 'i': return gI; case 's': return kSign; case 'k': return gK; case 'b': return gB; case 'a': return gA; case 'd': return gD; case 'v': return gV; default: return gW; }
}

void setGain(char key, float v) {
    if (!isfinite(v)) return;
    switch (key) {
        case 'p': gP = constrain(v, 0.0f, 100.0f); break;
        case 'i': gI = constrain(v, 0.0f, 20.0f); break;
        case 'd': gD = constrain(v, 0.0f, 10.0f); break;
        case 'v': gV = constrain(v, 0.5f, 6.0f); break;  // ~2.6 A stall at 2.3 ohm; DRV8313 peak 2.5 A, continuous 1.75 A
        case 'w': gW = constrain(v, 5.0f, 120.0f); break;
        case 'k': gK = constrain(v, 0.0f, 0.3f); break;
        case 'b': gB = constrain(v, 0.0f, 0.2f); break;
        case 'a': gA = constrain(v, 1.0f, 200.0f); break;
        case 's': kSign = v < 0 ? -1.0f : 1.0f; break;
    }
}

float balanceError() { return tilt - setpoint; }
float balanceWheel() { return wheelTarget; }

void zeroBalance() {
    if (!tiltOk) return;
    setpoint = tilt;
    integ = 0;
    rateLp = 0;       // clear filter/command state so the new setpoint does not cause a spike
    wheelTarget = 0;
    clCmd = 0;
    velOffset = (clMode && balancing_) ? motor.shaft_velocity * clVelSign : 0;  // current wheel speed becomes the zero reference
    Serial.printf("# BALANCE setpoint zeroed at %.2f deg\n", setpoint);
}
bool enabled() { return outputEnabled; }

void observeEncoder(bool readOk, uint8_t status) {
    if ((sequence.running() || sequence.armed() || balancing_) && !encoderAllowsMotion(readOk, status, manualPulse))
        stop("telemetry observed encoder failure or required magnet status lost");
}

bool handle(char command) {
    if ((sequence.running() || balancing_) && command != 'x') return true;
    const uint32_t now = millis();
    switch (command) {
        case 'x': stop("serial stop"); return true;
        case 'l':
        case 'r':
            if (initialized && encoderPresent && now - encoderTime <= 50 &&
                sequence.startPulse(now, command == 'r')) {
                manualPulse = true;
                Serial.println(encoderHealthy ? "# Manual one-second pulse accepted."
                                              : "# Manual open-loop pulse; magnet field WARNING, angle unverified.");
            } else Serial.println("# Pulse rejected: check driver readiness, encoder read and magnet detection.");
            return true;
        case 'a':
            if (initialized && encoderHealthy && now - encoderTime <= 50 && sequence.arm()) {
                manualPulse = false;
                armedTime = now;
                Serial.println("# ARMED: send t within 5 seconds; EN still 0.");
            } else Serial.println("# ARM rejected: automatic sequence requires healthy encoder.");
            return true;
        case 't':
            if (initialized && encoderHealthy && now - encoderTime <= 50 && sequence.start(now)) {
                manualPulse = false;
                Serial.println("# TEST accepted: one sequence only.");
            } else Serial.println("# TEST rejected: arm first; encoder must be healthy.");
            return true;
        default: return false;
    }
}

void tick() {
    web.handleClient();
    uint32_t now = millis();
    if (sequence.running() && now - loopTime > 50) stop("control loop delayed >50ms");
    loopTime = now;
    if (initialized && now - pollTime >= 10) {
        pollTime = now;
        readEncoder();
        now = millis();  // Health timestamp may advance during the I2C transaction.
    }
    if (balancing_ && (!encoderPresent || now - encoderTime > 50 || now - tiltTime > 50))
        stop("balance: encoder or IMU data stale");
    if ((sequence.running() || sequence.armed()) &&
        (!(manualPulse ? encoderPresent : encoderHealthy) || now - encoderTime > 50))
        stop("encoder unavailable or required magnet status lost");
    if (sequence.armed() && now - armedTime >= 5000) stop("arming expired");
    sequence.update(now);
    const auto phase = sequence.phase();
    if (phase != previousPhase) {
        if (previousPhase == MotionTest::Phase::Negative || previousPhase == MotionTest::Phase::Positive) {
            disableOutput();
            Serial.printf("# PULSE %s measured_delta_deg=%.2f\n",
                          previousPhase == MotionTest::Phase::Negative ? "negative" : "positive",
                          (positionCounts - pulseStartCounts) * (360.0f / 4096));
        }
        if (phase == MotionTest::Phase::Negative || phase == MotionTest::Phase::Positive) {
            pulseStartCounts = positionCounts;
            motor.controller = MotionControlType::velocity_openloop;
            motor.voltage_limit = 0;
            motor.enable();  // Physical EN is still LOW here.
            digitalWrite(Config::driverEnable, HIGH);
            outputEnabled = true;
            Serial.println(phase == MotionTest::Phase::Negative ? "# NEGATIVE pulse" : "# POSITIVE pulse");
        } else {
            disableOutput();
            Serial.println(phase == MotionTest::Phase::Idle ? "# COMPLETE: EN=0, disarmed" : "# COAST: EN=0");
        }
        previousPhase = phase;
    }
    if (balancing_) {
        motor.voltage_limit = gV;
        if (clMode) {
            motor.loopFOC();
            motor.move(clCmd);
        } else {
            motor.move(wheelTarget);
            motor.loopFOC();
        }
    } else if (outputEnabled) {
        const uint32_t pulseMs = sequence.pulseElapsed(now);
        const float ramp = min(1.0f, min(pulseMs / 200.0f, (1000 - pulseMs) / 200.0f));
        const float spd = min(gA * pulseMs / 1000.0f, gW);  // open-loop speed ramps at gA
        motor.voltage_limit = gV * ramp;
        motor.move(phase == MotionTest::Phase::Negative ? -spd : spd);
        motor.loopFOC();  // SimpleFOC 2.4 applies PWM separately from move().
    }
}
}  // namespace WheelControl
