#pragma once
#include <cstdint>

namespace WheelControl {
void begin();
void tick();
void printHelp();
bool handle(char command);
bool busy();
bool enabled();
void balanceUpdate(float angleDeg, float rateDps, float dt, bool ok);
bool toggleBalance();  // returns new state; default OFF
void zeroBalance();    // current tilt becomes the balance setpoint
bool balancing();
bool toggleClosedLoop();  // aligns rotor on first use; returns new state (true = closed loop)
bool closedLoop();
float gainValue(char key);           // p i d v(olts) w(max wheel rad/s)
void setGain(char key, float value);  // clamped to safe ranges
float balanceError();
float balanceWheel();
void observeEncoder(bool readOk, uint8_t status);
}
