#include <Adafruit_NeoPixel.h>

#define LEDPIN		6
#define PSUPIN		12
#define NUMPIXELS	554 // This has to be set accurately on both sides, otherwise updates will be out of sync. Also my setup has 576 LEDs but if this is set to 555 or higher it doesn't write any of them.

#define SERIAL_BAUDRATE	250000

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

/* Accepted commands are ("?" symbol stands for "don't care" byte):
	"123:\x00\xff\x80\n": Set pixel 123 to 0x0 red, 0xff green and 0x80 blue
	"-1:?\n": Display loaded values on LED strip (takes significant time)
	"0:\x80\n": If the value after the colon is not 0, then enable the LED power supply.
After each command is completed, the string "OK\n" is sent. When sent, it means the board is
ready for more commands.
*/

void loop() {
    while(!Serial.available()){}
    int index = Serial.parseInt(SKIP_ALL);
    Serial.read();
    if(index==0){
        int val = Serial.read();
        digitalWrite(PSUPIN, val);
    } else if (index==-1) {
        pixels.show();
    } else {
        int r,g,b;
        r=Serial.read();
        g=Serial.read();
        b=Serial.read();
	pixels.setPixelColor(index, pixels.Color(r,g,b));
    }
    Serial.print("OK\n");
    Serial.flush();
    Serial.readStringUntil('\n');
  }
}
