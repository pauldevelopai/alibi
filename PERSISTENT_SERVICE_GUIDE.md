# 🚀 Alibi Persistent Services Guide

**Run Alibi 24/7 without keeping terminals open**

---

## ✅ What is This?

Instead of running Alibi in a terminal (which stops when you close it), you can now run it as **persistent background services** that:

- ✅ **Stay running** even after closing terminals
- ✅ **Survive restarts** (optional)
- ✅ **Auto-restart** if they crash
- ✅ **Run in background** silently
- ✅ **Keep logs** for debugging

---

## 🎯 Quick Start

### Start Persistent Services
```bash
./start_persistent.sh
```

**What this does:**
- Starts API on port 8000 (HTTPS)
- Starts Console on port 5173
- Runs both in background
- Creates log files
- Saves process IDs

### Stop Services
```bash
./stop_persistent.sh
```

### Check Status
```bash
./status_persistent.sh
```

---

## 📋 Complete Commands

### Starting Services

```bash
cd "/Users/paulmcnally/Developai Dropbox/Paul McNally/DROPBOX/ONMAC/PYTHON 2025/alibi"
./start_persistent.sh
```

Output:
```
╔═══════════════════════════════════════════════════════════════════════╗
║         Starting Alibi as Persistent Background Services             ║
╚═══════════════════════════════════════════════════════════════════════╝

✅ API started (PID: 12345)
✅ Console started (PID: 12346)

🌐 Access Alibi at:
   https://McNallyMac.local:8000/
```

### Checking Status

```bash
./status_persistent.sh
```

Shows:
- ✅ Which services are running
- 📊 Process IDs
- 📝 Recent log entries
- 🌐 Access URLs

### Stopping Services

```bash
./stop_persistent.sh
```

Cleanly stops both API and Console.

### Restarting Services

```bash
./stop_persistent.sh && ./start_persistent.sh
```

---

## 📂 Log Files

Logs are saved in `logs/` directory:

### API Logs
```bash
# View live logs
tail -f logs/alibi_api.log

# View last 50 lines
tail -50 logs/alibi_api.log

# Search logs
grep "error" logs/alibi_api.log -i
```

### Console Logs
```bash
# View live logs
tail -f logs/alibi_console.log

# View last 50 lines
tail -50 logs/alibi_console.log
```

### Log Rotation

Logs grow over time. To clear them:

```bash
# Backup old logs
mv logs/alibi_api.log logs/alibi_api.log.old
mv logs/alibi_console.log logs/alibi_console.log.old

# Or just delete
rm logs/*.log

# Services will create new log files automatically
```

---

## 🔄 Auto-Start on Mac Restart (Optional)

Currently, services stop when you restart your Mac. To make them start automatically on boot:

### Option 1: Add to Login Items (Simple)

1. Open **System Settings** → **General** → **Login Items**
2. Click **+** under "Open at Login"
3. Navigate to and select `start_persistent.sh`
4. Done! Alibi starts when you login

### Option 2: Create Launch Agent (Advanced)

This is more robust but requires more setup. See the `install_service.sh` script for automated setup.

---

## 🛠️ Troubleshooting

### Services Won't Start

**Check if ports are in use:**
```bash
lsof -i :8000    # Check API port
lsof -i :5173    # Check Console port
```

**Kill existing processes:**
```bash
./stop_persistent.sh
pkill -f "uvicorn.*alibi"
pkill -f "vite.*console"
```

**Then start again:**
```bash
./start_persistent.sh
```

### Services Keep Stopping

**Check logs for errors:**
```bash
tail -100 logs/alibi_api.log
tail -100 logs/alibi_console.log
```

**Common issues:**
- Missing dependencies: `pip install -r requirements.txt`
- Missing Node modules: `cd alibi/console && npm install`
- Permission issues: Check file permissions
- Port conflicts: Stop other services using ports 8000/5173

### Can't Access Alibi

**Check if services are running:**
```bash
./status_persistent.sh
```

**Try accessing:**
- HTTPS: `https://McNallyMac.local:8000/`
- HTTP fallback: `http://localhost:8000/`
- Console: `http://localhost:5173/`

**Check firewall:**
```bash
# macOS Firewall might block connections
# System Settings → Network → Firewall
```

### High CPU/Memory Usage

**Check resource usage:**
```bash
top -pid $(cat logs/alibi_api.pid)
top -pid $(cat logs/alibi_console.pid)
```

**Restart services:**
```bash
./stop_persistent.sh && sleep 2 && ./start_persistent.sh
```

---

## 📊 Monitoring

### Watch Services in Real-Time

**Terminal 1 - API Logs:**
```bash
tail -f logs/alibi_api.log
```

**Terminal 2 - Console Logs:**
```bash
tail -f logs/alibi_console.log
```

**Terminal 3 - Status Check:**
```bash
watch -n 5 './status_persistent.sh'
```

### Check Service Health

```bash
# API health check
curl -k https://localhost:8000/health

# Expected output:
# {"status":"healthy","timestamp":"..."}
```

### Monitor Disk Usage

```bash
# Check log file sizes
ls -lh logs/

# Check total data directory size
du -sh alibi/data/
```

---

## 🎯 Best Practices

### 1. Regular Log Rotation

```bash
# Weekly log cleanup script
cat > cleanup_logs.sh << 'EOF'
#!/bin/bash
cd "/Users/paulmcnally/Developai Dropbox/Paul McNally/DROPBOX/ONMAC/PYTHON 2025/alibi"
mv logs/alibi_api.log logs/alibi_api.$(date +%Y%m%d).log
mv logs/alibi_console.log logs/alibi_console.$(date +%Y%m%d).log
find logs/ -name "*.log" -mtime +7 -delete
EOF

chmod +x cleanup_logs.sh
```

### 2. Health Check Script

```bash
# Create health_check.sh
cat > health_check.sh << 'EOF'
#!/bin/bash
if curl -k -s https://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Alibi is healthy"
else
    echo "❌ Alibi is down - restarting..."
    ./stop_persistent.sh
    sleep 2
    ./start_persistent.sh
fi
EOF

chmod +x health_check.sh
```

Run hourly via cron:
```bash
# Edit crontab
crontab -e

# Add line:
0 * * * * cd "/Users/paulmcnally/Developai Dropbox/Paul McNally/DROPBOX/ONMAC/PYTHON 2025/alibi" && ./health_check.sh >> logs/health_check.log 2>&1
```

### 3. Backup Configuration

```bash
# Backup important data
tar -czf alibi_backup_$(date +%Y%m%d).tar.gz \
  alibi/data/users.json \
  alibi/data/alibi_settings.json \
  alibi/data/zones.json \
  ssl/
```

---

## 🚀 Production Deployment

For true production deployment (e.g., Namibia pilot), use proper service manager:

### Install as System Service (macOS)

```bash
# Not yet implemented - use persistent scripts for now
# Future: ./install_service.sh
```

### Using Process Manager (PM2)

Alternative option using PM2:

```bash
# Install PM2
npm install -g pm2

# Start with PM2
pm2 start ecosystem.config.js

# Save configuration
pm2 save

# Auto-start on boot
pm2 startup
```

---

## 📝 Summary

**Current Setup (Persistent Background):**
- ✅ Services run in background
- ✅ Survive terminal closures
- ✅ Manual start after Mac restart
- ✅ Full logging
- ✅ Easy management scripts

**Commands:**
```bash
./start_persistent.sh    # Start services
./stop_persistent.sh     # Stop services
./status_persistent.sh   # Check status
tail -f logs/*.log       # View logs
```

**Access:**
- Main app: `https://McNallyMac.local:8000/`
- Console: `http://localhost:5173/`
- Logs: `logs/` directory

---

## ✅ Checklist

After running `./start_persistent.sh`:

- [ ] Check status: `./status_persistent.sh`
- [ ] Access app: `https://McNallyMac.local:8000/`
- [ ] Test login
- [ ] Test camera
- [ ] Check logs: `tail -f logs/alibi_api.log`
- [ ] Verify it keeps running after closing terminal
- [ ] Bookmark the URL for easy access

---

**You can now close your terminal and Alibi will keep running! 🚀**
