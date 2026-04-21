// =============================================================================
// Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
// =============================================================================
// IFT-016 COMPLIANCE NOTICE:
// This firmware does NOT modify the ESP32's default Wi-Fi or BLE transmission
// power registers.  No calls to esp_wifi_set_max_tx_power() or
// esp_ble_tx_power_set() are present.  The default SDK gain values comply
// with the maximum EIRP limits established by IFT-016 for unlicensed
// operation in the 2.4 GHz ISM band within Mexican territory.
// =============================================================================

#include <Arduino.h>
#include <Wire.h>
#include <esp_sleep.h>
#include "core/TelemetryUseCase.h"
#include "../lib/sensors/Dht20Adapter.h"
#include "../lib/sensors/Ltr390Adapter.h"
#include "../lib/sensors/AnalogMoisture.h"
#include "../lib/comms/WifiMqttAdapter.h"
#include "../lib/comms/BleAdapter.h"

using namespace MoleAI;

// 1. Definición de Hardware y Credenciales
const char* WIFI_SSID = "Tu_Red_WiFi";
const char* WIFI_PASS = "Tu_Password";
const char* MQTT_BROKER = "192.168.1.100"; // IP de tu Edge Node
const int SOIL_PIN = 34; // Pin ADC para sensor capacitivo

// Deep Sleep interval: 5 minutes (300 seconds) — configurable per agronomist
static constexpr uint64_t DEEP_SLEEP_INTERVAL_US = 300ULL * 1000000ULL;

// 2. Instanciamos los Adaptadores (Objetos concretos)
Adapters::Dht20Adapter dht20;
Adapters::Ltr390Adapter ltr390;
Adapters::AnalogMoisture soilSensor(SOIL_PIN);
Adapters::WifiMqttAdapter wifiComm(WIFI_SSID, WIFI_PASS, MQTT_BROKER, 1883);
Adapters::BleAdapter bleComm("Mole_Node_Emiliano");

// 3. El Cerebro
Core::TelemetryUseCase moleCore("NODE-EMILIANO-001");

void setup() {
    Serial.begin(115200);
    Wire.begin(); // Iniciamos I2C para DHT20 y LTR390

    // Inyección de Dependencias: Conectamos los adaptadores al núcleo
    moleCore.addSensor(&dht20);
    moleCore.addSensor(&ltr390);
    moleCore.addSensor(&soilSensor);
    
    moleCore.addComm(&wifiComm); // Prioridad 1: WiFi
    moleCore.addComm(&bleComm);  // Prioridad 2: Bluetooth

    moleCore.initAll();
    Serial.println("🌿 Mole.AI Sensor Node Inicializado");
}

void loop() {
    // Ejecutamos la lógica de lectura y envío
    moleCore.executeCycle();

    // Enter Deep Sleep to conserve battery.
    // The ESP32 will wake up after DEEP_SLEEP_INTERVAL_US and restart
    // from setup(). This is the production-grade power management mode.
    Serial.println("💤 Entering Deep Sleep...");
    Serial.flush();
    esp_sleep_enable_timer_wakeup(DEEP_SLEEP_INTERVAL_US);
    esp_deep_sleep_start();
    // Execution never reaches here — the chip resets on wake-up.
}