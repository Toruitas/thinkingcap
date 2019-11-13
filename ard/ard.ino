int analogPin = 3;
int data = 0;
char userInput;
unsigned long currentTime = 0;  // 32-bit positive numbers. About 50 days of data logging.2^32 
unsigned long prevTime = 0;


void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}

void loop() {
  // if data is in the serial buffer
  if (Serial.available()){
      userInput = Serial.read();
      
      if(userInput=='g'){
        data = analogRead(analogPin);
        Serial.println(data);
      }
      
      if(userInput=='c'){
        // This just shows time elapsed since last time. First time is from time the program started.
        prevTime = currentTime;
        currentTime = millis();

        data = analogRead(analogPin);
        Serial.print(data);
        Serial.print('-');
        Serial.print(currentTime-prevTime);
        Serial.println("ms");
      }
    }
}
