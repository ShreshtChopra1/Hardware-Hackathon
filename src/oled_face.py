# oled_face.py — Animated sensor-reactive smiley on SSD1327 1.5" OLED.
#
# HC-SR04-R distance controls the expression:
#   < 10 cm   ->  SCARED    (wide eyes, open-O mouth, V-shaped brows)
#   10-40 cm  ->  SURPRISED (medium eyes, oval mouth, raised brows)
#   40-90 cm  ->  HAPPY     (normal eyes, big smile, rosy cheeks)
#   > 90 cm   ->  SLEEPY    (half-closed eyes, lazy smile, floating ZZZ)
#
# MPU-6050 tilt shifts the eye pupils in real time.
# Eyes blink automatically every ~2-4 s.
# Boot plays an expanding-ring animation.
#
# Deploy:
#   mpremote connect /dev/cu.usbmodem11103 cp src/ssd1327.py  :ssd1327.py
#   mpremote connect /dev/cu.usbmodem11103 cp src/mpu6050.py  :mpu6050.py
#   mpremote connect /dev/cu.usbmodem11103 cp src/hcsr04.py   :hcsr04.py
#   mpremote connect /dev/cu.usbmodem11103 run src/oled_face.py
import utime
import pyb
from machine import Pin, SoftI2C

from ssd1327 import SSD1327
from mpu6050 import MPU6050, MPU6050Error
from hcsr04  import HCSR04,  HCSR04Error

led = pyb.LED(1)

# Face geometry
CX, CY, FR = 64, 58, 50     # centre x, centre y, face radius
ELX = CX - 17               # left  eye x
ERX = CX + 17               # right eye x
EY  = CY - 20               # eye row y
MY  = CY + 16               # mouth y


def _clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


# ── Boot animation ──────────────────────────────────────────────────────────

def startup_animation(oled):
    """Rings expand outward, brightening as they reach face radius."""
    for r in range(4, FR + 8, 4):
        oled.fill(0)
        c = _clamp((r * 15) // (FR + 8), 1, 15)
        oled.ellipse(CX, CY, r + 4, r + 4, _clamp(c - 7, 1, 6))
        oled.ellipse(CX, CY, r,     r,     c)
        oled.show()
        utime.sleep_ms(45)
    # Flash full-bright then clear
    oled.fill(0)
    oled.ellipse(CX, CY, FR, FR, 15)
    oled.show()
    utime.sleep_ms(120)
    oled.fill(0)
    oled.show()
    utime.sleep_ms(80)


# ── Drawing helpers ─────────────────────────────────────────────────────────

def _draw_eye(oled, ex, ey, er, pdx, pdy):
    """Open eye: white eyeball with a dark pupil shifted by (pdx, pdy)."""
    oled.ellipse(ex, ey, er, er, 15, True)
    px = _clamp(ex + pdx, ex - er + 3, ex + er - 3)
    py = _clamp(ey + pdy, ey - er + 3, ey + er - 3)
    oled.ellipse(px, py, er // 3, er // 3, 0, True)


def _draw_closed_eye(oled, ex, ey, er):
    """Blink: draw only the top arc of the ellipse (squinted shut)."""
    oled.ellipse(ex, ey, er, er // 3, 15, False, 3)  # mask 3 = top two quadrants


def _draw_half_eye(oled, ex, ey, er):
    """Sleepy eye: fill the full circle, then black-out the top half."""
    oled.ellipse(ex, ey, er, er, 15, True)
    oled.fill_rect(ex - er, ey - er, er * 2 + 1, er, 0)   # erase top half
    oled.hline(ex - er, ey, er * 2, 15)                    # eyelid crease


# ── Main draw ───────────────────────────────────────────────────────────────

def draw_frame(oled, expr, blink, pdx, pdy, zz_y, dist_str):
    oled.fill(0)

    # Face with grayscale glow halo
    oled.ellipse(CX, CY, FR + 5, FR + 5, 2)
    oled.ellipse(CX, CY, FR + 2, FR + 2, 5)
    oled.ellipse(CX, CY, FR,     FR,     15)

    er = {'scared': 12, 'surprised': 10, 'happy': 8, 'sleepy': 8}[expr]
    by = EY - er - 5   # brow y baseline

    # ── Eyebrows ──────────────────────────────────────────────────────────
    if expr == 'scared':
        # Angled inward — classic fear
        oled.line(ELX - 10, by - 5, ELX + 5, by, 15)
        oled.line(ERX - 5,  by,     ERX + 10, by - 5, 15)
    elif expr == 'surprised':
        # High flat arcs
        oled.hline(ELX - 9, by - 4, 18, 15)
        oled.hline(ERX - 9, by - 4, 18, 15)
    elif expr == 'happy':
        # Gentle raised arcs
        oled.ellipse(ELX, by, 9, 3, 15, False, 3)
        oled.ellipse(ERX, by, 9, 3, 15, False, 3)
    else:   # sleepy
        # Drooping outward
        oled.line(ELX - 9, by - 2, ELX + 9, by - 6, 15)
        oled.line(ERX - 9, by - 6, ERX + 9, by - 2, 15)

    # ── Eyes ──────────────────────────────────────────────────────────────
    if blink:
        _draw_closed_eye(oled, ELX, EY, er)
        _draw_closed_eye(oled, ERX, EY, er)
    elif expr == 'sleepy':
        _draw_half_eye(oled, ELX, EY, er)
        _draw_half_eye(oled, ERX, EY, er)
    else:
        _draw_eye(oled, ELX, EY, er, pdx, pdy)
        _draw_eye(oled, ERX, EY, er, pdx, pdy)

    # ── Nose (subtle dot) ─────────────────────────────────────────────────
    oled.fill_rect(CX - 1, CY - 2, 3, 3, 9)

    # ── Mouth ─────────────────────────────────────────────────────────────
    if expr == 'scared':
        # Wide-open O
        oled.ellipse(CX, MY + 2, 13, 16, 15, True)
        oled.ellipse(CX, MY + 2,  9, 12,  0, True)
    elif expr == 'surprised':
        # Oval O
        oled.ellipse(CX, MY, 9, 11, 15, True)
        oled.ellipse(CX, MY, 6,  8,  0, True)
    elif expr == 'happy':
        # Big curved smile (bottom two quadrants, mask=12)
        oled.ellipse(CX, MY - 2, 22, 13, 15, False, 12)
        oled.ellipse(CX, MY - 2, 20, 11,  8, False, 12)  # inner glow line
        # Rosy cheeks
        oled.ellipse(ELX - 6, MY - 4, 8, 4, 4, True)
        oled.ellipse(ERX + 6, MY - 4, 8, 4, 4, True)
    else:  # sleepy
        # Small lazy smile
        oled.ellipse(CX, MY + 4, 14, 7, 15, False, 12)

    # ── Floating ZZZ for sleepy ───────────────────────────────────────────
    if expr == 'sleepy':
        oled.text("z", CX + 32, zz_y,      10)
        oled.text("Z", CX + 41, zz_y - 11, 13)
        oled.text("Z", CX + 50, zz_y - 22, 15)

    # ── Distance label at bottom ──────────────────────────────────────────
    label = ("  " + dist_str)[-10:]   # right-align in 10 chars
    oled.text(dist_str, 2, 120, 7)


# ── Hardware init ────────────────────────────────────────────────────────────

i2c   = SoftI2C(scl=Pin("B8"), sda=Pin("B9"), freq=400_000)
oled  = SSD1327(i2c)
sonar = HCSR04(trig_pin="B10", echo_pin="C7")
imu   = MPU6050(i2c)

imu_ok = False
try:
    imu.init()
    imu_ok = True
except (MPU6050Error, OSError):
    pass    # face still runs; pupils just won't tilt

startup_animation(oled)

# Discard first sonar reading (cold-start)
utime.sleep_ms(100)
try:
    sonar.distance_cm()
except HCSR04Error:
    pass
utime.sleep_ms(60)

# ── Main loop ────────────────────────────────────────────────────────────────

frame    = 0
blink    = False
blink_cd = 25       # frames until next blink
zz_y     = 50       # ZZZ starting y (floats upward)
pdx = pdy = 0       # pupil offset from IMU
expr      = 'happy'

while True:
    utime.sleep_ms(100)

    # ── Read HC-SR04-R ──────────────────────────────────────────────────
    dist_str = "no echo"
    try:
        cm = sonar.distance_cm()
        if 2.0 <= cm <= 400.0:
            dist_str = "%.0f cm" % cm
            if   cm < 10:  expr = 'scared'
            elif cm < 40:  expr = 'surprised'
            elif cm < 90:  expr = 'happy'
            else:          expr = 'sleepy'
        else:
            expr = 'sleepy'
    except HCSR04Error:
        expr = 'sleepy'

    # ── Read MPU-6050 for pupil tilt ────────────────────────────────────
    if imu_ok:
        try:
            ax, ay, az, gx, gy, gz = imu.read_raw()
            # ax/ay range ±16384 at ±2g — map to ±4 px pupil shift
            pdx = _clamp(ax // 4096, -4, 4)
            pdy = _clamp(ay // 4096, -4, 4)
        except OSError:
            pass

    # ── Blink ───────────────────────────────────────────────────────────
    blink_cd -= 1
    if blink_cd <= 0:
        blink    = True
        blink_cd = 25 + (frame % 18)   # vary interval so it feels natural
    elif blink:
        blink = False   # blink lasts exactly one frame (~100 ms)

    # ── ZZZ float upward (resets when it scrolls off top of face) ───────
    if expr == 'sleepy':
        zz_y -= 1
        if zz_y < 28:
            zz_y = 55

    # ── Render ──────────────────────────────────────────────────────────
    draw_frame(oled, expr, blink, pdx, pdy, zz_y, dist_str)
    oled.show()
    led.toggle()
    frame += 1
