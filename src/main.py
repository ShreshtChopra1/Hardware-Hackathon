import pyb
import time

led = pyb.LED(1)  # LD2 (green user LED, PA5)

while True:
    led.toggle()
    time.sleep_ms(500)
