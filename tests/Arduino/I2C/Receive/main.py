import smbus
import time

SLAVE_ADDR = 0x08
I2C_BUS = 1
MAX_LEN = 32

bus = smbus.SMBus(I2C_BUS)

def send_and_receive(message):
    # 1. Send string to Arduino
    # smbus automatically prepends a "register" byte (0x00 here)
    data = [ord(c) for c in message]
    bus.write_i2c_block_data(SLAVE_ADDR, 0x00, data)
    
    # 2. Give Arduino loop() time to process and prepare txBuffer
    time.sleep(0.05)
    
    # 3. Request response (fixed length)
    raw_bytes = bus.read_i2c_block_data(SLAVE_ADDR, 0x00, MAX_LEN)
    
    # 4. Decode & clean null padding
    response = bytes(raw_bytes).decode('utf-8', errors='ignore').rstrip('\x00')
    return response

try:
    while True:
        msg = "Hello from RPi5!"
        resp = send_and_receive(msg)
        print(f"Sent: '{msg}' | Received: '{resp}'")
        time.sleep(1)
        
except KeyboardInterrupt:
    bus.close()
    print("\nI2C communication stopped.")
except Exception as e:
    bus.close()
    print(f"\nError: {e}")