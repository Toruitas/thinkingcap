#include <ArduinoJson.h>


int VIBEPIN_1 = 2;
int LEDPIN = 8;
int OVERRIDEPIN = 7;
int IRPIN = 10; 
int TIME_BETWEEN_UPDATES = 100;  // ms. How long between measurements to report back to the server.
bool focused = false;
bool focused_prev = false;
bool wearing = false;
bool wearing_prev = false;
bool hatRunning = false;
bool hatRunning_prev = false;
bool syncState = true;
bool userOverride = false;
bool btnPressed = false;
bool btnPressed_prev = false;
unsigned long startTime = 0;  // timestamp to measure against w/ currentTime
unsigned long currentTime = 0;  // timestamp which helps track elapsed time w/ startTime

String updateServerString = "";
String updateFromServerString = "";

StaticJsonDocument<JSON_OBJECT_SIZE(3)> sendToServerDoc;
StaticJsonDocument<JSON_OBJECT_SIZE(6)> receiveFromServerDoc;


void setup() {
  pinMode(VIBEPIN_1, OUTPUT);  // set up the piezos-controlling pin.
  pinMode(LEDPIN, OUTPUT);  // set up the LED strip data pin.
  pinMode(OVERRIDEPIN, INPUT_PULLUP);  // manual override. 
  pinMode(IRPIN, INPUT);  // Infrared sensor pin. 
  
  Serial.begin(9600);
  delay(100);
  hatRunning = true;
  
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

void vibrate(){
  digitalWrite(VIBEPIN_1, HIGH);
  delay(100);
  digitalWrite(VIBEPIN_1, LOW);
}

void sendState(){
  // This fn sends the current local environment state of the Arduino to the server.
  // Will be sent every TIME_BETWEEN_MEASUREMENTS: calclated as: (currentTime-startTime)  > TIME_BETWEEN_MEASUREMENTS in the main loop
  // The states will be changed as appropriate during the regular loop.
  // https://www.daniweb.com/programming/software-development/threads/108931/how-to-insert-variables-into-string-with-sign
  // http://www.cplusplus.com/reference/cstdio/sprintf/
  // https://arduinojson.org/v6/doc/serialization/
  
  sendToServerDoc["focused"].set(focused);
  sendToServerDoc["wearing"].set(wearing);
  sendToServerDoc["userOverride"].set(userOverride);
  
  // Cast the JsonVariant to a string and send it over serial.
  updateServerString = ""+sendToServerDoc.as<String>();
  Serial.println(updateServerString);
}

void readState(){
  // This fn copies a state update from the server to the local Arduino environment.
  // The server ONLY sends a message if the Thinking cap state changes. 
  // Focused or Not.
  // https://www.youtube.com/watch?v=iuHxPQB6Rx4 for JSON parsing info. 
  if (Serial.available()){
    updateFromServerString = Serial.readString();

    // load updateFromServerString into the JSON doc receiveFromServerDoc
    DeserializationError err = deserializeJson(receiveFromServerDoc, updateFromServerString);
    
    // if parsing failed
    if(err){
      Serial.println("Error");
      return;
    // if it succeeded
    }else{
      // update focused state
      focused = receiveFromServerDoc["focused"];
      // new focused state. 
      if(focused && !focused_prev){
        focused_prev = focused;
        userOverride = false;  // override 
        vibrate();
        // color = "red" on Neopixel
      // new un-focused state
      }else if(!focused && focused_prev){
        focused_prev = focused;
        vibrate();
        // color = "green" on Neopixel.
      // focused state unchanged.
      }else{
        // if the state matches, reset the override. Not necessary anymore. 
        userOverride = false;
      }
    }
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
  // Reads the button for overriding. 
  btnPressed = digitalRead(OVERRIDEPIN);
//  Serial.println(btnPressed);
  // user pressed the button. Toggle the state.
  if (btnPressed != btnPressed_prev && btnPressed==HIGH){  // if this is the first time the button is pressed, it will be different than btn_pressed
    // User pressed the button freshly. Toggle the state.
    focused = !focused;  // 
    focused_prev = !focused_prev;
    userOverride = true;  // overriding, 
    btnPressed_prev = btnPressed;  // store this press for comparison.
  }else{ 
    btnPressed_prev = btnPressed;  // store this non-press for comparison.
  }
}

void loop(){
  // set wearing using IR
  //readWearing();
  wearing = true;  // todo: remove this line and uncomment the above
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
        readState();
      }
  }
  
}
