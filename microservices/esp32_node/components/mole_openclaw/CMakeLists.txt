idf_component_register(
    SRCS "mole_openclaw.c"
    INCLUDE_DIRS "include"
    REQUIRES
        sensor_dht20
        sensor_ltr390
        sensor_soil
        mole_identity
        mole_ntp
        cjson
        main
        esp-openclaw-node
)
