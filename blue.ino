#include <SPI.h>
#include <GxEPD2_BW.h>
#include <Adafruit_GFX.h>
#include <Fonts/FreeSansBold9pt7b.h>
#include <Fonts/FreeSans9pt7b.h>
#include <qrcode_gen.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <Preferences.h>

/* ===== PIN YAPARLARI (LILYGO T-DISPLAY-S3 EPD) ===== */
#define EPD_BUSY    2
#define EPD_RST     3
#define EPD_DC      4
#define EPD_CS      5
#define EPD_CLK     6
#define EPD_DIN     7
#define BUTTON_PIN  10 

GxEPD2_BW<GxEPD2_290_T94, GxEPD2_290_T94::HEIGHT> display(GxEPD2_290_T94(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));
Preferences preferences;

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

String displayName, displayTitle, displayURL;
bool shouldUpdate = false, isBTActive = false; 

// Reset ve Buton Zamanlayıcıları
unsigned long buttonPressStartTime = 0;
bool isButtonPressed = false;
bool resetTriggered = false;

/* ===== YARDIMCI FONKSİYONLAR ===== */
String formatText(String metin) {
    metin.replace("\\u0026", "&"); metin.replace("u0026", "&");
    metin.replace("\\u002D", "-"); metin.replace("u002D", "-");
    metin.replace("ç", "c"); metin.replace("Ç", "C");
    metin.replace("ğ", "g"); metin.replace("Ğ", "G");
    metin.replace("ı", "i"); metin.replace("İ", "I");
    metin.replace("ö", "o"); metin.replace("Ö", "O");
    metin.replace("ş", "s"); metin.replace("Ş", "S");
    metin.replace("ü", "u"); metin.replace("Ü", "U");
    metin.trim();
    return metin;
}

// Dikey yüksekliği sığdırmak için ölçüm yapar
int calculateWrappedHeight(String text, int maxWidth, int lineSpacing, const GFXfont* f) {
    display.setFont(f);
    int16_t x1, y1; uint16_t w, h;
    String currentLine = ""; int currentY = 0; int start = 0;
    while (start < text.length()) {
        int end = text.indexOf(' ', start);
        if (end == -1) end = text.length();
        String word = text.substring(start, end);
        String testLine = (currentLine == "" ? "" : currentLine + " ") + word;
        display.getTextBounds(testLine, 0, 0, &x1, &y1, &w, &h);
        if (w > maxWidth && currentLine != "") {
            currentY += lineSpacing; currentLine = word;
        } else { currentLine = testLine; }
        start = end + 1;
    }
    return currentY + 15;
}

// Metni ekrana sığdırarak basan motor
int printEngine(String text, int x, int y, int maxWidth, int maxHeight, int lineSpacing, const GFXfont* f) {
    display.setFont(f);
    int16_t x1, y1; uint16_t w, h;
    String currentLine = ""; int currentY = y; int start = 0;
    while (start < text.length()) {
        int end = text.indexOf(' ', start);
        if (end == -1) end = text.length();
        String word = text.substring(start, end);
        String testLine = (currentLine == "" ? "" : currentLine + " ") + word;
        display.getTextBounds(testLine, 0, 0, &x1, &y1, &w, &h);
        if (w > maxWidth && currentLine != "") {
            display.setCursor(x, currentY); display.print(currentLine);
            currentY += lineSpacing; currentLine = word;
            if (currentY > maxHeight) return currentY; 
        } else { currentLine = testLine; }
        start = end + 1;
    }
    if (currentY <= maxHeight + 5) {
        display.setCursor(x, currentY); display.print(currentLine);
    }
    return currentY;
}

/* ===== BLUETOOTH CALLBACKS ===== */
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      std::string value = pCharacteristic->getValue();
      if (value.length() > 0) {
        String data = String(value.c_str());
        int p1 = data.indexOf('*');
        int lastP = data.lastIndexOf('*');
        if(p1 != -1 && lastP != -1 && p1 != lastP) {
          displayName = data.substring(0, p1);
          displayTitle = data.substring(p1 + 1, lastP);
          displayURL = data.substring(lastP + 1);
          preferences.begin("badge", false);
          preferences.putString("name", displayName);
          preferences.putString("title", displayTitle);
          preferences.putString("url", displayURL);
          preferences.end();
          shouldUpdate = true;
        }
      }
    }
};

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  SPI.begin(EPD_CLK, -1, EPD_DIN, EPD_CS);
  display.init(115200);
  display.setRotation(2);

  preferences.begin("badge", true);
  displayName = preferences.getString("name", "Huseyin CAKIR");
  displayTitle = preferences.getString("title", "Designer & AI Product Builder");
  displayURL = preferences.getString("url", "https://google.com");
  preferences.end();

  BLEDevice::init("Badge_Pro_V31");
  BLEServer *pServer = BLEDevice::createServer();
  BLEService *pService = pServer->createService(SERVICE_UUID);
  BLECharacteristic *pChar = pService->createCharacteristic(CHARACTERISTIC_UUID, BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_READ);
  pChar->setCallbacks(new MyCallbacks());
  pService->start();
  BLEDevice::getAdvertising()->addServiceUUID(SERVICE_UUID);
  
  drawBadge();
}

void loop() {
  bool currentButtonState = (digitalRead(BUTTON_PIN) == LOW);

  if (currentButtonState) {
    if (!isButtonPressed) {
      buttonPressStartTime = millis();
      isButtonPressed = true;
      resetTriggered = false;
    } else {
      unsigned long pressDuration = millis() - buttonPressStartTime;
      
      // 10 Saniye dolduğunda RESET işlemi
      if (pressDuration >= 10000 && !resetTriggered) {
        resetTriggered = true;
        
        display.setFullWindow();
        display.firstPage();
        do {
            display.fillScreen(GxEPD_WHITE);
            display.setTextColor(GxEPD_BLACK);
            display.setFont(&FreeSansBold9pt7b);
            display.setCursor(15, 140); 
            display.print("RESETLENIYOR...");
        } while (display.nextPage());

        preferences.begin("badge", false);
        preferences.clear();
        preferences.end();
        
        delay(2000);
        ESP.restart(); 
      }
    }
  } else {
    if (isButtonPressed) {
      unsigned long pressDuration = millis() - buttonPressStartTime;
      if (pressDuration < 10000 && pressDuration > 50) {
        isBTActive = !isBTActive;
        if (isBTActive) BLEDevice::getAdvertising()->start(); 
        else BLEDevice::getAdvertising()->stop();
        drawBadge();
      }
      isButtonPressed = false;
    }
  }

  if (shouldUpdate) { drawBadge(); shouldUpdate = false; }
}

void drawBadge() {
  display.setFullWindow();
  display.firstPage();
  do {
    display.fillScreen(GxEPD_WHITE);
    display.setTextColor(GxEPD_BLACK);

    // Üst Bölüm
    display.setFont(); 
    display.setCursor(45, 7);
    display.print(isBTActive ? "BT: ON" : "BT: OFF");
    display.drawFastHLine(0, 18, 128, GxEPD_BLACK);

    // QR Ayırıcı Çizgisi
    int sepY = display.height() - 135; 
    display.drawFastHLine(0, sepY, 128, GxEPD_BLACK);

    int safeWidth = 110; // R harfi ve taşmalar için en güvenli alan
    String cleanName = formatText(displayName);
    String cleanTitle = formatText(displayTitle);

    // 1. İsim Yazımı (Bold)
    display.setFont(&FreeSansBold9pt7b);
    int nameLastY = printEngine(cleanName, 5, 40, safeWidth, sepY - 50, 22, &FreeSansBold9pt7b);

    // 2. Unvan Yazımı (Kademeli Ölçekleme)
    int titleStartY = nameLastY + 25;
    int availableHeight = sepY - titleStartY - 5;
    int h9 = calculateWrappedHeight(cleanTitle, safeWidth, 18, &FreeSans9pt7b);
    
    if (h9 <= availableHeight) {
        printEngine(cleanTitle, 5, titleStartY, safeWidth, sepY - 10, 18, &FreeSans9pt7b);
    } else {
        display.setFont(NULL); // Sığmıyorsa varsayılan küçük fonta geç
        display.setTextSize(1);
        printEngine(cleanTitle, 5, titleStartY, safeWidth, sepY - 5, 10, NULL);
    }

    // 3. QR Kod Çizimi
    QRCode qrcode;
    uint8_t qrcodeData[qrcode_getBufferSize(5)]; 
    qrcode_initText(&qrcode, qrcodeData, 5, ECC_LOW, displayURL.c_str());
    int scale = 3; int qrSize = qrcode.size * scale;
    int yOff = sepY + 12;
    int xOff = (128 - qrSize) / 2;
    display.fillRect(xOff - 2, yOff - 2, qrSize + 4, qrSize + 4, GxEPD_WHITE);
    for (uint8_t y = 0; y < qrcode.size; y++) {
      for (uint8_t x = 0; x < qrcode.size; x++) {
        if (qrcode_getModule(&qrcode, x, y)) {
          display.fillRect(xOff + x * scale, yOff + y * scale, scale, scale, GxEPD_BLACK);
        }
      }
    }
  } while (display.nextPage());
  display.hibernate();
}