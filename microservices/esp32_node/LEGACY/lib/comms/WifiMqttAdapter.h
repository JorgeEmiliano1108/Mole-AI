#pragma once
#include <WiFi.h>
#include <PubSubClient.h>
#include "../../include/ports/IComm.h"

namespace MoleAI {
namespace Adapters {

    class WifiMqttAdapter : public Ports::IComm {
    private:
        const char* _ssid;
        const char* _password;
        const char* _mqttServer;
        int _mqttPort;
        
        WiFiClient _espClient;
        PubSubClient _mqttClient;

    public:
        WifiMqttAdapter(const char* ssid, const char* pass, const char* broker, int port) 
            : _ssid(ssid), _password(pass), _mqttServer(broker), _mqttPort(port), _mqttClient(_espClient) {}

        bool begin() override {
            // IFT-016 COMPLIANCE: WiFi.begin() uses the ESP32's default TX
            // power (≈ 20 dBm).  We intentionally do NOT call
            // esp_wifi_set_max_tx_power() to stay within IFT-016 EIRP limits
            // for unlicensed 2.4 GHz ISM operation in Mexico.
            WiFi.begin(_ssid, _password);
            _mqttClient.setServer(_mqttServer, _mqttPort);
            return true; 
        }

        bool isConnected() override {
            return (WiFi.status() == WL_CONNECTED && _mqttClient.connected());
        }

        bool sendData(const Domain::TelemetryData& data) override {
            if (!isConnected()) return false;

            // === JSON Payload compatible con Django SensorBatchReadingSerializer ===
            // Campos: device_id, recorded_at, air_temperature, air_humidity, 
            // soil_moisture, light_level, uv_index
            String payload = "{";
            payload += "\"device_id\":\"" + data.device_id + "\",";
            payload += "\"recorded_at\":\"" + data.timestamp + "\",";
            payload += "\"air_temperature\":" + String(data.temp_c, 1) + ",";
            payload += "\"air_humidity\":" + String(data.hum_pct, 1) + ",";
            payload += "\"soil_moisture\":" + String(data.soil_moist_pct, 1) + ",";
            payload += "\"light_level\":" + String(data.light_lux, 1) + ",";
            payload += "\"uv_index\":" + String(data.uv_index, 1);
            payload += "}";

            // === Topic MQTT dinámico (C-001) ===
            // Formato: mole/sensors/ESP-A1B2C3
            String topic = "mole/sensors/" + data.device_id;
            
            return _mqttClient.publish(topic.c_str(), payload.c_str());
        }
    };

} // namespace Adapters
} // namespace MoleAI