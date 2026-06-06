# Hardware-Hackathon — NUCLEO-G474RE + MicroPython

Programming the STM32G4 Nucleo-64 (NUCLEO-G474RE, MB1367) in Python by running
MicroPython directly on the MCU.

## Our Project
We have developed a wearable device for 

## What's installed

- `.venv/` — project Python virtual environment
- `firmware/NUCLEO_G474RE.hex` — MicroPython v1.28.0 firmware (Apr 2026)
- `src/main.py` — example LED blink to copy onto the board
- Tools in the venv: `mpremote` (REPL + file transfer), `pyserial`

## One-time: flash MicroPython onto the board

The on-board STLINK-V3E exposes the board as a USB mass-storage drive, so
flashing is drag-and-drop — no extra tooling needed.

1. Plug the board into your Mac via USB Micro-B. A volume named
   **`NOD_G474RE`** mounts on the desktop (also visible at `/Volumes/NOD_G474RE`).
2. Copy the firmware onto it:

   ```sh
   cp firmware/NUCLEO_G474RE.hex /Volumes/NOD_G474RE/
   ```

3. The STLINK programs the chip automatically. The LED next to the USB
   connector flashes red/green during programming (~5 s). When it finishes,
   the volume re-mounts. You now have MicroPython on the board.

## Daily use: REPL + push code

Activate the venv first:

```sh
source .venv/bin/activate
```

Open a live Python REPL on the board:

```sh
mpremote connect /dev/cu.usbmodem11103 repl
```

(Exit the REPL with `Ctrl-]`. If the device path changes after a re-plug,
list candidates with `mpremote devs`.)

At the `>>>` prompt you can type Python that runs on the MCU:

```python
>>> from machine import Pin
>>> led = Pin("A5", Pin.OUT)
>>> led.on()
>>> led.off()
```

`A5` is LD2, the user LED on the Nucleo (PA5 per UM2505 §6.4).

## Push a script to run on boot

Copy `src/main.py` to the board's filesystem (it runs automatically after
`boot.py` on power-up):

```sh
mpremote connect /dev/cu.usbmodem11103 cp src/main.py :main.py
mpremote connect /dev/cu.usbmodem11103 reset
```

The user LED should now blink at 1 Hz.

To run a script once *without* persisting it:

```sh
mpremote connect /dev/cu.usbmodem11103 run src/main.py
```

## Useful mpremote commands

```sh
mpremote devs                            # list connected MicroPython boards
mpremote ls                              # list files on the board
mpremote cp src/foo.py :                 # copy file to board root
mpremote cp :main.py main_backup.py      # copy file FROM board
mpremote rm :main.py                     # delete file on board
mpremote reset                           # soft-reset the board
mpremote soft-reset                      # restart MicroPython without losing USB
```

## Reference

- Board manual: `datasheets/um2505-stm32g4-nucleo64-boards-mb1367-stmicroelectronics (1).pdf`
- MicroPython STM32 quickref: https://docs.micropython.org/en/latest/stm32/quickref.html
- MicroPython `machine` API: https://docs.micropython.org/en/latest/library/machine.html
