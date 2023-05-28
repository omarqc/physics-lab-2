#define R_REF 1000.0
#define AVERAGES 10

void setup() {
  Serial.begin(9600);
}

void loop()
{
  while(Serial.available)
  {
    if (Serial.read() == 'r')
    {
      Serial.println(get_resistance());
    }
  }
  delay(5);
}

float get_resistance()
{
  float r;
  adc = analogRead(A0);
  r = R_REF * adc/(1024.0 - adc);
  return r;
}
