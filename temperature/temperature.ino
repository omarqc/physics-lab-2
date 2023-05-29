#define R_REF 1000.0
#define AVERAGES 10
#define DELAY 20

int ready = 0;

void setup() {
  Serial.begin(9600);
}

/*
OPTION 1: print current resistance value upon request of 'main.py'
*/
void loop()
{
  if (ready == 1)
  {
    while(Serial.available)
    {
      if (Serial.read() == 'r')
      {
        Serial.println(millis() + ',' + String(get_resistance()));
      }
      delay(5);
    }

  } else 
  {
    // start non-stop data collection upon initial 'main.py' request
    if (Serial.read() == 's') 
    {
      ready = 1;
    }
  }
}

float get_resistance()
{
  float r;
  adc = analogRead(A0);
  r = R_REF * adc/(1024.0 - adc);
  return r;
}

/* 
OPTION 2: constantly print resistance data.
'main.py' will read the data more slowly. Real-time plot is delayed depending of loop() frequency
*/

/*
void loop()
{
  if (ready == 1)
  {
    float r;
    adc = analogRead(A0);
    r = R_REF * adc/(1024.0 - adc);
    Serial.println(millis() + ',' + String(r));
    delay(DELAY);
  } else 
  {
    // start non-stop data collection upon initial 'main.py' request
    if (Serial.read() == 's') 
    {
      ready = 1;
    }
  }
}

*/
