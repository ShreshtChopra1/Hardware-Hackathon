# stm32-micropython-drivers

Hand-written MicroPython drivers for the **STM32G4 Nucleo-64 (NUCLEO-G474RE)**,
plus a demo that wires them together into a sensor-reactive animated face on a
128×128 grayscale OLED.

Everything here runs *on the MCU* — MicroPython on bare STM32, no Arduino layer,
no vendored libraries.

## Drivers

| Module | Device | Notes |
|---|---|---|
| `src/ssd1327.py` | Waveshare 1.5" 128×128 OLED | 4-bit grayscale over I²C. Uses `framebuf` in `GS4_HMSB` — high nibble is the left pixel — into an 8,192-byte buffer |
| `src/hcsr04.py` | HC-SR04-R ultrasonic | `time_pulse_us` echo timing, 2–400 cm. Enforces 60 ms between readings so trigger/echo don't cross-talk |
| `src/mpu6050.py` | InvenSense MPU-6050 | 6-axis IMU over I²C at 0x68, raw int16 with the LSB/g and LSB/dps scale factors documented |
| `src/audio.py` | PWM tone generation | TIM3_CH1 square wave into a PAM8302 class-D amp. `Timer.freq()` retunes cleanly across the range despite TIM3 being 16-bit |

The OLED and the IMU **share one I²C bus** (PB8/PB9), and the audio pin was
chosen specifically to dodge PA5 (user LED), PB8/PB9 (that shared bus), PA2/PA3
(the virtual COM port) and PA4 (reserved for a later DAC1 + DMA upgrade). Pin
conflicts on a 64-pin part are the actual constraint; each driver documents its
wiring at the top of the file.

## Demo — `src/oled_face.py`

An animated face whose expression is driven by live sensor data:

| Ultrasonic distance | Expression |
|---|---|
| < 10 cm | Scared — wide eyes, open-O mouth, V brows |
| 10–40 cm | Surprised — raised brows, oval mouth |
| 40–90 cm | Happy — big smile, rosy cheeks |
| > 90 cm | Sleepy — half-closed eyes, floating ZZZ |

MPU-6050 tilt shifts the pupils in real time, eyes blink on a 2–4 s random
interval, and boot plays an expanding-ring animation.

```sh
mpremote connect /dev/cu.usbmodem11103 cp src/ssd1327.py :ssd1327.py
mpremote connect /dev/cu.usbmodem11103 cp src/mpu6050.py :mpu6050.py
mpremote connect /dev/cu.usbmodem11103 cp src/hcsr04.py  :hcsr04.py
mpremote connect /dev/cu.usbmodem11103 run src/oled_face.py
```

`src/main.py` is the current boot script: PWM audio bring-up (A4, a C-major
scale, a short melody) followed by an IMU stream and LED heartbeat.

## Hardware

- **MCU:** STM32G474RET6 — Cortex-M4 @ 170 MHz, 512 KB flash, 128 KB SRAM, LQFP64
- **Debugger:** on-board STLINK-V3E, which exposes both a USB mass-storage volume
  for drag-and-drop flashing *and* a USB CDC serial port for the REPL
- **Firmware:** MicroPython v1.28.0 (`firmware/NUCLEO_G474RE.hex`)

## Flashing MicroPython (one time)

The STLINK-V3E mounts the board as a drive, so there's no toolchain to set up.

1. Plug in over USB Micro-B. A volume named **`NOD_G474RE`** mounts.
2. `cp firmware/NUCLEO_G474RE.hex /Volumes/NOD_G474RE/`
3. The LED by the USB connector flashes red/green for ~5 s, then the volume
   re-mounts. MicroPython is on the board.

## Daily loop

```sh
python3 -m venv .venv && .venv/bin/pip install mpremote pyserial
source .venv/bin/activate

mpremote connect /dev/cu.usbmodem11103 repl   # live REPL on the MCU, Ctrl-] to exit
mpremote devs                                 # if the device path changed after a re-plug
```

At the `>>>` prompt you're running Python on the microcontroller:

```python
>>> from machine import Pin
>>> led = Pin("A5", Pin.OUT)   # LD2, PA5 per UM2505 section 6.4
>>> led.on()
```

Copy a script to run on every power-up, or run it once without persisting:

```sh
mpremote connect /dev/cu.usbmodem11103 cp src/main.py :main.py
mpremote connect /dev/cu.usbmodem11103 reset

mpremote connect /dev/cu.usbmodem11103 run src/main.py   # one-shot, not saved
```

Other useful commands: `mpremote ls` (files on the board), `mpremote rm :main.py`,
`mpremote soft-reset` (restart MicroPython without dropping USB).

## Layout

```
src/            drivers + demos — the source of truth
firmware/       MicroPython .hex for this board
datasheets/     board manual (UM2505) and sensor datasheets
test-scripts/   standalone sensor bring-up scripts
```

The board's own filesystem is deployment state, not version control. Edit in
`src/`, then push with `mpremote cp`.

## Further reading

`DOCS.md` carries the full source map, board notes and complete pin map.

## Reference

- [MicroPython STM32 quickref](https://docs.micropython.org/en/latest/stm32/quickref.html)
- [MicroPython `machine` API](https://docs.micropython.org/en/latest/library/machine.html)
- Board manual: UM2505, in `datasheets/`

## License

MIT
