# 🔒 Alibi Deployment & Security Guide

**For: Namibia Police 3-Month Pilot**  
**Date**: 2026-01-18  
**Status**: Production Ready with Security Hardening

---

## ⚠️ PRE-DEPLOYMENT SECURITY CHECKLIST

### ✅ COMPLETED (Implemented in this release)

- [x] **Strong Password Generation**: Default users now created with cryptographically strong random passwords
- [x] **Persistent JWT Secret**: JWT secret key persists across restarts in `.jwt_secret` file
- [x] **Environment Configuration**: API URL configurable via `ALIBI_API_URL` environment variable
- [x] **Security Warnings**: Clear warnings displayed on first startup
- [x] **Password File Security**: Initial passwords saved with restricted permissions (chmod 600)
- [x] **Gitignore Protection**: Sensitive files excluded from version control

### 🔧 REQUIRED BEFORE DEPLOYMENT

- [ ] Configure reverse proxy (nginx/Apache) with HTTPS
- [ ] Set up firewall rules
- [ ] Configure backup system
- [ ] Change default passwords after first login
- [ ] Review and customize `alibi_settings.json`
- [ ] Import DMV/police databases
- [ ] Test all systems end-to-end

---

## 📋 DEPLOYMENT STEPS

### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.10 python3-pip nginx postgresql redis-server -y

# Create application user
sudo useradd -r -s /bin/false alibi
sudo mkdir -p /var/lib/alibi
sudo chown alibi:alibi /var/lib/alibi

# Create directories
sudo mkdir -p /var/lib/alibi/data
sudo mkdir -p /var/lib/alibi/evidence
sudo mkdir -p /var/log/alibi
sudo mkdir -p /backup/alibi

# Set permissions
sudo chown -R alibi:alibi /var/lib/alibi
sudo chown -R alibi:alibi /var/log/alibi
sudo chmod 750 /var/lib/alibi/data
```

### Step 2: Install Alibi

```bash
# Clone repository
cd /opt
sudo git clone <repository-url> alibi
cd alibi

# Install Python dependencies
sudo pip3 install -r requirements.txt

# Set ownership
sudo chown -R alibi:alibi /opt/alibi
```

### Step 3: Configure Environment

```bash
# Copy and customize environment file
sudo cp alibi/config/production.env.template /etc/alibi/production.env
sudo nano /etc/alibi/production.env

# Generate JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output to ALIBI_JWT_SECRET in production.env

# Restrict permissions
sudo chmod 600 /etc/alibi/production.env
sudo chown alibi:alibi /etc/alibi/production.env
```

### Step 4: First Startup

```bash
# Start API (as alibi user)
sudo -u alibi python3 -m uvicorn alibi.alibi_api:app --host 0.0.0.0 --port 8000

# IMPORTANT: Note the generated passwords displayed!
# Example output:
# ======================================================================
# [Auth] ✅ Created 3 users with STRONG generated passwords
# ======================================================================
# 
# 🔒 SECURITY NOTICE:
#    Initial passwords saved to: alibi/data/.initial_passwords.txt
#    
#    operator1:   XkJ9_vR2nPqL4wTy8sSm3g
#    supervisor1: mN7cVx4kLp9wRt2bYq5gFs
#    admin:       pQ8wLk3xRv6nYt2cZs4mBg
# 
# ⚠️  CRITICAL: 
#    1. Copy these passwords NOW
#    2. Change them immediately after first login
#    3. Delete alibi/data/.initial_passwords.txt after copying
# ======================================================================

# Copy passwords immediately!
sudo cat /var/lib/alibi/data/.initial_passwords.txt

# Delete after copying (IMPORTANT!)
sudo rm /var/lib/alibi/data/.initial_passwords.txt
```

### Step 5: Configure HTTPS (Nginx)

```nginx
# /etc/nginx/sites-available/alibi
server {
    listen 443 ssl http2;
    server_name alibi.police.gov.na;

    # SSL Certificate (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/alibi.police.gov.na/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/alibi.police.gov.na/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to Alibi API
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Websocket support (for SSE)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }

    # Evidence files (with authentication check)
    location /evidence/ {
        internal;  # Only accessible via X-Accel-Redirect
        alias /var/lib/alibi/evidence/;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=alibi_limit:10m rate=10r/s;
    limit_req zone=alibi_limit burst=20 nodelay;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name alibi.police.gov.na;
    return 301 https://$server_name$request_uri;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/alibi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Set Up Systemd Service

```ini
# /etc/systemd/system/alibi-api.service
[Unit]
Description=Alibi Police Oversight API
After=network.target postgresql.service

[Service]
Type=simple
User=alibi
Group=alibi
WorkingDirectory=/opt/alibi
EnvironmentFile=/etc/alibi/production.env

ExecStart=/usr/bin/python3 -m uvicorn alibi.alibi_api:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info

Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/alibi /var/log/alibi

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable alibi-api
sudo systemctl start alibi-api
sudo systemctl status alibi-api
```

### Step 7: Video Worker Setup

```ini
# /etc/systemd/system/alibi-worker.service
[Unit]
Description=Alibi Video Processing Worker
After=network.target alibi-api.service

[Service]
Type=simple
User=alibi
Group=alibi
WorkingDirectory=/opt/alibi
EnvironmentFile=/etc/alibi/production.env

ExecStart=/usr/bin/python3 -m alibi.video.worker \
    --config /etc/alibi/cameras.json \
    --zones /etc/alibi/zones.json

Restart=always
RestartSec=30

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/alibi /var/log/alibi

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable alibi-worker
sudo systemctl start alibi-worker
```

---

## 🔐 FIRST LOGIN & PASSWORD CHANGES

### Step 1: Initial Login

1. Open browser: `https://alibi.police.gov.na`
2. Login as **admin** with generated password from startup
3. **IMMEDIATELY** go to user settings
4. Change password to new strong password:
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - Example: `N@mibia2026!SecurePass`

### Step 2: Password Policy

**Enforce this policy for all users:**
- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character
- No common words or patterns
- Change every 90 days

**Store passwords securely:**
- Use password manager (KeePass, 1Password, Bitwarden)
- NEVER write on paper
- NEVER share via email/SMS
- NEVER reuse passwords

---

## 📊 POST-DEPLOYMENT VERIFICATION

### Security Tests

```bash
# 1. Verify HTTPS is working
curl -I https://alibi.police.gov.na
# Should return 200 OK with SSL certificate info

# 2. Verify HTTP redirects to HTTPS
curl -I http://alibi.police.gov.na
# Should return 301 Moved Permanently

# 3. Test authentication
curl -X POST https://alibi.police.gov.na/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"OLD_PASSWORD"}'
# Should return 401 Unauthorized (password changed)

# 4. Verify JWT persistence
# Restart API and ensure existing tokens still work

# 5. Check file permissions
ls -la /var/lib/alibi/data/.jwt_secret
# Should show: -rw------- (600)

ls -la /etc/alibi/production.env
# Should show: -rw------- (600)
```

### Functional Tests

1. **Login Test**: Verify all user roles can login
2. **Incident Creation**: Create test incident and verify workflow
3. **Decision Recording**: Make decisions and verify audit log
4. **Evidence Capture**: Verify snapshots and clips are saved
5. **Detector Test**: Verify all detectors are active
6. **Watchlist Test**: Enroll face and verify detection
7. **Plate Detection**: Test plate reading and hotlist matching
8. **Mismatch Detection**: Test plate-vehicle mismatch alerts
9. **Console Access**: Verify all UI pages load correctly
10. **Role-Based Access**: Verify operator/supervisor/admin permissions

---

## 🔄 MAINTENANCE & MONITORING

### Daily Checks

```bash
# Check service status
sudo systemctl status alibi-api
sudo systemctl status alibi-worker

# Check logs for errors
sudo journalctl -u alibi-api -n 100 --no-pager
sudo journalctl -u alibi-worker -n 100 --no-pager

# Check disk space
df -h /var/lib/alibi
```

### Weekly Maintenance

```bash
# Review audit logs
tail -100 /var/lib/alibi/data/audit.jsonl

# Check incident statistics
# (Use console UI /metrics page)

# Verify backups
ls -lh /backup/alibi/

# Check for software updates
cd /opt/alibi
sudo git fetch
sudo git status
```

### Security Monitoring

Monitor for:
- Failed login attempts (>5 in 5 minutes)
- Unauthorized access attempts
- Unusual incident patterns
- System resource spikes
- Disk space warnings
- Certificate expiration (90 days before)

---

## 🆘 TROUBLESHOOTING

### Issue: Cannot login after password change

**Solution**: 
```bash
# Reset admin password (requires server access)
sudo -u alibi python3 -m alibi.auth.reset_password --username admin
```

### Issue: JWT tokens invalidated after restart

**Check**:
```bash
# Verify JWT secret file exists and persists
cat /var/lib/alibi/data/.jwt_secret
# Should show the same secret after restart
```

### Issue: Evidence files not accessible

**Check permissions**:
```bash
sudo ls -la /var/lib/alibi/evidence/
sudo chown -R alibi:alibi /var/lib/alibi/evidence/
sudo chmod -R 755 /var/lib/alibi/evidence/
```

---

## 📞 SUPPORT & ESCALATION

**Technical Issues**: Contact Alibi Support Team  
**Security Incidents**: Immediately contact Namibia Police IT Security  
**Emergency**: Shutdown services if breach suspected

```bash
# Emergency shutdown
sudo systemctl stop alibi-api
sudo systemctl stop alibi-worker
```

---

## 📜 AUDIT & COMPLIANCE

All actions are logged to `/var/lib/alibi/data/audit.jsonl` including:
- User logins/logouts
- Password changes
- Incident decisions
- Evidence access
- Settings changes
- User management actions

**Retention**: 90 days minimum (configurable)  
**Review**: Weekly by supervisor, monthly by admin

---

**Deployment completed**: __________ (Date)  
**Deployed by**: __________ (Name)  
**Reviewed by**: __________ (Name)  
**Next review**: __________ (Date)
