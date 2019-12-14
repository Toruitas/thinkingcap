int VIBEPIN_1 = 2;
int LEDPIN = 8;
int OVERRIDEPIN = 9;
int IRPIN = 10; 
int TIME_BETWEEN_UPDATES = 100;  // ms. How long between measurements to report back to the server.
bool focused = false;
bool focused_prev = false;
bool wearing = false;
bool wearing_prev = false;
bool hatRunning = false;
bool hatRunning_prev = false;
bool syncState = true;
unsigned long startTime = 0;  // timestamp to measure against w/ currentTime
unsigned long currentTime = 0;  // timestamp which helps track elapsed time w/ startTime
char updateString = "";
bool userOverride = false;
bool btnPressed = false;

void setup() {
  pinMode(VIBEPIN_1, OUTPUT);  // set up the piezos-controlling pin.
  pinMode(LEDPIN, OUTPUT);  // set up the LED strip data pin.
  pinMode(OVERRIDEPIN, INPUT);  // manual override. 
  pinMode(IRPIN, INPUT);  // Infrared sensor pin. 
  
  Serial.begin(9600);
  delay(100);
  if (Serial.available()){
    Serial.write("Thinking cap connected");
  }
  startTime = millis();  // set the first timer.
}

// Tests setting Arduino from Python server
//void loop() {
//  if (Serial.available()){
//    userInput = Serial.read();
//
//    if(userInput=='f'){
//      focused = true;
//      // Set the parts on the hat to turn on. 
//      // Vibrate on.
//      digitalWrite(VIBEPIN_1, HIGH);
//      delay(100);
//      digitalWrite(VIBEPIN_1, LOW);
//      // Lights on. 
//      // digitalWrite(LIGHTPIN_1, HIGH);
//      Serial.println(focused);
//    }
//    if (userInput!='f'){
//      focused = false;
//      // turn everything off.
//      digitalWrite(VIBEPIN_1, LOW);
//      Serial.println(focused);
//    }
//  }
//}

// test sending info from Arduino to Python (should be over BLE, but that's tough right now)
// The challenge here is to Keep the state synced between the two.
// 

void sendState(){
  // This fn sends the current local environment state of the Arduino to the server.
  // Will be sent every TIME_BETWEEN_MEASUREMENTS: calclated as: (currentTime-startTime)  > TIME_BETWEEN_MEASUREMENTS in the main loop
  // The states will be changed as appropriate during the regular loop.
  // https://www.daniweb.com/programming/software-development/threads/108931/how-to-insert-variables-into-string-with-sign
  // http://www.cplusplus.com/reference/cstdio/sprintf/
  if (Serial.available()){
    sprintf(updateString,"{'focused':'%c','wearing':'%c','userOverride':'%c'}",focused, wearing, userOverride);
    Serial.write(updateString);
  }
}

void readState(){
  // This fn copies a state update from the server to the local Arduino environment.
  // The server ONLY sends a message if the Thinking cap state changes. 
  // Focused or Not.
  if (Serial.available()){
    Serial.read();
  }
}

void readWearing(){
  // Depending on stability of the sensor, may have to put this into an array. Get 3 readings over a certain amount of time to mean something.
  // Likely have to compensate some for "adjusting the hat" for comfort? 
    if(digitalRead(IRPIN)==HIGH){
      wearing = HIGH;
    }else{
      wearing = LOW;
    }
}

void updateLEDS(){
  // update the lights. Lights always on as long as the hat is being worn. Defaults to green for "please talk to me" just for more theatrics. Gotta see the change!
  // LEDPIN
}

void readOverride(){
  userOverride = digitalRead(OVERRIDEPIN);
  if(userOverride){
    // user pressed the button. Toggle the state.
    if (userOverride != btnPressed){  // if this is the first time the button is pressed, it will be different than btn_pressed
      wearing = !wearing;
      wearing_prev = !wearing_prev;
    }
    btnPressed = true;  // set the button to true to show that the button is still being pressed. This will cause userOverride == btn_pressed. State won't change.
    
  }else{ 
    btnPressed = false;
  }
}

void loop(){
  // set wearing using IR
  //readWearing();
  wearing = true;  // todo: remove this line
  if(wearing){
      // See if there's an override. Yes, only if the hat is being worn. 
      readOverride();

      if(syncState){
        // Determine if we should send the state to the server.
        currentTime = millis();
        if((currentTime-startTime)  > TIME_BETWEEN_UPDATES){
          sendState();
          startTime = currentTime;
        }
      }
  }
  
}
