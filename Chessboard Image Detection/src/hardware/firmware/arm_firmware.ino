#include <Arduino.h>

// Buffer
String incomingData = ""; 

void setup() {
    // Start serial communication at the exact baud rate Python is using
    Serial.begin(115200); 
    
    // Built-in LED used as a basic visual confirmation gate
    pinMode(LED_BUILT_IN, OUTPUT); 
}

void loop() {
    // Check if Python has sent any bytes over the USB link
    while (Serial.available() > 0) {
        char c = Serial.read(); // Read the next single character
        
        if (c == '\n') { // The newline character triggers our parsing logic
            parseAndExecute(incomingData);
            incomingData = ""; // Flush the buffer for the next move
        } else {
            incomingData += c; // Build the string character by character
        }
    }
}

// Basic string parsing to see what Python wants us to do
void parseAndExecute(String command) {
    command.trim(); // Clean up any invisible trailing spaces

    // Check if it's a move command (e.g., "from: E2 to: E4")
    if (command.startsWith("from:")) {
        // Blinking the built-in LED simulates the arm moving for now
        digitalWrite(LED_BUILT_IN, HIGH);
        delay(500); 
        digitalWrite(LED_BUILT_IN, LOW);
        
        // Send a receipt acknowledgment back to Python
        Serial.print("ACK: Executed move -> ");
        Serial.println(command);
    } 
    // Check if it's a winner announcement (e.g., "winner:White")
    else if (command.startsWith("winner:")) {
        // Party mode for the LED to celebrate the win
        for(int i = 0; i < 5; i++) {
            digitalWrite(LED_BUILT_IN, HIGH); delay(100);
            digitalWrite(LED_BUILT_IN, LOW);  delay(100);
        }
        Serial.print("ACK: Registered winner -> ");
        Serial.println(command);
    }
}