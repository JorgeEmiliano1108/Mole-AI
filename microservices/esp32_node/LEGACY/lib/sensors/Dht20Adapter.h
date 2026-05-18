#pragma once
#include <Arduino.h>
#include <Wire.h>          // Librería nativa de I2C
#include "DHT20.h"         // Librería del fabricante
#include "../../include/ports/ISensor.h"

namespace MoleAI {
namespace Adapters {

    class Dht20Adapter : public Ports::ISensor {
    private:
        DHT20 _dht;

    public:
        // Constructor: Le pasamos la referencia del bus I2C (Wire)
        Dht20Adapter() : _dht(&Wire) {}

        bool init() override {
            // Wire.begin() se suele llamar en el main.cpp, pero es seguro iniciarlo aquí.
            // Si retorna false, significa que los cables SDA o SCL están mal conectados.
            return _dht.begin(); 
        }

        void read(Domain::TelemetryData& data) override {
            // dht.read() interroga al sensor físicamente
            if (_dht.read() == DHT20_OK) {
                data.temp_c = _dht.getTemperature();
                data.hum_pct = _dht.getHumidity();
            } else {
                // Si falla (ej. se desconectó el cable), podríamos poner -999 
                // para que la IA (mole_chat) sepa que el sensor está dañado.
                // Por ahora lo dejamos sin modificar (conserva el 0.0 o el valor anterior)
            }
        }
    };

} // namespace Adapters
} // namespace MoleAI