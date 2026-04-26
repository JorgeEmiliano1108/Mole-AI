idf_component_register(
    SRCS "mole_identity.c"
    INCLUDE_DIRS "include"
    REQUIRES nvs_flash mbedtls main
)
