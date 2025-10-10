#!/bin/bash
# Quick Self-Signed SSL Certificate Generator for Scholarport
# This creates certificates that work immediately (browser will show warning)

set -e

DOMAIN="scholarport.co"
CERT_DIR="$HOME/scholarport-backend/certbot/conf/live/$DOMAIN"

echo "🔐 Creating Self-Signed SSL Certificate for $DOMAIN"
echo "=================================================="

# Create directories
mkdir -p "$CERT_DIR"
mkdir -p "$HOME/scholarport-backend/certbot/conf/archive/$DOMAIN"

# Generate self-signed certificate (valid for 365 days)
docker run --rm -v "$HOME/scholarport-backend/certbot/conf:/etc/letsencrypt" \
  alpine/openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "/etc/letsencrypt/live/$DOMAIN/privkey.pem" \
  -out "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" \
  -subj "/C=US/ST=State/L=City/O=Scholarport/CN=$DOMAIN" \
  -addext "subjectAltName=DNS:$DOMAIN,DNS:www.$DOMAIN"

# Create cert.pem and chain.pem (required by some configs)
docker run --rm -v "$HOME/scholarport-backend/certbot/conf:/etc/letsencrypt" \
  alpine/openssl sh -c "cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /etc/letsencrypt/live/$DOMAIN/cert.pem"

docker run --rm -v "$HOME/scholarport-backend/certbot/conf:/etc/letsencrypt" \
  alpine/openssl sh -c "cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /etc/letsencrypt/live/$DOMAIN/chain.pem"

echo ""
echo "✅ Self-signed certificate created!"
echo "📁 Location: $CERT_DIR"
echo ""
echo "⚠️  NOTE: Browsers will show 'Not Secure' warning (expected for self-signed certs)"
echo "    Click 'Advanced' → 'Proceed to site' to bypass"
echo ""
echo "📋 Certificate files created:"
ls -lh "$CERT_DIR"

echo ""
echo "🔄 Next steps:"
echo "1. Activate SSL nginx config:"
echo "   cd ~/scholarport-backend/nginx/conf.d/"
echo "   mv backup/scholarport-ssl.conf ."
echo "   rm active.conf"
echo ""
echo "2. Restart nginx:"
echo "   cd ~/scholarport-backend"
echo "   docker-compose restart nginx"
echo ""
echo "3. Test HTTPS:"
echo "   curl -k https://scholarport.co/api/chat/health/"
echo ""
echo "✨ Your backend will now work with HTTPS!"
