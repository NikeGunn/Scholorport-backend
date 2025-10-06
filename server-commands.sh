#!/bin/bash
# Scholarport Backend Server Management Commands
# Run these commands on your EC2 instance

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

show_menu() {
    echo ""
    echo -e "${BLUE}🎓 Scholarport Backend Server Management${NC}"
    echo "=========================================="
    echo "1. 🚀 Initial Setup (First time - installs Docker)"
    echo "2. 🔧 Start Services"
    echo "3. 📊 Setup Database & Load Data"
    echo "4. 👤 Create Superuser"
    echo "5. ⏸️  Stop Services"
    echo "6. 🔄 Restart Services"
    echo "7. � View Logs"
    echo "8. 🏥 Health Check"
    echo "9. 📈 System Status"
    echo "10. � Update Application (from new upload)"
    echo "11. 🗄️  Database Backup"
    echo "12. 🧹 Clean Docker Resources"
    echo "13. � View Container Stats"
    echo "0. 🚪 Exit"
    echo ""
    echo -n "Select an option: "
}

initial_setup() {
    echo -e "${YELLOW}🚀 Running initial setup...${NC}"

    # Update system
    echo "📦 Updating system packages..."
    sudo apt-get update
    sudo apt-get upgrade -y

    # Install Docker
    if ! command -v docker &> /dev/null; then
        echo "🐳 Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker ubuntu
        rm get-docker.sh
        echo -e "${GREEN}✅ Docker installed${NC}"
    else
        echo -e "${GREEN}✅ Docker already installed${NC}"
    fi

    # Install Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "🐳 Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo -e "${GREEN}✅ Docker Compose installed${NC}"
    else
        echo -e "${GREEN}✅ Docker Compose already installed${NC}"
    fi

    # Create necessary directories
    mkdir -p ~/scholarport-backend/logs
    mkdir -p ~/scholarport-backend/staticfiles
    mkdir -p ~/scholarport-backend/certbot/conf
    mkdir -p ~/scholarport-backend/certbot/www
    mkdir -p ~/backups

    # Set executable permissions
    chmod +x ~/scholarport-backend/docker-entrypoint.sh

    # Create .env from template if it doesn't exist
    if [ ! -f ~/scholarport-backend/.env ]; then
        echo -e "${YELLOW}⚠️  .env file not found!${NC}"
        echo "Please ensure .env file was uploaded properly"
    fi

    echo -e "${GREEN}✅ Initial setup completed!${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANT: Log out and back in for Docker permissions to take effect${NC}"
    echo -e "${YELLOW}⚠️  Run: exit, then ssh back in${NC}"
}

start_services() {
    echo -e "${YELLOW}🚀 Starting services...${NC}"
    cd ~/scholarport-backend

    # Check if .env exists
    if [ ! -f .env ]; then
        echo -e "${RED}❌ .env file not found!${NC}"
        echo "Please ensure .env file is in ~/scholarport-backend/"
        return 1
    fi

    echo "Building and starting containers..."
    docker-compose up -d --build

    echo -e "${GREEN}✅ Services started!${NC}"
    echo ""
    echo "Waiting for services to initialize..."
    sleep 15

    echo ""
    echo "📊 Container Status:"
    docker-compose ps

    echo ""
    echo "🔍 Checking backend logs..."
    docker-compose logs --tail=20 backend

    echo ""
    echo -e "${YELLOW}💡 Run migrations and load data:${NC}"
    echo "   docker-compose exec backend python manage.py migrate"
    echo "   docker-compose exec backend python manage.py load_universities"
    echo "   docker-compose exec backend python manage.py collectstatic --no-input"
}

stop_services() {
    echo -e "${YELLOW}⏸️  Stopping services...${NC}"
    cd ~/scholarport-backend
    docker-compose down
    echo -e "${GREEN}✅ Services stopped!${NC}"
}

restart_services() {
    echo -e "${YELLOW}🔄 Restarting services...${NC}"
    cd ~/scholarport-backend
    docker-compose restart
    echo -e "${GREEN}✅ Services restarted!${NC}"
}

view_logs() {
    echo -e "${YELLOW}📊 Service logs (Ctrl+C to exit):${NC}"
    echo ""
    echo "Which service logs?"
    echo "1. All services"
    echo "2. Backend only"
    echo "3. Nginx only"
    echo "4. Database only"
    echo ""
    echo -n "Select: "
    read log_choice

    cd ~/scholarport-backend
    case $log_choice in
        1) docker-compose logs -f ;;
        2) docker-compose logs -f backend ;;
        3) docker-compose logs -f nginx ;;
        4) docker-compose logs -f db ;;
        *) docker-compose logs -f ;;
    esac
}

health_check() {
    echo -e "${YELLOW}🏥 Performing health check...${NC}"
    cd ~/scholarport-backend

    # Check Docker containers
    echo ""
    echo "🐳 Docker Containers:"
    docker-compose ps

    # Check API health
    echo ""
    echo "🌐 API Health Check:"
    if command -v curl &> /dev/null; then
        echo "Local: http://localhost/api/chat/health/"
        curl -s http://localhost/api/chat/health/ | python3 -m json.tool 2>/dev/null || echo "❌ API not responding"
    else
        wget -qO- http://localhost/api/chat/health/ || echo "❌ API not responding"
    fi

    # Check database
    echo ""
    echo "🗄️  Database Status:"
    docker-compose exec -T db pg_isready -U scholarport || echo "❌ Database not ready"

    # Check university data
    echo ""
    echo "📚 University Data:"
    docker-compose exec -T backend python manage.py shell -c "from chat.models import University; print(f'Universities loaded: {University.objects.count()}')" 2>/dev/null || echo "Run load_universities command"

    # Get public IP
    echo ""
    echo "🌍 Public Access:"
    PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)
    echo "   API: http://$PUBLIC_IP/api/chat/health/"
    echo "   Admin: http://$PUBLIC_IP/admin/"
}

system_status() {
    echo -e "${YELLOW}📈 System Status:${NC}"
    echo ""
    echo "💾 Disk Usage:"
    df -h / | tail -1
    echo ""
    echo "🧠 Memory Usage:"
    free -h | grep Mem
    echo ""
    echo "⚡ CPU Load:"
    uptime
    echo ""
    echo "🐳 Docker Stats:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

setup_database() {
    echo -e "${YELLOW}� Setting up database and loading data...${NC}"
    cd ~/scholarport-backend

    echo "🔄 Running migrations..."
    docker-compose exec -T backend python manage.py migrate

    echo ""
    echo "📚 Loading university data..."
    docker-compose exec -T backend python manage.py load_universities

    echo ""
    echo "📦 Collecting static files..."
    docker-compose exec -T backend python manage.py collectstatic --no-input

    echo ""
    echo -e "${GREEN}✅ Database setup complete!${NC}"

    # Show stats
    echo ""
    echo "📊 Database Statistics:"
    docker-compose exec -T backend python manage.py shell -c "from chat.models import University; print(f'Universities: {University.objects.count()}')"
}

create_superuser() {
    echo -e "${YELLOW}👤 Creating superuser...${NC}"
    cd ~/scholarport-backend

    echo ""
    echo "You will be prompted to enter:"
    echo "  - Username (e.g., admin)"
    echo "  - Email address"
    echo "  - Password (enter twice)"
    echo ""

    docker-compose exec backend python manage.py createsuperuser

    echo ""
    echo -e "${GREEN}✅ Superuser created!${NC}"

    # Get public IP for admin URL
    PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)
    echo ""
    echo "🌍 Access admin panel at:"
    echo "   http://$PUBLIC_IP/admin/"
}

backup_database() {
    echo -e "${YELLOW}🗄️  Creating database backup...${NC}"
    BACKUP_FILE="scholarport_backup_$(date +%Y%m%d_%H%M%S).sql"
    cd ~/scholarport-backend
    docker-compose exec -T db pg_dump -U scholarport_user scholarport > ~/backups/$BACKUP_FILE
    echo -e "${GREEN}✅ Backup created: ~/backups/$BACKUP_FILE${NC}"
}

update_application() {
    echo -e "${YELLOW}🔄 Updating application...${NC}"
    cd ~/scholarport-backend

    # Backup database first
    echo "💾 Creating backup before update..."
    BACKUP_FILE="scholarport_backup_$(date +%Y%m%d_%H%M%S).sql"
    docker-compose exec -T db pg_dump -U scholarport scholarport > ~/backups/$BACKUP_FILE
    echo "✓ Backup saved: ~/backups/$BACKUP_FILE"

    # Stop services
    echo "⏸️  Stopping services..."
    docker-compose down

    # Rebuild images
    echo "🔨 Rebuilding backend image..."
    docker-compose build --no-cache backend

    # Start services
    echo "🚀 Starting updated services..."
    docker-compose up -d

    # Wait for services
    echo "⏳ Waiting for services to start..."
    sleep 15

    # Run migrations
    echo "📊 Running migrations..."
    docker-compose exec -T backend python manage.py migrate

    # Collect static files
    echo "📦 Collecting static files..."
    docker-compose exec -T backend python manage.py collectstatic --no-input

    echo ""
    echo -e "${GREEN}✅ Application updated successfully!${NC}"
    echo ""
    echo "🔍 Checking status..."
    docker-compose ps
    echo ""
    echo "📋 Recent logs:"
    docker-compose logs --tail=20 backend
}

clean_docker() {
    echo -e "${YELLOW}🧹 Cleaning Docker resources...${NC}"
    echo ""
    echo "⚠️  This will remove:"
    echo "  - Stopped containers"
    echo "  - Unused images"
    echo "  - Unused networks"
    echo "  - Build cache"
    echo ""
    read -p "Continue? (y/n): " confirm

    if [ "$confirm" = "y" ]; then
        docker system prune -af
        echo -e "${GREEN}✅ Docker resources cleaned!${NC}"
    else
        echo "Cancelled"
    fi
}

container_stats() {
    echo -e "${YELLOW}📋 Container Statistics (Ctrl+C to exit):${NC}"
    docker stats
}

# Main menu loop
while true; do
    show_menu
    read choice

    case $choice in
        1) initial_setup ;;
        2) start_services ;;
        3) setup_database ;;
        4) create_superuser ;;
        5) stop_services ;;
        6) restart_services ;;
        7) view_logs ;;
        8) health_check ;;
        9) system_status ;;
        10) update_application ;;
        11) backup_database ;;
        12) clean_docker ;;
        13) container_stats ;;
        0) echo -e "${GREEN}👋 Goodbye!${NC}"; exit 0 ;;
        *) echo -e "${RED}❌ Invalid option${NC}" ;;
    esac

    echo ""
    read -p "Press Enter to continue..."
done
