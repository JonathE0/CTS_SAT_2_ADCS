#include "control_state.h"
#include "gyro_settings.h"
#include "telemetry.h"
#include "mpu_registers.h"
#include <cassert>
#include <cmath>
#include <cstring>

struct RegisterBus {
    int endStatus = 0;
    size_t received = 2;
    int nextRead = 0;
    uint8_t values[2] = {0x04, 0x18}; // DLPF_CFG=4: 21 Hz; FS_SEL=3: +/-2000 deg/s.
    bool missingByte = false;
    void beginTransmission(uint8_t address) { assert(address == 0x68); }
    size_t write(uint8_t reg) { assert(reg == 0x1A); return 1; }
    int endTransmission(bool stop) { assert(!stop); return endStatus; }
    size_t requestFrom(uint8_t address, size_t length) {
        assert(address == 0x68 && length == 2);
        return received;
    }
    int read() { return missingByte ? -1 : values[nextRead++]; }
};

int main() {
    // A failed read must not turn into masked enum 3 (+/-2000).
    uint8_t registers[2];
    RegisterBus ok;
    assert(readMpuRegisters(ok, 0x68, 0x1A, registers, 2));
    assert(gyroSettings(2000).matchesRegisters(registers[1], registers[0]));
    assert(!gyroSettings(500).matchesRegisters(registers[1], registers[0]));
    assert(!gyroSettings(2000).matchesRegisters(0x18, 0x03)); // 3 means 44 Hz, not 21 Hz.
    assert(gyroSettings(500).matchesRegisters(0x08, 0x04)); // Startup configuration.
    RegisterBus nack;
    nack.endStatus = 2;
    assert(!readMpuRegisters(nack, 0x68, 0x1A, registers, 2));
    RegisterBus shortRead;
    shortRead.received = 1;
    assert(!readMpuRegisters(shortRead, 0x68, 0x1A, registers, 2));
    RegisterBus failedRead;
    failedRead.missingByte = true;
    assert(!readMpuRegisters(failedRead, 0x68, 0x1A, registers, 2));
    const int ranges[] = {250, 500, 1000, 2000};
    const float scales[] = {131.0f, 65.5f, 32.8f, 16.4f};
    for (int i = 0; i < 4; ++i) {
        const GyroSettings s = gyroSettings(ranges[i]);
        assert(s.rangeDps == ranges[i]);
        assert(s.registerValue == i);
        assert(s.lsbPerDps == scales[i]);
        assert(std::fabs(s.rateDps(1640) - 1640.0f / scales[i]) < 0.0001f);
        assert(std::fabs(s.rateDps(-1640) + 1640.0f / scales[i]) < 0.0001f);
    }
    assert(gyroSettings(0).rangeDps == 0);
    assert(gyroSettings(750).rangeDps == 0);
    ControlState state;
    assert(state.gyroRangeDps == 500 && !state.calibrating);
    assert(state.enable(0, 42));
    assert(!state.requestGyroRange(750));
    assert(state.enabled); // Invalid input must not change control state.
    assert(state.requestGyroRange(250));
    assert(!state.enabled && state.calibrating);
    assert(state.requestedGyroRangeDps == 250);
    assert(state.gyroRangeDps == 500); // Active range changes only after calibration.
    assert(!state.enable(1, 42));
    assert(!state.requestGyroRange(1000));
    assert(state.duty(100.0f, 1) == 0);
    state.finishGyroCalibration();
    assert(state.gyroRangeDps == 250 && !state.calibrating && !state.enabled);
    assert(state.enable(3000, 42));
    state.latchFault();
    assert(!state.requestGyroRange(500));
    assert(!state.enable(3001, 42));

    char row[256];
    const TelemetrySample sample{1234, -1310, -10.0f, -9.5f, -15, 2.0f, true, 250, 131.0f, 21};
    const int length = formatTelemetryCsv(row, sizeof(row), sample);
    assert(length == static_cast<int>(std::strlen(row)));
    assert(std::strcmp(row, "1234,-1310,-10.0000,-9.5000,-15,2,1,250,131,21,auto,0\n") == 0);
    TelemetrySample manualSample = sample;
    manualSample.enabled = false;
    manualSample.manual = true;
    manualSample.throttlePercent = 50;
    manualSample.pwm = -128;
    formatTelemetryCsv(row, sizeof(row), manualSample);
    assert(std::strcmp(row, "1234,-1310,-10.0000,-9.5000,-128,2,0,250,131,21,manual,50\n") == 0);
    char small[8];
    assert(formatTelemetryCsv(small, sizeof(small), sample) >= static_cast<int>(sizeof(small)));
}
