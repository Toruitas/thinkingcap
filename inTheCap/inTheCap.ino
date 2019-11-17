int VIBEPIN_1 = 2;
bool focused = false;
bool wearing = false;
bool hatRunning = false;
char userInput;

void setup() {
  pinMode(VIBEPIN_1, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()){
    userInput = Serial.read();

    if(userInput=='f'){
      focused = true;
      // Set the parts on the hat to turn on. 
      // Vibrate on.
      digitalWrite(VIBEPIN_1, HIGH);
      delay(100);
      digitalWrite(VIBEPIN_1, LOW);
      // Lights on. 
      // digitalWrite(LIGHTPIN_1, HIGH);
      Serial.println(focused);
    }
    if (userInput!='f'){
      focused = false;
      // turn everything off.
      digitalWrite(VIBEPIN_1, LOW);
      Serial.println(focused);
    }
  }
}
