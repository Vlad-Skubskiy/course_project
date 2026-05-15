#include <SPI.h>
#include <Adafruit_PN532.h>
#include <WiFi.h>
#include <HTTPClient.h>

// Конфігурація Wi-Fi та Сервера
const char* ssid = "TP-Link_C694_2.4G";
const char* password = "33173924";
const char* serverUrl = "http://192.168.0.92:8000/api/scan"; // Твій IPv4 з ipconfig

// Піни SPI (PN532)
#define PN532_SCK  (18)
#define PN532_MISO (19)
#define PN532_MOSI (23)
#define PN532_SS   (5)
#define BUZZER_PIN (17)

Adafruit_PN532 nfc(PN532_SCK, PN532_MISO, PN532_MOSI, PN532_SS);

void setup(void) {
  Serial.begin(115200);
  pinMode(BUZZER_PIN, OUTPUT);

  // 1. Підключення до Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Підключення до Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi підключено!");

  // 2. Ініціалізація PN532
  nfc.begin();
  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.print("PN532 не знайдено!");
    while (1);
  }
  nfc.SAMConfig();
  
  // Звуковий сигнал готовності
  tone(BUZZER_PIN, 2000, 200);
  Serial.println("DeltaPlan готовий до роботи...");
}

void loop(void) {
  uint8_t success;
  uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };
  uint8_t uidLength;

  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 500);

  if (success) {
    // 3. Перетворюємо UID у String (Hex формат)
    String uidString = "";
    for (uint8_t i = 0; i < uidLength; i++) {
      if (uid[i] < 0x10) uidString += "0";
      uidString += String(uid[i], HEX);
    }
    uidString.toUpperCase();

    Serial.println("Зчитано карту: " + uidString);
    tone(BUZZER_PIN, 200, 100);

    // 4. Відправка на сервер
    sendToServer(uidString);
    
    delay(2000); // Пауза, щоб не дублювати зчитування
  }
}

void sendToServer(String uid) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    // Формуємо JSON вручну (щоб не тягнути важку ArduinoJson для одного запиту)
    String json = "{\"nfc_uuid\": \"" + uid + "\", \"device_id\": \"ESP32_PillBox_1\"}";

    int httpResponseCode = http.POST(json);

    if (httpResponseCode > 0) {
      Serial.print("Сервер відповів: ");
      Serial.println(httpResponseCode);
    } else {
      Serial.print("Помилка запиту: ");
      Serial.println(http.errorToString(httpResponseCode).c_str());
    }
    http.end();
  } else {
    Serial.println("Wi-Fi розірвано!");
  }
}