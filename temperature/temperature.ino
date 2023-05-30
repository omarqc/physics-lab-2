#define R_REF 1000.0
#define AVERAGES 10
#define DELAY 20

int ready = 0;
static float R = 0;
static uint8_t i = 0;
void setup() {
  Serial.begin(9600);
}
//
///*
//OPTION 1: print current resistance value upon request of 'main.py'
//*/
//void loop()
//{
//  if (ready == 1)
//  {
//    while(Serial.available())
//    {
//      if (Serial.read() == 'r')
//      {
//        get_resistance();
//      }
//      delay(5);
//    }
//
//  } else 
//  {
//    // start non-stop data collection upon initial 'main.py' request
//    if (Serial.read() == 's') 
//    {
//      ready = 1;
//    }
//  }
//}
//
//void get_resistance()
//{
//  float r;
//  uint16_t adc;
//  adc = analogRead(A0);
//  r = R_REF * adc/(1024.0 - adc);
//  Serial.println(String(millis()) + "," + String(r));
//}

/*
OPTION 2: constantly print resistance data.
'main.py' will read the data more slowly. Real-time plot is delayed depending of loop() frequency
*/


void loop()
{
  float start;
  if (ready == 1)
  {
    uint16_t adc;
    float r;
 
    adc = analogRead(A0);
    r = R_REF * adc/(1024.0 - adc);
    R = R + r;
    i++;
    if (i==AVERAGES)
    {
      Serial.println(String(millis()-start) + "," + String(R/AVERAGES));
      R = 0;
      i = 0;
    }
    delay(DELAY);
  } else 
  {
    start = millis();
    // start non-stop data collection upon initial 'main.py' request
    if (Serial.read() == 's') 
    {
      ready = 1;
    }
  }
}
