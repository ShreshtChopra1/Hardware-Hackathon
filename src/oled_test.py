# oled_test.py — Live sensor dashboard on SSD1327 1.5" OLED, MicroPython/STM32.
#
# Shows HC-SR04-R distance + MPU-6050 IMU data on the 128x128 grayscale display.
#
# Wiring summary:
#   OLED (SSD1327) VCC->3V3  GND->GND  SCL->D15(PB8)  SDA->D14(PB9)  [0x3C]
#   MPU-6050       VCC->3V3  GND->GND  SCL->D15(PB8)  SDA->D14(PB9)  [0x68]
#   HC-SR04-R      VCC->CN6-3V3  GND->GND  TRIG->D6(PB10)  ECHO->D9(PC7)
#
# Run on the board:
#   mpremote connect /dev/cu.usbmodem11103 cp src/ssd1327.py  :ssd1327.py
#   mpremote connect /dev/cu.usbmodem11103 cp src/mpu6050.py  :mpu6050.py
#   mpremote connect /dev/cu.usbmodem11103 cp src/hcsr04.py   :hcsr04.py
#   mpremote connect /dev/cu.usbmodem11103 run src/oled_test.py
import utime
import pyb
from machine import Pin, SoftI2C

from ssd1327 import SSD1327
from mpu6050 import MPU6050, MPU6050Error
from hcsr04 import HCSR04, HCSR04Error

# ------------------------------------------------------------------ setup ---

led = pyb.LED(1)  # LD2 (PA5) — blinks each display refresh

print("=== NUCLEO-G474RE: OLED sensor dashboard ===")

# Single shared I2C bus at 400 kHz — OLED (0x3C) + MPU-6050 (0x68) both here.
i2c = SoftI2C(scl=Pin("B8"), sda=Pin("B9"), freq=400_000)
print("I2C scan:", [hex(a) for a in i2c.scan()])

# Initialise OLED first so we can report errors on-screen.
oled = SSD1327(i2c)
oled.fill(0)
oled.text("Starting up...", 0, 60, 15)
oled.show()

# MPU-6050 — raises on missing/miswired sensor.
imu = MPU6050(i2c)
try:
    imu.init()
    print("MPU-6050 OK")
except (MPU6050Error, OSError) as e:
    oled.fill(0)
    oled.text("MPU6050 FAIL", 0, 52, 15)
    oled.text(str(e)[:16], 0, 68, 10)
    oled.show()
    raise

# HC-SR04-R — one warm-up ping discarded.
sonar = HCSR04(trig_pin="B10", echo_pin="C7")
utime.sleep_ms(100)
try:
    sonar.distance_cm()
except HCSR04Error:
    pass

print("All sensors OK — running display loop. Ctrl-C to stop.")

# ------------------------------------------------------------------ loop ---
#
# Display layout (128 x 128, 8 x 8 font, 10 px line pitch):
#
#  y=  0  "SENSOR DASHBOARD"          title
#  y= 10  ────────────────────        divider
#  y= 14  "SONAR"                     section label
#  y= 24  "Dist: XXX.X cm"
#  y= 34  "      XXXX mm"
#  y= 44  ────────────────────        divider
#  y= 48  "IMU (raw)"                 section label
#  y= 58  "ax: +XXXXX"
#  y= 68  "ay: +XXXXX"
#  y= 78  "az: +XXXXX"
#  y= 88  "gx: +XXXXX"
#  y= 98  "gy: +XXXXX"
#  y=108  "gz: +XXXXX"
#  y=118  "n=XXXXXX"                  frame counter

n = 0
while True:
    utime.sleep_ms(100)   # >= 60 ms required by HC-SR04-R datasheet

    # ---- read HC-SR04-R ----
    try:
        cm = sonar.distance_cm()
        if 2.0 <= cm <= 400.0:
            dist_line1 = "Dist:%6.1fcm" % cm
            dist_line2 = "    %7dmm" % round(cm * 10)
        else:
            dist_line1 = "Out of range"
            dist_line2 = "(%.1fcm)" % cm
    except HCSR04Error:
        dist_line1 = "Timeout"
        dist_line2 = "No echo"

    # ---- read MPU-6050 ----
    try:
        ax, ay, az, gx, gy, gz = imu.read_raw()
        imu_ok = True
    except OSError:
        imu_ok = False

    # ---- build frame ----
    oled.fill(0)

    # Title
    oled.text("SENSOR DASHBOARD", 0, 0, 15)
    oled.hline(0, 10, 128, 6)

    # Sonar section
    oled.text("SONAR", 0, 14, 10)
    oled.text(dist_line1, 0, 24, 15)
    oled.text(dist_line2, 0, 34, 12)
    oled.hline(0, 44, 128, 6)

    # IMU section
    oled.text("IMU (raw)", 0, 48, 10)
    if imu_ok:
        oled.text("ax:%+6d" % ax, 0,  58, 15)
        oled.text("ay:%+6d" % ay, 0,  68, 15)
        oled.text("az:%+6d" % az, 0,  78, 15)
        oled.text("gx:%+6d" % gx, 0,  88, 11)
        oled.text("gy:%+6d" % gy, 0,  98, 11)
        oled.text("gz:%+6d" % gz, 0, 108, 11)
    else:
        oled.text("IMU READ ERROR", 0, 68, 15)

    # Frame counter
    oled.text("n=%d" % n, 0, 118, 5)

    oled.show()
    led.toggle()
    n += 1
