# 🇿🇦 Alibi Vision Improvement System

**Data Collection & Fine-Tuning for South African Context**

---

## 🎯 Overview

The Vision Improvement System continuously collects user feedback to make Alibi Vision **infinitely better** for South African and Namibian contexts.

**Key Innovation**: Every time a user corrects the AI or adds context, that data is used to fine-tune the model for regional accuracy.

---

## 🌍 Why This Matters

OpenAI's base models are trained on global data, which means they may miss:

❌ **Regional Vehicles**: Minibus taxis (Toyota Quantum), bakkies (pickups)  
❌ **Local Architecture**: Townships, RDP houses, informal settlements  
❌ **Cultural Context**: Braai, spaza shops, shebeens, taxi ranks  
❌ **SA Wildlife**: Oryx, springbok, kudu (Namibia)  
❌ **Regional Terms**: South African English, Afrikaans terminology  
❌ **Security Features**: Electric fences, armed response, burglar bars  

**Your feedback teaches the AI about Southern Africa!**

---

## 🔄 How It Works

### 1. AI Analyzes Camera Footage
```
Camera → AI Vision → "Person near building"
```

### 2. User Provides Feedback
```
User corrects → "Minibus taxi loading at taxi rank in township"
User adds context → "This is a typical SA scene with informal traders"
```

### 3. Data is Collected
```
- Original AI description
- Corrected description
- SA-specific context
- Accuracy rating
- What AI missed
```

###  4. Model is Improved
```
100+ corrections → Fine-tuning dataset → OpenAI fine-tuning → Better model
```

### 5. Deploy Improved Model
```
Fine-tuned model understands SA context → More accurate descriptions!
```

---

## 📱 For Users: How to Provide Feedback

### Step 1: Use Camera
```
https://McNallyMac.local:8000/camera/mobile-stream
```
Point camera at various South African scenes

### Step 2: Go to Camera History
```
https://McNallyMac.local:8000/camera/history
```
Browse your captured snapshots

### Step 3: Click Any Snapshot
Full details modal appears

### Step 4: Tap "Provide Feedback" Button
Feedback form opens

### Step 5: Fill Out Feedback
- **Corrected Description**: What AI should have said
- **SA Context Notes**: Regional context AI missed
- **What AI Missed**: Specific objects/activities
- **Accuracy Rating**: 1-5 stars

### Step 6: Submit
Your feedback is saved and will improve the model!

---

## 📊 What Data is Collected

### Stored for Each Feedback:
- ✅ Original AI description
- ✅ User's corrected description
- ✅ South African context notes
- ✅ What AI missed
- ✅ Accuracy rating (1-5 stars)
- ✅ User who provided feedback
- ✅ Timestamp
- ✅ User role

### Privacy:
- ❌ **No images stored** in feedback (only hashes for linking)
- ❌ **No personal info** beyond username
- ✅ **Anonymous aggregation** for fine-tuning
- ✅ **Used only for model improvement**

---

## 🇿🇦 South African Context Database

### Pre-loaded Regional Knowledge:

**Vehicles:**
- Minibus taxis (Toyota Quantum, 14-16 seaters)
- Bakkies (pickup trucks)
- Delivery vehicles (Takealot, Mr D Food, etc.)

**Locations:**
- Townships
- Informal settlements  
- RDP houses
- Security estates
- Boom gates

**Objects:**
- Braai (BBQ)
- Spaza shops
- Shebeens (informal taverns)
- Prepaid electricity boxes
- Burglar bars
- Electric fences

**Activities:**
- Queueing (at taxi ranks, shops, ATMs)
- Street vendors/informal traders
- Taxi rank loading
- Load shedding effects
- Braaiing

**Security Features:**
- Electric fences
- Armed response vehicles (ADT, Fidelity)
- Boom gates
- Burglar bars on windows

**Namibian Context:**
- Wildlife: Oryx, springbok, kudu, elephants
- Desert landscapes
- Arid environments
- Unique architecture

---

## 👥 For Admins: Managing Data Collection

### View Statistics

```
GET /camera/improvement-stats
```

Returns:
```json
{
  "stats": {
    "total_feedback": 156,
    "corrections": 120,
    "confirmations": 36,
    "avg_rating": 3.8,
    "improvement_rate": 76.9,
    "sa_context_notes": 89
  },
  "vocabulary": {
    "objects": ["minibus_taxi", "bakkie", "spaza_shop", ...],
    "activities": ["queueing", "braaiing", ...],
    "total_unique_terms": 45
  },
  "fine_tuning_readiness": true,
  "recommended_examples": 0
}
```

### Generate Improvement Report

```
GET /camera/improvement-report
```

Returns markdown report with:
- Total feedback collected
- User corrections vs confirmations
- Average accuracy rating
- SA-specific vocabulary discovered
- Recommendations for next steps

### Prepare Fine-Tuning Dataset

```
POST /camera/prepare-fine-tuning
```

Creates:
```
alibi/data/fine_tuning_dataset.jsonl
```

Format ready for OpenAI fine-tuning API.

---

## 🚀 Fine-Tuning Process

### Requirements:
- **Minimum**: 100 high-quality corrections
- **Recommended**: 500+ diverse examples
- **Best**: 1000+ covering all SA contexts

### Steps:

#### 1. Collect Data
```bash
# Users provide feedback through Camera History
# System collects corrections automatically
```

#### 2. Check Readiness
```bash
curl https://McNallyMac.local:8000/camera/improvement-stats
# Check: "fine_tuning_readiness": true
```

#### 3. Prepare Dataset
```bash
curl -X POST https://McNallyMac.local:8000/camera/prepare-fine-tuning \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Output: `alibi/data/fine_tuning_dataset.jsonl`

#### 4. Upload to OpenAI
```bash
# Install OpenAI CLI
pip install openai

# Upload training file
openai api files.create \
  -f alibi/data/fine_tuning_dataset.jsonl \
  -p fine-tune

# Note the file ID (e.g., file-abc123)
```

#### 5. Start Fine-Tuning Job
```bash
openai api fine_tuning.jobs.create \
  -t file-abc123 \
  -m gpt-4o-mini \
  --suffix "alibi-sa-context"
```

#### 6. Monitor Progress
```bash
openai api fine_tuning.jobs.retrieve -i ftjob-xyz789
```

#### 7. Test Fine-Tuned Model
```bash
# Update scene_analyzer.py to use fine-tuned model
model="ft:gpt-4o-mini:org:alibi-sa-context:abc123"
```

#### 8. Deploy
```bash
# Update production config
# Monitor improvement metrics
```

---

## 📈 Expected Improvements

### After 100 Corrections:
- ✅ Basic SA vehicle recognition
- ✅ Common terms (braai, bakkie, etc.)
- ✅ Township/informal settlement awareness

### After 500 Corrections:
- ✅ Nuanced SA context understanding
- ✅ Regional activity recognition
- ✅ Cultural sensitivity
- ✅ Accurate security feature detection

### After 1000+ Corrections:
- ✅ Expert-level SA context
- ✅ Namibian wildlife recognition
- ✅ Load shedding impact detection
- ✅ Multilingual context hints

---

## 💡 Tips for High-Quality Feedback

### DO:
✅ Be specific: "Minibus taxi" not just "vehicle"  
✅ Add regional context: "Township scene with RDP houses"  
✅ Mention what AI missed: "Didn't see spaza shop in background"  
✅ Use SA terminology: "Bakkie" not "truck", "Braai" not "BBQ"  
✅ Note cultural elements: "Informal traders at intersection"  

### DON'T:
❌ Be vague: "This is wrong"  
❌ Use judgment: "Poor area" → Use "Township" or "Informal settlement"  
❌ Skip context: Just correcting without explaining why  
❌ Use slang: Use respectful, factual terms  

---

## 🔒 Privacy & Ethics

### Data Collection Ethics:
- ✅ **User consent**: Feedback is voluntary
- ✅ **Transparent use**: Only for model improvement
- ✅ **No PII**: No personal info beyond username
- ✅ **Secure storage**: Append-only audit trail
- ✅ **Respectful terminology**: Cultural sensitivity built-in

### Image Privacy:
- ✅ **No images in feedback**: Only snapshot hash for linking
- ✅ **Snapshots auto-deleted**: 7-day retention
- ✅ **No facial recognition**: General scene description only
- ✅ **Local processing**: Data doesn't leave server

---

## 📊 Monitoring Progress

### Dashboard (Admin Only)

```
https://McNallyMac.local:8000/camera/improvement-stats
```

Shows:
- Total feedback collected
- Improvement rate (% needing correction)
- Average accuracy rating
- SA vocabulary growth
- Fine-tuning readiness

### Weekly Reports

Generate weekly report:
```bash
curl https://McNallyMac.local:8000/camera/improvement-report \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Alerts

Set up alerts for:
- Feedback milestone reached (100, 500, 1000)
- Low accuracy ratings (< 3.0 average)
- High correction rate (> 80%)
- Fine-tuning dataset ready

---

## 🎯 Success Metrics

### Model Accuracy:
- **Baseline**: 60-70% accuracy for SA context (base model)
- **Target after 100**: 75-80% accuracy
- **Target after 500**: 85-90% accuracy
- **Target after 1000**: 90-95% accuracy

### User Satisfaction:
- **Average rating**: Target 4.0+ stars
- **Correction rate**: Target < 30% need correction
- **SA context coverage**: 100+ unique regional terms

### Business Impact:
- Fewer false alarms
- Better incident descriptions
- Improved officer confidence in system
- Reduced manual review time

---

## 🚀 Roadmap

### Phase 1: Data Collection (Weeks 1-4)
- ✅ Feedback system deployed
- ✅ SA context database loaded
- 🎯 Collect 100+ corrections
- 🎯 Identify common gaps

### Phase 2: First Fine-Tuning (Week 5)
- 🎯 Prepare dataset
- 🎯 Submit to OpenAI
- 🎯 Test fine-tuned model
- 🎯 Compare with baseline

### Phase 3: Iteration (Weeks 6-12)
- 🎯 Collect 500+ corrections
- 🎯 Second fine-tuning round
- 🎯 A/B testing
- 🎯 Production deployment

### Phase 4: Continuous Improvement (Ongoing)
- 🎯 Monthly fine-tuning updates
- 🎯 Expand to new contexts
- 🎯 Multi-language support
- 🎯 Custom model training

---

## 📚 Resources

### API Endpoints:
- `POST /camera/feedback` - Submit feedback
- `GET /camera/improvement-stats` - View statistics
- `GET /camera/improvement-report` - Generate report
- `POST /camera/prepare-fine-tuning` - Create dataset

### Files:
- `alibi/data/vision_feedback.jsonl` - All feedback
- `alibi/data/fine_tuning_dataset.jsonl` - Training dataset
- `alibi/vision/south_african_context.py` - SA knowledge base
- `alibi/vision/data_collection.py` - Collection system

### Documentation:
- OpenAI Fine-Tuning: https://platform.openai.com/docs/guides/fine-tuning
- Dataset Best Practices: https://platform.openai.com/docs/guides/fine-tuning/preparing-your-dataset

---

## ✅ Summary

**The Vision Improvement System makes Alibi Vision infinitely better for South African context through continuous user feedback and fine-tuning.**

**Key Features**:
- 📸 Easy feedback on every snapshot
- 🇿🇦 Pre-loaded SA context database  
- 🔄 Continuous improvement cycle
- 🚀 OpenAI fine-tuning ready
- 🔒 Privacy-preserving
- 📊 Progress tracking

**Get Started**:
1. Use camera and capture snapshots
2. Review in Camera History
3. Provide feedback on AI descriptions
4. System automatically improves!

**Every correction you provide makes Alibi Vision smarter for South Africa!** 🇿🇦✨
