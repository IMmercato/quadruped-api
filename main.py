import serial
import time
import threading
from queue import Queue
from enum import Enum

PACKET_HEADER = bytes([0xAA, 0x55])
MAX_PAYLOAD_SIZE = 255

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
            ping_packet = self.create_packet(0x01)
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

if __name__ == "__main__":
    controller = QuadrupedController()

    if (controller.__init__):
        print("Connected successfully!")

        try:
            # LED ON
            controller.create_packet(0x01, bytes([0xFF]))
            time.sleep(1)

        except KeyboardInterrupt:
            print("\nStopping...")

        finally:
            controller.diconnect
    else:
        print("Failed to connect")