#include <ArduinoJson.h>
#include <SharpIR.h>
#include <Adafruit_NeoPixel.h>
#include <bluefruit.h>
#include <Adafruit_LittleFS.h>
#include <InternalFileSystem.h>

int OVERRIDEPIN = 5;
#define IR A0 // define signal pin for infrared
#define model 1080 // used 1080 because model GP2Y0A21YK0F is used
int TIME_BETWEEN_UPDATES = 250;  // ms. How long between measurements to report back to the server.
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

// Vibrator settings
int VIBEPIN_1 = 10;
unsigned long vibeStartTime = 0;
unsigned long vibeCurrentTime = 0;
int vibeTime = 75; // ms for vibe to last

// potentiometer settings for determining maximum brightness for LEDs
#define potPin A5  // Analog!
int potReading = 0;

// State string/json variables for state syncing.
String updateServerString = "";
String updateFromServerString = "";

// BLE Service
BLEDfu  bledfu;  // OTA DFU service
BLEDis  bledis;  // device information
BLEUart bleuart; // uart over ble
BLEBas  blebas;  // battery

StaticJsonDocument<JSON_OBJECT_SIZE(3)> sendToServerDoc;
StaticJsonDocument<JSON_OBJECT_SIZE(7)> receiveFromServerDoc;

SharpIR SharpIR(IR, model);
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);  // https://coolcomponents.co.uk/products/ws2815-digital-addressable-led-strip-60-leds-m-1m-adafruit-neopixel-compatible?variant=29496998264893


void setup() {
  pinMode(VIBEPIN_1, OUTPUT);  // set up the piezos-controlling pin.
  pinMode(OVERRIDEPIN, INPUT_PULLUP);  // manual override. 

  // configure BLE, based on Feather Bleuart example code.
  Bluefruit.autoConnLed(true);
  Bluefruit.configPrphBandwidth(BANDWIDTH_MAX);
  Bluefruit.begin();
  Bluefruit.setTxPower(4);    // Check bluefruit.h for supported values
  Bluefruit.setName("Bluefruit52");
  Bluefruit.Periph.setConnectCallback(connect_callback);
  Bluefruit.Periph.setDisconnectCallback(disconnect_callback);
  // To be consistent OTA DFU should be added first if it exists
  bledfu.begin();

  // Configure and Start Device Information Service
  bledis.setManufacturer("Adafruit Industries");
  bledis.setModel("Bluefruit Feather52");
  bledis.begin();

  // Configure and Start BLE Uart Service
  bleuart.begin();

  // Start BLE Battery Service
  blebas.begin();
  blebas.write(100);

  // Set up and start advertising
  startAdv();
  
  delay(100);
  hatRunning = true;

  strip.begin();
  strip.show();  // clear prior light settings
  
  startTime = millis();  // set the first timer.

  Serial.begin(9600);  // serial when connected for logging
  
}

void startAdv(void)
{
  // This whole method is from the Bleuart example code.
  // Advertising packet
  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addTxPower();

  // Include bleuart 128-bit uuid
  Bluefruit.Advertising.addService(bleuart);

  // Secondary Scan Response packet (optional)
  // Since there is no room for 'Name' in Advertising packet
  Bluefruit.ScanResponse.addName();
  
  /* Start Advertising
   * - Enable auto advertising if disconnected
   * - Interval:  fast mode = 20 ms, slow mode = 152.5 ms
   * - Timeout for fast mode is 30 seconds
   * - Start(timeout) with timeout = 0 will advertise forever (until connected)
   * 
   * For recommended advertising interval
   * https://developer.apple.com/library/content/qa/qa1931/_index.html   
   */
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.setInterval(32, 244);    // in unit of 0.625 ms
  Bluefruit.Advertising.setFastTimeout(30);      // number of seconds in fast mode
  Bluefruit.Advertising.start(0);                // 0 = Don't stop advertising after n seconds  
}

/**
 * Callback invoked when a connection is dropped
 * @param conn_handle connection where this event happens
 * @param reason is a BLE_HCI_STATUS_CODE which can be found in ble_hci.h
 */
void disconnect_callback(uint16_t conn_handle, uint8_t reason)
{
  // this whole method is from the Bleuart example
  (void) conn_handle;
  (void) reason;

//  Serial.println();
//  Serial.print("Disconnected, reason = 0x"); Serial.println(reason, HEX);
}

// callback invoked when central connects
void connect_callback(uint16_t conn_handle)
{
  // Get the reference to current connection
  BLEConnection* connection = Bluefruit.Connection(conn_handle);

  char central_name[32] = { 0 };
  connection->getPeerName(central_name, sizeof(central_name));

//  Serial.print("Connected to ");
//  Serial.println(central_name);
}

void vibrate(){
  // This runs when focus is detected.
    digitalWrite(VIBEPIN_1, HIGH);
    vibeStartTime = millis();
}

void stopvibrate(){
  // This runs on every loop to catch any active vibrations.
  vibeCurrentTime = millis();
  if(vibeCurrentTime - vibeStartTime >= vibeTime){
    digitalWrite(VIBEPIN_1, LOW);
  }  
}

// test sending info from Arduino to Python (should be over BLE, but that's tough right now)
// The challenge here is to Keep the state synced between the two.
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
  
  // Cast the JsonVariant to a string and send it over BLE.
  updateServerString = ""+sendToServerDoc.as<String>();
  
  uint8_t buf[64];  // 64 should be enough to send the whole state. 
  updateServerString.getBytes(buf,sizeof(buf));
  bleuart.write( buf,  sizeof(buf));
}

void readState(){
  // This fn copies a state update from the server to the local Arduino environment.
  // The server ONLY sends a message if the Thinking cap state changes. 
  // Focused or Not.
  // https://www.youtube.com/watch?v=iuHxPQB6Rx4 for JSON parsing info. 
  updateFromServerString = bleuart.read();

  if (updateFromServerString != "-1"){

    // load updateFromServerString into the JSON doc receiveFromServerDoc
    DeserializationError err = deserializeJson(receiveFromServerDoc, updateFromServerString);
  
    // if parsing failed
    if(err){
      if(Serial.available()){
        Serial.println("Error deserializing");
      }
      return;
    // if it succeeded
    }else{
      // update focused state
      if (receiveFromServerDoc["focused"] != -1){
        focused = receiveFromServerDoc["focused"];
      }else{
        focused = focused;
      }
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
  Serial.println(updateFromServerString);
  
}

void readWearing(){
  // Depending on stability of the sensor, may have to put this into an array. Get 3 readings over a certain amount of time to mean something.
  // Likely have to compensate some for "adjusting the hat" for comfort? 

  // wearing is the leading indicator, so on the next loop, update wearing_prev to indicate continued wearing.
  // probably need some kind of debounce here, too. Or could use the array average method. 
  if (wearing != wearing_prev){
    wearing_prev = wearing;
  }

  // Get the distance. If w/in 1-14cm, it should read as wearing. Why 1cm? 0 seems to fire frequently on bad readings. 
  int dis=SharpIR.distance();
  if(dis<8 && dis>1){
    wearing = true;
  }else{
    wearing = false;
  }
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
    if(!focused){
      strip.fill(strip.Color(0, strip.gamma8(floor(currentBrightness*(UserMaxBrightness/255))),0));  // green for hi there!
    }else{
      strip.fill(strip.Color(strip.gamma8(floor(currentBrightness*(UserMaxBrightness/255))),0,0)); // red for stay away
    }    
    strip.show();
//    Serial.println(currentBrightness*(UserMaxBrightness/255));
    updateLEDs = false;
  }
}

void turnOffLights(){
    // This turns the lights off in the case of not being worn. 
    strip.fill(strip.Color(0, 0,0));
    strip.show();
  }

void readMaxBrightness(){
  // Gets the setting of the potentiometer, which determines how high the maximum brightness of the LEDs are
  // References here: https://learn.adafruit.com/adafruit-arduino-lesson-8-analog-inputs/arduino-code & https://www.arduino.cc/en/Tutorial/AnalogReadSerial
  potReading  = analogRead(potPin);  // 0-1023 for 5v, 0-654 for 3.3v
  UserMaxBrightness = floor(potReading/(654.0/255.0));  // 1023/255.0 for 5v
}

void readOverride(){
  // Reads the button for overriding. 
  btnPressed = digitalRead(OVERRIDEPIN);
//  Serial.println(btnPressed);
  // user pressed the button. Toggle the state.
  if (btnPressed != btnPressed_prev && btnPressed==HIGH){  // if this is the first time the button is pressed, it will be different than btn_pressed
    // User pressed the button freshly. Toggle the state.
    // Do I need a debounce time?
    focused = !focused;  // 
    focused_prev = !focused_prev;
    vibrate();
    userOverride = true;  // overriding, 
    btnPressed_prev = btnPressed;  // store this press for comparison.
  }else{ 
    btnPressed_prev = btnPressed;  // store this non-press for comparison.
  }
}

void loop(){

    // set wearing using IR. 
    readWearing();
    // See if there's an override. Yes, only if the hat is being worn.
    readOverride();
    stopvibrate();
    if(wearing){
      // See if the user has adjusted max brightness
      readMaxBrightness();
      fadeInOrOut();
    }else{
      turnOffLights();
    }
    if(syncState){
      // Determine if we should send the state to the server.
      currentTime = millis();
      if((currentTime-startTime)  > TIME_BETWEEN_UPDATES){
        sendState();
        startTime = currentTime;
      }
      readState();
    }
    
    if(Serial.available()){
      Serial.println(userOverride);
    }
  
  
}
