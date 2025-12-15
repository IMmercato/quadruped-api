# ESP32 UART Communication Test

This test demonstrates UART (serial) communication between a Raspberry Pi 5 and an ESP32 microcontroller for controlling the built-in LED.

## Overview

This setup establishes bidirectional UART communication using custom GPIO pins on the ESP32 (UART2) to avoid conflicts with the USB serial debugging interface (UART0).

### Communication Flow

```
┌─────────────────┐         ┌─────────────────┐
│ Raspberry Pi 5  │  UART   │     ESP32       │
│                 │ ◄─────► │                 │
│  Python Script  │ 115200  │  Arduino Code   │
│                 │  baud   │                 │
└─────────────────┘         └────────┬────────┘
                                     │
                                     ▼
                                  LED GPIO2
```

## Hardware Connections

### Wiring Diagram

```
┌─────────────────────────┐         ┌──────────────────────┐
│    Raspberry Pi 5       │         │       ESP32          │
│                         │         │                      │
│  GPIO 14 (TXD) Pin 8 ───┼─────────┼───→ GPIO 16 (RX)     │
│  GPIO 15 (RXD) Pin 10───┼─────────┼───→ GPIO 17 (TX)     │
│  GND           Pin 6 ───┼─────────┼───→ GND              │
│  5V            Pin 2 ───┼─────────┼───→ VIN (or 3.3V)    │
│                         │         │                      │
└─────────────────────────┘         │  GPIO 2 ──→ LED      │
                                    │  (built-in)          │
                                    └──────────────────────┘
```

### Pin Mapping

| Raspberry Pi 5 | Physical Pin | ESP32 | Function |
|----------------|--------------|-------|----------|
| GPIO 14 (TX)   | Pin 8        | GPIO 16 (RX) | Pi transmits → ESP32 receives |
| GPIO 15 (RX)   | Pin 10       | GPIO 17 (TX) | Pi receives ← ESP32 transmits |
| GND            | Pin 6        | GND | Common ground (CRITICAL) |
| 5V             | Pin 2        | VIN | Power supply |

### Important Notes

- **TX → RX Connection**: Raspberry Pi TX goes to ESP32 RX
- **RX → TX Connection**: Raspberry Pi RX goes to ESP32 TX
- **Common Ground**: Essential for proper communication
- **Baud Rate**: 115200 (must match on both devices)
- **Logic Levels**: Both use 3.3V logic - no level shifter needed
- **UART2**: ESP32 uses UART2 to keep UART0 free for USB debugging

## Prerequisites

### Raspberry Pi Setup

1. **Enable UART interface:**
```bash
sudo raspi-config
# Navigate to: Interface Options → Serial Port
# Login shell over serial: NO
# Serial port hardware enabled: YES
```

2. **Install Python serial library:**
```bash
pip install pyserial
```

3. **Verify UART device:**
```bash
ls -l /dev/serial0
# Should show: /dev/serial0 -> ttyAMA0
```

4. **Add user to dialout group:**
```bash
sudo usermod -a -G dialout $USER
# Logout and login again
```

### ESP32 Setup

1. **Install Arduino IDE** (if not already installed)
2. **Add ESP32 board support:**
   - File → Preferences → Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
3. **Install ESP32 boards:**
   - Tools → Board → Boards Manager → Search "ESP32" → Install

## Installation

### 1. Upload ESP32 Firmware

1. Open `main.ino` in Arduino IDE
2. Select your ESP32 board:
   - Tools → Board → ESP32 Arduino → ESP32 Dev Module
3. Select the correct port:
   - Tools → Port → `/dev/ttyUSB0` (or similar)
4. Upload the sketch (Ctrl+U)

### 2. Verify ESP32 Operation

Open Serial Monitor (115200 baud) - you should see:
```
=== ESP32 UART Slave Ready (UART2) ===
RX: GPIO16, TX: GPIO17
Baud: 115200
Commands: '1' = ON, '0' = OFF
ESP32_READY_UART2
```

The LED should blink 3 times on startup.

### 3. Test from Raspberry Pi

Make the Python script executable:
```bash
chmod +x main.py
```

## Usage

### Command Syntax

```bash
python main.py <command>
```

**Available Commands:**
- `on` - Turn LED on
- `off` - Turn LED off

### Examples

**Turn LED ON:**
```bash
python main.py on
```

Expected output:
```
Sent: LED ON
Response: OK:LED_ON
```

**Turn LED OFF:**
```bash
python main.py off
```

Expected output:
```
Sent: LED OFF
Response: OK:LED_OFF
```

### Integration with API Server

The main API server (`server.js`) calls this Python script:

```javascript
app.post("/api/tests/led", (req, res) => {
    const { state } = req.body;
    
    execFile("python", ["tests/ESP-32/UART/main.py", state], 
        (error, stdout, stderr) => {
            if (error) {
                return res.status(500).json({ error: "Script failed" });
            }
            res.json({ ok: true, output: stdout.trim() });
        }
    );
});
```

Test via REST API:
```bash
curl -X POST http://localhost:3000/api/tests/led \
  -H "Content-Type: application/json" \
  -d '{"state":"on"}'
```

## Communication Protocol

### Command Format

Commands are sent as single ASCII characters:
- `'1'` (0x31) - Turn LED ON
- `'0'` (0x30) - Turn LED OFF

### Response Format

ESP32 responds with human-readable status messages:
- `OK:LED_ON` - LED successfully turned on
- `OK:LED_OFF` - LED successfully turned off
- `ERROR:UNKNOWN_COMMAND` - Invalid command received

### Data Flow

```
Raspberry Pi                    ESP32
     │                           │
     │───── '1' (LED ON) ───────►│
     │                           │ [Turn on LED]
     │◄──── "OK:LED_ON" ─────────│
     │                           │
     │───── '0' (LED OFF) ───────►│
     │                           │ [Turn off LED]
     │◄──── "OK:LED_OFF" ────────│
     │                           │
```

## File Structure

```
tests/ESP-32/UART/
├── README.md           # This file
├── diagram.md          # Wiring diagram
├── main.py            # Python control script (Raspberry Pi)
├── main.c             # Arduino source code (for reference)
└── main/
    └── main.ino       # Arduino sketch (ESP32)
```

## Troubleshooting

### Issue: "Serial error: [Errno 2] could not open port"

**Solution:**
```bash
# Check if UART is enabled
ls -l /dev/serial0

# If not found, enable in raspi-config
sudo raspi-config

# Add user to dialout group
sudo usermod -a -G dialout $USER
# Logout and login
```

### Issue: "Permission denied: '/dev/serial0'"

**Solution:**
```bash
sudo chmod 666 /dev/serial0
# Or add user to dialout group (preferred)
sudo usermod -a -G dialout $USER
```

### Issue: No response from ESP32

**Checks:**
1. Verify wiring (especially GND connection)
2. Check TX→RX and RX→TX are crossed correctly
3. Ensure ESP32 is powered and sketch is uploaded
4. Monitor ESP32 Serial Monitor for debug messages
5. Verify baud rate matches (115200)

### Issue: Garbage characters on serial

**Causes & Solutions:**
- **Baud rate mismatch**: Ensure both devices use 115200
- **Loose connections**: Check all wires are firmly connected
- **Power issues**: Ensure stable 5V power supply to ESP32

### Issue: ESP32 not detected in Arduino IDE

**Solution:**
1. Install CP210x or CH340 USB-to-Serial drivers
2. Check USB cable (must support data, not just power)
3. Press BOOT button while uploading if needed

## Testing Guide

### Step-by-Step Test

1. **Upload ESP32 code:**
   ```bash
   # Open main.ino in Arduino IDE and upload
   ```

2. **Open Serial Monitor** (115200 baud) to verify ESP32 startup

3. **Test from Python:**
   ```bash
   python main.py on
   # LED should turn on
   
   python main.py off
   # LED should turn off
   ```

4. **Check both outputs:**
   - Raspberry Pi terminal shows command sent and response
   - ESP32 Serial Monitor shows command received and LED status

### Expected Behavior

✅ **Success indicators:**
- LED blinks 3 times on ESP32 startup
- Python script prints command sent and response received
- LED turns on/off as commanded
- No error messages

❌ **Failure indicators:**
- Timeout errors in Python
- No response from ESP32
- LED doesn't respond to commands
- Garbage characters in serial output

## Technical Details

### ESP32 UART Configuration

```cpp
HardwareSerial MySerial(2);  // UART2
#define RX_PIN 16
#define TX_PIN 17
#define BAUD_RATE 115200

MySerial.begin(BAUD_RATE, SERIAL_8N1, RX_PIN, TX_PIN);
```

### Raspberry Pi Serial Configuration

```python
SERIAL_PORT = '/dev/serial0'
BAUD_RATE = 115200
TIMEOUT = 1  # second

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
```

### Why UART2 on ESP32?

- **UART0**: Used for USB debugging (Serial Monitor)
- **UART1**: Used for flash operations
- **UART2**: Available for custom applications (our choice)

This allows simultaneous USB debugging while communicating with Raspberry Pi.

## Advantages Over I2C

| Feature | UART | I2C |
|---------|------|-----|
| Speed | Up to 115200 baud | 100-400 kHz |
| Wiring | Simple (TX, RX, GND) | Requires pull-up resistors |
| Full-duplex | Yes | No |
| Range | Better for longer distances | Limited to short distances |
| Debug | Easy with serial monitors | Requires special tools |

## Next Steps

- Extend protocol for motor control commands
- Implement sensor data streaming from ESP32 to Pi
- Add command acknowledgment and error handling
- Create binary protocol for faster data transfer
- Implement command queue for complex sequences

## References

- [ESP32 Arduino Core Documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/)
- [Raspberry Pi UART Configuration](https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-uarts)
- [PySerial Documentation](https://pyserial.readthedocs.io/)

## License

MIT License - See project root LICENSE file

# Author

Imesh (IMmercato)