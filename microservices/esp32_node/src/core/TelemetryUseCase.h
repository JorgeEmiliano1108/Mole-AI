#pragma once
#include <vector>
#include "../domain/TelemetryData.h"
#include "../ports/ISensor.h"
#include "../ports/IComm.h"

namespace MoleAI {
namespace Core {

    class TelemetryUseCase {
    private:
        std::vector<Ports::ISensor*> _sensors;
        std::vector<Ports::IComm*> _comms;
        String _deviceId;

    public:
        TelemetryUseCase(String deviceId) : _deviceId(deviceId) {}

        // Inyectamos los adaptadores a través de los puertos
        void addSensor(Ports::ISensor* sensor) { _sensors.push_back(sensor); }
        void addComm(Ports::IComm* comm) { _comms.push_back(comm); }

        void initAll() {
            for (auto s : _sensors) s->init();
            for (auto c : _comms) c->begin();
        }

        void executeCycle() {
            Domain::TelemetryData data;
            data.device_id = _deviceId;
            data.timestamp = millis(); // O usar un RTC si está disponible

            // 1. Recolección de datos (RAG-Ready)
            for (auto s : _sensors) {
                s->read(data);
            }

            // 2. Orquestación de Envío Híbrido (Lógica de Negocio)
            bool sent = false;
            
            // Intentamos enviar por cada canal disponible (WiFi -> BLE)
            for (auto c : _comms) {
                if (c->sendData(data)) {
                    Serial.printf("Datos enviados.\n");
                    sent = true;
                    break; // Salimos si ya se envió por el canal prioritario
                }
            }

            if (!sent) {
                Serial.println("Error: Todos los canales de comunicación fallaron.");
                // Aquí se podría llamar a un IStoragePort en el futuro (Store & Forward)
            }
        }
    };

} // namespace Core
} // namespace MoleAI