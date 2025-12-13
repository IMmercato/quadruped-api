import sys
import smbus

I2C_ADDR = 0x08
bus = smbus.SMBus(1)

angle = int(sys.argv[1])
angle = max(0, min(180, angle))

bus.write_byte(I2C_ADDR, angle)

print(f"Sent angle {angle}")