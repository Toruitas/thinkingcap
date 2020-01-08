// Vibrator settings
int VIBEPIN_1 = 10;
unsigned long vibeStartTime = 0;
unsigned long vibeCurrentTime = 0;
int vibeTime = 75; // ms for vibe to last

void setup() {
  // put your setup code here, to run once:
  pinMode(VIBEPIN_1, OUTPUT);
  digitalWrite(VIBEPIN_1, LOW);
  delay(1000);
  vibrate();
//  vibrate();
}

void loop() {
  // put your main code here, to run repeatedly:
//  vibrate();
  stopvibrate();
//  digitalWrite(VIBEPIN_1, HIGH);
//  delay(vibeTime);
//  digitalWrite(VIBEPIN_1, LOW);
//  delay(500);
}

void vibrate(){
//  if(vibeCurrentTime - vibeStartTime >= vibeTime){
    digitalWrite(VIBEPIN_1, HIGH);
    vibeStartTime = millis();
//  }
}

void stopvibrate(){
  vibeCurrentTime = millis();
  if(vibeCurrentTime - vibeStartTime >= vibeTime){
    digitalWrite(VIBEPIN_1, LOW);
    delay(1500);
  }  
}
