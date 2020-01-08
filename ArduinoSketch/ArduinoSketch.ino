#include <Adafruit_NeoPixel.h>

#define PIN        6
#define NUMPIXELS 554 // This has to be set accurately on both sides, otherwise updates will be out of sync. Also my setup has 576 LEDs but if this is set to 555 or higher it doesn't write any of them.

#define SERIAL_BAUDRATE 250000

Adafruit_NeoPixel pixels(NUMPIXELS, PIN);


void setup() {
  pixels.begin();
  pixels.setBrightness(50);
  pixels.clear();
  Serial.begin(SERIAL_BAUDRATE);
}

byte readOneByte() {
  int ans = -1;
  while (ans == -1) {
    ans = Serial.read();
  }
  return (byte)ans;
}

byte last_color[] = {0,0,0};

void loop() {
restartLoop:
  for (int i = 0; i < NUMPIXELS; i++) { // For each pixel...

//    Serial.print("Reading pix ");
//    Serial.println(i);
    while(!Serial.available()){}
    int index = Serial.parseInt(SKIP_ALL);
    Serial.read();
    int r,g,b;
    r=Serial.parseInt(SKIP_ALL);
    Serial.read();
    g=Serial.parseInt(SKIP_ALL);
    Serial.read();
    b=Serial.parseInt(SKIP_ALL);
    Serial.readStringUntil('\n');
  
    Serial.print(index);
    Serial.print(" ==> ");
    Serial.print(r);
    Serial.print(" ");
    Serial.print(g);
    Serial.print(" ");
    Serial.println(b);


    pixels.setPixelColor(index, pixels.Color(r,g,b));

    if(index==-1){pixels.show();}
  }
}
