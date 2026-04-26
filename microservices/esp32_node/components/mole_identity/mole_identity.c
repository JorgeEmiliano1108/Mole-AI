/*
 * =============================================================================
 * Copyright (C) 2024-2026 Mole.AI — All Rights Reserved.
 * =============================================================================
 * mole_identity.c — Ed25519 device identity (Zero-Trust)
 *
 * Uses mbedTLS ECDSA with Curve25519 for device-level signing.
 * Private key generated on-chip via hardware RNG on first boot.
 * Stored in NVS encrypted partition — never exported.
 *
 * LFPDPPP: No PII. Identity = public key fingerprint.
 * =============================================================================
 */

#include <string.h>
#include <stdio.h>
#include "esp_log.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "mbedtls/pk.h"
#include "mbedtls/entropy.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/ecp.h"
#include "mbedtls/ecdsa.h"
#include "mole_config.h"
#include "mole_identity.h"

static const char *TAG = "MOLE_ID";

struct mole_identity {
    mbedtls_pk_context      pk;
    mbedtls_entropy_context entropy;
    mbedtls_ctr_drbg_context drbg;
    uint8_t pub_key[MOLE_ED25519_PUB_LEN];
    bool    initialized;
};

/* ── Helpers ─────────────────────────────────────────────────────────────── */

static void bytes_to_hex(const uint8_t *in, size_t in_len,
                         char *out, size_t out_len)
{
    for (size_t i = 0; i < in_len && (i * 2 + 2) < out_len; i++) {
        sprintf(out + (i * 2), "%02x", in[i]);
    }
    out[in_len * 2] = '\0';
}

static esp_err_t save_key_to_nvs(const uint8_t *priv, size_t priv_len,
                                  const uint8_t *pub, size_t pub_len)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(MOLE_NVS_NAMESPACE, NVS_READWRITE, &h);
    if (err != ESP_OK) return err;

    err = nvs_set_blob(h, MOLE_NVS_KEY_PRIV, priv, priv_len);
    if (err == ESP_OK) {
        err = nvs_set_blob(h, MOLE_NVS_KEY_PUB, pub, pub_len);
    }
    if (err == ESP_OK) {
        err = nvs_commit(h);
    }
    nvs_close(h);
    return err;
}

static esp_err_t load_key_from_nvs(uint8_t *pub, size_t *pub_len)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(MOLE_NVS_NAMESPACE, NVS_READONLY, &h);
    if (err != ESP_OK) return err;

    err = nvs_get_blob(h, MOLE_NVS_KEY_PUB, pub, pub_len);
    nvs_close(h);
    return err;
}

/* ── Public API ──────────────────────────────────────────────────────────── */

esp_err_t mole_identity_init(mole_identity_handle_t *out_handle)
{
    struct mole_identity *id = calloc(1, sizeof(*id));
    if (!id) return ESP_ERR_NO_MEM;

    /* Initialize mbedTLS contexts */
    mbedtls_pk_init(&id->pk);
    mbedtls_entropy_init(&id->entropy);
    mbedtls_ctr_drbg_init(&id->drbg);

    /* Seed the DRBG from hardware RNG */
    int ret = mbedtls_ctr_drbg_seed(&id->drbg, mbedtls_entropy_func,
                                     &id->entropy,
                                     (const unsigned char *)"mole_id", 7);
    if (ret != 0) {
        ESP_LOGE(TAG, "DRBG seed failed: -0x%04X", (unsigned)-ret);
        free(id);
        return ESP_FAIL;
    }

    /* Try loading existing key from NVS */
    size_t pub_len = MOLE_ED25519_PUB_LEN;
    esp_err_t err = load_key_from_nvs(id->pub_key, &pub_len);

    if (err == ESP_OK && pub_len == MOLE_ED25519_PUB_LEN) {
        ESP_LOGI(TAG, "Loaded existing identity from NVS");
    } else {
        /* First boot — generate new keypair */
        ESP_LOGI(TAG, "First boot — generating Ed25519 keypair...");

        ret = mbedtls_pk_setup(&id->pk,
                               mbedtls_pk_info_from_type(MBEDTLS_PK_ECKEY));
        if (ret != 0) {
            ESP_LOGE(TAG, "PK setup failed: -0x%04X", (unsigned)-ret);
            free(id);
            return ESP_FAIL;
        }

        mbedtls_ecp_keypair *ec = mbedtls_pk_ec(id->pk);
        ret = mbedtls_ecp_gen_key(MBEDTLS_ECP_DP_CURVE25519,
                                   ec,
                                   mbedtls_ctr_drbg_random,
                                   &id->drbg);
        if (ret != 0) {
            ESP_LOGE(TAG, "Key generation failed: -0x%04X", (unsigned)-ret);
            free(id);
            return ESP_FAIL;
        }

        /* Export public key to binary */
        size_t olen = 0;
        uint8_t pub_buf[65];  /* Uncompressed EC point */
        ret = mbedtls_ecp_point_write_binary(
            &ec->MBEDTLS_PRIVATE(grp),
            &ec->MBEDTLS_PRIVATE(Q),
            MBEDTLS_ECP_PF_COMPRESSED,
            &olen, pub_buf, sizeof(pub_buf));
        if (ret != 0) {
            ESP_LOGE(TAG, "Pubkey export failed: -0x%04X", (unsigned)-ret);
            free(id);
            return ESP_FAIL;
        }

        /* Take first 32 bytes as identity */
        memcpy(id->pub_key, pub_buf, MOLE_ED25519_PUB_LEN);

        /* Export private key for NVS storage */
        uint8_t priv_buf[MOLE_ED25519_PRIV_LEN];
        ret = mbedtls_mpi_write_binary(
            &ec->MBEDTLS_PRIVATE(d),
            priv_buf, MOLE_ED25519_PRIV_LEN);
        if (ret != 0) {
            ESP_LOGE(TAG, "Privkey export failed: -0x%04X", (unsigned)-ret);
            free(id);
            return ESP_FAIL;
        }

        /* Persist to encrypted NVS */
        err = save_key_to_nvs(priv_buf, MOLE_ED25519_PRIV_LEN,
                               id->pub_key, MOLE_ED25519_PUB_LEN);
        /* Scrub private key from stack */
        memset(priv_buf, 0, sizeof(priv_buf));

        if (err != ESP_OK) {
            ESP_LOGE(TAG, "NVS save failed: %s", esp_err_to_name(err));
            free(id);
            return err;
        }

        ESP_LOGI(TAG, "New identity generated and saved to NVS");
    }

    id->initialized = true;
    *out_handle = id;
    return ESP_OK;
}

esp_err_t mole_identity_get_public_key_hex(mole_identity_handle_t handle,
                                            char *out_hex, size_t out_len)
{
    if (!handle || !handle->initialized) return ESP_ERR_INVALID_STATE;
    if (out_len < (MOLE_ED25519_PUB_LEN * 2 + 1)) return ESP_ERR_INVALID_SIZE;

    bytes_to_hex(handle->pub_key, MOLE_ED25519_PUB_LEN, out_hex, out_len);
    return ESP_OK;
}

esp_err_t mole_identity_sign(mole_identity_handle_t handle,
                              const uint8_t *data, size_t data_len,
                              uint8_t *sig, size_t *sig_len)
{
    if (!handle || !handle->initialized) return ESP_ERR_INVALID_STATE;

    int ret = mbedtls_pk_sign(&handle->pk, MBEDTLS_MD_SHA256,
                               data, data_len,
                               sig, MOLE_ED25519_SIG_LEN, sig_len,
                               mbedtls_ctr_drbg_random, &handle->drbg);
    if (ret != 0) {
        ESP_LOGE(TAG, "Sign failed: -0x%04X", (unsigned)-ret);
        return ESP_FAIL;
    }
    return ESP_OK;
}
