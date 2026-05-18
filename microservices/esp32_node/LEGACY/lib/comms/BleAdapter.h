#pragma once
#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include "../../include/ports/IComm.h"

// UUIDs únicos para identificar a Mole.AI en el aire
#define MOLE_SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define MOLE_CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

namespace MoleAI {
namespace Adapters {

    // Heredamos de IComm (nuestro puerto) y de BLEServerCallbacks (para saber si se conectó el celular)
    class BleAdapter : public Ports::IComm, public BLEServerCallbacks {
    private:
        BLEServer* _pServer = nullptr;
        BLECharacteristic* _pCharacteristic = nullptr;
        bool _deviceConnected = false;
        String _deviceName;

    public:
        // Constructor: Recibe el nombre con el que el ESP32 aparecerá en el celular
        BleAdapter(String deviceName = "Mole_Node_01") : _deviceName(deviceName) {}

        // --- Callbacks de Conexión BLE ---
        void onConnect(BLEServer* pServer) override {
            _deviceConnected = true;
            Serial.println("Agrónomo conectado por BLE");
        }

        void onDisconnect(BLEServer* pServer) override {
            _deviceConnected = false;
            Serial.println("Agrónomo desconectado. Reiniciando Advertising...");
            // Si el celular se va, volvemos a transmitir para que otro se pueda conectar
            BLEDevice::startAdvertising();
        }

        // --- Implementación de IComm ---
        bool begin() override {
            // 1. Inicializamos el chip Bluetooth
            BLEDevice::init(_deviceName.c_str());

            // Nota LFPDPPP / IFT-016: Usamos la potencia por defecto del ESP32 para
            // no violar los límites de transmisión y ahorrar batería.

            // 2. Creamos el Servidor GATT y le asignamos nuestros callbacks
            _pServer = BLEDevice::createServer();
            _pServer->setCallbacks(this);

            // 3. Creamos el Servicio Principal (Como si fuera el "canal")
            BLEService *pService = _pServer->createService(MOLE_SERVICE_UUID);

            // 4. Creamos la Característica (El "buzón" donde pondremos los datos)
            // Habilitamos READ y NOTIFY para que la app se actualice sola
            _pCharacteristic = pService->createCharacteristic(
                                    MOLE_CHARACTERISTIC_UUID,
                                    BLECharacteristic::PROPERTY_READ |
                                    BLECharacteristic::PROPERTY_NOTIFY
                                );

            // Añadimos un descriptor estándar para que las notificaciones BLE funcionen en iOS y Android
            _pCharacteristic->addDescriptor(new BLE2902());

            // 5. Encendemos el servicio
            pService->start();

            // 6. Empezamos a gritar "¡Estoy aquí!" (Advertising)
            BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
            pAdvertising->addServiceUUID(MOLE_SERVICE_UUID);
            pAdvertising->setScanResponse(false);
            pAdvertising->setMinPreferred(0x0); // Configuración recomendada por Apple/Google
            BLEDevice::startAdvertising();

            return true;
        }

        bool isConnected() override {
            return _deviceConnected;
        }

        bool sendData(const Domain::TelemetryData& data) override {
            if (!_deviceConnected) return false; // No gastamos energía si no hay nadie escuchando

            // Serializamos los datos a nuestro JSON Wide Table
            String payload = "{";
            payload += "\"dev_id\":\"" + data.device_id + "\",";
            payload += "\"temp\":" + String(data.temp_c) + ",";
            payload += "\"hum\":" + String(data.hum_pct) + ",";
            payload += "\"soil\":" + String(data.soil_moist_pct) + ",";
            payload += "\"light\":" + String(data.light_lux);
            payload += "}";

            // Empaquetamos el JSON en la característica y notificamos a la App
            _pCharacteristic->setValue(payload.c_str());
            _pCharacteristic->notify();

            return true;
        }
    };

} // namespace Adapters
} // namespace MoleAI