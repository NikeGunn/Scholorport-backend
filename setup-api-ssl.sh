#!/bin/bash
# =============================================================
# SSL Setup Script for api.scholarport.co
# Run this script on your AWS EC2 server
# =============================================================

set -e  # Exit on error

echo "=========================================="
echo "SSL Setup for api.scholarport.co"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Create certbot webroot directory
echo -e "\n${YELLOW}[1/6] Creating certbot directory...${NC}"
sudo mkdir -p /var/www/certbot
sudo chown -R $USER:$USER /var/www/certbot

# Step 2: Install certbot if not installed
echo -e "\n${YELLOW}[2/6] Checking certbot installation...${NC}"
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt update
    sudo apt install -y certbot
else
    echo "Certbot already installed"
fi

# Step 3: Stop nginx temporarily to free port 80
echo -e "\n${YELLOW}[3/6] Stopping nginx temporarily...${NC}"
sudo docker-compose down || true
sudo systemctl stop nginx 2>/dev/null || true

# Step 4: Get SSL certificate using standalone mode
echo -e "\n${YELLOW}[4/6] Obtaining SSL certificate for api.scholarport.co...${NC}"
sudo certbot certonly \
    --standalone \
    --preferred-challenges http \
    -d api.scholarport.co \
    --email admin@scholarport.co \
    --agree-tos \
    --non-interactive \
    --force-renewal

# Step 5: Verify certificate was created
echo -e "\n${YELLOW}[5/6] Verifying certificate...${NC}"
if [ -f "/etc/letsencrypt/live/api.scholarport.co/fullchain.pem" ]; then
    echo -e "${GREEN}✓ SSL certificate successfully obtained!${NC}"
    sudo ls -la /etc/letsencrypt/live/api.scholarport.co/
else
    echo -e "${RED}✗ Certificate not found! Check certbot logs.${NC}"
    exit 1
fi

# Step 6: Start Docker containers
echo -e "\n${YELLOW}[6/6] Starting Docker containers...${NC}"
cd ~/scholarport || cd /home/ubuntu/scholarport || cd /app
sudo docker-compose up -d --build

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Test the SSL
echo -e "\n${GREEN}=========================================="
echo "Testing HTTPS connection..."
echo "==========================================${NC}"
curl -I https://api.scholarport.co/api/docs/ 2>/dev/null | head -5 || echo "Waiting for nginx to fully start..."

echo -e "\n${GREEN}=========================================="
echo "SSL Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Your API is now available at:"
echo "  https://api.scholarport.co/api/"
echo ""
echo "Update your Vercel frontend environment variable:"
echo "  NEXT_PUBLIC_API_URL=https://api.scholarport.co"
echo ""
echo "To renew certificate automatically, add this cron job:"
echo "  sudo crontab -e"
echo "  0 0 1 * * certbot renew --quiet && docker-compose restart nginx"
