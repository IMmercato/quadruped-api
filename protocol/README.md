# Binary Messaging Protocol

## Overview

A lightweight binary messaging protocol designed for efficient Master–Slave communication. It replaces heavier text-based formats like JSON, prioritizing:

- **Low latency** — minimal processing overhead  
- **Resource efficiency** — optimized for constrained slave devices  
- **Data integrity** — built‑in checksum verification  
- **Compact size** — binary format reduces bandwidth usage  

## Protocol Variants

This protocol comes in two variants:

### **Standard Protocol (Variable Length)**
General‑purpose communication with flexible payload sizes.

### **Compact‑5 Protocol (Fixed 40‑bit)**
Ultra‑optimized 5‑byte packets for real‑time servo control with zero jitter.  
**Recommended for robotics applications.**

---

# Standard Protocol

## Packet Structure

Every message follows a fixed 5‑byte header plus variable payload:

```
┌──────────────────────┐
│        Header        │
└──────────┬───────────┘
│    ID    │   Length  │
└──────────└───────────┘
│       Payload        │
└──────────────────────┘
│       Checksum       │
└──────────────────────┘
```

```
┌─────────────────────────────────────────┐
│ Header (2B)   │ 0xAA 0x55               │
├───────────────┼─────────────────────────┤
│ Command (1B)  │ Action identifier       │
├───────────────┼─────────────────────────┤
│ Length (1B)   │ Payload size (0–255)    │
├───────────────┼─────────────────────────┤
│ Payload (N)   │ Command‑specific data   │
├───────────────┼─────────────────────────┤
│ Checksum (1B) │ XOR of all previous     │
└───────────────┴─────────────────────────┘
```

### Field Specifications

| Field      | Size    | Description                                      |
|------------|---------|--------------------------------------------------|
| Header     | 2 bytes | Static sync bytes: `0xAA 0x55`                   |
| Command ID | 1 byte  | Defines the action                               |
| Length     | 1 byte  | Payload size (0–255)                             |
| Payload    | N bytes | Command‑specific data                            |
| Checksum   | 1 byte  | XOR of all bytes from Header through Payload     |

## Example Packet

**Command:** Set LED state to ON (`0x01`)

```
AA 55 01 01 FF AA
│  │  │  │  │  └─ Checksum (XOR of all previous bytes)
│  │  │  │  └──── Payload (0xFF = ON)
│  │  │  └──────── Length
│  │  └─────────── Command ID
│  └────────────── Header
```

---

# Compact‑5 Protocol (40‑bit Fixed)

**Designed for real‑time servo control with zero jitter and constant timing.**

## Packet Structure

```
┌────────────────────────────────────────────────┐
│ Byte 0 │ Sync (0xA5)                           │
├────────┼───────────────────────────────────────┤
│ Byte 1 │ Command (4b) │ Servo ID (4b)          │
├────────┼───────────────────────────────────────┤
│ Byte 2 │ Angle (0–255)                         │
├────────┼───────────────────────────────────────┤
│ Byte 3 │ Speed (0–255)                         │
├────────┼───────────────────────────────────────┤
│ Byte 4 │ Checksum (XOR of bytes 0–3)           │
└────────┴───────────────────────────────────────┘
```

### Field Specifications

| Byte | Field      | Bits | Range    | Description                          |
|------|------------|------|----------|--------------------------------------|
| 0    | Sync       | 8    | `0xA5`   | Static sync byte                     |
| 1    | Command    | 4    | 0–15     | High nibble                          |
| 1    | Servo ID   | 4    | 0–15     | Low nibble                           |
| 2    | Angle      | 8    | 0–255    | Servo position (mapped to 0–180°)    |
| 3    | Speed      | 8    | 0–255    | Velocity control                     |
| 4    | Checksum   | 8    | —        | XOR of bytes 0–3                     |

### Example Compact‑5 Packet

**Move servo 3 to 90° at speed 128**

```
A5 23 5A 80 C8
│  │  │  │  └─ Checksum
│  │  │  └──── Speed
│  │  └──────── Angle
│  └──────────── Command=2, ServoID=3
└──────────────── Sync
```

Byte 1 breakdown:

```
0x23 = 0010 0011
         ││││ ││││
         ││││ └┴┴┴─ Servo ID = 3
         └┴┴┴────── Command = 2
```

---

# Compact‑5 Command Set

| Command ID | Name       | Description                    |
|------------|------------|--------------------------------|
| `0x0`      | MOVE       | Move servo to position         |
| `0x1`      | POSE       | Set multiple servos            |
| `0x2`      | GAIT       | Execute gait pattern           |
| `0x3`      | STOP       | Emergency stop                 |
| `0x4`      | CALIBRATE  | Zero/calibrate servo           |
| `0x5`      | READ       | Request servo position         |
| `0x6–0xF`  | Custom     | Application‑specific commands  |

---

# Advantages Over JSON

## Standard Protocol vs JSON

| Aspect           | Binary Protocol | JSON Equivalent |
|------------------|-----------------|-----------------|
| Message size     | 7 bytes         | ~25 bytes       |
| Parse complexity | O(1)            | O(n)            |
| CPU overhead     | Minimal         | High            |
| Memory usage     | Fixed buffers   | Dynamic         |
| Type safety      | Built‑in        | Requires checks |

## Compact‑5 vs JSON vs Standard

| Aspect            | JSON      | Standard | Compact‑5 |
|-------------------|-----------|----------|-----------|
| Total Size        | ~45 bytes | 7–8 B    | **5 B**   |
| Bandwidth         | 1.0×      | 6.4×     | **9×**    |
| Latency           | High      | Low      | **Ultra‑low** |
| Jitter            | Variable  | Low      | **Zero**  |
| Parse Time        | 100–500 µs| 10–50 µs | **5–10 µs** |
| Buffer Safety     | Complex   | Good     | **Guaranteed** |
| Servo Control     | Poor      | Good     | **Excellent** |

---

# Command Table (Standard Protocol)

| Command ID | Name        | Payload Format | Description           |
|------------|-------------|----------------|-----------------------|
| `0x01`     | SET_LED     | 1 byte (0/1)   | Control LED state     |
| `0x02`     | READ_SENSOR | None           | Request sensor data   |
| `0x03`     | SET_PWM     | 2 bytes        | Set PWM duty cycle    |
| `0x04`     | ACK         | 1 byte         | Acknowledgment        |
| `0x05`     | NACK        | 1 byte         | Negative acknowledge  |

---

# Implementation Notes

## Checksum Calculation

```c
uint8_t calculate_checksum(uint8_t *packet, size_t length) {
    uint8_t checksum = 0;
    for (size_t i = 0; i < length; i++) {
        checksum ^= packet[i];
    }
    return checksum;
}
```

## Packet Validation

1. Check header (`0xAA 0x55`)
2. Verify length matches payload
3. Compute checksum
4. Parse only after validation

## Error Handling

- Invalid header → discard until sync  
- Checksum mismatch → send NACK  
- Unknown command → NACK with error code  
- Timeout → retry with exponential backoff  

---

# Usage Examples

## Master (Python)

```python
def create_packet(command_id, payload):
    header = bytes([0xAA, 0x55])
    length = len(payload)
    packet = header + bytes([command_id, length]) + payload

    checksum = 0
    for byte in packet:
        checksum ^= byte

    return packet + bytes([checksum])

# LED ON
packet = create_packet(0x01, bytes([0xFF]))
serial.write(packet)
```

## Slave (C/Arduino)

```c
bool parse_packet(uint8_t *buffer, size_t len) {
    if (len < 5 || buffer[0] != 0xAA || buffer[1] != 0x55)
        return false;

    uint8_t cmd = buffer[2];
    uint8_t payload_len = buffer[3];
    uint8_t expected_checksum = calculate_checksum(buffer, 4 + payload_len);

    if (buffer[4 + payload_len] != expected_checksum)
        return false;

    handle_command(cmd, &buffer[4], payload_len);
    return true;
}
```

---

# Compact‑5 Implementation

## Master (Python)

```python
def create_compact5_packet(cmd_id, servo_id, angle, speed):
    sync = 0xA5
    cmd_byte = ((cmd_id & 0x0F) << 4) | (servo_id & 0x0F)

    packet = bytes([sync, cmd_byte, angle, speed])

    checksum = 0
    for b in packet:
        checksum ^= b

    return packet + bytes([checksum])
```

## Slave (C++/Arduino)

```cpp
void handleCompact5() {
    if (Serial.available() >= 5) {
        if (Serial.read() == 0xA5) {
            uint8_t cmd_byte = Serial.read();
            uint8_t angle = Serial.read();
            uint8_t speed = Serial.read();
            uint8_t received_crc = Serial.read();

            uint8_t cmd = (cmd_byte >> 4) & 0x0F;
            uint8_t id  = cmd_byte & 0x0F;

            uint8_t calc = 0xA5 ^ cmd_byte ^ angle ^ speed;

            if (received_crc == calc) {
                executeServoCommand(cmd, id, angle, speed);
            }
        }
    }
}
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Imesh (IMmercato) 

---