# 📱 Alibi Mobile Camera Guide

**Stream ANY Camera to Alibi and Get Real-Time Feedback**

---

## 🎯 What This Does

Point **ANY camera** (iPhone, Android, webcam, etc.) at something and Alibi will tell you **in plain English** what it sees:

- "A cat sitting on a windowsill" ✅
- "Two men fighting near a parked car" ⚠️
- "Empty parking lot, no activity" ✅
- "Person entering through back door" 👤

**No more technical jargon** - just natural language descriptions of what's actually happening.

---

## 🚀 Quick Start

### Option 1: Use Your Phone (Easiest)

1. **Login to Alibi** on your computer: http://localhost:5173
2. **On your phone**, open browser and go to:
   ```
   http://YOUR-COMPUTER-IP:8000/camera/mobile-stream
   ```
   (Replace YOUR-COMPUTER-IP with your computer's local IP, e.g., 192.168.1.100)

3. **Allow camera access** when prompted
4. **Point your phone at something** and watch the real-time feedback at the bottom of the screen!

### Option 2: Use Webcam

Same as above, but open `http://localhost:8000/camera/mobile-stream` on the same computer.

### Option 3: API Upload (For Developers)

```bash
# Take a photo and analyze it
curl -X POST http://localhost:8000/camera/analyze-frame \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@photo.jpg"

# Response:
{
  "description": "A cat sitting on a windowsill",
  "confidence": 0.85,
  "detected_objects": ["cat", "window"],
  "safety_concern": false,
  "timestamp": "2026-01-19T..."
}
```

---

## 🔧 Setup

### 1. Install Vision AI (Choose One)

**Option A: OpenAI Vision (Recommended - Best Quality)**

```bash
# Install OpenAI library (already in requirements.txt)
pip install openai

# Set API key
export OPENAI_API_KEY="sk-your-api-key-here"

# Or add to .env file
echo "OPENAI_API_KEY=sk-your-api-key-here" >> .env
```

**Cost**: ~$0.01 per image (very affordable for real-time analysis)

**Option B: Google Cloud Vision**

```bash
pip install google-cloud-vision

# Set up Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

**Option C: No Setup (Fallback)**

Works out of the box with basic computer vision (face detection, motion analysis). Not as detailed as OpenAI/Google but requires no API keys.

### 2. Restart API

```bash
# The mobile camera endpoints are now available!
python -m uvicorn alibi.alibi_api:app --host 0.0.0.0 --port 8000
```

---

## 📱 Mobile Streaming Interface

### Features

**Real-Time Feedback**
- Analyzes frames every 2 seconds
- Shows natural language description
- Displays detected objects
- Highlights safety concerns

**Camera Controls**
- 🔄 **Flip**: Switch between front/back camera
- ⏸ **Pause**: Stop analysis to save API calls

**Visual Indicators**
- 🟢 Green pulse: Actively analyzing
- ⚠️ Red banner: Safety concern detected
- 📊 Confidence score and method shown

### Screenshots

```
┌─────────────────────────────┐
│  [Camera Feed]              │
│                             │
│                             │
│                             │
│  🔄 Flip    ⏸ Pause        │
├─────────────────────────────┤
│ 🟢 Analyzing camera feed... │
│                             │
│ Two men arguing near        │
│ a parked car                │
│                             │
│ Objects: person, person, car│
│ Confidence: 85%             │
│ Method: openai_vision       │
│                             │
│ ⚠️ SAFETY CONCERN DETECTED  │
└─────────────────────────────┘
```

---

## 🎮 Use Cases

### 1. **Testing Detectors**

Point phone at different scenes to test:
- Cat → Should NOT trigger person detector
- Person walking → Should detect correctly
- Two people fighting → Should flag as concern
- Empty room → Should report no activity

### 2. **Training Data Collection**

- Stream real scenarios
- Get labeled descriptions
- Build training dataset
- Validate detector accuracy

### 3. **Live Demonstrations**

- Show police how system works
- Demonstrate accuracy in real-time
- Test different lighting conditions
- Validate with real-world scenarios

### 4. **Remote Monitoring**

- Use old phone as security camera
- Stream to Alibi from anywhere on network
- Get instant alerts for concerning activity
- No special camera hardware needed

---

## 🔍 API Endpoints

### `POST /camera/analyze-frame`

Upload a single frame for analysis.

**Request**:
```bash
curl -X POST http://localhost:8000/camera/analyze-frame \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@image.jpg" \
  -F "prompt=describe_scene"
```

**Prompts**:
- `describe_scene` - General description (default)
- `detect_activity` - Focus on human activity
- `count_people` - Count people in frame
- Custom prompts also supported

**Response**:
```json
{
  "description": "Two men fighting near a parked car",
  "confidence": 0.85,
  "detected_objects": ["person", "person", "car"],
  "detected_activities": ["fighting"],
  "safety_concern": true,
  "method": "openai_vision",
  "timestamp": "2026-01-19T12:00:00"
}
```

### `GET /camera/stream-feedback`

Server-Sent Events stream of recent analyses.

```javascript
const eventSource = new EventSource(
  '/camera/stream-feedback?token=YOUR_TOKEN'
);

eventSource.onmessage = (event) => {
  const analysis = JSON.parse(event.data);
  console.log(analysis.description);
};
```

### `GET /camera/mobile-stream`

Web interface for mobile streaming (HTML page).

---

## 🧠 How It Works

### Analysis Pipeline

1. **Capture Frame**
   - Mobile browser captures frame from camera
   - Resizes to optimize bandwidth
   - Converts to JPEG (80% quality)

2. **Send to API**
   - Uploads frame with JWT auth
   - API receives and validates

3. **Vision AI Analysis**
   - OpenAI Vision API analyzes image
   - Extracts objects, activities, safety concerns
   - Returns natural language description

4. **Real-Time Feedback**
   - Description shown instantly on phone
   - Objects and confidence displayed
   - Safety warnings highlighted

### Fallback Chain

```
OpenAI Vision (best) 
  ↓ if unavailable
Google Cloud Vision (good)
  ↓ if unavailable  
Basic CV (okay)
```

---

## 💡 Tips & Tricks

### Getting Best Results

**Lighting**
- Good lighting gives better descriptions
- Avoid backlit subjects
- Night mode works but with lower confidence

**Camera Position**
- Hold steady for clearer analysis
- Frame subjects fully in view
- Avoid rapid movements

**Network**
- Faster WiFi = faster feedback
- Can work on cellular but slower
- Local network recommended

### Saving API Costs

**If using OpenAI**:
- Pause analysis when not needed
- Increase analysis interval (modify JS: 2000ms → 5000ms)
- Use "low" detail mode (already set)
- Consider batch analysis vs real-time

**Cost Estimate**:
- Real-time (1 frame/2sec): ~$0.30/hour
- Moderate (1 frame/5sec): ~$0.12/hour
- Manual (on-demand only): <$0.01/session

---

## 🔐 Security

### Authentication

- All endpoints require JWT token
- Token stored in localStorage (from login)
- Mobile page checks for valid auth
- 401 errors redirect to login

### Privacy

- Frames analyzed in real-time, not stored (unless OpenAI/Google retention)
- No video recording by default
- Local analysis (basic CV) never leaves server
- Can run fully offline with basic CV mode

### Network Security

- Use HTTPS in production
- Camera stream stays on local network
- API calls authenticated
- No public internet exposure needed

---

## 🐛 Troubleshooting

### "Please login first"

**Problem**: No auth token in localStorage

**Solution**:
1. Go to http://localhost:5173
2. Login with your credentials
3. Then open mobile stream page

### "Camera access denied"

**Problem**: Browser blocked camera access

**Solution**:
1. Go to browser settings
2. Allow camera for this site
3. Reload page
4. Click "Allow" when prompted

### "Analysis failed" or slow responses

**Problem**: No vision AI configured or API quota exceeded

**Solution**:
- Check `OPENAI_API_KEY` environment variable
- Verify API quota/billing
- Fallback to basic CV mode (automatic)

### IP address not working

**Problem**: Computer IP address changed or unreachable

**Solution**:
```bash
# Find your computer's IP
# Mac/Linux:
ipconfig getifaddr en0  

# Windows:
ipconfig

# Use that IP from phone:
http://YOUR-IP:8000/camera/mobile-stream
```

---

## 📊 Integration with Detectors

The mobile camera system can be integrated with existing Alibi detectors:

### Enhancing Incidents

When detectors trigger, add natural language context:

```python
# In detector logic
from alibi.vision import SceneAnalyzer

analyzer = SceneAnalyzer()
description = analyzer.quick_describe(frame)

# Add to incident metadata
incident.metadata["scene_description"] = description
```

### Validation

Use scene understanding to validate detector results:

```python
# Validate watchlist match
if "watchlist_match" in incident:
    description = analyzer.analyze_frame(frame)
    if "person" not in description.detected_objects:
        # Flag as false positive
        incident.add_warning("No person detected in scene")
```

---

## 🎯 Examples

### Example 1: Cat on Windowsill

**Input**: Photo of cat
**Output**:
```
Description: "A cat sitting on a windowsill looking outside"
Objects: cat, window
Confidence: 92%
Safety Concern: No
```

### Example 2: Two Men Fighting

**Input**: Video frame of altercation
**Output**:
```
Description: "Two men in physical altercation near parked vehicle"
Objects: person, person, car
Activities: fighting
Confidence: 87%
Safety Concern: YES ⚠️
```

### Example 3: Empty Parking Lot

**Input**: Photo of empty lot
**Output**:
```
Description: "Empty parking lot, no vehicles or people visible"
Objects: (none)
Confidence: 78%
Safety Concern: No
```

---

## 📈 Future Enhancements

**Planned Features**:
- [ ] Video clip upload (not just single frames)
- [ ] Real-time object tracking across frames
- [ ] Automatic incident creation from mobile feed
- [ ] Multi-camera sync (point multiple phones at same scene)
- [ ] Offline mode with local AI models
- [ ] Integration with phone's existing security apps

---

## 🚀 Production Deployment

For production use with Namibia Police:

1. **HTTPS Required**: Mobile cameras must use HTTPS
2. **VPN Recommended**: For remote camera access
3. **API Key Management**: Rotate OpenAI keys regularly
4. **Cost Monitoring**: Track API usage and costs
5. **Audit Logging**: Log all camera analyses
6. **Bandwidth**: Ensure adequate network capacity

---

## 📞 Support

**Having issues?**
- Check API logs: `journalctl -u alibi-api -f`
- Verify token: Login again to refresh
- Test with webcam first before mobile
- Check firewall allows port 8000

**Questions?**
- Review DEPLOYMENT_SECURITY_GUIDE.md
- Check API docs: http://localhost:8000/docs
- Test with curl commands above

---

**Now point ANY camera at something and see what Alibi sees! 📹👀**
