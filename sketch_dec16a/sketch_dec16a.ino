/*
 * Arduino/Genuino 101 example
 * to read button and turn ON/OFF LED accordingly
 */

int LED = 6;
int BTN = 7;

void setup() {

  Serial.begin(9600);
  pinMode(LED, OUTPUT);
  pinMode(BTN, INPUT_PULLUP);

}

void loop() {
  digitalWrite(LED, digitalRead(BTN));
  Serial.println(digitalRead(BTN));
  delay(100);
}
