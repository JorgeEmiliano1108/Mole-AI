// ==========================================================================
// ESP32 – Mole-AI Sensor Data POST (Wide Table format)
// ==========================================================================
// Envía datos de sensores directamente como columnas planas al endpoint
// Django: POST /api/v1/sensor-data/
//
// Dependencias: ArduinoJson 7.x, WiFi, HTTPClient
// ==========================================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ---- Configuración ----
const char* WIFI_SSID     = "TU_SSID";
const char* WIFI_PASSWORD = "TU_PASSWORD";
const char* SERVER_URL    = "http://TU_SERVER:8000/api/v1/sensor-data/";
const char* API_KEY       = "TU_HARDWARE_API_KEY";
const char* PLANT_ID      = "11111111-1111-1111-1111-111111111111"; // UUID de la planta

// ---- Intervalo de envío (ms) ----
const unsigned long SEND_INTERVAL = 60000;  // 1 minuto

void setup() {
    Serial.begin(115200);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi conectado");
}

void sendSensorData(float soilHumidity, float airTemp,
                    float uvIndex, float lightLevel, float phLevel) {
    if (WiFi.status() != WL_CONNECTED) return;

    HTTPClient http;
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Hardware-Api-Key", API_KEY);

    // Construir JSON plano (Wide Table)
    JsonDocument doc;
    doc["plant_id"]        = PLANT_ID;
    // recorded_at es opcional: el servidor puede usar now() si se omite
    doc["soil_humidity"]    = soilHumidity;
    doc["air_temperature"]  = airTemp;
    doc["uv_index"]         = uvIndex;
    doc["light_level"]      = lightLevel;
    doc["ph_level"]         = phLevel;

    String payload;
    serializeJson(doc, payload);

    int httpCode = http.POST(payload);
    if (httpCode == 201) {
        Serial.println("✅ Datos enviados OK");
    } else {
        Serial.printf("⚠️ Error HTTP %d: %s\n", httpCode,
                       http.getString().c_str());
    }
    http.end();
}

void loop() {
    // --- Leer sensores reales aquí ---
    float soilHumidity   = analogRead(34) / 40.95;  // Ejemplo: 0-100%
    float airTemp        = 25.0;  // Reemplazar con lectura real (DHT22, etc.)
    float uvIndex        = 5.0;   // Reemplazar con sensor UV
    float lightLevel     = 400.0; // Reemplazar con LDR / BH1750
    float phLevel        = 6.5;   // Reemplazar con sensor pH

    sendSensorData(soilHumidity, airTemp, uvIndex, lightLevel, phLevel);

    delay(SEND_INTERVAL);
}
