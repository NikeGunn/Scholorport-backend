#!/bin/bash
# Get Let's Encrypt SSL Certificate for Backend
# This replaces the self-signed certificate with a trusted certificate

set -e

DOMAIN="43.205.95.162"
EMAIL="tech.scholarport@gmail.com"

echo "🔐 Getting Let's Encrypt Certificate"
echo "=================================================="
echo "⚠️  NOTE: Let's Encrypt does NOT support IP addresses!"
echo "   You need a domain name like api.scholarport.co"
echo ""
echo "📋 Current Setup:"
echo "   - Backend IP: 43.205.95.162"
echo "   - Frontend Domain: scholarport.co → 13.232.108.169"
echo ""
echo "🎯 SOLUTION: Create a subdomain for your backend"
echo ""
echo "1. Go to your DNS provider (where you registered scholarport.co)"
echo "2. Add an A record:"
echo "   Name: api"
echo "   Type: A"
echo "   Value: 43.205.95.162"
echo "   TTL: 300"
echo ""
echo "3. Wait 5-10 minutes for DNS propagation"
echo ""
echo "4. Test DNS resolution:"
echo "   nslookup api.scholarport.co"
echo "   # Should return: 43.205.95.162"
echo ""
echo "5. Run Let's Encrypt:"
cat << 'COMMANDS'
cd ~/scholarport-backend

# Update nginx config to use api.scholarport.co
# Edit nginx/conf.d/scholarport-ssl.conf
# Change server_name to: api.scholarport.co

# Get certificate
docker-compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email tech.scholarport@gmail.com \
  --agree-tos \
  --no-eff-email \
  -d api.scholarport.co

# Update certificate paths in nginx config if needed
# Restart nginx
docker-compose restart nginx

# Test
curl https://api.scholarport.co/api/chat/health/
COMMANDS

echo ""
echo "📝 After this, your admin panel will be:"
echo "   https://api.scholarport.co/admin/"
echo ""
echo "✅ No more 'Not secure' warning!"
echo "✅ Trusted by all browsers"
echo "✅ Auto-renewal every 90 days"
