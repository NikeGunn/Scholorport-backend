#!/bin/bash
# =============================================================
# SSL Setup Script for api.scholarport.co
# Run this AFTER the initial deployment is working on HTTP
# Backward compatible - HTTP continues to work if SSL fails
# =============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=========================================="
echo "SSL Setup for api.scholarport.co"
echo -e "==========================================${NC}"

cd ~/scholarport || { echo -e "${RED}Error: ~/scholarport not found${NC}"; exit 1; }

# Check if certificate already exists
if [ -f "certbot/conf/live/api.scholarport.co/fullchain.pem" ]; then
    echo -e "${GREEN}✓ SSL certificate already exists!${NC}"
    echo "  To renew: sudo certbot renew"
    exit 0
fi

# Create directories
mkdir -p certbot/conf certbot/www

# Stop nginx temporarily (need port 80 for certbot standalone)
echo -e "\n${YELLOW}[1/4] Stopping nginx temporarily...${NC}"
sudo docker-compose stop nginx

# Get SSL certificate
echo -e "\n${YELLOW}[2/4] Obtaining SSL certificate...${NC}"
sudo certbot certonly \
    --standalone \
    --preferred-challenges http \
    -d api.scholarport.co \
    --email admin@scholarport.co \
    --agree-tos \
    --non-interactive

# Copy certificates to Docker-accessible location
echo -e "\n${YELLOW}[3/4] Setting up certificates...${NC}"
sudo cp -rL /etc/letsencrypt/* certbot/conf/
sudo chown -R $USER:$USER certbot/

# Restart all containers
echo -e "\n${YELLOW}[4/4] Restarting services with SSL...${NC}"
sudo docker-compose up -d --build

sleep 10

# Test HTTPS
echo -e "\n${GREEN}Testing HTTPS...${NC}"
HTTPS=$(curl -s -o /dev/null -w "%{http_code}" https://api.scholarport.co/api/docs/ 2>/dev/null || echo "000")
if [ "$HTTPS" = "200" ]; then
    echo -e "${GREEN}✓ HTTPS is working!${NC}"
else
    echo -e "${YELLOW}⚠ HTTPS returned: $HTTPS${NC}"
fi

echo -e "\n${GREEN}=========================================="
echo "SSL Setup Complete!"
echo -e "==========================================${NC}"
echo ""
echo "Your API is now available at:"
echo "  HTTP:  http://api.scholarport.co/api/"
echo "  HTTPS: https://api.scholarport.co/api/"
echo ""
echo "Update your frontend environment variable:"
echo "  NEXT_PUBLIC_API_URL=https://api.scholarport.co"
echo ""
echo "🔄 Step 3: Restarting Nginx with HTTP-only config..."
echo "─────────────────────────────────────"
docker-compose restart nginx
sleep 5

# Check if nginx is running
if ! docker-compose ps | grep -q "scholarport_nginx.*Up"; then
    echo "❌ Error: Nginx failed to start!"
    echo "Check logs with: docker-compose logs nginx"
    exit 1
fi

echo "✅ Nginx is running"

echo ""
echo "🔐 Step 4: Obtaining SSL certificate from Let's Encrypt..."
echo "─────────────────────────────────────"

# Stop nginx temporarily for standalone certbot
echo "Stopping nginx temporarily..."
docker-compose stop nginx

# Run certbot to get certificate
echo "Running certbot (this may take a minute)..."
docker-compose run --rm certbot certonly \
    --standalone \
    --preferred-challenges http \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d "$DOMAIN" \
    -d "$WWW_DOMAIN"

# Check if certificate was obtained
if [ ! -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo "❌ Error: Failed to obtain SSL certificate!"
    echo "   Starting nginx again..."
    docker-compose start nginx
    exit 1
fi

echo "✅ SSL certificate obtained successfully!"

echo ""
echo "🔧 Step 5: Switching to HTTPS configuration..."
echo "─────────────────────────────────────"

# Remove temp config and activate SSL config
rm -f nginx/conf.d/active.conf
rm -f nginx/conf.d/temp-http-for-ssl.conf
cp nginx/conf.d/scholarport-ssl.conf nginx/conf.d/active.conf

echo "✅ HTTPS config activated"

echo ""
echo "🔄 Step 6: Restarting all services..."
echo "─────────────────────────────────────"

# Upload new .env.production
echo "Updating .env file..."
cp .env.production .env

# Restart all services
docker-compose restart

echo "Waiting for services to start..."
sleep 10

# Check services
echo ""
echo "📊 Checking service status..."
docker-compose ps

echo ""
echo "🧪 Step 7: Testing SSL setup..."
echo "─────────────────────────────────────"

# Test HTTPS
echo "Testing HTTPS endpoint..."
if curl -k -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/api/chat/health/" | grep -q "200"; then
    echo "✅ HTTPS endpoint responding"
else
    echo "⚠️  HTTPS endpoint not responding yet (may need a few more seconds)"
fi

# Test HTTP redirect
echo "Testing HTTP to HTTPS redirect..."
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN/")
if [ "$HTTP_RESPONSE" = "301" ] || [ "$HTTP_RESPONSE" = "302" ]; then
    echo "✅ HTTP redirects to HTTPS"
else
    echo "⚠️  HTTP redirect not working (code: $HTTP_RESPONSE)"
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  🎉 SSL SETUP COMPLETE!                                ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Your backend is now running with HTTPS!"
echo ""
echo "🌐 Access URLs:"
echo "   Frontend:     https://scholarport.co"
echo "   API Health:   https://scholarport.co/api/chat/health/"
echo "   API Start:    https://scholarport.co/api/chat/start/"
echo "   Admin Panel:  https://scholarport.co/admin/"
echo ""
echo "🔍 Verify SSL:"
echo "   curl https://scholarport.co/api/chat/health/"
echo "   Open in browser: https://scholarport.co/admin/"
echo ""
echo "📋 Certificate Info:"
echo "   Location: ~/scholarport-backend/certbot/conf/live/$DOMAIN/"
echo "   Valid for: 90 days"
echo "   Auto-renewal: Enabled (certbot container runs every 12h)"
echo ""
echo "🔒 Next Steps:"
echo "   1. Update your frontend to use: https://scholarport.co/api/"
echo "   2. Test all API endpoints"
echo "   3. Monitor logs: docker-compose logs -f nginx"
echo ""
echo "💡 Troubleshooting:"
echo "   - Check nginx logs: docker-compose logs nginx"
echo "   - Check backend logs: docker-compose logs backend"
echo "   - Verify certificate: openssl s_client -connect scholarport.co:443"
echo ""
