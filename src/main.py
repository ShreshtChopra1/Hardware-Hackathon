# main.py — Phase 2 (MicroPython): PWM audio bring-up, then the Phase 1
# MPU-6050 stream + LED heartbeat.
#
# On boot: play A4 (440Hz) for 1s, an ascending C-major scale, then a short
# melody once. Then fall into the Phase 1 IMU/heartbeat loop.
#
# Output goes to the USB REPL/VCP — watch with `mpremote ... repl`.
#
# Wiring:
#   MPU-6050 (AD0 low): VCC->3V3, GND->GND, SCL->PB8, SDA->PB9
#   STEMMA speaker:     signal(white)->PB4 (D5), power(red)->3-5V, GND(black)->GND
import time
import pyb
from machine import Pin, SoftI2C

from mpu6050 import MPU6050, MPU6050Error
from audio import Audio, NOTES

led = pyb.LED(1)  # LD2 (green user LED, PA5)


def fast_blink_forever():
    # Fast blink = wiring problem (sensor not responding).
    while True:
        led.toggle()
        time.sleep_ms(100)


print()
print("=== NUCLEO-G474RE Phase 2: PWM audio + MPU-6050 (MicroPython) ===")

# --- Audio: TIM3_CH1 on PB4 (Arduino D5) -> STEMMA speaker signal in ---
audio = Audio()
audio.init()

# 1) Single 440 Hz tone for 1s — "is the speaker wired right?" check.
print("tone: A4 440Hz, 1s")
audio.play_note(440, 1000)
time.sleep_ms(200)

# 2) Ascending C-major scale.
print("scale: C major")
for name in ("C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"):
    audio.play_note(NOTES[name], 250)
time.sleep_ms(200)

# 3) Short recognizable melody (Twinkle Twinkle, first phrase). Data-driven
# (note, duration) so it can be sequenced/retempo'd from a table later.
print("melody")
melody = (
    ("C4", 400), ("C4", 400), ("G4", 400), ("G4", 400),
    ("A4", 400), ("A4", 400), ("G4", 800),
    ("F4", 400), ("F4", 400), ("E4", 400), ("E4", 400),
    ("D4", 400), ("D4", 400), ("C4", 800),
)
audio.play_melody((NOTES[name], dur) for name, dur in melody)

# --- Phase 1: MPU-6050 stream + heartbeat ---
i2c = SoftI2C(scl=Pin("B8"), sda=Pin("B9"), freq=100000)
imu = MPU6050(i2c)
try:
    imu.init()
except (MPU6050Error, OSError) as e:
    print("MPU6050 not found:", e)
    print("Check wiring: VCC=3V3, GND, SCL=PB8, SDA=PB9, AD0=GND")
    fast_blink_forever()

print("MPU6050 OK")

# Stream all six raw axes at ~10 Hz, toggling the LED each line.
while True:
    try:
        ax, ay, az, gx, gy, gz = imu.read_raw()
        print("ax=%d ay=%d az=%d gx=%d gy=%d gz=%d" % (ax, ay, az, gx, gy, gz))
    except OSError as e:
        print("read error:", e)
    led.toggle()
    time.sleep_ms(100)
