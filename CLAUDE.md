# Hardware-Hackathon — project context for Claude

## What this project is

Embedded hackathon project targeting the **STM32G4 Nucleo-64 (NUCLEO-G474RE, MB1367)**
board, programmed in Python via **MicroPython** running directly on the MCU.

- MCU: STM32G474RET6 (Cortex-M4 @ 170 MHz, 512 KB flash, 128 KB SRAM, LQFP64)
- On-board debugger: STLINK-V3E, exposes both a USB mass-storage volume
  (`/Volumes/NOD_G474RE`) for drag-and-drop firmware flashing *and* a USB CDC
  serial port (`/dev/cu.usbmodem11103` on this machine) for the MicroPython REPL.
- Board user manual: `datasheets/um2505-stm32g4-nucleo64-boards-mb1367-stmicroelectronics (1).pdf`
- Additional sensors in the hackathon kit (datasheets/): MCP9808 (I²C temp),
  MPU-6000 (IMU), HC-SR04 ultrasonic, plus `3885_Web.pdf`.

## Repository layout

```
.venv/                    # host Python venv (gitignored). Has mpremote + pyserial.
firmware/
  NUCLEO_G474RE.hex       # MicroPython v1.28.0 firmware for this board.
src/
  main.py                 # current on-board script (copied to ":main.py")
datasheets/               # hardware reference PDFs
README.md                 # human-facing setup guide
CLAUDE.md                 # this file
```

`src/` is the source of truth for what should run on the board. Edit there, then
push to the board with `mpremote cp` (see below). The board's own filesystem
(`boot.py`, `main.py`) is the deployed state, not version-controlled.

## Setup (already done; redo only if cloning fresh)

```sh
python3 -m venv .venv
.venv/bin/pip install mpremote pyserial
# Firmware is already in firmware/ — re-download from micropython.org/download/NUCLEO_G474RE/
# if you ever need a newer version.
```

## Flashing MicroPython firmware (one-time per board)

The STLINK-V3E uses Mbed-style mass-storage flashing:

```sh
cp firmware/NUCLEO_G474RE.hex /Volumes/NOD_G474RE/
```

Volume unmounts/remounts in ~5 s. Programming is successful if `FAIL.TXT` is
*not* present in the remounted volume. Verify by opening the REPL — see below.

## Running and iterating on Python code

Always activate the venv first:

```sh
source .venv/bin/activate
```

Find the board's serial device (path can change across re-plugs):

```sh
mpremote devs    # look for the row with "STLINK-V3" in it
```

Open a live REPL on the MCU:

```sh
mpremote connect /dev/cu.usbmodem11103 repl
# Ctrl-] to exit. Ctrl-D inside REPL = soft reboot.
```

Push a script to the board and run it on the next reset:

```sh
mpremote connect /dev/cu.usbmodem11103 cp src/main.py :main.py
mpremote connect /dev/cu.usbmodem11103 reset
```

Run a script *once* without persisting it to the board's filesystem:

```sh
mpremote connect /dev/cu.usbmodem11103 run src/main.py
```

Other useful commands:

```sh
mpremote ls                              # list files on board
mpremote cp :main.py local_backup.py     # copy FROM board
mpremote rm :foo.py                      # delete file on board
mpremote cat :boot.py                    # read file on board
```

## MicroPython API notes (gotchas on the STM32 port)

- **`machine.Pin` has no `.toggle()` method on the STM32 port.** Use one of:
  - `pyb.LED(1).toggle()`  (cleanest for the on-board user LED LD2)
  - `pin.value(not pin.value())`  (portable across MicroPython ports)
- `pyb` is the board-specific module; it ships imported by default in the
  stock `boot.py` and gives you `pyb.LED(1..4)`, `pyb.UART`, `pyb.Timer`, etc.
- Pin naming: both `Pin("A5", ...)` and `Pin("PA5", ...)` work for PA5.
- LD2 (the green user LED) is wired to PA5, equivalently `pyb.LED(1)`.
- Default `boot.py` shipped with the firmware runs `import pyb` and leaves
  the default behaviour of executing `main.py` after boot — no need to
  uncomment `pyb.main('main.py')`.

## Git remote

Origin is `github.com/ShreshtChopra1/Hardware-Hackathon` (team repo). The
local user's `SAbbineni24` GitHub account has push access. Push protocol over
HTTPS using gh CLI token auth.
