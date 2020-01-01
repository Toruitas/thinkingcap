#include <SharpIR.h>

#define ir A0
#define model 20150
// ir: the pin where your sensor is attached
// model: an int that determines your sensor:  1080 for GP2Y0A21Y
//                                            20150 for GP2Y0A02Y
//                                            (working distance range according to the datasheets)
// updated by Ahmad Nejrabi from Robojax.com
// get latest datasheets: http://www.sharp-world.com/products/device/lineup/selection/opto/haca/diagram.html
// model: an int that determines your sensor:
/*
 * GP2Y0A02YK0F --> "20150"
 GP2Y0A21YK --> "1080"
 GP2Y0A710K0F --> "100500"
  GP2YA41SK0F --> "430"
 */

SharpIR SharpIR(ir, model);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
}

void loop() {
  delay(2000);   

  unsigned long startTime=millis();  // takes the time before the loop on the library begins

  int dis=SharpIR.distance();  // this returns the distance to the object you're measuring


  Serial.print("Mean distance: ");  // returns it to the serial monitor
  Serial.println(dis);
  
  unsigned long calcTime=millis()-startTime;  // the following gives you the time taken to get the measurement
  Serial.print("Time taken (ms): ");
  Serial.println(calcTime);  

}