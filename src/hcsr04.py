# hcsr04.py — HC-SR04-R ultrasonic distance driver, MicroPython / STM32.
#
# Wiring (kit HC-SR04-R):
#   VCC  -> CN6 3V3
#   GND  -> GND
#   TRIG -> D6  (PB10)
#   ECHO -> D9  (PC7)
#
# Range: 2 cm – 400 cm, accuracy ~3 mm.
# Keep at least 60 ms between readings to prevent trigger/echo crosstalk.
import utime
from machine import Pin, time_pulse_us

# 400 cm at 340 m/s = ~23.5 ms round-trip; 30 ms gives comfortable margin.
_ECHO_TIMEOUT_US = 30_000


class HCSR04Error(Exception):
    """No echo received within timeout — object out of range or miswiring."""


class HCSR04:
    def __init__(self, trig_pin="B10", echo_pin="C7"):
        self._trig = Pin(trig_pin, Pin.OUT, value=0)
        self._echo = Pin(echo_pin, Pin.IN)

    def _pulse_us(self):
        """Fire 10 µs trigger, return round-trip echo duration in µs."""
        self._trig.value(1)
        utime.sleep_us(10)
        self._trig.value(0)
        duration = time_pulse_us(self._echo, 1, _ECHO_TIMEOUT_US)
        if duration < 0:
            raise HCSR04Error("echo timeout")
        return duration

    def distance_cm(self):
        """Distance in cm (float). Raises HCSR04Error if out of range."""
        return self._pulse_us() / 58.0

    def distance_mm(self):
        """Distance in mm (int). Raises HCSR04Error if out of range."""
        return round(self.distance_cm() * 10)
