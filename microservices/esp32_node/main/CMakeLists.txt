idf_component_register(
    SRCS "main.c" "ble_provisioning.c" "payload_builder.c" "fee2_frame.c" "transport_layer.c" "state_machine.c" "offline_buffer.c"
    INCLUDE_DIRS "include"
    # Ancla CA de laboratorio (issue B-03): solo el cert público; la llave
    # vive en infrastructure/nginx/certs (gitignored).
    EMBED_TXTFILES "certs/lab_ca.pem"
    REQUIRES
        nvs_flash
        esp_wifi
        esp_netif
        esp_event
        esp_http_server
        esp_http_client
        esp_timer
        driver
        esp_adc
        esp_websocket_client
        cjson
        sensor_dht20
        sensor_ltr390
        sensor_soil
        mole_ntp
        bt
)
