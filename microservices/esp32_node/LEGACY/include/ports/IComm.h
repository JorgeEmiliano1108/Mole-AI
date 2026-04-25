#pragma once
#include "domain/TelemetryData.h"

namespace MoleAI {
namespace Ports {

    class IComm {
    public:
        virtual ~IComm() = default;

        // Inicializa el stack de comunicaciones
        virtual bool begin() = 0;

        // Intenta enviar los datos. Retorna true si tuvo éxito.
        virtual bool sendData(const Domain::TelemetryData& data) = 0;

        // Verifica si el canal está disponible actualmente
        virtual bool isConnected() = 0;
    };

} // namespace Ports
} // namespace MoleAI