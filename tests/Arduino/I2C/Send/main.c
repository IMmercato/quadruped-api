#include <Wire.h>

#define SLAVE_ADDR 0x08
String receivedData = "";

void setup() {
  Serial.begin(9600);
  Wire.begin(SLAVE_ADDR);
  Wire.onReceive(receiveEvent);
  Serial.println("Mega I2C Slave Ready");
}

void loop() {
  delay(100);
}

void receiveEvent(int howMany) {
  receivedData = "";
  while (Wire.available() > 0) {
    receivedData += (char)Wire.read();
  }
  Serial.print("Received: ");
  Serial.println(receivedData);
}