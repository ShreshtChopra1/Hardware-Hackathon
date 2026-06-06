# Component Docs

This project runs MicroPython on the STM32 NUCLEO-G474RE and currently wires
together three main hardware components:

- MPU-6050 IMU for acceleration and gyroscope readings
- Adafruit STEMMA speaker driven by PWM audio
- HC-SR04-R ultrasonic distance sensor

The current boot demo in `src/main.py` plays a few tones, then streams raw
MPU-6050 readings while blinking the user LED.

## Source Map

| File | Purpose |
| --- | --- |
| `src/main.py` | Main Phase 2 demo: initializes PWM audio, plays test tones, then streams MPU-6050 raw IMU data at about 10 Hz. |
| `src/audio.py` | PWM square-wave tone driver for the STEMMA speaker. Includes a `NOTES` table from C4 through C6. |
| `src/mpu6050.py` | Minimal MPU-6050 driver. Probes `WHO_AM_I`, wakes the sensor, configures default ranges, and reads six raw axes. |
| `src/hcsr04.py` | HC-SR04-R ultrasonic distance driver. Sends trigger pulses and converts echo timing to cm/mm. |
| `src/hcsr04_test.py` | Continuous ultrasonic range test with LED status feedback. |
| `src/hcsr04_table.py` | Fixed 20-sample ultrasonic range test that prints a formatted table and exits. |
| `test-scripts/MPU-6050-test.py` | Older standalone MPU-6050 test with scaled accel/gyro/temp output and optional interrupt pin read. |

## Board

### STM32 NUCLEO-G474RE

- Runs MicroPython from `firmware/NUCLEO_G474RE.hex`.
- User LED LD2 is on PA5.
- USB serial is used for `mpremote` REPL, file transfer, and printed output.
- Current scripts assume a serial path like `/dev/cu.usbmodem11103`; run `mpremote devs` if the path changes.

## Pin Map

| Signal | Board Pin | MCU Pin | Used By |
| --- | --- | --- | --- |
| User LED LD2 | Built in | PA5 | `src/main.py`, HC-SR04 tests |
| I2C SCL | D15 | PB8 | MPU-6050 |
| I2C SDA | D14 | PB9 | MPU-6050 |
| PWM speaker signal | D5 | PB4 | STEMMA speaker / `src/audio.py` |
| Ultrasonic TRIG | D6 | PB10 | HC-SR04-R |
| Ultrasonic ECHO | D9 | PC7 | HC-SR04-R |
| Optional IMU INT | D2 | PA10 | `test-scripts/MPU-6050-test.py` only |

## Components

### MPU-6050 IMU

The MPU-6050 is a 6-axis inertial measurement unit with a 3-axis accelerometer
and 3-axis gyroscope.

Wiring:

| MPU-6050 Pin | Connect To |
| --- | --- |
| VCC | 3V3 |
| GND | GND |
| SCL | PB8 / D15 |
| SDA | PB9 / D14 |
| AD0 | GND |
| INT | PA10 / D2, optional test-script only |

Code:

- Driver: `src/mpu6050.py`
- Main demo use: `src/main.py`
- Standalone scaled test: `test-scripts/MPU-6050-test.py`

Runtime behavior:

- Uses I2C address `0x68` when AD0 is tied low.
- Checks `WHO_AM_I` and expects `0x68`.
- Wakes the device from sleep.
- Sets accel range to `+/-2 g`.
- Sets gyro range to `+/-250 deg/s`.
- Sets DLPF config to roughly 44 Hz accel / 42 Hz gyro bandwidth.
- `src/mpu6050.py` returns raw signed 16-bit values as:

```python
(ax, ay, az, gx, gy, gz)
```

Troubleshooting:

- If `src/main.py` prints `MPU6050 not found`, check VCC, GND, PB8/PB9, and AD0.
- Fast LED blinking in `src/main.py` means the IMU did not initialize.
- If the board was unplugged, run `mpremote devs` and update the serial path.

### STEMMA Speaker / PWM Audio

The speaker is driven by a PWM square wave from TIM3 channel 1 on PB4.

Wiring:

| Speaker Wire | Connect To |
| --- | --- |
| Signal / white | PB4 / D5 |
| Power / red | 3V to 5V |
| GND / black | GND |

Code:

- Driver: `src/audio.py`
- Main demo use: `src/main.py`

Runtime behavior:

- `Audio.init()` configures TIM3 channel 1 in PWM mode.
- `Audio.set_freq(hz)` retunes the timer and uses 50% duty cycle for sound.
- `Audio.set_freq(0)` gates the channel off with 0% duty cycle.
- `Audio.play_note(freq_hz, duration_ms)` plays one tone.
- `Audio.play_melody(melody, gap_ms=40)` plays `(frequency, duration)` pairs with short gaps.

The `NOTES` table includes equal-temperament notes from C4 through C6, rounded
to whole Hz.

Boot demo sequence in `src/main.py`:

1. A4 at 440 Hz for 1 second
2. Ascending C-major scale
3. First phrase of "Twinkle Twinkle"
4. MPU-6050 raw data stream

Troubleshooting:

- If there is no sound, check the white signal wire on PB4 / D5.
- Check that speaker power and board ground share the same ground.
- PB4 was chosen to avoid PA5 LED, PB8/PB9 I2C, PA2/PA3 USB serial, and PA4 reserved for later DAC work.

### HC-SR04-R Ultrasonic Sensor

The HC-SR04-R measures distance by timing the echo from a short trigger pulse.

Wiring:

| HC-SR04-R Pin | Connect To |
| --- | --- |
| VCC | CN6 3V3 |
| GND | GND |
| TRIG | PB10 / D6 |
| ECHO | PC7 / D9 |

Code:

- Driver: `src/hcsr04.py`
- Continuous test: `src/hcsr04_test.py`
- Fixed table test: `src/hcsr04_table.py`

Runtime behavior:

- Sends a 10 us trigger pulse.
- Waits up to 30 ms for the echo pulse.
- Converts echo duration to distance with `duration_us / 58.0`.
- Supports:

```python
distance_cm()  # returns float
distance_mm()  # returns int
```

Expected range:

- Reliable range: about 2 cm to 400 cm.
- Keep at least 60 ms between readings to reduce trigger/echo crosstalk.
- The test scripts sample every 100 ms.

Status behavior:

- Valid reading: prints distance and toggles LD2.
- Out of range: prints `OUT OF RANGE`.
- Timeout: prints `TIMEOUT` and leaves LD2 on.

Troubleshooting:

- A timeout usually means no echo, object out of range, or ECHO wiring issue.
- If values are unstable, increase spacing between readings or test against a flat surface.
- Make sure TRIG is on PB10 / D6 and ECHO is on PC7 / D9.

## Running The Code

Activate the local environment:

```sh
source .venv/bin/activate
```

List connected boards:

```sh
mpremote devs
```

Run the main demo once without saving it to the board:

```sh
mpremote connect /dev/cu.usbmodem11103 cp src/audio.py :
mpremote connect /dev/cu.usbmodem11103 cp src/mpu6050.py :
mpremote connect /dev/cu.usbmodem11103 run src/main.py
```

Install the main demo so it runs on boot:

```sh
mpremote connect /dev/cu.usbmodem11103 cp src/audio.py :
mpremote connect /dev/cu.usbmodem11103 cp src/mpu6050.py :
mpremote connect /dev/cu.usbmodem11103 cp src/main.py :main.py
mpremote connect /dev/cu.usbmodem11103 reset
```

Run the continuous HC-SR04-R test:

```sh
mpremote connect /dev/cu.usbmodem11103 cp src/hcsr04.py :
mpremote connect /dev/cu.usbmodem11103 run src/hcsr04_test.py
```

Run the 20-sample HC-SR04-R table test:

```sh
mpremote connect /dev/cu.usbmodem11103 cp src/hcsr04.py :
mpremote connect /dev/cu.usbmodem11103 run src/hcsr04_table.py
```

Open a REPL:

```sh
mpremote connect /dev/cu.usbmodem11103 repl
```

Exit the REPL with `Ctrl-]`.

## Current Data Outputs

### Main Demo

After the audio checks, `src/main.py` prints raw IMU readings:

```text
ax=<raw> ay=<raw> az=<raw> gx=<raw> gy=<raw> gz=<raw>
```

### Ultrasonic Continuous Test

`src/hcsr04_test.py` prints:

```text
dist_cm      dist_mm      status
```

### Ultrasonic Table Test

`src/hcsr04_table.py` prints 20 rows and then stops:

```text
| #     | dist_cm    | dist_mm    | status            |
```

## Expansion Notes

- `src/audio.py` is currently PWM square-wave audio. Comments note a later DAC1 + DMA sine-wave upgrade.
- `src/mpu6050.py` currently returns raw values. Scaled accel/gyro output exists in `test-scripts/MPU-6050-test.py` and can be folded into the driver later.
- The HC-SR04-R driver is independent of the main demo right now; integrate it into `src/main.py` when the project needs live distance data during normal boot.
