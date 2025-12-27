import serial
import time
import threading
import socket
import os
from queue import Queue
from enum import Enum
from typing import Dict, Optional, Tuple

PACKET_HEADER = bytes([0xAA, 0x55])
MAX_PAYLOAD_SIZE = 255

class CommandID(Enum):
    """Command IDs for communication protocol"""
    # Basic Commands
    PING = 0x01
    LED_CONTROL = 0x02

    # Servo Commands
    # Sensor Commands

    # Emergency
    EMERGENCY_STOP = 0xFF

class QuadrupedController:
    def __init__(self, port='/dev/serial0', baud_rate=115200, timeout=0.1):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.ser = None
        self.connected = False

        # Communication queues
        self.command_queue = Queue(maxsize=100)
        self.response_queue = Queue(maxsize=100)
        
        # Threads
        self.send_thread = None
        self.receive_thread = None
        self.running = False

        # State tracking
        self.last_battery_voltage = 0.0
        self.error_count = 0

        #Statistics
        self.packets_sent = 0
        self.packets_received = 0
        self.checksum_errors = 0
        
    def create_packet(self, command_id: int, payload: bytes = b'') -> bytes:
        """
        Create a packet with header, command, length, payload, and checksum

        Packet structure:
        [HEADER(2)] [COMMAND_ID(1)] [LENGTH(1)] [PAYLOAD(0-255)] [CHECKSUM(1)]

        Look at this protocol: https://github.com/IMmercato/quadruped-api/tree/main/protocol
        """
        if len(payload) > MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload too large: {len(payload)} > {MAX_PAYLOAD_SIZE}")
        
        packet = PACKET_HEADER + bytes([command_id, len(payload)]) + payload

        # XOR checksum
        checksum = 0
        for byte in packet:
            checksum ^= byte

        return packet + bytes([checksum])
    
    def parse_packet(self, data: bytes) -> Optional[Tuple[int, bytes]]:
        """
        Parse received packet and validate checksum

        Returns: (command_id, payload) or None if invalid
        """
        if len(data) < 5:   # Minimum packet size
            return None
        
        # Verify header
        if data[0:2] != PACKET_HEADER:
            return None
        
        command_id = data[2]
        payload_length = data[3]

        # Check paacket length
        expected_length = 4 + payload_length + 1    # header(2) + cmd(1) + len(1) + payload + checksum(1)
        if len(data) < expected_length:
            return None
        
        # Verify checksum
        received_checksum = data[expected_length - 1]
        calculated_checksum = 0
        for byte in data[:expected_length - 1]:
            calculated_checksum ^= byte

        if received_checksum != calculated_checksum:
            self.checksum_errors += 1
            print(f"Checksum error: expected {calculated_checksum:02X}, got {received_checksum:02X}")
            return None
        
        # Extract payload
        payload = data[4:4 + payload_length]
        return (command_id, payload)

    def connect(self) -> bool:
        """Establish UART connection with Slave"""
        try:
            self.ser = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=self.timeout,
                write_timeout=1.0
            )
            time.sleep(0.2)

            # Clear buffers
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            # PING
            ping_packet = self.create_packet(CommandID.PING.value)
            self.ser.write(ping_packet)
            self.ser.flush()

            # response
            start_time = time.time()
            while time.time() - start_time < 3.0:
                if self.ser.in_waiting >= 5:
                    response = self.ser.read(self.ser.in_waiting)
                time.sleep(0.1)

            print("Warning: No ping response from Slave, but continuing...")
            self.connected = True
            self._start_threads()
            return True
        except serial.SerialException as e:
            print(f"Connection failed: {e}")
            return False
        
    def disconnect(self):
        """Close connection and stop threads"""
        self.running = False

        if self.send_thread:
            self.send_thread.join(timeout=2.0)
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)

        if self.ser and self.ser.is_open:
            self.ser.close()
        
        self.connected = False
        print("Disconnectedfrom Slave")

    def _start_threads(self):
        """Start communication threads: send & receive"""
        self.running = True
        self.send_thread = threading.Thread(target=self._send_worker, daemon=True)
        self.receive_thread = threading.Thread(target=self._receive_worker, daemon=True)
        # Start Threads
        self.send_thread.start()
        self.receive_thread.start()

    def _send_worker(self):
        """Thread for sending commands to Slave"""
        while self.running:
            try:
                if not self.command_queue.empty():
                    packet = self.command_queue.get(timeout=0.1)
                    self.ser.write(packet)
                    self.ser.flush()
                    self.packets_sent += 1
                else:
                    time.sleep(0.001)
            except Exception as e:
                print(f"Send thread error: {e}")
                self.error_count += 1

    def _receive_worker(self):
        """Thread for receiving responses from Slave"""
        buffer = bytearray()

        while self.running:
            try:
                if self.ser and self.ser.in_waiting:
                    # Read available data
                    data = self.ser.read(self.ser.in_waiting)
                    buffer.extend(data)

                    # Try to find and parse packets
                    while len(buffer) >= 5:
                        # Look for packets header
                        header_index = buffer.find(PACKET_HEADER)

                        if header_index == -1:
                            buffer.clear()
                            break

                        # Remove data before header
                        if header_index > 0:
                            buffer = buffer[header_index:]

                        # Check if we have enough data for length field
                        if len(buffer) < 4:
                            break

                        payload_length = buffer[3]
                        packet_length = 4 + payload_length + 1

                        # Wait for complete packet
                        if len(buffer) < packet_length:
                            break

                        # Extract and parse packet
                        packet = bytes(buffer[:packet_length])
                        result = self.parse_packet(packet)

                        if result:
                            self.packets_received += 1
                            self._process_response(result[0], result[1])

                        # Remove processed packet from buffer
                        buffer = buffer[packet_length:]
                else:
                    time.sleep(0.001)

            except Exception as e:
                print(f"Receive thread error: {e}")
                self.error_count += 1

    def _process_response(self, command_id: int, payload: bytes):
        """Process parsed response packet"""
        try:
            # Process the payload as you need to
            if command_id == CommandID.x.value:
                if len(payload) >= 3:
                    servo_id = payload[0]
        
            # Store response for user retrival
            self.response_queue.put({
                'command_id': command_id,
                'payload': payload,
                'timestamp': time.time()
            })

        except Exception as e:
            print(f"Error processing response: {e}")

    # LED Control - TEST
    def led_control(self, state: bool) -> bool:
        """Control LED on/off"""
        if not self.connected:
            print("Not connected to Slave")
            return False
        
        payload = bytes([0xFF if state else 0x00])
        packet = self.create_packet(CommandID.LED_CONTROL.value, payload)

        try:
            self.command_queue.put(packet, timeout=0.5)
            return True
        except:
            print("Command queue full")
            return False

    def emergency_stop(self) -> bool:
        """Immediately stop all motors"""
        if not self.connected:
            return False
        
        packet = self.create_packet(CommandID.EMERGENCY_STOP.value)

        # High priority - send immediately without queue
        try:
            self.ser.write(packet)
            self.ser.flush()
            return True
        except:
            return False

    def get_status(self) -> Dict:
        """Get overall system status"""
        return {
            'connected': self.connected,
            'error_count': self.error_count,
            'packets_sent': self.packets_sent,
            'checksum_errors': self.checksum_errors,
            'command_queue_size': self.command_queue.qsize(),
            'response_queue_size': self.response_queue.qsize(),
            'battery_voltage': self.last_battery_voltage
        }
    
    # Socket listener
    def run_ipc_server(controller):
        """Listens for commands from the Node.js server without closing the UART"""
        server_address = '/tmp/quadruped_sock'

        # Clean up the socket file
        if os.path.exists(server_address):
            os.remove(server_address)

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(server_address)
        sock.listen(1)

        print(f"IPC Server started at {server_address}")

        try:
            while True:
                connection, client_address = sock.accept()
                try:
                    data = connection.recv(1024).decode('utf-8').strip()
                    if not data: continue

                    print(f"IPC Received: {data}")

                    # Logic to route commands to your controller
                    if data == "on":
                        controller.led_control(True)
                    elif data == "off":
                        controller.led_control(False)
                    elif data == "stop":
                        controller.emergency_stop()

                    connection.sendall(b"OK")
                finally:
                    connection.close()
        except KeyboardInterrupt:
            pass
        finally:
            os.remove(server_address)

if __name__ == "__main__":
    controller = QuadrupedController('/dev/serial0', 115200)

    if controller.connect():
        print("Connected successfully!")
        print(f"Initial status: {controller.get_status()}")

        controller.run_ipc_server(controller)

        """
        try:
            # LED Control
            print("\n--- LED Test ---")
            controller.led_control(True)
            time.sleep(1)
            controller.led_control(False)
            time.sleep(1)

            # Final status
            print(f"\nFinal status: {controller.get_status()}")

        except KeyboardInterrupt:
            print("\nStopping...")
            controller.emergency_stop()

        finally:
            controller.disconnect()
        """
    else:
        print("Failed to connect")