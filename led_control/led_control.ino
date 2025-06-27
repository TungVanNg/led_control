/*
 * LED Hand Gesture Control - Arduino Code
 * 5 Purple LEDs Control (No FastLED)
 * Compatible with Hand Gesture Recognition System
 */

// Định nghĩa chân LED (Digital pins) - THEO YEU CAU: 2, 4, 5, 18, 19
const int LED_PINS[] = {2, 4, 5, 18, 19}; // 5 LED tím
const int NUM_LEDS = 5;

// Biến điều khiển
String command = "";
unsigned long previousMillis = 0;
int currentEffect = 0;
int stepCounter = 0;
int brightness = 255;
bool increasing = true;

// Định nghĩa các hiệu ứng
enum Effects {
  EFFECT_OFF = 0,
  EFFECT_ALL_ON = 1,
  EFFECT_BLINK = 2,
  EFFECT_CHASE = 3,
  EFFECT_BREATHE = 4,
  EFFECT_RAINBOW = 5,
  EFFECT_WAVE = 6,
  EFFECT_FADE = 7,
  EFFECT_STROBE = 8,
  EFFECT_TWINKLE = 9,
  EFFECT_TEST = 10
};

void setup() {
  // Khởi tạo Serial
  Serial.begin(115200);
  Serial.println("Arduino LED Controller Started");
  Serial.println("5 Purple LEDs - Pins: 2, 4, 5, 18, 19");
  
  // Khởi tạo các chân LED
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(LED_PINS[i], OUTPUT);
    digitalWrite(LED_PINS[i], LOW);
  }
  
  // Test sequence khi khởi động
  testSequence();
  Serial.println("Ready for commands...");
}

void loop() {
  // Đọc lệnh từ Serial
  if (Serial.available()) {
    command = Serial.readStringUntil('\n');
    command.trim();
    parseCommand(command);
  }
  
  // Chạy hiệu ứng hiện tại
  runCurrentEffect();
}

void parseCommand(String cmd) {
  Serial.println("Received: " + cmd);
  
  // RESET hiệu ứng cũ khi nhận lệnh mới
  stepCounter = 0;
  brightness = 255;
  increasing = true;
  previousMillis = millis();
  
  if (cmd == "ALL_OFF") {
    currentEffect = EFFECT_OFF;
    allLedsOff(); // TẮT NGAY LẬP TỨC
  } else if (cmd == "ALL_ON") {
    currentEffect = EFFECT_ALL_ON;
    allLedsOn(); // SÁNG NGAY LẬP TỨC
  } else if (cmd == "BLINK") {
    currentEffect = EFFECT_BLINK;
  } else if (cmd == "CHASE") {
    currentEffect = EFFECT_CHASE;
  } else if (cmd == "BREATHE") {
    currentEffect = EFFECT_BREATHE;
  } else if (cmd == "RAINBOW") {
    currentEffect = EFFECT_RAINBOW;
  } else if (cmd == "WAVE") {
    currentEffect = EFFECT_WAVE;
  } else if (cmd == "FADE") {
    currentEffect = EFFECT_FADE;
  } else if (cmd == "STROBE") {
    currentEffect = EFFECT_STROBE;
  } else if (cmd == "TWINKLE") {
    currentEffect = EFFECT_TWINKLE;
  } else if (cmd == "TEST") {
    currentEffect = EFFECT_TEST;
  }
}

void runCurrentEffect() {
  unsigned long currentMillis = millis();
  
  switch (currentEffect) {
    case EFFECT_OFF:
      allLedsOff();
      break;
      
    case EFFECT_ALL_ON:
      allLedsOn();
      break;
      
    case EFFECT_BLINK:
      if (currentMillis - previousMillis >= 500) {
        blinkEffect();
        previousMillis = currentMillis;
      }
      break;
      
    case EFFECT_CHASE:
      if (currentMillis - previousMillis >= 200) {
        chaseEffect();
        previousMillis = currentMillis;
      }
      break;
      
    case EFFECT_BREATHE:
      if (currentMillis - previousMillis >= 20) {
        breatheEffect();
        previousMillis = currentMillis;
      }
      break;
      
    case EFFECT_RAINBOW:
      if (currentMillis - previousMillis >= 300) {
        rainbowEffect();
        previousMillis = currentMillis;
      }
      break;
      
    case EFFECT_WAVE:
      if (currentMillis - previousMillis >= 150) {
        waveEffect();
        previousMillis = currentMillis;
      }
      break;
      
    case EFFECT_FADE:
      if (currentMillis - previousMillis >= 30) {
        fadeEffect();
        previousMillis = currentMillis;
      }
      break;
      
    case EFFECT_STROBE:
      if (currentMillis - previousMillis >= 80) {
        strobeEffect();
        previousMillis = currentMillis;
      }
      break;
      
    case EFFECT_TWINKLE:
      if (currentMillis - previousMillis >= 200) {
        twinkleEffect();
        previousMillis = currentMillis;
      }
      break;
      
    case EFFECT_TEST:
      if (currentMillis - previousMillis >= 200) {
        testEffect();
        previousMillis = currentMillis;
      }
      break;
  }
}

// === CÁC HIỆU ỨNG LED ===

void allLedsOff() {
  for (int i = 0; i < NUM_LEDS; i++) {
    digitalWrite(LED_PINS[i], LOW);
  }
}

void allLedsOn() {
  for (int i = 0; i < NUM_LEDS; i++) {
    digitalWrite(LED_PINS[i], HIGH);
  }
}

void blinkEffect() {
  static bool state = false;
  state = !state;
  
  for (int i = 0; i < NUM_LEDS; i++) {
    digitalWrite(LED_PINS[i], state ? HIGH : LOW);
  }
}

void chaseEffect() {
  allLedsOff();
  digitalWrite(LED_PINS[stepCounter % NUM_LEDS], HIGH);
  stepCounter++;
}

void breatheEffect() {
  static bool increasing = true;
  static int brightness = 0;
  
  if (increasing) {
    brightness += 5;
    if (brightness >= 255) {
      brightness = 255;
      increasing = false;
    }
  } else {
    brightness -= 5;
    if (brightness <= 0) {
      brightness = 0;
      increasing = true;
    }
  }
  
  // Mô phỏng PWM bằng cách bật/tắt nhanh
  for (int i = 0; i < NUM_LEDS; i++) {
    analogWrite(LED_PINS[i], brightness);
  }
}

void rainbowEffect() {
  // Hiệu ứng cầu vồng đơn giản - lần lượt từng LED
  allLedsOff();
  for (int i = 0; i < (stepCounter % NUM_LEDS) + 1; i++) {
    digitalWrite(LED_PINS[i], HIGH);
  }
  stepCounter++;
  if (stepCounter >= NUM_LEDS * 2) stepCounter = 0;
}

void waveEffect() {
  // Hiệu ứng sóng - LED sáng lan tỏa từ giữa
  allLedsOff();
  int center = NUM_LEDS / 2;
  int spread = stepCounter % (NUM_LEDS / 2 + 1);
  
  for (int i = 0; i < spread; i++) {
    if (center - i >= 0) digitalWrite(LED_PINS[center - i], HIGH);
    if (center + i < NUM_LEDS) digitalWrite(LED_PINS[center + i], HIGH);
  }
  stepCounter++;
}

void fadeEffect() {
  static int brightness = 0;
  static bool increasing = true;
  
  if (increasing) {
    brightness += 3;
    if (brightness >= 255) {
      brightness = 255;
      increasing = false;
    }
  } else {
    brightness -= 3;
    if (brightness <= 0) {
      brightness = 0;
      increasing = true;
    }
  }
  
  for (int i = 0; i < NUM_LEDS; i++) {
    analogWrite(LED_PINS[i], brightness);
  }
}

void strobeEffect() {
  static bool state = false;
  state = !state;
  
  for (int i = 0; i < NUM_LEDS; i++) {
    digitalWrite(LED_PINS[i], state ? HIGH : LOW);
  }
}

void twinkleEffect() {
  // Tắt tất cả
  allLedsOff();
  
  // Bật ngẫu nhiên 1-3 LED
  int numTwinkle = random(1, 4);
  for (int i = 0; i < numTwinkle; i++) {
    int randomLed = random(0, NUM_LEDS);
    digitalWrite(LED_PINS[randomLed], HIGH);
  }
}

void testEffect() {
  // Test từng LED lần lượt
  allLedsOff();
  digitalWrite(LED_PINS[stepCounter % NUM_LEDS], HIGH);
  stepCounter++;
  
  if (stepCounter >= NUM_LEDS * 3) {
    currentEffect = EFFECT_OFF; // Kết thúc test
    stepCounter = 0;
  }
}

void testSequence() {
  Serial.println("Running startup test...");
  
  // Test từng LED
  for (int i = 0; i < NUM_LEDS; i++) {
    digitalWrite(LED_PINS[i], HIGH);
    delay(200);
    digitalWrite(LED_PINS[i], LOW);
  }
  
  // Sáng tất cả
  allLedsOn();
  delay(500);
  allLedsOff();
  delay(200);
  
  // Nhấp nháy 3 lần
  for (int i = 0; i < 3; i++) {
    allLedsOn();
    delay(150);
    allLedsOff();
    delay(150);
  }
  
  Serial.println("Test completed!");
}