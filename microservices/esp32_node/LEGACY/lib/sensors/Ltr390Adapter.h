#pragma once
#include <Arduino.h>
#include <Wire.h>
#include "Adafruit_LTR390.h"
#include "../../include/ports/ISensor.h"

namespace MoleAI {
namespace Adapters {

    class Ltr390Adapter : public Ports::ISensor {
    private:
        Adafruit_LTR390 _ltr;

    public:
        Ltr390Adapter() {}

        bool init() override {
            if (!_ltr.begin()) {
                return false; // Falla si el sensor no responde en el bus I2C
            }
            // Configuramos la sensibilidad del sensor (Ganancia 3 y 16 bits son ideales para sol)
            _ltr.setGain(LTR390_GAIN_3);
            _ltr.setResolution(LTR390_RESOLUTION_16BIT);
            return true;
        }

        void read(Domain::TelemetryData& data) override {
            // 1. Leer Luz Ambiental (ALS - Ambient Light Sensor)
            _ltr.setMode(LTR390_MODE_ALS);
            delay(100); // Pequeña pausa para que el chip cambie su cristal interno
            if (_ltr.newDataAvailable()) {
                data.light_lux = _ltr.readALS();
            }

            // 2. Leer Índice Ultravioleta (UVS)
            _ltr.setMode(LTR390_MODE_UVS);
            delay(100); 
            if (_ltr.newDataAvailable()) {
                // readUVS da el valor crudo, se divide entre un factor (usualmente ~2300 para LTR390) 
                // para sacar el Índice UV real (0 a 11+). Adafruit lo maneja en crudo, 
                // así que lo enviaremos y el backend (CAG) hará la normalización si es necesario.
                data.uv_index = _ltr.readUVS();
            }
        }
    };

} // namespace Adapters
} // namespace MoleAI