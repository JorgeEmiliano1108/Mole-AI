idf_component_register(
    SRCS "main.c"
    INCLUDE_DIRS "include"
    REQUIRES
        nvs_flash
        esp_wifi
        esp_netif
        esp_event
        driver
        esp_adc
        mbedtls
        wifi_provisioning
        sensor_dht20
        sensor_ltr390
        sensor_soil
        mole_identity
        mole_ntp
        mole_openclaw
)
