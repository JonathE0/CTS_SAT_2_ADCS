# ESP32 Cube Balancing System Wiring

2026-11-23 update: the exact kit listing's detailed photos identify a SimpleFOC
Mini v1.0 / DRV8313 and AS5600 encoder. See [motor-test evidence and limits](docs/motor-test.md).
The unresolved items below describe the original inspection; listing evidence
does not replace checking the physical wiring or measuring current.

## Hardware

- ESP32 DevKit V1
- MiniFOC 3-phase motor driver
- 2804 three-phase motor purchased from Amazon
- MPU6050 6-axis IMU
- Rotary encoder shared with the MPU6050 on I2C
- Cube balancing mechanism

The final mechanical goal is to balance a cube on its side using a reaction wheel.

## Intended I2C connections

The MPU6050 and encoder share the ESP32 I2C bus.

| Device pin | ESP32 pin |
|---|---|
| MPU6050 VCC | 3V3 |
| Encoder VCC | 3V3 |
| MPU6050 GND | GND |
| Encoder GND | GND |
| Shared SCL | D32 |
| Shared SDA | D33 |

The ESP32 and all connected logic boards should share a common ground.

The encoder and MPU6050 must use distinct I2C addresses. For example, a common MPU6050 address is `0x68` or `0x69`, while an AS5600 encoder commonly uses `0x36`.

Use 2.2-4.7 kOhm pull-up resistors from SDA and SCL to 3.3 V if the breakout boards do not already include them.

## MiniFOC connections

| MiniFOC pin | ESP32 pin |
|---|---|
| EN | D13 |
| IN1 | D27 |
| IN2 | D25 |
| IN3 | D26 |
| GND | GND |

The motor's three phase wires connect to the MiniFOC U, V, and W or A, B, and C outputs.

Motor power must come from a supply suitable for the board and 2804 motor. It must not be supplied from the ESP32 3V3 pin.

Do not connect or enable the motor supply until the motor-driver supply voltage and enable polarity have been confirmed.

## Connection notes

- D34 was initially used for EN but was replaced with D13 because D34 is input-only on the ESP32.
- GPIO13 is not a boot strapping pin on the classic ESP32 used by the DevKit V1. It is also a JTAG pin. Confirm the actual module variant and ensure the driver stays disabled during reset using an external pull resistor selected for its confirmed EN polarity; firmware alone cannot guarantee the reset state.
- Confirm whether the MiniFOC EN pin is active-high or active-low.
- Confirm that IN1, IN2, and IN3 accept 3.3 V logic. Use level shifters if they require 5 V logic.
- A separate motor supply may be required.
- All grounds must be electrically common.
- Add an appropriately rated fuse and bulk capacitor near the motor-driver motor-power terminals.
- Fuse rating and capacitance should be selected according to the motor's stall current and the driver's specifications.

## Amazon link

ESP32 pin reference: [Espressif GPIO documentation](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/gpio.html).

The listed MiniFOC hardware is from:

https://www.amazon.ca/dp/B0FXKN9YMJ

Amazon returned HTTP 503 while the listing was being inspected, so the exact product specifications could not be verified.

## Missing information still needed

Before first motor activation, provide or inspect:

1. A clear photo of the MiniFOC board with pin labels and voltage markings visible.
2. The full Amazon title and specification text.
3. Photos of the MPU6050 and encoder board, especially VCC, GND, SCL, and SDA markings.
4. A photo or specification sheet for the 2804 motor showing wire count and connector type.

The exact MiniFOC board model is required to confirm:

- Logic supply voltage
- Enable pin voltage and polarity
- PWM input polarity
- Motor supply voltage range
- Maximum phase current
- Whether brake, enable, fault, or direction pins require external pull-ups or pull-downs
