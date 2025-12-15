// ON/OFF ESP-32 Built-in LED

#include <Wire.h>

#define I2C_SLAVE_ADDR 0x08
#define SDA_PIN 21
#define SCL_PIN 22
#define LED_PIN 2  // Built-in LED

void receiveEvent(int howMany) {
  if (howMany < 1) return;
  
  int command = Wire.read();
  
  if (command == 1) {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("LED ON");
  } else if (command == 0) {
    digitalWrite(LED_PIN, LOW);
    Serial.println("LED OFF");
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  Wire.begin(I2C_SLAVE_ADDR, SDA_PIN, SCL_PIN);
  Wire.onReceive(receiveEvent);
  
  Serial.println("ESP32 I2C Slave Ready");
  Serial.println("Send 1 to turn LED ON, 0 to turn LED OFF");
}

void loop() {
  delay(10);
}