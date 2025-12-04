#!/bin/bash
# =============================================================
# Nginx SSL Auto-Configuration Script
# This script runs at container startup and enables HTTPS
# only if SSL certificates exist. Otherwise, HTTP-only mode.
# =============================================================

SSL_CERT="/etc/letsencrypt/live/api.scholarport.co/fullchain.pem"
SSL_KEY="/etc/letsencrypt/live/api.scholarport.co/privkey.pem"
HTTPS_TEMPLATE="/etc/nginx/conf.d/api-https.conf.template"
HTTPS_CONF="/etc/nginx/conf.d/api-https.conf"

echo "=========================================="
echo "Nginx SSL Auto-Configuration"
echo "=========================================="

# Check if SSL certificates exist
if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
    echo "✓ SSL certificates found!"
    echo "  - Certificate: $SSL_CERT"
    echo "  - Key: $SSL_KEY"
    
    # Enable HTTPS configuration
    if [ -f "$HTTPS_TEMPLATE" ]; then
        cp "$HTTPS_TEMPLATE" "$HTTPS_CONF"
        echo "✓ HTTPS configuration enabled"
        echo "  API available at: https://api.scholarport.co"
    fi
else
    echo "⚠ SSL certificates not found"
    echo "  - Expected: $SSL_CERT"
    echo "  HTTP-only mode enabled"
    echo "  API available at: http://api.scholarport.co"
    
    # Remove HTTPS config if it exists (to avoid nginx errors)
    if [ -f "$HTTPS_CONF" ]; then
        rm -f "$HTTPS_CONF"
        echo "  Removed HTTPS config (no certificates)"
    fi
fi

echo ""
echo "Also available via IP: http://43.205.95.162"
echo "=========================================="

# Test nginx configuration
nginx -t

# Start nginx
exec nginx -g 'daemon off;'
