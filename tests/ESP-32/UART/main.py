import sys
import serial
import time

# UART configuration
SERIAL_PORT = '/dev/serial0'  # or '/dev/ttyAMA0'
BAUD_RATE = 115200
TIMEOUT = 1  # seconds

def send_command(command):
    try:
        # Open serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        time.sleep(0.1)  # Wait for connection to stabilize
        
        # Clear any pending data
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Send command
        if command == "on":
            ser.write(b'1')
            print("Sent: LED ON")
        elif command == "off":
            ser.write(b'0')
            print("Sent: LED OFF")
        else:
            print(f"Invalid command: {command}")
            ser.close()
            return False
        
        # Wait for response
        time.sleep(0.1)
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(f"Response: {response}")
        
        ser.close()
        return True
        
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        print(f"Make sure UART is enabled and ESP32 is connected")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <on|off>")
        print("Example: python main.py on")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command not in ["on", "off"]:
        print("Invalid command. Use 'on' or 'off'")
        sys.exit(1)
    
    success = send_command(command)
    sys.exit(0 if success else 1)