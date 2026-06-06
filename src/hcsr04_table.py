# hcsr04_table.py — HC-SR04-R fixed-sample table test, MicroPython / STM32.
#
# Wiring: VCC->CN6-3V3, GND->GND, TRIG->D6(PB10), ECHO->D9(PC7)
# Takes 20 readings and prints them in a formatted table, then stops.
import utime
import pyb
from hcsr04 import HCSR04, HCSR04Error

led = pyb.LED(1)
sensor = HCSR04(trig_pin="B10", echo_pin="C7")

# Settle
utime.sleep_ms(100)
try:
    sensor.distance_cm()
except HCSR04Error:
    pass

NUM_READINGS = 20

print()
print("+-------+------------+------------+-------------------+")
print("| #     | dist_cm    | dist_mm    | status            |")
print("+-------+------------+------------+-------------------+")

for i in range(1, NUM_READINGS + 1):
    utime.sleep_ms(100)
    try:
        cm = sensor.distance_cm()
        mm = round(cm * 10)
        if cm < 2.0 or cm > 400.0:
            print("| %-5d | %-10s | %-10s | OUT OF RANGE      |" % (i, "--", "--"))
        else:
            print("| %-5d | %-10.1f | %-10d | OK                |" % (i, cm, mm))
            led.toggle()
    except HCSR04Error:
        print("| %-5d | %-10s | %-10s | TIMEOUT           |" % (i, "--", "--"))
        led.on()

print("+-------+------------+------------+-------------------+")
print("Done.")
