// ESP32 UART LED Control

#include <HardwareSerial.h>

// Use GPIO 16 & 17 instead of default UART0 pins
#define RX_PIN 16  // ESP32 GPIO16 will receive from Pi
#define TX_PIN 17  // ESP32 GPIO17 will transmit to Pi
#define LED_PIN 2  // Built-in LED

HardwareSerial MySerial(2);  // Use UART2

void setup() {
  // Debug serial (USB) - THIS STAYS ON UART0
  Serial.begin(115200);
  delay(1000);
  
  // UART communication with Raspberry Pi - NOW USING UART2
  MySerial.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);
  
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("=== ESP32 UART Slave Ready (UART2) ===");
  Serial.println("RX: GPIO16, TX: GPIO17");
  Serial.println("Baud: 115200");
  Serial.println("Commands: '1' = ON, '0' = OFF");
  
  // Success indication
  for(int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(150);
    digitalWrite(LED_PIN, LOW);
    delay(150);
  }
  
  // Send ready message to Raspberry Pi
  MySerial.println("ESP32_READY_UART2");
}

void loop() {
  if (MySerial.available()) {
    char command = MySerial.read();
    
    if (command == '1') {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("LED ON");
      MySerial.println("OK:LED_ON");
      
    } else if (command == '0') {
      digitalWrite(LED_PIN, LOW);
      Serial.println("LED OFF");
      MySerial.println("OK:LED_OFF");
      
    } else if (command == '\n' || command == '\r') {
      // Ignore newline characters
      return;
      
    } else {
      Serial.printf("Unknown command: '%c' (0x%02X)\n", command, command);
      MySerial.println("ERROR:UNKNOWN_COMMAND");
    }
  }
  
  delay(10);
}