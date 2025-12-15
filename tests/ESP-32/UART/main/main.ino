#include <HardwareSerial.h>

#define RX_PIN 16
#define TX_PIN 17
#define LED_PIN 2  // Built-in LED

// Create a hardware serial object
HardwareSerial MySerial(1);  // Use UART1

void setup() {
  // Debug serial (USB)
  Serial.begin(115200);
  delay(1000);
  
  // UART communication with Raspberry Pi
  // Format: begin(baud, config, rxPin, txPin)
  MySerial.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);
  
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("=== ESP32 UART Slave Ready ===");
  Serial.println("RX: GPIO16, TX: GPIO17");
  Serial.println("Baud: 115200");
  Serial.println("Commands: '1' = ON, '0' = OFF");
  
  // Success indication (3 quick blinks)
  for(int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(150);
    digitalWrite(LED_PIN, LOW);
    delay(150);
  }
  
  // Send ready message to Raspberry Pi
  MySerial.println("ESP32_READY");
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