# 📱 iPhone Access Guide - Alibi 24/7

**Access Alibi from your iPhone anytime, anywhere (on your local network)**

---

## 🌐 iPhone Access URL

**Bookmark this on your iPhone:**

```
https://McNallyMac.local:8000/
```

---

## 📲 Quick Setup (One-Time)

### Step 1: Open Safari on iPhone

**Why Safari?** It has the best camera permissions on iOS.

### Step 2: Visit the URL

1. Open Safari
2. Type: `https://McNallyMac.local:8000/`
3. Tap "Show Details" when you see the certificate warning
4. Tap "visit this website"
5. Confirm

### Step 3: Bookmark It

1. Tap the **Share** button (square with arrow)
2. Tap **Add to Home Screen**
3. Name it: **Alibi Camera**
4. Tap **Add**

**Now you have an app icon on your home screen!** 🎉

### Step 4: Grant Camera Permission

1. First time you use camera, Safari will ask for permission
2. Tap **Allow**
3. If you accidentally denied:
   - Go to **Settings** → **Safari** → **Camera**
   - Set to **Allow**

---

## 🎯 Features Available on iPhone

### 1. Live Camera Stream
- Tap "Live Camera Stream" card
- Aim at anything
- Get real-time AI analysis
- See objects, activities, safety concerns

### 2. Camera History
- Tap "Camera History" card  
- View all analyzed snapshots
- See AI descriptions
- Provide feedback
- View safety concerns

### 3. View Incidents (if logged in as operator/supervisor)
- Real-time incident monitoring
- Make decisions
- View evidence

### 4. Reports & Metrics
- Generate shift reports
- View KPIs
- Monitor performance

---

## 🔒 Login Credentials

**First Time Login:**

Check your Mac for initial passwords:
```bash
cat alibi/data/.initial_passwords.txt
```

**Admin Account:**
- Username: `admin`
- Password: (see above file)

**Change password after first login!**

---

## ✅ iPhone Quick Checklist

After setup, you should be able to:

- [ ] Open Safari on iPhone
- [ ] Visit `https://McNallyMac.local:8000/`
- [ ] Accept certificate warning (one-time)
- [ ] See the Alibi dashboard
- [ ] Add to home screen
- [ ] Tap the home screen icon → Opens instantly
- [ ] Use camera stream
- [ ] View camera history
- [ ] Everything works even when Mac terminal is closed

---

## 🔄 Always Available

**Because services are now persistent:**

✅ Alibi runs 24/7 on your Mac
✅ iPhone can connect anytime
✅ No need to start services manually
✅ No need to keep terminal open
✅ Just open the home screen icon!

**As long as:**
- Your Mac is on
- Your iPhone is on the same WiFi network

---

## 🛠️ Troubleshooting iPhone Access

### "Can't connect to server"

**Check Mac is on:**
```bash
# On Mac, check services are running:
./status_persistent.sh
```

If not running:
```bash
./start_persistent.sh
```

### "Camera not working"

**Grant permissions:**
1. iPhone Settings → Safari → Camera → Allow
2. Refresh the page
3. Try again

**Alternative:**
- Use **Settings** → **Safari** → **Privacy & Security** → **Camera Access**

### "Certificate warning keeps appearing"

This is normal for self-signed certificates. You need to:
1. Tap "Show Details"
2. Tap "visit this website"  
3. This is safe - it's your own Mac!

### "McNallyMac.local not found"

**Alternative access methods:**

Find your Mac's IP address:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Then use IP address instead:
```
https://192.168.X.X:8000/
```

---

## 📱 Creating Home Screen Icon

### Method 1: Add to Home Screen

1. Open Safari
2. Visit `https://McNallyMac.local:8000/`
3. Tap **Share** button
4. Scroll down, tap **Add to Home Screen**
5. Tap **Add**

### Method 2: Save as Bookmark

1. Visit the URL in Safari
2. Tap the **Bookmarks** button
3. Tap **Add Bookmark**
4. Save to **Favorites**

---

## 🎨 Using Alibi Features on iPhone

### Live Camera Stream

1. Tap **Live Camera Stream** card
2. Allow camera access
3. Point at anything:
   - People → Describes activities
   - Objects → Identifies them
   - Scenes → Describes setting
   - Safety concerns → Alerts you
4. Analysis appears in real-time below camera
5. Everything is automatically saved!

### Camera History

1. Tap **Camera History** card
2. See grid of all snapshots
3. Tap any snapshot to view:
   - Full-size image
   - AI analysis
   - Detected objects
   - Activities
   - Safety concerns
4. Provide feedback if AI got something wrong
5. Help improve the system!

### Providing Feedback

1. Open Camera History
2. Tap a snapshot
3. Tap **✏️ Provide Feedback**
4. Fill out form:
   - Corrected description
   - SA context notes
   - What AI missed
   - Star rating
5. Submit!
6. Your feedback improves the AI! 🇿🇦

---

## 🌐 Network Requirements

**Your iPhone must be on the same WiFi network as your Mac.**

**Check WiFi:**
- iPhone: Settings → WiFi → Connected to same network as Mac
- Mac: System Settings → WiFi → Note network name

**Both devices must be on:**
- Same network (e.g., "Home WiFi")
- Same subnet (usually automatic)

**Won't work:**
- On cellular data (4G/5G)
- On different WiFi network
- When Mac is off/sleeping

---

## 💡 Pro Tips

### Bookmark on Lock Screen

1. Add to home screen (see above)
2. Long-press the icon
3. Add to **Today View**
4. Access from lock screen!

### Quick Access Widget

1. Go to home screen
2. Long-press empty space
3. Tap **+** (top left)
4. Search **Safari**
5. Add **Siri Suggestions**
6. Alibi will appear as suggested!

### Voice Access (Siri)

1. Use Siri: "Open Alibi Camera"
2. Siri will open the bookmarked page

### Offline Message

If you get "Can't connect":
- Mac might be sleeping
- Check WiFi connection
- Check services: `./status_persistent.sh` on Mac

---

## 📊 What Gets Saved

Every time you use the camera:

✅ Snapshot saved (not video - saves space!)
✅ AI analysis saved
✅ Timestamp
✅ Objects detected
✅ Activities observed
✅ Safety concerns

**Storage-efficient:**
- Only snapshots, not videos (small files)
- Thumbnails for gallery (faster loading)
- Auto-cleanup after 7 days (configurable)

---

## 🔐 Security

**Your data stays local:**
- Everything stored on your Mac
- Nothing sent to cloud (except OpenAI API for analysis)
- Only accessible on your local network
- HTTPS encryption between iPhone and Mac

**Privacy:**
- No images sent in feedback
- Only you can access
- Secure login required

---

## ✅ Daily Usage

**Morning:**
1. Tap Alibi icon on iPhone home screen
2. Opens instantly (services already running!)
3. Use camera or view history

**Throughout Day:**
1. Access anytime
2. Camera always ready
3. History always available

**Evening:**
1. Review Camera History
2. Provide feedback on interesting captures
3. Help improve AI

**Mac:**
- Leave it on
- Services run automatically
- No manual start needed

---

## 🆘 Emergency Restart

**If iPhone can't connect:**

On Mac:
```bash
cd "/Users/paulmcnally/Developai Dropbox/Paul McNally/DROPBOX/ONMAC/PYTHON 2025/alibi"
./stop_persistent.sh
./start_persistent.sh
```

Wait 10 seconds, then try iPhone again.

---

## 📞 Quick Reference Card

**iPhone Quick Access:**
```
URL: https://McNallyMac.local:8000/
Home Screen Icon: Tap to open
Camera: Safari → Allow permissions
Works: When Mac is on + same WiFi
```

**Features:**
- Live Camera Stream
- Camera History
- Incident Monitoring
- Reports & Metrics

**Mac Commands:**
```bash
# Check status
./status_persistent.sh

# Restart if needed
./stop_persistent.sh && ./start_persistent.sh
```

---

## 🎉 You're All Set!

**iPhone can now access Alibi 24/7:**

✅ Services run persistently on Mac
✅ iPhone connects anytime
✅ Camera works
✅ History accessible
✅ No manual startup needed
✅ Add to home screen for one-tap access

**Just keep:**
- Mac powered on
- Both devices on same WiFi
- Bookmark saved on iPhone

**Now go analyze some footage! 📱🎥🇿🇦**
