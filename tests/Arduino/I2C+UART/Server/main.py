import smbus
import serial
import time
import socket
import os

# Configuration
I2C_ADDR = 0x08
I2C_BUS = 1
UART_PORT = '/dev/ttyAMA0'
SOCKET_PATH = '/tmp/quadruped_sock'  # Must match server.js

# Initialize Hardware
bus = smbus.SMBus(I2C_BUS)
ser = serial.Serial(UART_PORT, 9600, timeout=1)

def handle_command(command):
    """Routes server commands to I2C and UART"""
    print(f"Received from Server: {command}")
    
    if command == "on":
        # 1. Send to Arduino via I2C
        bus.write_byte(I2C_ADDR, ord('1'))
        # 2. Send status via UART
        ser.write(b"CMD: LED_ON\n")
        return "LED Turned On"
    
    elif command == "off":
        # 1. Send to Arduino via I2C
        bus.write_byte(I2C_ADDR, ord('0'))
        # 2. Send status via UART
        ser.write(b"CMD: LED_OFF\n")
        return "LED Turned Off"
    
    return "Unknown Command"

def main():
    # Clean up old socket if it exists
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    # Create Unix Socket
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(1)
    
    print(f"Python Listener Active at {SOCKET_PATH}...")

    try:
        while True:
            conn, _ = server.accept()
            try:
                # Receive command from Node.js (server.js)
                data = conn.recv(1024).decode('utf-8').strip()
                if data:
                    result = handle_command(data)
                    
                    # Optional: Read Arduino UART response to prove connection
                    if ser.in_waiting > 0:
                        arduino_reply = ser.readline().decode('utf-8').strip()
                        print(f"Arduino UART says: {arduino_reply}")
                    
                    # Send response back to Node.js
                    conn.sendall(result.encode())
            finally:
                conn.close()

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.close()
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        ser.close()

if __name__ == "__main__":
    main()