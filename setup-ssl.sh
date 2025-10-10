#!/bin/bash
# SSL Setup Script for Scholarport Backend
# Domain: scholarport.co

set -e

echo "🔐 Scholarport SSL Setup Script"
echo "================================"
echo ""

# Configuration
DOMAIN="scholarport.co"
WWW_DOMAIN="www.scholarport.co"
EMAIL="your-email@example.com"  # CHANGE THIS!

echo "📋 Configuration:"
echo "   Domain: $DOMAIN"
echo "   WWW: $WWW_DOMAIN"
echo "   Email: $EMAIL"
echo ""

# Check if email is still default
if [ "$EMAIL" = "your-email@example.com" ]; then
    echo "⚠️  WARNING: Please edit this script and change the EMAIL variable!"
    echo "   Email is required for Let's Encrypt certificate notifications."
    read -p "Enter your email address: " EMAIL
fi

echo ""
echo "🔍 Step 1: Checking prerequisites..."
echo "─────────────────────────────────────"

# Check if running in correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found!"
    echo "   Please run this script from ~/scholarport-backend/"
    exit 1
fi

# Check if domain resolves correctly
echo "Checking DNS resolution for $DOMAIN..."
RESOLVED_IP=$(dig +short $DOMAIN | tail -n1)
CURRENT_IP=$(curl -s ifconfig.me)

echo "   Domain resolves to: $RESOLVED_IP"
echo "   Server IP: $CURRENT_IP"

if [ "$RESOLVED_IP" != "$CURRENT_IP" ]; then
    echo "⚠️  WARNING: Domain does not resolve to this server!"
    echo "   Make sure DNS A record points to $CURRENT_IP"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "📦 Step 2: Preparing Nginx configuration..."
echo "─────────────────────────────────────"

# Backup existing configs
if [ -d "nginx/conf.d" ]; then
    echo "Backing up existing configs..."
    mkdir -p nginx/conf.d/backup
    cp nginx/conf.d/*.conf nginx/conf.d/backup/ 2>/dev/null || true
fi

# Remove old configs
echo "Cleaning up old configs..."
rm -f nginx/conf.d/simple-http.conf
rm -f nginx/conf.d/http-with-static.conf
rm -f nginx/conf.d/scholarport.conf
rm -f nginx/conf.d/production.conf

# Use temp HTTP config for SSL acquisition
echo "Activating temporary HTTP config..."
cp nginx/conf.d/temp-http-for-ssl.conf nginx/conf.d/active.conf

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
