# 🚀 Complete SSL Deployment Guide for Scholarport

## Architecture Overview

```
Internet
    ↓
DNS: scholarport.co → 13.232.108.169 (Frontend EC2)
DNS: Backend via same domain with /api/ path
    ↓
Frontend EC2 (13.232.108.169)
    ├── Frontend Files (React/HTML)
    └── Nginx → https://scholarport.co
            ↓
Backend EC2 (43.205.95.162)
    ├── Nginx (Port 443) → SSL Termination
    ├── Django/Gunicorn (Port 8000)
    └── PostgreSQL (Port 5432)
```

## Current Setup Status

✅ Domain registered: scholarport.co
✅ DNS pointing to: 13.232.108.169 (Frontend)
✅ Backend EC2: 43.205.95.162
✅ Database: PostgreSQL with 243 universities
⏳ SSL: Ready to configure

## Important: Two-Server Architecture

**You have TWO separate EC2 instances:**

1. **Frontend EC2** (13.232.108.169) - `scholarport.co`
   - Serves static frontend files
   - Proxies `/api/*` requests to backend

2. **Backend EC2** (43.205.95.162) - No public domain
   - Runs Django API
   - Accessed only through frontend EC2 proxy

## Deployment Plan

### Phase 1: Backend SSL Setup (This Server - 43.205.95.162)

Since your domain points to the FRONTEND server, we need to use the IP address for backend:

**Option A: Keep Backend on IP (Recommended for now)**
- Backend stays at: `http://43.205.95.162`
- Frontend proxies to it
- Simpler setup, works immediately

**Option B: Get Subdomain for Backend (Better for production)**
- Create `api.scholarport.co` → point to 43.205.95.162
- Backend gets its own SSL certificate
- More professional setup

### Phase 2: Frontend Configuration

Update your frontend EC2 to proxy API requests to backend.

---

## 🎯 Quick Start: Deploy with Current Setup

### Step 1: Upload Files to Backend EC2 (43.205.95.162)

```powershell
# From Windows (your local machine)
cd C:\Users\Nautilus\Desktop\sch

# Upload updated configs
scp -i scholarport-backend.pem .env.production ubuntu@43.205.95.162:~/scholarport-backend/.env
scp -i scholarport-backend.pem nginx/conf.d/temp-http-for-ssl.conf ubuntu@43.205.95.162:~/scholarport-backend/nginx/conf.d/
scp -i scholarport-backend.pem nginx/conf.d/scholarport-ssl.conf ubuntu@43.205.95.162:~/scholarport-backend/nginx/conf.d/
scp -i scholarport-backend.pem setup-ssl.sh ubuntu@43.205.95.162:~/scholarport-backend/
```

### Step 2: DECISION - Choose Your Approach

#### 🅰️ OPTION A: Backend on IP (Quick & Simple)

**Backend:** Keep using `http://43.205.95.162`

**On Backend EC2:**
```bash
cd ~/scholarport-backend

# Remove SSL configs (not needed for IP)
rm -f nginx/conf.d/temp-http-for-ssl.conf
rm -f nginx/conf.d/scholarport-ssl.conf

# Use simple HTTP config
rm -f nginx/conf.d/*.conf
mv nginx/conf.d/http-with-static.conf nginx/conf.d/active.conf

# Restart
docker-compose restart nginx
```

**Update Frontend Nginx on Frontend EC2 (13.232.108.169):**
```nginx
# Frontend EC2 nginx config
server {
    listen 443 ssl http2;
    server_name scholarport.co www.scholarport.co;

    # Your SSL certs here

    # Serve frontend files
    location / {
        root /var/www/scholarport;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://43.205.95.162:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 🅱️ OPTION B: Backend with Subdomain (Professional)

**Create DNS record:**
- `api.scholarport.co` → `43.205.95.162`

**Wait for DNS propagation (5-15 minutes):**
```bash
# Test from your local machine
nslookup api.scholarport.co
# Should return: 43.205.95.162
```

**On Backend EC2 (43.205.95.162):**
```bash
cd ~/scholarport-backend

# Edit setup-ssl.sh
nano setup-ssl.sh
# Change:
#   DOMAIN="scholarport.co"
# To:
#   DOMAIN="api.scholarport.co"
#   WWW_DOMAIN=""  # Remove www, not needed for API

# Make executable and run
chmod +x setup-ssl.sh
./setup-ssl.sh
```

**Update Frontend Nginx on Frontend EC2 (13.232.108.169):**
```nginx
# Frontend EC2 nginx config
server {
    listen 443 ssl http2;
    server_name scholarport.co www.scholarport.co;

    # Your SSL certs here

    # Serve frontend files
    location / {
        root /var/www/scholarport;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend subdomain
    location /api/ {
        proxy_pass https://api.scholarport.co;
        proxy_ssl_server_name on;
        proxy_set_header Host $proxy_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 📋 Detailed Steps for Option B (Subdomain Approach)

### 1. Create DNS Record

In your domain registrar (where you bought scholarport.co):

```
Type: A
Name: api
Value: 43.205.95.162
TTL: 300 (5 minutes)
```

### 2. Verify DNS Propagation

```bash
# From any machine
nslookup api.scholarport.co

# Should show:
# Name: api.scholarport.co
# Address: 43.205.95.162
```

### 3. Update Backend Configuration

**On Backend EC2:**
```bash
cd ~/scholarport-backend

# Make SSL script executable
chmod +x setup-ssl.sh

# Edit script with your email
nano setup-ssl.sh
# Change line 10:
# EMAIL="your-email@example.com"
# To your actual email

# Also change domain:
# DOMAIN="api.scholarport.co"
# WWW_DOMAIN=""  # Leave empty or remove

# Run SSL setup
./setup-ssl.sh
```

The script will:
1. ✅ Check DNS resolution
2. ✅ Configure Nginx for HTTP
3. ✅ Obtain SSL certificate from Let's Encrypt
4. ✅ Switch to HTTPS configuration
5. ✅ Restart all services
6. ✅ Test endpoints

### 4. Configure Frontend Nginx

**On Frontend EC2 (13.232.108.169):**

```bash
# SSH to frontend server
ssh -i scholarport-frontend.pem ubuntu@13.232.108.169

# Edit nginx config
sudo nano /etc/nginx/sites-available/scholarport.conf
```

```nginx
# Frontend Nginx Configuration
server {
    listen 80;
    server_name scholarport.co www.scholarport.co;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name scholarport.co www.scholarport.co;

    # SSL Configuration (get certificate first with certbot)
    ssl_certificate /etc/letsencrypt/live/scholarport.co/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/scholarport.co/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Frontend files
    root /var/www/scholarport;
    index index.html;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        # Remove /api prefix when proxying
        rewrite ^/api/(.*)$ /$1 break;

        proxy_pass https://api.scholarport.co;
        proxy_ssl_server_name on;
        proxy_ssl_verify off;  # Set to 'on' after testing

        proxy_http_version 1.1;
        proxy_set_header Host api.scholarport.co;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;

        # Timeouts
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files (if any on frontend)
    location /static/ {
        alias /var/www/scholarport/static/;
        expires 30d;
    }
}
```

### 5. Get SSL Certificate for Frontend

**On Frontend EC2:**
```bash
# Install certbot if not already installed
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# Stop nginx temporarily
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone \
    --preferred-challenges http \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    -d scholarport.co \
    -d www.scholarport.co

# Start nginx
sudo systemctl start nginx
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Update Frontend Code

Update your frontend API configuration:

```javascript
// config.js or api.js
const API_BASE_URL = 'https://scholarport.co/api';

// All API calls will go through:
// https://scholarport.co/api/chat/start/
// Which nginx proxies to:
// https://api.scholarport.co/api/chat/start/
// Which Django handles at:
// http://backend:8000/api/chat/start/
```

---

## 🧪 Testing

### Test Backend (Direct)

```bash
# From anywhere
curl https://api.scholarport.co/api/chat/health/
# Expected: {"success":true,"message":"Scholarport Backend API is running",...}

# Test admin
curl https://api.scholarport.co/admin/
# Expected: HTML response
```

### Test Frontend + Backend (Through Proxy)

```bash
# Frontend serving
curl https://scholarport.co/
# Expected: Your frontend HTML

# API through frontend
curl https://scholarport.co/api/chat/health/
# Expected: {"success":true,"message":"Scholarport Backend API is running",...}
```

### Test in Browser

1. **Frontend:** https://scholarport.co
   - Should show your app
   - Check browser console for errors

2. **API Call:** Open browser console:
   ```javascript
   fetch('https://scholarport.co/api/chat/health/')
       .then(r => r.json())
       .then(d => console.log(d))
   ```
   - Should show health check response
   - No CORS errors

3. **Admin Panel:** https://api.scholarport.co/admin/
   - Should show Django admin login
   - CSS should load properly

---

## 🔒 Security Checklist

After deployment:

- [ ] SSL certificates obtained for both domains
- [ ] HTTP redirects to HTTPS working
- [ ] HSTS header enabled
- [ ] CORS configured correctly in Django
- [ ] Django `ALLOWED_HOSTS` includes both domains
- [ ] Django `CSRF_TRUSTED_ORIGINS` includes both domains
- [ ] Firewall rules allow only ports 80, 443, 22
- [ ] Strong SECRET_KEY in production
- [ ] DEBUG=False in production
- [ ] Database password is strong
- [ ] Regular backups scheduled

---

## 🐛 Troubleshooting

### Backend SSL Issues

```bash
# Check nginx config
docker-compose exec nginx nginx -t

# Check certificate files
ls -la certbot/conf/live/api.scholarport.co/

# View nginx logs
docker-compose logs nginx | tail -50

# View backend logs
docker-compose logs backend | tail -50

# Restart everything
docker-compose restart
```

### Frontend Proxy Issues

```bash
# On frontend EC2
sudo nginx -t
sudo tail -f /var/log/nginx/error.log

# Test backend connectivity
curl -v https://api.scholarport.co/api/chat/health/
```

### CORS Errors

Check `.env` on backend:
```bash
# Should have:
CORS_ALLOWED_ORIGINS=https://scholarport.co,https://www.scholarport.co
CSRF_TRUSTED_ORIGINS=https://scholarport.co,https://www.scholarport.co
```

Restart backend:
```bash
docker-compose restart backend
```

### DNS Not Resolving

```bash
# Check DNS
nslookup api.scholarport.co

# If not resolving, wait 5-15 minutes for propagation
# Check with online tools:
# https://www.whatsmydns.net/
```

---

## 📊 Final URLs

After complete setup:

| Service | URL | Notes |
|---------|-----|-------|
| Frontend | https://scholarport.co | Main application |
| API (proxied) | https://scholarport.co/api/ | Through frontend |
| Backend (direct) | https://api.scholarport.co | If using subdomain |
| Admin Panel | https://api.scholarport.co/admin/ | Backend admin |
| Health Check | https://scholarport.co/api/chat/health/ | System status |

---

## 🎯 Recommendation

**For your setup, I recommend Option B (Subdomain)**:

✅ More professional
✅ Better SSL management
✅ Cleaner architecture
✅ Easier to debug
✅ Can add more services later (e.g., docs.scholarport.co)

**Steps:**
1. Create `api.scholarport.co` DNS record → 43.205.95.162
2. Run `./setup-ssl.sh` on backend EC2
3. Configure frontend Nginx to proxy to `api.scholarport.co`
4. Get SSL cert for `scholarport.co` on frontend
5. Update frontend code to use `https://scholarport.co/api/`
6. Test everything
7. Deploy!

---

## 📞 Next Steps

1. **Choose Option A or B** (I recommend B)
2. **If Option B:** Create DNS record first, wait for propagation
3. **Upload files** to backend EC2
4. **Run SSL script** on backend
5. **Configure frontend** Nginx and SSL
6. **Update frontend code** API URLs
7. **Test thoroughly**
8. **Go live!** 🚀

Need help with any step? Let me know! 💪
