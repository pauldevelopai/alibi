# 📱 Alibi Mobile - Complete System Guide

**Everything works from iPhone Safari. No desktop required.**

---

## 🚀 Quick Start

### **One URL for Everything:**

```
http://YOUR-IP:8000/
```

That's it! This gives you:
- ✅ Login
- ✅ Mobile home dashboard
- ✅ Live camera streaming with AI
- ✅ Incident monitoring
- ✅ Reports & analytics
- ✅ Vehicle search
- ✅ System settings (admin only)

---

## 📱 Step-by-Step First Use

1. **Open Safari** on your iPhone
2. **Go to:** `http://YOUR-IP:8000/`
3. **Login** with credentials shown on page
4. **See mobile home** with all features as cards
5. **Tap any card** to access that feature!

---

## 🏠 Mobile Home Dashboard

After login, you'll see a beautiful card-based dashboard:

### **Featured:**
- 📱 **Live Camera Stream** - Point phone at anything, get instant AI feedback

### **Operations:**
- 🚨 **Live Incidents** - Monitor and respond to alerts
- 📋 **Reports** - Generate shift reports
- 📈 **Metrics Dashboard** - View KPIs
- 🚗 **Vehicle Search** - Search by make/model/color

### **Administration** (admin only):
- ⚙️ **System Settings** - Configure everything
- 📚 **API Documentation** - Interactive API docs

---

## 📸 Live Camera Stream

### **How to Use:**

1. From mobile home, tap **"Live Camera Stream"**
2. **Allow camera access** when prompted
3. **Point at something**
4. Watch real-time AI descriptions appear at bottom of screen!

### **What It Detects:**

- **People:** "Person walking through doorway"
- **Animals:** "A cat sitting on a windowsill"  
- **Vehicles:** "White sedan parked in driveway"
- **Activities:** "Two people in conversation"
- **Safety Concerns:** "⚠️ SAFETY CONCERN: Physical altercation detected"

### **Controls:**

- **🔄 Flip** - Switch between front/back camera
- **⏸ Pause** - Stop analysis (saves API costs)

---

## 👮 Features by Role

### **Operator Can:**
- ✅ Stream camera feed
- ✅ View live incidents
- ✅ Confirm/Dismiss/Close incidents
- ✅ Generate shift reports
- ✅ Search vehicles
- ✅ View metrics

### **Supervisor Can:**
- ✅ Everything operators can do, PLUS:
- ✅ Escalate incidents
- ✅ Approve dispatch decisions
- ✅ Manage hotlist plates
- ✅ Access watchlist

### **Admin Can:**
- ✅ Everything supervisors can do, PLUS:
- ✅ Change system settings
- ✅ Create/manage users
- ✅ Configure detectors
- ✅ Manage zones
- ✅ View audit logs

---

## 💡 Pro Tips

### **Add to Home Screen:**
1. In Safari, tap **Share** button
2. Tap **"Add to Home Screen"**
3. Now Alibi appears like a native app! 📱

### **For Best Results:**
- Use **back camera** for better quality
- Ensure **good lighting**
- Hold phone **steady** for accurate analysis
- **Pause** when not testing to save API costs

### **Mobile-Optimized:**
- Touch-friendly large buttons
- Swipe gestures
- Native iOS styling
- Works in portrait & landscape
- Fast loading
- Offline-capable (some features)

---

## 🌐 All URLs

| Purpose | URL |
|---------|-----|
| **Main Entry** | `http://YOUR-IP:8000/` |
| **Direct Login** | `http://YOUR-IP:8000/camera/login` |
| **Camera Stream** | `http://YOUR-IP:8000/camera/mobile-stream` |
| **Incidents** | `http://YOUR-IP:5173/incidents` |
| **Reports** | `http://YOUR-IP:5173/reports` |
| **Metrics** | `http://YOUR-IP:5173/metrics` |
| **Vehicle Search** | `http://YOUR-IP:5173/search/vehicles` |
| **Settings** | `http://YOUR-IP:5173/settings` |
| **API Docs** | `http://YOUR-IP:8000/docs` |

*(Replace `YOUR-IP` with your computer's IP address)*

---

## 📋 Real-World Use Cases

### **1. Field Officer:**
- Receives alert on phone
- Opens Alibi mobile
- Reviews incident + evidence
- Makes decision on-site
- Dismisses or escalates immediately

### **2. Supervisor on Patrol:**
- Gets escalation notification
- Reviews incident from patrol vehicle
- Approves dispatch authorization
- All without returning to office

### **3. Training & Demonstrations:**
- Show police what system detects
- Point phone at different scenarios
- Get live AI feedback
- Demonstrates system accuracy

### **4. Command Center Mobile:**
- Monitor all active incidents
- Generate and review reports
- Check performance metrics
- No desktop needed

---

## 🔐 Security

- ✅ **JWT Authentication** - Secure token-based auth
- ✅ **Role-Based Access** - See only what your role allows
- ✅ **Auto-Logout** - Expires after 30 minutes inactivity
- ✅ **Audit Logging** - All actions logged
- ✅ **Secure Passwords** - Strong requirements enforced
- ✅ **HTTPS Ready** - Use reverse proxy in production

---

## 🎯 Key Features

### **Live AI Camera:**
- Stream from ANY phone camera
- Real-time natural language descriptions
- Object detection (people, vehicles, animals)
- Activity recognition
- Safety concern detection
- Evidence capture (snapshots + clips)

### **Incident Management:**
- Real-time incident stream
- View evidence (photos, videos)
- Make decisions (Confirm/Dismiss/Escalate)
- Require supervisor approval
- Complete audit trail

### **Reports & Analytics:**
- Generate shift reports (8h/24h/custom)
- View KPIs and metrics
- Alert fatigue tracking
- Top cameras/zones analysis
- Export capabilities

### **Vehicle Intelligence:**
- Search by make/model/color
- License plate hotlist
- Plate-vehicle mismatch detection
- Complete sighting history
- Evidence for each sighting

---

## 🚨 Troubleshooting

### **Can't connect from iPhone:**
- ✓ iPhone on same WiFi as computer?
- ✓ Using correct IP address?
- ✓ Both API (port 8000) and Console (port 5173) running?
- ✓ Firewall allowing connections?

### **Camera not working:**
- ✓ Allowed camera access in Safari?
- ✓ Try Settings → Safari → Camera → Allow
- ✓ Use Safari (not Chrome) for best compatibility

### **"Please login first" error:**
- ✓ Go to main URL first: `http://YOUR-IP:8000/`
- ✓ Login on that page
- ✓ Then navigate to other features

### **Features not showing:**
- ✓ Logged in as correct role?
- ✓ Operators can't see admin features
- ✓ Check user role in dashboard

---

## 📞 Support

**Documentation:**
- `START_ALIBI.md` - Complete startup guide
- `MOBILE_CAMERA_GUIDE.md` - Camera streaming details
- `DEPLOYMENT_SECURITY_GUIDE.md` - Production deployment
- `SECURITY_HARDENING_COMPLETE.md` - Security audit

**Interactive Docs:**
- http://YOUR-IP:8000/docs - Full API documentation

---

## ✨ Summary

**Alibi is now a complete mobile-first police oversight system.**

✅ **No Desktop Required** - Everything works from iPhone  
✅ **Real-Time AI** - Point camera, get instant feedback  
✅ **Full Featured** - All admin/supervisor functions  
✅ **Production Ready** - Secure, audited, hardened  
✅ **Role-Based** - Operators, Supervisors, Admins  
✅ **Evidence Tracking** - Complete audit trail  
✅ **Mobile Optimized** - Touch-friendly, fast  

**Perfect for the Namibia Police pilot deployment!** 🇳🇦

---

**Get started now:** Open Safari → `http://YOUR-IP:8000/` → Login → Explore! 🚀
