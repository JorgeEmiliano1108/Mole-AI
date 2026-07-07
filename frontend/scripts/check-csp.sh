#!/bin/sh
# Validate CSP header in nginx.conf

NGINX_CONF="nginx.conf"
[ ! -f "$NGINX_CONF" ] && echo "ERROR: nginx.conf not found" && exit 1

CSP_VALUE=$(grep -oP 'set \$csp_policy "\K[^"]+' "$NGINX_CONF" | head -1)
[ -z "$CSP_VALUE" ] && echo "FAIL: Could not extract CSP policy" && exit 1

echo "CSP: $CSP_VALUE"

# script-src must NOT have unsafe-inline (check only script-src directive)
SCRIPT_SRC=$(echo "$CSP_VALUE" | grep -oP 'script-src [^;]+')
echo "$SCRIPT_SRC" | grep -q "unsafe-inline" \
  && echo "FAIL: script-src contains 'unsafe-inline'" && exit 1

# Must have default-src
echo "$CSP_VALUE" | grep -q "default-src" \
  || { echo "FAIL: CSP missing default-src"; exit 1; }

# script-src must not have external CDN URLs
SCRIPT_SRC=$(echo "$CSP_VALUE" | grep -oP 'script-src [^;]+')
echo "$SCRIPT_SRC" | grep -qE 'https?://' \
  && echo "FAIL: script-src has external URLs: $SCRIPT_SRC" && exit 1

# Must have frame-ancestors 'none'
echo "$CSP_VALUE" | grep -q "frame-ancestors 'none'" \
  || { echo "FAIL: CSP missing frame-ancestors 'none'"; exit 1; }

echo "PASS: CSP policy is secure"
