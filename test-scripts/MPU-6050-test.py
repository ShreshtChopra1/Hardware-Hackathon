# MPU-6050 read test for NUCLEO-G474RE (MicroPython)
#
# Wiring (Arduino-style headers on the Nucleo-64):
#   MPU6050 SCL -> D15 (PB8, I2C1_SCL)
#   MPU6050 SDA -> D14 (PB9, I2C1_SDA)
#   MPU6050 INT -> D2  (PA10)
#   MPU6050 VCC -> 3V3
#   MPU6050 GND -> GND
#
# Run once without persisting:
#   mpremote connect /dev/cu.usbmodem11103 run test-scripts/MPU-6050-test.py
# Or deploy as main.py:
#   mpremote connect /dev/cu.usbmodem11103 cp test-scripts/MPU-6050-test.py :main.py

import time
from machine import I2C, Pin

# --- MPU-6000/6050 registers (datasheet RM-MPU-6000A, sections 4.x) ---
MPU_ADDR     = 0x68    # 7-bit I2C address with AD0 tied to GND (0x69 if AD0 = VCC)

SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B    # FS_SEL in bits [4:3]
ACCEL_CONFIG = 0x1C    # AFS_SEL in bits [4:3]
INT_PIN_CFG  = 0x37
INT_ENABLE   = 0x38
INT_STATUS   = 0x3A
ACCEL_XOUT_H = 0x3B    # start of 14-byte sensor block: AX, AY, AZ, TEMP, GX, GY, GZ
PWR_MGMT_1   = 0x6B
WHO_AM_I     = 0x75    # reads back 0x68 for a healthy MPU-6050

# Sensitivities for the default full-scale ranges we set below
ACCEL_LSB_PER_G   = 16384.0   # AFS_SEL = 0  -> ±2g
GYRO_LSB_PER_DPS  = 131.0     # FS_SEL  = 0  -> ±250 °/s


def _s16_be(buf, off):
    """Decode a big-endian signed 16-bit value out of a bytes-like buffer."""
    val = (buf[off] << 8) | buf[off + 1]
    return val - 0x10000 if val & 0x8000 else val


def mpu_init(i2c):
    who = i2c.readfrom_mem(MPU_ADDR, WHO_AM_I, 1)[0]
    if who != 0x68:
        raise OSError("MPU-6050 not responding correctly (WHO_AM_I=0x{:02x}, expected 0x68)".format(who))

    # Wake the device (PWR_MGMT_1.SLEEP defaults to 1 at boot) and select the
    # PLL with X-gyro reference as the clock source — more stable than the
    # internal 8 MHz oscillator.
    i2c.writeto_mem(MPU_ADDR, PWR_MGMT_1, b"\x01")
    time.sleep_ms(50)

    # Sample-rate divider: gyro output rate is 1 kHz when DLPF is enabled
    # below, so SMPLRT_DIV = 7 gives 1 kHz / (1 + 7) = 125 Hz.
    i2c.writeto_mem(MPU_ADDR, SMPLRT_DIV, b"\x07")
    # DLPF_CFG = 3 -> ~44 Hz accel / 42 Hz gyro bandwidth.
    i2c.writeto_mem(MPU_ADDR, CONFIG,      b"\x03")
    # Default full-scale ranges: ±250 °/s gyro, ±2g accel.
    i2c.writeto_mem(MPU_ADDR, GYRO_CONFIG,  b"\x00")
    i2c.writeto_mem(MPU_ADDR, ACCEL_CONFIG, b"\x00")

    # INT pin: active-high, push-pull, latched until INT_STATUS is read.
    # Enable DATA_RDY interrupt so the INT line tracks sample availability.
    i2c.writeto_mem(MPU_ADDR, INT_PIN_CFG, b"\x20")  # LATCH_INT_EN = 1
    i2c.writeto_mem(MPU_ADDR, INT_ENABLE,  b"\x01")  # DATA_RDY_EN  = 1


def mpu_read(i2c):
    """Burst-read all 14 sensor bytes in one transaction and decode them."""
    buf = i2c.readfrom_mem(MPU_ADDR, ACCEL_XOUT_H, 14)
    ax = _s16_be(buf,  0) / ACCEL_LSB_PER_G
    ay = _s16_be(buf,  2) / ACCEL_LSB_PER_G
    az = _s16_be(buf,  4) / ACCEL_LSB_PER_G
    # Temperature formula from datasheet section 4.19.
    temp_c = _s16_be(buf, 6) / 340.0 + 36.53
    gx = _s16_be(buf,  8) / GYRO_LSB_PER_DPS
    gy = _s16_be(buf, 10) / GYRO_LSB_PER_DPS
    gz = _s16_be(buf, 12) / GYRO_LSB_PER_DPS
    return ax, ay, az, temp_c, gx, gy, gz


def main():
    # Hardware I2C1: SCL=PB8 (D15), SDA=PB9 (D14). 400 kHz fast-mode.
    i2c = I2C(1, freq=400_000)
    int_pin = Pin("A10", Pin.IN, Pin.PULL_DOWN)  # D2

    print("I2C scan:", [hex(d) for d in i2c.scan()])
    mpu_init(i2c)
    print("MPU-6050 initialized. Streaming at ~10 Hz. Ctrl-C to stop.")
    print("{:>8} {:>8} {:>8}  {:>6}  {:>8} {:>8} {:>8}  {:>3}".format(
        "ax[g]", "ay[g]", "az[g]", "T[C]", "gx[dps]", "gy[dps]", "gz[dps]", "INT"))

    while True:
        ax, ay, az, t, gx, gy, gz = mpu_read(i2c)
        # Reading the sensor block also clears the latched DATA_RDY interrupt.
        print("{:>8.3f} {:>8.3f} {:>8.3f}  {:>6.2f}  {:>8.2f} {:>8.2f} {:>8.2f}  {:>3d}".format(
            ax, ay, az, t, gx, gy, gz, int_pin.value()))
        time.sleep_ms(100)


if __name__ == "__main__":
    main()
