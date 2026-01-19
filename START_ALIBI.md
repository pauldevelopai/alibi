# 🚀 How to Start Alibi - Complete Guide

**Everything you need to get Alibi running from scratch**

---

## ✅ QUICK START (5 Minutes)

### Step 1: Install Dependencies

```bash
cd "/Users/paulmcnally/Developai Dropbox/Paul McNally/DROPBOX/ONMAC/PYTHON 2025/alibi"

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Set OpenAI API Key (For Mobile Camera Vision AI)

```bash
# Set environment variable (temporary - for this session)
export OPENAI_API_KEY="your-openai-key-here"

# OR add to .env file (permanent)
echo 'OPENAI_API_KEY=your-openai-key-here' > .env
```

**Don't have OpenAI key?** That's okay! The system will work with basic CV (free fallback).

### Step 3: Start the Backend API

```bash
# Start API server
python -m uvicorn alibi.alibi_api:app --host 0.0.0.0 --port 8000 --reload
```

**Wait for**: 
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**You'll see** (on first run):
```
======================================================================
[Auth] ✅ Created 3 users with STRONG generated passwords
======================================================================

operator1:   [RANDOM-PASSWORD]
supervisor1: [RANDOM-PASSWORD]
admin:       [RANDOM-PASSWORD]

⚠️  COPY THESE PASSWORDS NOW!
======================================================================
```

**IMPORTANT**: Copy these passwords immediately!

### Step 4: Start the Frontend Console (New Terminal)

```bash
# Open new terminal, then:
cd "/Users/paulmcnally/Developai Dropbox/Paul McNally/DROPBOX/ONMAC/PYTHON 2025/alibi/alibi/console"

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Wait for**:
```
VITE v5.4.21  ready in 702 ms

➜  Local:   http://localhost:5173/
```

### Step 5: Access & Login

1. **Open browser**: http://localhost:5173
2. **Login** with admin credentials from Step 3
3. **Change password** (Settings → Change Password)

### Step 6: Test Mobile Camera (Optional)

**On your phone browser**:
1. Go to: `http://YOUR-COMPUTER-IP:8000/camera/mobile-stream`
2. Allow camera access
3. Point at something and watch the feedback!

---

## 📋 DETAILED STEP-BY-STEP

### Prerequisites Check

```bash
# Check Python version (need 3.10+)
python --version

# Check Node.js (need 16+)
node --version

# Check npm
npm --version

# Check you're in the right directory
pwd
# Should show: .../PYTHON 2025/alibi
```

---

### Part 1: Backend API Setup

#### 1.1 Install Python Dependencies

```bash
cd "/Users/paulmcnally/Developai Dropbox/Paul McNally/DROPBOX/ONMAC/PYTHON 2025/alibi"

pip install -r requirements.txt

# If you get errors, try:
pip install --upgrade pip
pip install -r requirements.txt
```

#### 1.2 Configure Environment (Optional)

```bash
# Create .env file for configuration
cat > .env << 'EOF'
# OpenAI API Key (for Vision AI)
OPENAI_API_KEY=sk-your-openai-key-here

# API Configuration (optional)
ALIBI_API_URL=http://localhost:8000
ALIBI_LOG_LEVEL=INFO
EOF

# OR just export for this session:
export OPENAI_API_KEY="sk-your-key"
```

#### 1.3 Start API Server

```bash
# Option A: With auto-reload (development)
python -m uvicorn alibi.alibi_api:app --host 0.0.0.0 --port 8000 --reload

# Option B: Production mode
python -m uvicorn alibi.alibi_api:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 1.4 Verify API is Running

**Open new terminal and test**:

```bash
# Check health
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","timestamp":"2026-01-19T..."}

# Check API docs
open http://localhost:8000/docs
```

#### 1.5 Copy Initial Passwords

**Look in the API terminal output for**:
```
======================================================================
[Auth] ✅ Created 3 users with STRONG generated passwords
======================================================================

operator1:   ABC123XYZ...
supervisor1: DEF456UVW...
admin:       GHI789RST...

⚠️  COPY THESE PASSWORDS NOW!
======================================================================
```

**Save these somewhere secure!** They won't be shown again.

**Or check the file**:
```bash
cat alibi/data/.initial_passwords.txt
```

---

### Part 2: Frontend Console Setup

#### 2.1 Install Frontend Dependencies

```bash
# Navigate to console directory
cd alibi/console

# Install dependencies (first time only)
npm install

# This might take a few minutes...
```

#### 2.2 Start Development Server

```bash
# Start Vite dev server
npm run dev
```

**Should see**:
```
VITE v5.4.21  ready in 702 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

#### 2.3 Build for Production (Optional)

```bash
# Build optimized production bundle
npm run build

# Serve production build
npm run preview
```

---

### Part 3: First Login & Configuration

#### 3.1 Access Console

1. **Open browser**: http://localhost:5173
2. **You should see**: Alibi login page with demo credentials

#### 3.2 Login

**Use admin credentials from Step 1.5**:
- Username: `admin`
- Password: `[the long random password]`

#### 3.3 Change Your Password

1. Click your username (top right)
2. Go to **Settings** (admin only)
3. **Change Password** section
4. Enter new strong password
5. **Save**

#### 3.4 Explore the Console

**Available Pages**:
- **Incidents** - Live incident stream (empty until cameras added)
- **Reports** - Shift reports
- **Metrics** - KPI dashboard
- **Vehicle Search** - Search vehicle sightings
- **Settings** - System configuration (admin only)

---

### Part 4: Mobile Camera Setup

#### 4.1 Find Your Computer's IP Address

```bash
# Mac/Linux:
ipconfig getifaddr en0

# Or:
ifconfig | grep "inet "

# Windows:
ipconfig

# Example output: 192.168.1.100
```

#### 4.2 Test Mobile Camera

**On your phone browser** (Safari on iPhone, Chrome on Android):

1. Go to: `http://YOUR-IP:8000/camera/mobile-stream`
   - Example: `http://192.168.1.100:8000/camera/mobile-stream`

2. **Allow camera access** when prompted

3. **You should see**:
   - Live camera feed
   - Real-time feedback at bottom
   - Controls at top

4. **Test it**:
   - Point at your face → Should say "person" or describe you
   - Point at a cat → Should say "cat"
   - Point at empty space → Should say "no activity"

#### 4.3 Mobile Camera Controls

- **🔄 Flip** - Switch between front/back camera
- **⏸ Pause** - Stop analysis (save API calls)

---

## 🔍 VERIFICATION CHECKLIST

### ✅ Backend API

- [ ] API running on http://localhost:8000
- [ ] Health check returns `{"status":"healthy"}`
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Initial passwords copied and saved
- [ ] JWT secret file exists at `alibi/data/.jwt_secret`

**Test**:
```bash
curl http://localhost:8000/health
```

### ✅ Frontend Console

- [ ] Console running on http://localhost:5173
- [ ] Login page loads
- [ ] Can login with admin credentials
- [ ] Dashboard shows (empty incidents list is OK)
- [ ] All navigation tabs work

**Test**: 
- Open http://localhost:5173 in browser
- Should see login page, not errors

### ✅ Authentication

- [ ] Can login with admin account
- [ ] JWT token persists (don't need to re-login)
- [ ] Password change works
- [ ] Can logout and login again

**Test**:
```bash
# Login via API
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR-PASSWORD"}'

# Should return token
```

### ✅ Mobile Camera (Optional)

- [ ] Can access mobile stream page from phone
- [ ] Camera permission granted
- [ ] Live feed shows
- [ ] Real-time feedback appears
- [ ] Descriptions are accurate

**Test**: Point phone at different objects and verify descriptions

---

## 🐛 TROUBLESHOOTING

### Problem: "pip: command not found"

**Solution**:
```bash
# Try pip3
pip3 install -r requirements.txt

# Or use python -m pip
python -m pip install -r requirements.txt
```

### Problem: "Port 8000 already in use"

**Solution**:
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
python -m uvicorn alibi.alibi_api:app --host 0.0.0.0 --port 8001
```

### Problem: "npm: command not found"

**Solution**:
```bash
# Install Node.js first
# Mac (with Homebrew):
brew install node

# Or download from: https://nodejs.org/
```

### Problem: "Cannot login - wrong password"

**Solution**:
```bash
# Check the password file
cat alibi/data/.initial_passwords.txt

# Or reset by deleting users file and restarting API
rm alibi/data/users.json
# Restart API - new passwords will be generated
```

### Problem: "Mobile camera shows 'Please login first'"

**Solution**:
1. First login at http://localhost:5173
2. Then open mobile stream page
3. Token is stored in localStorage from login

### Problem: "Mobile camera - slow or no responses"

**Solution**:
```bash
# Check if OpenAI key is set
echo $OPENAI_API_KEY

# If not set:
export OPENAI_API_KEY="sk-your-key"

# Restart API after setting
```

### Problem: "Cannot access from phone"

**Solution**:
```bash
# 1. Find your IP
ipconfig getifaddr en0

# 2. Make sure firewall allows port 8000
# Mac: System Preferences → Security & Privacy → Firewall

# 3. Make sure phone is on same WiFi network

# 4. Try: http://YOUR-IP:8000/camera/mobile-stream
```

---

## 📁 DIRECTORY STRUCTURE

```
alibi/
├── alibi/                          # Python package
│   ├── alibi_api.py               # Main API server
│   ├── auth.py                    # Authentication
│   ├── video/                     # Video processing
│   ├── vision/                    # Vision AI (NEW)
│   ├── mobile_camera.py           # Mobile camera API (NEW)
│   └── console/                   # React frontend
│       ├── src/
│       ├── package.json
│       └── vite.config.ts
│
├── alibi/data/                    # Runtime data
│   ├── .jwt_secret               # JWT secret key
│   ├── .initial_passwords.txt    # Initial passwords
│   ├── users.json                # User credentials
│   ├── incidents.jsonl           # Incident data
│   ├── audit.jsonl               # Audit log
│   └── evidence/                 # Evidence files
│
├── requirements.txt               # Python dependencies
├── .env                          # Environment config (create this)
├── .gitignore                    # Git ignore rules
│
└── docs/
    ├── START_ALIBI.md            # This file
    ├── MOBILE_CAMERA_GUIDE.md    # Mobile camera docs
    ├── DEPLOYMENT_SECURITY_GUIDE.md
    └── SECURITY_HARDENING_COMPLETE.md
```

---

## 🚦 STARTUP SEQUENCE

**Recommended order**:

1. **Terminal 1**: Start API
   ```bash
   python -m uvicorn alibi.alibi_api:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Terminal 2**: Start Console
   ```bash
   cd alibi/console
   npm run dev
   ```

3. **Browser**: Open http://localhost:5173

4. **Phone** (optional): Open http://YOUR-IP:8000/camera/mobile-stream

---

## 🔄 DAILY STARTUP

After initial setup, starting Alibi is simple:

```bash
# Terminal 1: API
cd alibi
python -m uvicorn alibi.alibi_api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Console  
cd alibi/console
npm run dev

# Then open: http://localhost:5173
```

---

## 🛑 SHUTDOWN

```bash
# In each terminal, press:
Ctrl + C

# Or kill processes:
pkill -f "uvicorn.*alibi_api"
pkill -f "vite"
```

---

## 📊 WHAT'S RUNNING

When everything is started:

| Component | Port | URL | Purpose |
|-----------|------|-----|---------|
| API Backend | 8000 | http://localhost:8000 | Main API server |
| API Docs | 8000 | http://localhost:8000/docs | Interactive API docs |
| Frontend Console | 5173 | http://localhost:5173 | Web UI |
| Mobile Camera | 8000 | http://YOUR-IP:8000/camera/mobile-stream | Phone streaming |

---

## ✨ NEXT STEPS

After everything is running:

1. **Explore the Console**
   - Browse different pages
   - Try the vehicle search
   - Check metrics dashboard

2. **Test Mobile Camera**
   - Point at different objects
   - Test safety detection
   - Try front/back camera

3. **Review Documentation**
   - `MOBILE_CAMERA_GUIDE.md` - Mobile camera features
   - `DEPLOYMENT_SECURITY_GUIDE.md` - Production deployment
   - `SECURITY_HARDENING_COMPLETE.md` - Security audit

4. **Configure for Your Needs**
   - Add camera configurations
   - Import plate registry
   - Set up zones
   - Customize thresholds

---

## 🎯 QUICK REFERENCE

### Start Everything
```bash
# Terminal 1
python -m uvicorn alibi.alibi_api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2
cd alibi/console && npm run dev
```

### Check Status
```bash
curl http://localhost:8000/health
```

### View Logs
```bash
# API logs (in Terminal 1)
# Console logs (in Terminal 2)
# Or check: alibi/data/app.log
```

### Get Help
```bash
# API help
python -m uvicorn alibi.alibi_api:app --help

# Check docs
open http://localhost:8000/docs
```

---

## 📞 SUPPORT

**Having issues?**

1. Check this guide's troubleshooting section
2. Check API logs in terminal
3. Verify all dependencies installed
4. Try restarting both services
5. Check firewall settings

**Documentation**:
- This guide: `START_ALIBI.md`
- Mobile camera: `MOBILE_CAMERA_GUIDE.md`
- Security: `SECURITY_HARDENING_COMPLETE.md`
- Deployment: `DEPLOYMENT_SECURITY_GUIDE.md`

---

**You're ready to go! 🚀**
