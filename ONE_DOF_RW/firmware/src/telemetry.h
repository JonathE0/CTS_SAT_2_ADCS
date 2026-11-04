#pragma once

#include <cstdint>
#include <cstdio>

constexpr char TELEMETRY_CSV_HEADER[] =
    "time_ms,gyro_y_raw_counts,gyro_y_raw_dps,gyro_y_corrected_dps,pwm,kp,enabled,gyro_range_dps,gyro_lsb_per_dps,filter_hz,mode,throttle_pct";

struct TelemetrySample {
    uint32_t timeMs;
    int32_t rawCounts;
    float rawRateDps;
    float correctedRateDps;
    int pwm;
    float kp;
    bool enabled;
    int rangeDps;
    float lsbPerDps;
    int filterHz;
    bool manual = false;
    int throttlePercent = 0;
};

inline int formatTelemetryCsv(char *buffer, size_t capacity, const TelemetrySample &sample) {
    return std::snprintf(buffer, capacity, "%lu,%ld,%.4f,%.4f,%d,%.6g,%d,%d,%.6g,%d,%s,%d\n",
        static_cast<unsigned long>(sample.timeMs), static_cast<long>(sample.rawCounts),
        sample.rawRateDps, sample.correctedRateDps, sample.pwm, sample.kp,
        sample.enabled ? 1 : 0, sample.rangeDps, sample.lsbPerDps, sample.filterHz,
        sample.manual ? "manual" : sample.enabled ? "auto" : "off",
        sample.manual ? sample.throttlePercent : 0);
}
