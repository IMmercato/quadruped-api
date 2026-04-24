import smbus
import serial
import time

# I2C Setup
SLAVE_ADDR = 0x08
bus = smbus.SMBus(1)

# UART Setup
ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)

def main():
    print("Starting I2C + UART Test...")
    led_state = True

    try:
        while True:
            # 1. I2C COMMUNICATION (Control LED)
            cmd = '1' if led_state else '0'
            bus.write_byte(SLAVE_ADDR, ord(cmd))
            print(f"Sent I2C: LED {'ON' if led_state else 'OFF'}")

            # 2. UART COMMUNICATION (Send/Receive Text)
            ser.write(f"Ping {time.time()}\n".encode())
            
            # Read response if available
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
                print(f"UART Response: {response}")

            # Toggle state and wait
            led_state = not led_state
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()