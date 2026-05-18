#pragma once
#include <Arduino.h>
#include "../../include/ports/ISensor.h"

namespace MoleAI {
namespace Adapters {

    // Heredamos (implementamos) el contrato ISensor que creaste antes
    class AnalogMoisture : public Ports::ISensor {
    private:
        int _pin;
        int _airValue;   // Valor crudo cuando el sensor está al aire libre (seco)
        int _waterValue; // Valor crudo cuando el sensor está sumergido (mojado)

    public:
        // Constructor: Recibe el pin y los valores de calibración
        // En el ESP32, el ADC suele ir de 0 a 4095.
        AnalogMoisture(int pin, int airValue = 4095, int waterValue = 1500) 
            : _pin(pin), _airValue(airValue), _waterValue(waterValue) {}

        // Implementación obligatoria 1: Inicializar
        bool init() override {
            pinMode(_pin, INPUT);
            return true; 
        }

        // Implementación obligatoria 2: Leer e inyectar en tu Wide Table
        void read(Domain::TelemetryData& data) override {
            int rawValue = analogRead(_pin);
            
            // Mapeamos el valor crudo a un porcentaje (0% a 100%)
            float pct = map(rawValue, _airValue, _waterValue, 0, 100);
            
            // Constrain asegura que si el valor se pasa, no envíe un -5% o 110%
            data.soil_moist_pct = constrain(pct, 0.0, 100.0);
        }
    };

} // namespace Adapters
} // namespace MoleAI