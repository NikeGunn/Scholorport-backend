#!/bin/bash
# Quick deployment verification script
# Run this on EC2 after deployment to verify everything works

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Scholarport Deployment Verification"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found${NC}"
    echo "Run this script from ~/scholarport-backend/"
    exit 1
fi

# Check Docker
echo -n "🐳 Docker installed: "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Check Docker Compose
echo -n "🐳 Docker Compose installed: "
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Check .env file
echo -n "⚙️  .env file exists: "
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    exit 1
fi

# Check Firebase credentials
echo -n "🔑 Firebase credentials exist: "
if [ -f "scholorport-firebase-adminsdk-fbsvc-b17f9acfbf.json" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "🏥 Health Check:"
HEALTH_RESPONSE=$(curl -s http://localhost/api/chat/health/)
if echo "$HEALTH_RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓ API is responding${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo -e "${RED}✗ API not responding${NC}"
fi

echo ""
echo "🗄️  Database Connection:"
if docker-compose exec -T db pg_isready -U scholarport > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connected${NC}"
else
    echo -e "${RED}✗ Database not ready${NC}"
fi

echo ""
echo "📚 University Data:"
UNIV_COUNT=$(docker-compose exec -T backend python manage.py shell -c "from chat.models import University; print(University.objects.count())" 2>/dev/null | tr -d '\r')
if [ "$UNIV_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Universities loaded: $UNIV_COUNT${NC}"
else
    echo -e "${YELLOW}⚠ No universities loaded (run: docker-compose exec backend python manage.py load_universities)${NC}"
fi

echo ""
echo "🌍 Public Access:"
PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)
echo "   API: http://$PUBLIC_IP/api/chat/health/"
echo "   Admin: http://$PUBLIC_IP/admin/"

echo ""
echo "📋 Recent Backend Logs:"
docker-compose logs --tail=10 backend

echo ""
echo "========================================"
if [ -n "$HEALTH_RESPONSE" ] && echo "$HEALTH_RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✅ Deployment looks good!${NC}"
else
    echo -e "${RED}⚠️  Some issues detected. Check logs above.${NC}"
fi
