# main.py — Phase 1 (MicroPython): stream MPU-6050 accel + gyro to the REPL.
#
# Keeps the Phase 0 LED heartbeat (LD2 = PA5) alive. Output goes to the USB
# REPL/VCP, so just watch it with `mpremote ... repl` — no UART setup needed.
#
# Wiring (kit MPU-6050, AD0 low): VCC->3V3, GND->GND, SCL->PB8, SDA->PB9.
import time
import pyb
from machine import Pin, SoftI2C

from mpu6050 import MPU6050, MPU6050Error

led = pyb.LED(1)  # LD2 (green user LED, PA5)


def fast_blink_forever():
    # Fast blink = wiring problem (sensor not responding).
    while True:
        led.toggle()
        time.sleep_ms(100)


print()
print("=== NUCLEO-G474RE Phase 1: MPU-6050 over I2C (MicroPython) ===")

# Bit-banged I2C on PB8 (SCL) / PB9 (SDA) at 100 kHz standard mode. SoftI2C
# pins the bus to exactly these pads regardless of board hardware-I2C mapping.
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
