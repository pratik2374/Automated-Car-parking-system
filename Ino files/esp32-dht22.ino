#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#include <LiquidCrystal_I2C.h>
LiquidCrystal_I2C lcd_1(0x27, 16, 2);
#include <ESP32Servo.h>
const int servoPin = 18;
Servo myServo;

const int avlSlot=4;
int SensorTRG[avlSlot + 1]={0,12,13,14,15};//using index from 1;
int SensorECH[avlSlot + 1]={0,25,26,27,32}; //index starting from 1


const char* WIFI_NAME = "Wokwi-GUEST";      // Your Wi-Fi SSID
const char* WIFI_PASSWORD = "";             // Your Wi-Fi Password
const char* server = "http://api.thingspeak.com";
const char* apiKeyRead = "OX2LVBJ9SB25SZA2";  // Replace with your Read API Key
const char* apiKeyWrite = "Q6I6HTVETTRCP7QO"; 
const int channelId = 2685441;              // Replace with your Channel ID

void setup() {
  lcd_1.init(); // initialize the lcd
  lcd_1.backlight();
  myServo.attach(servoPin, 500, 2400);
  myServo.write(90);
    for(int i = 1; i <= avlSlot; i++) {
    pinMode(SensorTRG[i] , OUTPUT);
    pinMode(SensorECH[i] , INPUT);
  }

  Serial.begin(115200);
  WiFi.begin(WIFI_NAME, WIFI_PASSWORD);

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  Serial.println("Connected to WiFi!");
}
long readDistance(int i) {
  digitalWrite(SensorTRG[i], LOW);
  delayMicroseconds(2);
  digitalWrite(SensorTRG[i], HIGH);
  delayMicroseconds(10);
  digitalWrite(SensorTRG[i], LOW);
  
  long duration = pulseIn(SensorECH[i], HIGH);
  
  long distance = duration * 0.034 / 2;  // Speed of sound is 0.034 cm/us
  
  return distance;
  
}
int parkingSlot() {
  
  for (int i = 1; i <= avlSlot; i++) {
    if(readDistance(i) > 100) {   // Empty slots are getting returned
      return i;
    }
  }
  
  return -1; // denotes that no slot is available for parking
}


void sendToThingSpeak(int slotAvailable) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String(server) + "/update?api_key=" + apiKeyWrite + "&field2=" + String(slotAvailable);
    
    http.begin(url);
    int httpCode = http.GET();
    
    if (httpCode == 200) {
      Serial.println("Data sent to ThingSpeak: " + String(slotAvailable));
    } else {
      Serial.println("Failed to send data. HTTP Code: " + String(httpCode));
    }
    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
}

void loop() {
  const char* fieldValue; //ENABLE THIS WHEN USIG SERVER AND
  //int fieldValue = 1; // DISABLE THIS LINE(USED AS A SWITVH NOW)

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    // Construct the URL to fetch data from ThingSpeak
    String url = String(server) + "/channels/" + String(channelId) + "/fields/1.json?api_key=" + apiKeyRead + "&results=1";

    // Send the request to ThingSpeak
    http.begin(url);
    int httpCode = http.GET();  // Send the GET request
    
    // If request was successful
    if (httpCode == 200) {
      String payload = http.getString();  // Get the response payload (data)
      Serial.println("Data received from ThingSpeak: " + payload);

      // Parse the JSON response to extract the field data
      DynamicJsonDocument doc(256);
      deserializeJson(doc, payload);
      
      // Accessing field1 value
      fieldValue = doc["feeds"][0]["field1"];
      Serial.println("Field 1 value: " + String(fieldValue));
      
    } else {
      Serial.println("Error in getting data from ThingSpeak. HTTP code: " + String(httpCode));
    }

    http.end();  // Close the connection

  } else {
    Serial.println("WiFi not connected");
  }

  
  
  
  
  
  // delay(500); 
  // lcd_1.setCursor(0, 1);
  // lcd_1.print("WELCOME");
  
  if(String(fieldValue)=="1") {  // requestYolo used earlier 
    int space = parkingSlot();
  // Serial.print(space);
    if(space != -1) {
      myServo.write(0);
      //LCD
      lcd_1.clear();
      lcd_1.print("slot no. ");
      lcd_1.print(space);
      delay(1000);
      myServo.write(90);
      delay(5000);
      sendToThingSpeak(space);
      delay(5000);
      
    }
    else {
      // SORRY
      lcd_1.clear();
      lcd_1.print("SPACE FULL");
      sendToThingSpeak(0);
      delay(10000);
      
    }
  }
  else {
  lcd_1.clear();
    lcd_1.setCursor(0, 0);
    lcd_1.print("CAR PARKING");
    delay(10000);
    
   }

  delay(1000);  // Fetch data every 1 seconds
}
