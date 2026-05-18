cmake_minimum_required(VERSION 3.16)

# =============================================================================
# Mole.AI — ESP32 Telemetry Node (Bare-Metal)
# ESP-IDF 5.x Native Firmware
# =============================================================================
# IFT-016 COMPLIANCE: Default SDK TX power. No EIRP overrides.
# ETSI EN 303 645: NTP-synchronized timestamps on all telemetry.
# LFPDPPP: Zero PII in flash. Identity = Device Token (UUID).
# =============================================================================

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(mole_telemetry_node)
