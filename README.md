# Quadruped Rover API

A Node.js-based REST and WebSocket API for controlling a quadruped rover through a master-slave architecture (Raspberry Pi 5 + Arduino).

## Overview

This API serves as the main controller for a quadruped rover, enabling remote control and monitoring from any connected device. The system operates with the Raspberry Pi 5 as the master controller hosting the API and acting as an access point, while an Arduino slave executes real-time motor and sensor commands.

### Architecture

```
┌─────────────────────┐
│   Client Device     │
│  (Web/Mobile/CLI)   │
└──────────┬──────────┘
           │ WiFi
           ↓
┌─────────────────────┐
│   Raspberry Pi 5    │
│   (Master/API)      │
│   - REST API        │
│   - WebSocket       │
│   - Access Point    │
└──────────┬──────────┘
           │ I2C/UART
           ↓
┌─────────────────────┐
│   Arduino           │
│   (Slave/Executor)  │
│   - Motor Control   │
│   - Sensors         │
│   - Real-time Exec  │
└─────────────────────┘
```

## Features

- **Dual Communication Protocols**
  - WebSocket for real-time control commands
  - REST API for status queries and testing
  
- **Master-Slave Communication**
  - UART protocol support
  - I2C protocol support
  - Bidirectional data flow

- **Control Interface**
  - Remote rover control from any connected device
  - Real-time command execution
  - Status monitoring and diagnostics

## Installation

### Prerequisites

- Node.js (v16 or higher)
- Python 3.x
- Raspberry Pi 5 with I2C/UART enabled
- Arduino or ESP32 board

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/quadruped-api.git
cd quadruped-api
```

2. Install dependencies:
```bash
npm install
```

3. Enable UART/I2C on Raspberry Pi:
```bash
sudo raspi-config
# Navigate to Interface Options → I2C/Serial → Enable
```

4. Upload the appropriate firmware to your Arduino/ESP32:
   - For UART: `tests/ESP-32/UART/main/main.ino`
   - For I2C: `tests/ESP-32/I2C/main/main.ino`

## Usage

### Starting the Server

```bash
node server.js
```

The server will start on `http://localhost:3000`

### REST API Endpoints

#### Status Endpoints

```http
GET /api/status
```
Returns rover status, battery level, and sensor data.

**Response:**
```json
{
  "status": "operational",
  "battery": "85%",
  "sensors": "active"
}
```

### WebSocket Connection

Connect to `ws://localhost:3000` for real-time bidirectional communication.

## Hardware Connections

### UART Connection for TESTING (Raspberry Pi ↔ ESP32)

```
Raspberry Pi 5          ESP32
GPIO 14 (TX)    ───────  GPIO 16 (RX)
GPIO 15 (RX)    ───────  GPIO 17 (TX)
GND             ───────  GND
5V              ───────  VIN
```

**Baud Rate:** 115200

## Project Structure

```
quadruped-api/
├── client/
│   └── index.html          # Web interface
├── tests/
│   └── ESP-32/
│       ├── I2C/            # I2C test code
│       └── UART/           # UART test code
├── server.js               # Main API server
├── main.py                 # Python UART bridge
├── package.json
└── README.md
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Imesh (IMmercato)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.