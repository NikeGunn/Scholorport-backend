#!/bin/bash
# Self-Signed SSL Certificate with IP Address Support
# Creates certificate for both domain AND IP address

set -e

DOMAIN="scholarport.co"
IP_ADDRESS="43.205.95.162"
CERT_DIR="$HOME/scholarport-backend/certbot/conf/live/$DOMAIN"

echo "🔐 Creating Self-Signed SSL Certificate"
echo "=================================================="
echo "📋 Domain: $DOMAIN, www.$DOMAIN"
echo "📋 IP Address: $IP_ADDRESS"
echo ""

# Create directories
mkdir -p "$CERT_DIR"
mkdir -p "$HOME/scholarport-backend/certbot/conf/archive/$DOMAIN"

# Create OpenSSL configuration file with IP address
cat > /tmp/openssl-san.cnf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=US
ST=State
L=City
O=Scholarport
CN=$DOMAIN

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = www.$DOMAIN
IP.1 = $IP_ADDRESS
EOF

echo "📝 Generating certificate with IP address support..."

# Generate self-signed certificate with IP address (valid for 365 days)
docker run --rm \
  -v "$HOME/scholarport-backend/certbot/conf:/etc/letsencrypt" \
  -v "/tmp/openssl-san.cnf:/tmp/openssl-san.cnf:ro" \
  alpine/openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "/etc/letsencrypt/live/$DOMAIN/privkey.pem" \
  -out "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" \
  -config /tmp/openssl-san.cnf \
  -extensions v3_req

# Create cert.pem and chain.pem (copies of fullchain.pem)
cp "$CERT_DIR/fullchain.pem" "$CERT_DIR/cert.pem"
cp "$CERT_DIR/fullchain.pem" "$CERT_DIR/chain.pem"

# Clean up temp file
rm -f /tmp/openssl-san.cnf

echo ""
echo "✅ Self-signed certificate created with IP address support!"
echo "📁 Location: $CERT_DIR"
echo ""
echo "✨ Certificate includes:"
echo "   - Domain: $DOMAIN"
echo "   - Domain: www.$DOMAIN"
echo "   - IP Address: $IP_ADDRESS"
echo ""
echo "⚠️  NOTE: Browsers will show 'Not Secure' warning (expected for self-signed certs)"
echo "    Click 'Advanced' → 'Proceed to site' to bypass"
echo ""
echo "📋 Certificate files created:"
ls -lh "$CERT_DIR"

echo ""
echo "🔄 Next steps:"
echo "1. Restart nginx:"
echo "   cd ~/scholarport-backend"
echo "   docker-compose restart nginx"
echo ""
echo "2. Test with domain:"
echo "   curl -k https://scholarport.co/admin/"
echo ""
echo "3. Test with IP address:"
echo "   curl -k https://43.205.95.162/admin/"
echo ""
echo "✅ Both should work now!"
