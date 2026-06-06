# audio.py — PWM square-wave tone generation for MicroPython on STM32G474.
#
# Drives a single timer PWM output that feeds the Adafruit STEMMA speaker
# (PAM8302 class-D amp, AC-coupled analog input). A 0-3.3V square wave at the
# note frequency is enough for audible tones; the amp/speaker pass the
# fundamental. This is the PWM bring-up before the DAC1 + DMA sine upgrade.
#
# Output pin: TIM3_CH1 on PB4 (Arduino D5). Chosen to avoid PA5 (LED),
# PB8/PB9 (IMU I2C), PA2/PA3 (VCP) and PA4 (reserved for DAC1 later).
#
# pyb.Timer handles the prescaler/period split internally, so a single
# Timer.freq(hz) call retunes cleanly across the whole musical range
# (well beyond the ~100Hz-2kHz we need here) despite TIM3 being 16-bit.
import time
from pyb import Timer, Pin

# Equal-temperament note frequencies, A4 = 440 Hz, rounded to whole Hz.
# Covers C4..C6 (sharps included). Use flats via the enharmonic sharp.
NOTES = {
    "C4": 262, "C#4": 277, "D4": 294, "D#4": 311, "E4": 330, "F4": 349,
    "F#4": 370, "G4": 392, "G#4": 415, "A4": 440, "A#4": 466, "B4": 494,
    "C5": 523, "C#5": 554, "D5": 587, "D#5": 622, "E5": 659, "F5": 698,
    "F#5": 740, "G5": 784, "G#5": 831, "A5": 880, "A#5": 932, "B5": 988,
    "C6": 1047,
}


class Audio:
    def __init__(self, timer_id=3, channel=1, pin="B4"):
        self.timer_id = timer_id
        self.channel_id = channel
        self.pin = pin
        self.tim = None
        self.ch = None

    def init(self):
        """Configure the timer in PWM mode, output enabled, initially silent."""
        # Start at a valid frequency but with 0% duty so the pin sits low
        # (silent) until the first note.
        self.tim = Timer(self.timer_id, freq=440)
        self.ch = self.tim.channel(
            self.channel_id, Timer.PWM,
            pin=Pin(self.pin), pulse_width_percent=0,
        )

    def set_freq(self, hz):
        """Set the PWM output frequency. hz <= 0 silences the output (0% duty)."""
        if hz <= 0:
            self.ch.pulse_width_percent(0)   # gate channel off -> pin held low
            return
        self.tim.freq(hz)                    # retunes prescaler + period
        self.ch.pulse_width_percent(50)      # 50% duty square wave

    def play_note(self, freq_hz, duration_ms):
        """Sound freq_hz for duration_ms, then go silent."""
        self.set_freq(freq_hz)
        time.sleep_ms(duration_ms)
        self.set_freq(0)

    def play_melody(self, melody, gap_ms=40):
        """Play an iterable of (freq_hz, duration_ms) pairs.

        Kept array-driven so melodies/tempo can be sequenced from data later.
        gap_ms inserts a short silence between notes so repeated pitches
        are audible as separate notes.
        """
        for freq_hz, duration_ms in melody:
            self.play_note(freq_hz, duration_ms)
            if gap_ms:
                time.sleep_ms(gap_ms)
