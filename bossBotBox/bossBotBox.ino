#include <ArduinoJson.h>

int RED_PIN = 5;
int YELLOW_PIN = 6;
int GREEN_PIN = 9;
double concentration_rate = 0.0;
double target = 0.0;

String updateFromServerString = "";
StaticJsonDocument<JSON_OBJECT_SIZE(6)> receiveFromServerDoc;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  delay(100);

  pinMode(RED_PIN, OUTPUT);
  pinMode(YELLOW_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);

  digitalWrite(GREEN_PIN, HIGH);
  digitalWrite(YELLOW_PIN, HIGH);
  digitalWrite(RED_PIN, HIGH);
}

void loop() {
  readState();
}


void readState(){
  if (Serial.available()){
    updateFromServerString = Serial.readString();
    Serial.println(updateFromServerString);

    if(updateFromServerString){
      DeserializationError err = deserializeJson(receiveFromServerDoc, updateFromServerString);
      if(err){
        if(Serial.available()){
          Serial.println("ERROR: ");
          Serial.println(err.c_str());
        }
        return;
        // if it succeeded
      }else{
        concentration_rate = receiveFromServerDoc["concentration_rate"];
        target = receiveFromServerDoc["target"];
        if (concentration_rate > target){
          digitalWrite(GREEN_PIN, HIGH);
          digitalWrite(YELLOW_PIN, LOW);
          digitalWrite(RED_PIN, LOW);
        }else if(concentration_rate > target & 
                concentration_rate < target/2.0){
          digitalWrite(GREEN_PIN, LOW);
          digitalWrite(YELLOW_PIN, HIGH);
          digitalWrite(RED_PIN, LOW);
        }else{
          digitalWrite(GREEN_PIN, LOW);
          digitalWrite(YELLOW_PIN, LOW);
          digitalWrite(RED_PIN, HIGH);
        }
      }
    }else{
      return;
    }
  } 
}
