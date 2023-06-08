#define R_REF 1000.0
#define AVERAGES 10
#define DELAY 20

int ready = 0;
static float R = 0;
static uint8_t i = 0;
void setup() {
  Serial.begin(9600);
}

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
