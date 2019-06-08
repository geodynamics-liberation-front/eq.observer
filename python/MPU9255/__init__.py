import smbus
import struct
import sys
import time
from . import register

ACCEL_SELF_TEST_X = 0b10000000
ACCEL_SELF_TEST_Y = 0b01000000
ACCEL_SELF_TEST_Z = 0b00100000
ACCEL_FS_SEL_2G   = 0b00000000
ACCEL_FS_SEL_4G   = 0b00001000
ACCEL_FS_SEL_8G   = 0b00010000
ACCEL_FS_SEL_16G  = 0b00011000

# PWR_MGMT_2
DISABLE_XA = 0b00100000
DISABLE_YA = 0b00010000
DISABLE_ZA = 0b00001000
DISABLE_XG = 0b00000100
DISABLE_YG = 0b00000010
DISABLE_ZG = 0b00000001

# Scale Values
SCALE_2G  =  2.0 / 0x7fff
SCALE_4G  =  4.0 / 0x7fff
SCALE_8G  =  8.0 / 0x7fff
SCALE_16G = 16.0 / 0x7fff

# I/O Structures
STRUCT_OUT = struct.Struct(">QBBBBBB")
STRUCT_IN = struct.Struct(">Qhhh")

# The default address for the MPU-2955 when the ADO pin is pulled low
ADDR = 0x68
# The i2c bus on the raspi /dev/ic2-1
BUS = 1

write_file = True

if "smbus" in sys.modules:
    bus = smbus.SMBus(BUS)


def binary(n, w=8):
    b = bin(n)[2:]
    return '0' * (w - len(b)) + b


def readUShort(register_high, register_low):
    return bus.read_byte_data(ADDR, register_high) << 8 | \
           bus.read_byte_data(ADDR, register_low)


def readShort(register_high, register_low):
    x = bus.read_byte_data(ADDR, register_high) << 8 | \
        bus.read_byte_data(ADDR, register_low)
    if (x & 0x8000 != 0):
        x -= 0x10000
    return x


def read(register):
    return bus.read_byte_data(ADDR, register)


def write(register, value):
    return bus.write_byte_data(ADDR, register, value)


def writeShort(register_high, register_low, value):
    write(register_high, value >> 8 & 0xff)
    write(register_low,  value       & 0xff)


def readAverage(func, n=1000):
    accumulator = 0
    for i in range(n):
        accumulator += func()
    return int(accumulator / n)


def readAccelX():
    return readShort(register.ACCEL_XOUT_H, register.ACCEL_XOUT_L)


def readAccelY():
    return readShort(register.ACCEL_YOUT_H, register.ACCEL_YOUT_L)


def readAccelZ():
    return readShort(register.ACCEL_ZOUT_H, register.ACCEL_ZOUT_L)


def configAccel(config):
    write(register.ACCEL_CONFIG, config)


def writeAccelOffsetX(offset):
    writeShort(register.XA_OFFSET_H, register.XA_OFFSET_L, offset)


def writeAccelOffsetY(offset):
    writeShort(register.YA_OFFSET_H, register.YA_OFFSET_L, offset)


def writeAccelOffsetZ(offset):
    writeShort(register.ZA_OFFSET_H, register.ZA_OFFSET_L, offset)


def readAccelOffsetX(offset):
    return readShort(register.XA_OFFSET_H, register.XA_OFFSET_L)


def readAccelOffsetY(offset):
    return readShort(register.YA_OFFSET_H, register.YA_OFFSET_L)


def readAccelOffsetZ(offset):
    return readShort(register.ZA_OFFSET_H, register.ZA_OFFSET_L)


def calculateOffset(offset_h, offset_l, readFunc, bias=0):
    offset = readUShort(offset_h, offset_l)
    print(("Current Offset : %d" % offset))
    configAccel(ACCEL_FS_SEL_16G)
    average = readAverage(readFunc, 1000) - bias
    print(("16g  : %d" % average))
    # bit 0 is reserved so don't change it
    offset -= (average & ~1)
    print(("Calibrated Offset : %d" % offset))
    return offset


def calibrateAccelX():
    writeAccelOffsetX(
        calculateOffset(
            register.XA_OFFSET_H, register.XA_OFFSET_L, readAccelX
        )
    )


def calibrateAccelY():
    writeAccelOffsetY(
        calculateOffset(
            register.YA_OFFSET_H, register.YA_OFFSET_L, readAccelY
        )
    )


def calibrateAccelZ():
    writeAccelOffsetZ(
        calculateOffset(
            register.ZA_OFFSET_H, register.ZA_OFFSET_L, readAccelZ, 0x7ff
        )
    )


def writeAccelData():
    write_file = True
    configAccel(ACCEL_FS_SEL_2G)
    start = time.time()
    file_time = int(start / 600) * 600
    f = open(" % d.bin" % file_time, "ab")
    while write_file:
        f.write(
            STRUCT_OUT.pack(
                int(1000 * time.time()),
                bus.read_byte_data(ADDR, register.ACCEL_XOUT_H),
                bus.read_byte_data(ADDR, register.ACCEL_XOUT_L),
                bus.read_byte_data(ADDR, register.ACCEL_YOUT_H),
                bus.read_byte_data(ADDR, register.ACCEL_YOUT_L),
                bus.read_byte_data(ADDR, register.ACCEL_ZOUT_H),
                bus.read_byte_data(ADDR, register.ACCEL_ZOUT_L)
            )
        )
        if time.time() - file_time > 600:
            f.close()
            file_time = int(time.time() / 600) * 600
            f = open(" % d.bin" % file_time, "ab")
    end = time.time()
    f.close()
    print(("Wrote 1000 records in %f seconds" % (end - start)))


def readAccelData():
    f = open('data.bin', 'rb')
    start = time.time()
    record = f.read(STRUCT_IN.size)
    records = []
    while record:
        t, x, y, z = STRUCT_IN.unpack(record)
        records.append([t, x, y, z])
        print((" % d: %f, %f, %f" %
              (t, x * SCALE_2G, y * SCALE_2G, z * SCALE_2G)))
        record = f.read(STRUCT_IN.size)
    end = time.time()
    f.close()
    print(("Read 1000 records in %f seconds" % (end - start)))
    return records


def printXYZ():
    data = (int(1000 * time.time()), readAccelX(), readAccelY(), readAccelZ())
    print((" % d : %d, %d, %d" % data))


def printAccelOffsets():
    offsetX = readShort(register.XA_OFFSET_H, register.XA_OFFSET_L)
    offsetY = readShort(register.YA_OFFSET_H, register.YA_OFFSET_L)
    offsetZ = readShort(register.ZA_OFFSET_H, register.ZA_OFFSET_L)
    print(("Offset X : %d" % offsetX))
    print(("Offset Y : %d" % offsetY))
    print(("Offset Z : %d" % offsetZ))


def test():
    print("Offsets:")
    printAccelOffsets()
    print("Config Flags:")
    print(("2g  : %s" % binary(ACCEL_FS_SEL_2G)))
    print(("4g  : %s" % binary(ACCEL_FS_SEL_4G)))
    print(("8g  : %s" % binary(ACCEL_FS_SEL_8G)))
    print(("16g : %s" % binary(ACCEL_FS_SEL_16G)))

    print("Accel Data:")
    configAccel(ACCEL_FS_SEL_2G)
    xyz = (
            readAverage(readAccelX, 100),
            readAverage(readAccelY, 100),
            readAverage(readAccelZ, 100)
          )
    print(("2g  : %d, %d, %d" % xyz))

    configAccel(ACCEL_FS_SEL_4G)
    xyz = (
            readAverage(readAccelX, 100),
            readAverage(readAccelY, 100),
            readAverage(readAccelZ, 100)
          )
    print(("4g  : %d, %d, %d" % xyz))

    configAccel(ACCEL_FS_SEL_8G)
    xyz = (
            readAverage(readAccelX, 100),
            readAverage(readAccelY, 100),
            readAverage(readAccelZ, 100)
          )
    print(("8g  : %d, %d, %d" % xyz))

    configAccel(ACCEL_FS_SEL_16G)
    xyz = (
            readAverage(readAccelX, 100),
            readAverage(readAccelY, 100),
            readAverage(readAccelZ, 100)
          )
    print(("16g : %d, %d, %d" % xyz))
