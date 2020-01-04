#include <Adafruit_NeoPixel.h>

// potentiometer settings
#define potPin A5  // pwm or A
int potReading = 0;

// LED variables
int LED_PIN = 6;
int LED_COUNT = 36;
unsigned long ledStartTime = 0;
unsigned long ledCurrentTime = 0;
int SystemMinBrightness = 0;       //value 0-255 
double UserMaxBrightness = 255;      //value 0-255--equation (maxBrightness*maxBrightness/255) hence maxBrightness^2/255 hence the value 170 actually equal to 113.33333 .
int SystemMaxBrightness = 255;
int currentBrightness = 127.5;
int fadeInWait = 5;          //lighting up speed, steps.
int fadeOutWait = 10;         //dimming speed, steps.
bool fadingIn = true;
bool updateLEDs = false;

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  strip.begin();
  strip.show();
}

void loop() {
  // put your main code here, to run repeatedly:
  potReading  = analogRead(potPin);  // 0-1023 for 5v, 0-654 for 3.3v
  UserMaxBrightness = floor(potReading/(654.0/255.0));  // 1023/255.0 for 5v
  fadeInOrOut();
}

void fadeInOrOut(){
  // update the lights. Lights always on as long as the hat is being worn. Defaults to green for "please talk to me" just for more theatrics. Gotta see the change!
  // LEDPIN
  // lights turn on if worn, turn off if not.
  // brightness determined by the potentiometer. 
  // https://forum.arduino.cc/index.php?topic=434825.0 or https://forums.adafruit.com/viewtopic.php?t=41143 for code on the brightness
  // I especially like the idea of using sine/cosine to modulate it. However it's too subtle for these LEDs, after experimentation. 
  // https://learn.adafruit.com/multi-tasking-the-arduino-part-3/fader
  
  updateLEDs = false;
  
  if(UserMaxBrightness>SystemMaxBrightness){
    UserMaxBrightness = SystemMaxBrightness; // Just in case somehow the potentiometer controlling brightness gets readings higher than the LEDs can go  
  }

  if (UserMaxBrightness>0){
    ledCurrentTime = millis();
    // Fading in is faster than fading out
    if(fadingIn){
      // has enough time elapsed to do it?
      if (ledCurrentTime - ledStartTime > fadeInWait){
        updateLEDs = true;
//        currentBrightness = currentBrightness + sin((currentBrightness/MaxBrightness)*M_PI);  // 0-1 PI will be values between 0 and +1.
        currentBrightness = currentBrightness + 1;
        ledStartTime = millis();  // update last time LEDs changed
      }
    }
    // fading out
    if(!fadingIn){
      if (ledCurrentTime - ledStartTime > fadeOutWait){
        updateLEDs = true;
//        currentBrightness = currentBrightness - sin((currentBrightness/MaxBrightness)*M_PI);
        currentBrightness = currentBrightness - 1;
        ledStartTime = millis();
      }
    }
    
//    strip.setBrightness(currentBrightness*(MaxBrightness/255));  // normalized for maxbrightness
//    strip.fill(red, 0, LED_COUNT);
//    for (int i=0;i<strip.numPixels();i++){
//          strip.setPixelColor(i,red);
//        }

    // it's maximally bright, time to fade out
    if(currentBrightness >= SystemMaxBrightness){
      fadingIn = false;
      currentBrightness = SystemMaxBrightness;
    }
    // it's minimally dim, time to fade in.
    if (currentBrightness <= SystemMinBrightness){
      fadingIn = true;
      currentBrightness = SystemMinBrightness;
    }
  }else{
    currentBrightness = 0;
  }

  if(updateLEDs){
    strip.fill(strip.Color(0, strip.gamma8(floor(currentBrightness*(UserMaxBrightness/255))),0));  // green for hi there!

    strip.show();
    Serial.println(currentBrightness*(UserMaxBrightness/255));
    updateLEDs = false;
  }
}
