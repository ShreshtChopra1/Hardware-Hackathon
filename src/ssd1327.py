# ssd1327.py — SSD1327 128x128 4-bit grayscale OLED driver (I2C), MicroPython/STM32.
#
# Wiring (Waveshare 1.5" OLED, shares bus with MPU-6050):
#   VCC -> 3V3
#   GND -> GND
#   SCL -> D15 (PB8)   [shared with MPU-6050]
#   SDA -> D14 (PB9)   [shared with MPU-6050]
#
# I2C address : 0x3C (default, SA0 low)
# Resolution  : 128 x 128 pixels
# Grayscale   : 4-bit (0 = black, 15 = full brightness)
# Framebuf fmt: GS4_HMSB — high nibble = left pixel, low nibble = right pixel
# Buffer size : 128 * 128 / 2 = 8 192 bytes
import framebuf

WIDTH  = 128
HEIGHT = 128
ADDR   = 0x3C


class SSD1327(framebuf.FrameBuffer):

    def __init__(self, i2c, addr=ADDR):
        self.i2c  = i2c
        self.addr = addr
        self.buf  = bytearray(WIDTH * HEIGHT // 2)
        super().__init__(self.buf, WIDTH, HEIGHT, framebuf.GS4_HMSB)
        # Pre-allocated write buffer: control byte + 128 data bytes (avoids
        # per-call heap allocation during show()).
        self._wb    = bytearray(129)
        self._wb[0] = 0x40
        self._init()

    # --- Low-level helpers --------------------------------------------------

    def _cmd(self, *args):
        """Send one or more command bytes in a single I2C transaction."""
        self.i2c.writeto(self.addr, b'\x00' + bytes(args))

    # --- Initialisation sequence (Waveshare 1.5" SSD1327) -------------------

    def _init(self):
        self._cmd(0xAE)               # display off
        self._cmd(0x15, 0x00, 0x3F)  # column address: 0 – 63 (each addr = 2 px)
        self._cmd(0x75, 0x00, 0x7F)  # row address: 0 – 127
        self._cmd(0x81, 0x80)         # contrast
        self._cmd(0xA0, 0x51)         # remap: col remap + COM remap + split OE
        self._cmd(0xA1, 0x00)         # display start line = 0
        self._cmd(0xA2, 0x00)         # display offset = 0
        self._cmd(0xA4)               # normal display (not all-on / all-off / inverse)
        self._cmd(0xA8, 0x7F)         # multiplex ratio = 128
        self._cmd(0xB1, 0x51)         # phase 1 = 1 DCLK, phase 2 = 5 DCLKs
        self._cmd(0xB3, 0x01)         # clock: div=1, freq=default
        self._cmd(0xAB, 0x01)         # function A: internal VDD regulator on
        self._cmd(0xB6, 0x01)         # second pre-charge period
        self._cmd(0xBE, 0x07)         # VCOMH deselect level
        self._cmd(0xBC, 0x08)         # pre-charge voltage
        self._cmd(0xB9)               # linear grayscale LUT
        self._cmd(0xD5, 0x62)         # function B: VSL external, GPIO low
        self._cmd(0xFD, 0x12)         # unlock commands
        self._cmd(0xAF)               # display on

    # --- Public API ---------------------------------------------------------

    def show(self):
        """Flush the framebuffer to the display."""
        self._cmd(0x15, 0x00, 0x3F)   # reset column window
        self._cmd(0x75, 0x00, 0x7F)   # reset row window
        wb  = self._wb
        buf = self.buf
        for off in range(0, len(buf), 128):
            wb[1:] = buf[off:off + 128]
            self.i2c.writeto(self.addr, wb)

    def contrast(self, value):
        """Set brightness 0 (dimmest) – 255 (brightest)."""
        self._cmd(0x81, value & 0xFF)

    def invert(self, on):
        """Invert all pixel values on the panel."""
        self._cmd(0xA7 if on else 0xA4)

    def poweroff(self):
        self._cmd(0xAE)

    def poweron(self):
        self._cmd(0xAF)
