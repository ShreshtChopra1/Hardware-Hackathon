# mpu6050.py — InvenSense MPU-6050 6-axis IMU driver (I2C), MicroPython / STM32.
#
# 7-bit address 0x68 (AD0 low). Raw int16 readings only for now; scaling and
# filtering come in a later phase. Takes any object with the standard
# machine.I2C / SoftI2C readfrom_mem / writeto_mem API.
#
# Sensitivity at the default ranges (for when we add scaling later):
#   accel +/-2 g    -> 16384 LSB/g
#   gyro  +/-250 dps -> 131 LSB/(deg/s)
import struct

# 7-bit I2C address with AD0 tied low.
ADDR = 0x68

# Register map (subset).
_PWR_MGMT_1   = 0x6B
_CONFIG       = 0x1A   # DLPF config
_GYRO_CONFIG  = 0x1B   # gyro full-scale range
_ACCEL_CONFIG = 0x1C   # accel full-scale range
_WHO_AM_I     = 0x75
_ACCEL_XOUT_H = 0x3B   # first of 14 data bytes

_WHO_AM_I_EXPECTED = 0x68


class MPU6050Error(Exception):
    """Raised when WHO_AM_I does not match (wrong/missing device)."""


class MPU6050:
    def __init__(self, i2c, addr=ADDR):
        self.i2c = i2c
        self.addr = addr

    def init(self):
        """Probe WHO_AM_I, wake the device, set accel +/-2g / gyro +/-250dps.

        Raises MPU6050Error on identity mismatch; I2C transfer failures
        propagate as OSError.
        """
        who = self.i2c.readfrom_mem(self.addr, _WHO_AM_I, 1)[0]
        if who != _WHO_AM_I_EXPECTED:
            raise MPU6050Error("WHO_AM_I=0x%02x (expected 0x68)" % who)

        # Wake from sleep: clear SLEEP bit, select internal 8 MHz oscillator.
        self.i2c.writeto_mem(self.addr, _PWR_MGMT_1, b"\x00")
        # DLPF ~44 Hz (accel) / 42 Hz (gyro) to cut noise.
        self.i2c.writeto_mem(self.addr, _CONFIG, b"\x03")
        # Gyro full scale +/-250 dps.
        self.i2c.writeto_mem(self.addr, _GYRO_CONFIG, b"\x00")
        # Accel full scale +/-2 g.
        self.i2c.writeto_mem(self.addr, _ACCEL_CONFIG, b"\x00")

    def read_raw(self):
        """Burst-read all six axes; returns (ax, ay, az, gx, gy, gz) as int16.

        14-byte read from ACCEL_XOUT_H. Layout (big-endian, H then L):
          accel X/Y/Z (0x3B-0x40), temp (0x41-0x42, skipped), gyro X/Y/Z (0x43-0x48).
        """
        d = self.i2c.readfrom_mem(self.addr, _ACCEL_XOUT_H, 14)
        ax, ay, az, _temp, gx, gy, gz = struct.unpack(">hhhhhhh", d)
        return ax, ay, az, gx, gy, gz
