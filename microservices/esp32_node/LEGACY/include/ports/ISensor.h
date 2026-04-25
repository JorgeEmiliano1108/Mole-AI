#pragma once
#include "../domain/TelemetryData.h"

namespace MoleAI {
namespace Ports {

    class ISensor {
    public:
        // Destructor virtual: Buena práctica en C++ para interfaces
        virtual ~ISensor() = default;

        // Inicializa el hardware (Ej. Wire.begin() para I2C)
        // Retorna true si el sensor se inicializó correctamente
        virtual bool init() = 0;

        // Lee el sensor e inyecta los datos en la estructura de telemetría
        virtual void read(Domain::TelemetryData& data) = 0;
    };

} // namespace Ports
} // namespace MoleAI