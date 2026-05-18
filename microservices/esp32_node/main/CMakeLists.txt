idf_component_register(
    SRCS "main.c"
    INCLUDE_DIRS "include"
    REQUIRES
        nvs_flash
        esp_wifi
        esp_netif
        esp_event
        esp_http_server
        esp_timer
        driver
        esp_adc
        esp_websocket_client
        cjson
        sensor_dht20
        sensor_ltr390
        sensor_soil
        mole_ntp
)
