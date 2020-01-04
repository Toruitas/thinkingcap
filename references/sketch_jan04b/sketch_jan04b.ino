#define potPin A5  // pwm or A


void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}

void loop() {
  // put your main code here, to run repeatedly:
  int reading  = analogRead(potPin);  // 0-1023 for 5v, 0-654 for 3.3v
  double UserMaxBrightness = floor(reading/(654.0/255.0));  // 1023/255.0 for 5v
  Serial.println(reading);
  Serial.println(UserMaxBrightness);
  delay(500);
}
