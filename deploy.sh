#!/bin/bash
# =============================================================
# Scholarport Deployment Script with Optional SSL
# Supports both HTTP and HTTPS - backward compatible
# =============================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=========================================="
echo "Scholarport Backend Deployment"
echo -e "==========================================${NC}"

# Navigate to project directory
cd ~/scholarport || { echo -e "${RED}Error: ~/scholarport not found${NC}"; exit 1; }

# Pull latest code
echo -e "\n${YELLOW}[1/5] Pulling latest code...${NC}"
git pull origin main

# Create required directories
echo -e "\n${YELLOW}[2/5] Creating directories...${NC}"
mkdir -p certbot/conf certbot/www staticfiles media logs

# Check if SSL should be obtained
echo -e "\n${YELLOW}[3/5] Checking SSL status...${NC}"
if [ -f "certbot/conf/live/api.scholarport.co/fullchain.pem" ]; then
    echo -e "${GREEN}✓ SSL certificate exists${NC}"
else
    echo -e "${YELLOW}⚠ No SSL certificate found${NC}"
    echo "  To obtain SSL, run: ./setup-ssl.sh"
    echo "  Continuing with HTTP-only mode..."
fi

# Stop existing containers
echo -e "\n${YELLOW}[4/5] Restarting containers...${NC}"
sudo docker-compose down

# Start containers
sudo docker-compose up -d --build

# Wait for services
echo "Waiting for services to start..."
sleep 10

# Test endpoints
echo -e "\n${YELLOW}[5/5] Testing endpoints...${NC}"

# Test HTTP on IP
echo -n "Testing http://43.205.95.162/api/docs/ ... "
HTTP_IP=$(curl -s -o /dev/null -w "%{http_code}" http://43.205.95.162/api/docs/ 2>/dev/null || echo "000")
if [ "$HTTP_IP" = "200" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}$HTTP_IP${NC}"
fi

# Test HTTP on domain
echo -n "Testing http://api.scholarport.co/api/docs/ ... "
HTTP_DOMAIN=$(curl -s -o /dev/null -w "%{http_code}" http://api.scholarport.co/api/docs/ 2>/dev/null || echo "000")
if [ "$HTTP_DOMAIN" = "200" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}$HTTP_DOMAIN${NC}"
fi

# Test HTTPS (if certificate exists)
if [ -f "certbot/conf/live/api.scholarport.co/fullchain.pem" ]; then
    echo -n "Testing https://api.scholarport.co/api/docs/ ... "
    HTTPS=$(curl -s -o /dev/null -w "%{http_code}" https://api.scholarport.co/api/docs/ 2>/dev/null || echo "000")
    if [ "$HTTPS" = "200" ]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}$HTTPS${NC}"
    fi
fi

echo -e "\n${GREEN}=========================================="
echo "Deployment Complete!"
echo -e "==========================================${NC}"
echo ""
echo "API Endpoints:"
echo "  HTTP:  http://43.205.95.162/api/"
echo "  HTTP:  http://api.scholarport.co/api/"
if [ -f "certbot/conf/live/api.scholarport.co/fullchain.pem" ]; then
    echo "  HTTPS: https://api.scholarport.co/api/"
fi
echo ""
echo "Swagger Docs:"
echo "  http://api.scholarport.co/api/docs/"
echo ""
