/*
 * Arduino/Genuino 101 example
 * to read button and turn ON/OFF LED accordingly
 */

int LED = PIN_NEOPIXEL; // 6
int BTN = 5;

void setup() {

  Serial.begin(9600);
//  pinMode(LED, OUTPUT);
//  pinMode(BTN, INPUT_PULLUP);
  pinMode(BTN, INPUT);

}

void loop() {
//  if(digitalRead(BTN)){
//    Serial.println("1");
//  }else{
//    Serial.println("0");
//    }
  // digitalWrite(LED, digitalRead(BTN));

  Serial.println(digitalRead(BTN));
  delay(100);
}
