import sys
import smbus

I2C_ADDR = 0x08
bus = smbus.SMBus(1)

if len(sys.argv) < 2:
    print("Usage: python main.py <on|off>")
    sys.exit(1)

state = sys.argv[1].lower()

if state == "on":
    bus.write_byte(I2C_ADDR, 1)
    print("LED ON")
elif state == "off":
    bus.write_byte(I2C_ADDR, 0)
    print("LED OFF")
else:
    print("Invalid command. Use 'on' or 'off'")