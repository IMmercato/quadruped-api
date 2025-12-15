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

IMPORTANT NOTES:
- Pi TX (GPIO 14) → ESP32 RX (GPIO 16)
- Pi RX (GPIO 15) → ESP32 TX (GPIO 17)
- Common GND is CRITICAL
- Baud rate: 115200
- No voltage level shifter needed (both use 3.3V logic)