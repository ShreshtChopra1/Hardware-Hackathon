# hcsr04_test.py — HC-SR04-R ultrasonic ranging test, MicroPython / STM32.
#
# Wiring:
#   HC-SR04-R  VCC  -> CN6 3V3
#   HC-SR04-R  GND  -> GND
#   HC-SR04-R  TRIG -> D6 (PB10)
#   HC-SR04-R  ECHO -> D9 (PC7)
#
# Run once without persisting:
#   mpremote connect /dev/cu.usbmodem11103 cp src/hcsr04.py :hcsr04.py
#   mpremote connect /dev/cu.usbmodem11103 run src/hcsr04_test.py
#
# Prints distance in cm and mm at ~10 Hz. LED blinks on each valid reading;
# stays solid on for timeout (nothing in range or miswiring).
import utime
import pyb
from machine import Pin

from hcsr04 import HCSR04, HCSR04Error

led = pyb.LED(1)  # LD2 green user LED (PA5)

print()
print("=== NUCLEO-G474RE: HC-SR04-R Ultrasonic Ranging Test ===")
print("TRIG=D6(PB10)  ECHO=D9(PC7)  VCC=CN6-3V3")
print("Range: 2 cm - 400 cm | Cycle: 100 ms")
print()
print("%-12s %-12s %-12s" % ("dist_cm", "dist_mm", "status"))
print("-" * 40)

sensor = HCSR04(trig_pin="B10", echo_pin="C7")

# Discard first reading — sensor needs one cycle to settle after power-on.
utime.sleep_ms(100)
try:
    sensor.distance_cm()
except HCSR04Error:
    pass

while True:
    utime.sleep_ms(100)  # >= 60 ms per datasheet to prevent echo/trigger crosstalk

    try:
        cm = sensor.distance_cm()
        mm = round(cm * 10)

        if cm < 2.0 or cm > 400.0:
            # Sensor returned a value but outside its reliable range.
            print("%-12s %-12s OUT OF RANGE (%.1f cm)" % ("--", "--", cm))
        else:
            print("%-12.1f %-12d OK" % (cm, mm))
            led.toggle()

    except HCSR04Error:
        # Echo timed out — no object detected or ECHO pin miswired.
        print("%-12s %-12s TIMEOUT - no echo" % ("--", "--"))
        led.on()
