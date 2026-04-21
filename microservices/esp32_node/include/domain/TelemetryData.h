#pragma once
#include <Arduino.h>

namespace MoleAI {
namespace Domain {

    // Estructura que almacena todas las lecturas de un ciclo
    struct TelemetryData {
        String device_id;
        unsigned long timestamp;
        float bat_lvl;
        String conn_type; // "wifi" o "ble"
        
        // Datos ambientales (DHT20)
        float temp_c;
        float hum_pct;
        
        // Datos de suelo (Capacitivo Analógico)
        float soil_moist_pct;
        
        // Datos de luz (LTR390-UV)
        float light_lux;
        float uv_index;

        // Constructor para inicializar valores por defecto (evitar basura en memoria)
        TelemetryData() : 
            device_id(""), timestamp(0), bat_lvl(0.0), conn_type("none"),
            temp_c(0.0), hum_pct(0.0), soil_moist_pct(0.0), light_lux(0.0), uv_index(0.0) {}
    };

} // namespace Domain
} // namespace MoleAI










