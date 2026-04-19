#include <Wire.h>

#define SLAVE_ADDR 0x08
#define BUF_SIZE 32

char rxBuffer[BUF_SIZE];
char txBuffer[BUF_SIZE];
volatile bool newData = false;

void setup() {
  Serial.begin(9600);
  Wire.begin(SLAVE_ADDR);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);
  
  memset(txBuffer, 0, BUF_SIZE);
  strcpy(txBuffer, "Ready");
  Serial.println("Mega I2C Slave Ready");
}

void loop() {
  if (newData) {
    newData = false;
    Serial.print("Received: ");
    Serial.println(rxBuffer);
    
    snprintf(txBuffer, BUF_SIZE, "Echo: %s", rxBuffer);
  }
  delay(10);
}

void receiveEvent(int howMany) {
  if (howMany > 0) Wire.read();
  
  int i = 0;
  while (Wire.available() && i < BUF_SIZE - 1) {
    rxBuffer[i++] = Wire.read();
  }
  rxBuffer[i] = '\0';
  newData = true;
}

void requestEvent() {
  Wire.write(txBuffer, BUF_SIZE);
}