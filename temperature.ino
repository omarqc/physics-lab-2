#define R_REF 1000

void setup() {
  Serial.begin(115200);
}

void loop()
{
  float resistance;
  uint16_t voltage;
  static uint8_t i = 0;
  adc_reading = analogRead(A0);
  resistance = R_REF*adc_reading/(1024-adc_reading);
  Serial.println(resistance);
  delay(10);
}
