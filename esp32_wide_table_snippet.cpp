// =============================================================================
// Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
//
// AVISO DE PROPIEDAD INTELECTUAL:
// Este archivo es propiedad exclusiva de Mole.AI y sus autores originales.
// Queda estrictamente prohibida la copia, modificación, distribución,
// sublicenciamiento o uso comercial de este código, total o parcialmente,
// sin la autorización expresa y por escrito de los titulares del Copyright.
//
// Cualquier uso no autorizado será perseguido conforme a la Ley Federal
// del Derecho de Autor (México) y tratados internacionales aplicables.
// =============================================================================
// ==========================================================================
// ESP32 – Mole-AI Sensor Data POST (Wide Table format)
// ==========================================================================
// Envía datos de sensores directamente como columnas planas al endpoint
// Django: POST /api/v1/sensor-data/
//
// Dependencias: ArduinoJson 7.x, WiFi, HTTPClient
//
// ETSI EN 303 645 — Anti-replay:
//   El servidor rechaza lecturas con timestamp > 60s de antigüedad.
//   Se sincroniza el reloj NTP al boot para garantizar que recorded_at
//   sea válido dentro de la ventana permitida.
// ==========================================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <time.h>   // NTP sync

// ---- Configuración ----
const char* WIFI_SSID     = "TU_SSID";
const char* WIFI_PASSWORD = "TU_PASSWORD";
const char* SERVER_URL    = "http://TU_SERVER:8000/api/v1/sensor-data/";
const char* API_KEY       = "TU_HARDWARE_API_KEY";
const char* PLANT_ID      = "11111111-1111-1111-1111-111111111111"; // UUID de la planta

// ---- NTP ----
const char* NTP_SERVER    = "pool.ntp.org";
const long  GMT_OFFSET    = 0;   // UTC
const int   DST_OFFSET    = 0;

// ---- Intervalo de envío (ms) ----
const unsigned long SEND_INTERVAL = 60000;  // 1 minuto

// Genera un timestamp ISO 8601 UTC a partir del reloj NTP sincronizado.
String getISO8601Timestamp() {
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
        Serial.println("⚠️ NTP no sincronizado — omitiendo recorded_at");
        return "";
    }
    char buf[30];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
    return String(buf);
}

void setup() {
    Serial.begin(115200);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi conectado");

    // Sincronizar reloj NTP (ETSI EN 303 645 — requisito anti-replay)
    configTime(GMT_OFFSET, DST_OFFSET, NTP_SERVER);
    Serial.print("Sincronizando NTP");
    struct tm timeinfo;
    int retries = 0;
    while (!getLocalTime(&timeinfo) && retries < 10) {
        delay(1000);
        Serial.print(".");
        retries++;
    }
    Serial.println("\nNTP sincronizado ✅");
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

    // ETSI EN 303 645: incluir recorded_at con timestamp NTP sincronizado.
    // El servidor rechazará payloads con timestamp > 60s de antigüedad.
    String ts = getISO8601Timestamp();
    if (ts.length() > 0) {
        doc["recorded_at"] = ts;
    }

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
