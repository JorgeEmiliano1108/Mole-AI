/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * mole_identity.h — Zero-Trust device identity via Ed25519 keypair in NVS
 *
 * LFPDPPP: No PII stored. Device identity = Ed25519 public key.
 * Zero-Trust: Private key never leaves the NVS encrypted partition.
 * =============================================================================
 */
#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct mole_identity *mole_identity_handle_t;

/**
 * @brief Initialize device identity.
 *
 * On first boot: generates an Ed25519 keypair using the hardware RNG
 * and stores it in the encrypted NVS partition.
 * On subsequent boots: loads the existing keypair from NVS.
 *
 * @param out_handle  Pointer to receive identity handle
 */
esp_err_t mole_identity_init(mole_identity_handle_t *out_handle);

/**
 * @brief Get the public key as a hex string (64 chars + null).
 */
esp_err_t mole_identity_get_public_key_hex(mole_identity_handle_t handle,
                                            char *out_hex, size_t out_len);

/**
 * @brief Sign a payload with the device's Ed25519 private key.
 *
 * @param handle   Identity handle
 * @param data     Data to sign
 * @param data_len Length of data
 * @param sig      Buffer for 64-byte signature
 * @param sig_len  Will be set to actual signature length
 */
esp_err_t mole_identity_sign(mole_identity_handle_t handle,
                              const uint8_t *data, size_t data_len,
                              uint8_t *sig, size_t *sig_len);

#ifdef __cplusplus
}
#endif
