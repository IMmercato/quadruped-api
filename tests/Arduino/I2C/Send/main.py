import smbus
import time

SLAVE_ADDR = 0x08
I2C_BUS = 1

bus = smbus.SMBus(I2C_BUS)

def send_string(address, message):
        data = [ord(c) for c in message]
        bus.write_i2c_block_data(address, 0, data)

try:
        while True:
                send_string(SLAVE_ADDR, "Hello")
                print("Sent: Hello")
                time.sleep(1)
except KeyboardInterrupt:
        bus.close()
        print("i2c communication stopped.")