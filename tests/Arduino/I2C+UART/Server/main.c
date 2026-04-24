#include <Wire.h>

#define SLAVE_ADDR 0x08
#define LED_PIN 13

void setup() {
  pinMode(LED_PIN, OUTPUT);

  // USB Debugging
  Serial.begin(9600);

  // UART
  Serial1.begin(9600);

  // I2C
  Wire.begin(SLAVE_ADDR);
  Wire.onReceive(receiveEvent);
  
  Serial.println("Mega I2C Slave + UART Ready");
}

void loop() {
  // UART
  if (Serial1.available()) {
    char c = Serial1.read();
    Serial.print("UART Received: ");
    Serial.println(c);

    Serial1.print("Arduino received UART: ");
    Serial1.println(c);
  }
  delay(10);
}

// I2C
void receiveEvent(int howMany) {
  while (Wire.available()) {
    char c = Wire.read();
    if (c == '1') {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("I2C Command: LED ON");
    } 
    else if (c == '0') {
      digitalWrite(LED_PIN, LOW);
      Serial.println("I2C Command: LED OFF");
    }
  }
}