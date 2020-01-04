#include <Adafruit_NeoPixel.h>

#define LED_PIN 6
#define LED_COUNT 36   //how many pixel on the strip.

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

int SystemMinBrightness = 0;       //value 0-255 
int UserMaxBrightness = 255;      //value 0-255--equation (maxBrightness*maxBrightness/255) hence maxBrightness^2/255 hence the value 170 actually equal to 113.33333 .
int SystemMaxBrightness = 255;
int currentBrightness = 127.5;

int fadeInWait = 5;          //lighting up speed, steps.
int fadeOutWait = 10;         //dimming speed, steps.
bool fadingIn = true;
bool updateLEDs = false;

# define M_PI           3.14159265358979323846  /* pi ripped from math.h module */

// code from xl97 on https://forums.adafruit.com/viewtopic.php?f=47&t=41143&start=90
uint32_t red = strip.Color(currentBrightness, 0, 0);
uint32_t green = strip.Color(0, currentBrightness, 0);

uint32_t Color1; // What colors are in use
uint32_t Color2; // What colors are in use

unsigned long ledStartTime = 0;
unsigned long ledCurrentTime = 0;

//---------------------------------------------------------------------------------------------------//

void setup() {
  Serial.begin(9600);
  strip.begin();
  strip.show();
}

void loop() {

//  strip.fill(strip.Color(255,0,0)); // green?!
//  strip.fill(strip.Color(0,255,0)); // red?!
//  strip.fill(strip.Color(0,0,255)); // blue?!
//strip.fill(strip.Color(floor(currentBrightness*(UserMaxBrightness/255)),0,0)); // should be red
//  delay(5);
//  strip.show();

  // if wearing
  fadeInOrOut();
 
  //---strip will stay lit for some time before dimming again.----
//  rgbFadeIn_Hold_Out(strip.Color(255,0,0),numLoops1);  //red.
//  rainbowFadeIn_Hold_Out(numLoops2);
// 
//  //---normal breathing.----
//  rgbFadeInOut(strip.Color(60,255,0),numLoops3);      //green.
//  rainbowFadeInOut(numLoops4);
}

void fadeInOrOut(){
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
//    strip.fill(strip.Color(strip.gamma8(floor(currentBrightness*(UserMaxBrightness/255))),0,0));  // red
    strip.fill(strip.Color(0, strip.gamma8(floor(currentBrightness*(UserMaxBrightness/255))),0));
    strip.show();
    Serial.println(currentBrightness*(UserMaxBrightness/255));
    updateLEDs = false;
  }
}
//
//void rgbFadeIn_Hold_Out(uint32_t c, uint8_t x) {
//  for (int j=0;j<x;j++){
//    for(uint8_t b=MinBrightness;b<MaxBrightness;b++){
//      strip.setBrightness(b*MaxBrightness/255);
//      for (uint16_t i=0;i<strip.numPixels();i++){
//        strip.setPixelColor(i,c);
//      }
//      strip.show();
//      delay(fadeInWait);
//    }
//    strip.setBrightness(MaxBrightness*MaxBrightness/255);
//    for (uint16_t i=0;i<strip.numPixels();i++){
//      strip.setPixelColor(i,c);
//      strip.show();
//      delay(fadeHoldWait);
//    }
//    for(uint8_t b=MaxBrightness;b>MinBrightness;b--){
//      strip.setBrightness(b*MaxBrightness/255);
//      for (uint16_t i=0;i<strip.numPixels();i++){
//        strip.setPixelColor(i,c);
//      }
//      strip.show();
//      delay(fadeOutWait);
//    }
//  }
//}
//
//void rainbowFadeIn_Hold_Out(uint8_t x) {
//  for (int j=0;j<x;j++){
//    for(uint8_t b=MinBrightness;b<MaxBrightness;b++){
//      strip.setBrightness(b*MaxBrightness/255);
//      for (uint8_t i=0;i<strip.numPixels();i++){
//        strip.setPixelColor(i,Wheel(i*256/strip.numPixels()));
//      }
//      strip.show();
//      delay(fadeInWait);
//    }
//    strip.setBrightness(MaxBrightness*MaxBrightness/255);
//    for(uint8_t i=0;i<strip.numPixels();i++){
//      strip.setPixelColor(i,Wheel(i*256/strip.numPixels()));
//      strip.show();
//      delay(fadeHoldWait);
//    }
//    for (uint8_t b=MaxBrightness;b>MinBrightness;b--){
//      strip.setBrightness(b*MaxBrightness/255);
//      for(uint8_t i=0;i<strip.numPixels();i++) {
//        strip.setPixelColor(i,Wheel(i*256/strip.numPixels()));
//      }
//      strip.show();
//      delay(fadeOutWait);
//    }
//  }
//}
//
//void rgbFadeInOut(uint32_t c, uint8_t x){
//  for(int j=0;j<x;j++){
//    for(uint8_t b=MinBrightness;b<MaxBrightness;b++){
//      strip.setBrightness(b*MaxBrightness/255);
//      for(uint16_t i=0;i<strip.numPixels();i++){
//        strip.setPixelColor(i,c);
//      }
//      strip.show();
//      delay(fadeInWait);
//    }
//    for(uint8_t b=MaxBrightness;b>MinBrightness;b--) {
//      strip.setBrightness(b*MaxBrightness/255);
//      for (uint16_t i=0;i<strip.numPixels();i++) {
//        strip.setPixelColor(i,c);
//      }
//      strip.show();
//      delay(fadeOutWait);
//    }
//  }
//}
//
//void rainbowFadeInOut(uint8_t x){
//  for(int j=0;j<x;j++){
//    for(uint8_t b=MinBrightness;b<MaxBrightness;b++){
//      strip.setBrightness(b*MaxBrightness/255);
//      for(uint8_t i=0;i<strip.numPixels();i++){
//        strip.setPixelColor(i,Wheel(i*256/strip.numPixels()));
//      }
//      strip.show();
//      delay(fadeInWait);
//    }
//    for(uint8_t b=MaxBrightness;b>MinBrightness;b--) {
//      strip.setBrightness(b*MaxBrightness/255);
//      for (uint8_t i=0;i<strip.numPixels();i++) {
//        strip.setPixelColor(i,Wheel(i*256/strip.numPixels()));
//      }
//      strip.show();
//      delay(fadeOutWait);
//    }
//  }
//}
//
//
////NeoPixel Wheel for Rainbow-----------------
//
//uint32_t Wheel(byte WheelPos) {
//  WheelPos = 127 - WheelPos;       //the value here means - for 255 the strip will starts with red, 127-red will be in the middle, 0 - strip ends with red.
//  if(WheelPos < 85) {
//    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
//  }
//  if(WheelPos < 170) {
//    WheelPos -= 85;
//    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
//  }
//  WheelPos -= 170;
//  return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
//}
