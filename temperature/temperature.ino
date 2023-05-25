#define R_REF 1000.0
#define AVERAGES 30

void setup() {
  Serial.begin(9600);
}

void loop()
{
    float resistance;
    uint16_t adc_reading;
    static float R = 0;
    static uint8_t i = 0;
    adc_reading = analogRead(A0);
    resistance = R_REF*adc_reading/(1024.0-adc_reading);
    R = R + resistance;
    i++;
    if (i==AVERAGES)
    {
      Serial.println(R/AVERAGES);
      R = 0;
      i = 0;
    }
    
    delay(500/AVERAGES);
}
