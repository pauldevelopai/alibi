# 🚀 Real Training Data Collection System

**Automatically collect and process training data from Hugging Face to improve your AI vision model!**

## 📋 Overview

This system automatically:
1. **Downloads** security-relevant images from Hugging Face datasets
2. **Filters** them for security use cases (people, vehicles, crowds, suspicious objects)
3. **Processes** them into OpenAI fine-tuning format
4. **Prepares** them for GPT-4 Vision fine-tuning

## 🎯 Data Sources

### 1. COCO Dataset (Common Objects in Context)
- **Size**: 330,000 images
- **Categories**: 80 object types
- **Use**: Person detection, vehicle recognition, object identification
- **Quality**: High-quality annotations

### 2. Open Images Dataset
- **Size**: 9 million images
- **Categories**: 600+ object types
- **Use**: Diverse real-world scenarios
- **Quality**: Professional annotations

### 3. Security-Focused Datasets
- **Crowd Counting**: Crowd behavior and density
- **Activity Recognition**: Actions and behaviors
- **Anomaly Detection**: Unusual patterns

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install datasets pillow huggingface-hub
```

Or use the auto-installer in the Training Data page!

### Step 2: Start Collection

**Via Web UI:**
1. Go to: `https://McNallyMac.local:8000/camera/training`
2. Login as admin
3. Scroll to "Admin Controls"
4. Click "🚀 Start Data Collection"

**Via API:**
```bash
curl -X POST https://McNallyMac.local:8000/data-collection/collect-from-huggingface \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"num_coco": 100, "num_open_images": 50, "num_security": 50}'
```

**Via Python:**
```python
from alibi.data_collection import collect_training_data
import asyncio

# Collect data
result = asyncio.run(collect_training_data(
    num_coco=100,
    num_open_images=50,
    num_security=50
))

print(f"Collected {result['total_collected']} examples!")
```

### Step 3: Check Status

```bash
curl https://McNallyMac.local:8000/data-collection/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 4: Convert to OpenAI Format

```bash
curl -X POST https://McNallyMac.local:8000/data-collection/convert-to-openai-format \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 5: Download Dataset

```bash
curl https://McNallyMac.local:8000/data-collection/download-training-dataset?format=openai \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o training_dataset.jsonl
```

## 📊 What Gets Collected

### Security-Relevant Categories:

1. **Person Detection** (`person`)
   - Single person
   - Multiple people
   - Actions and poses
   - **Use**: Watchlist matching, person tracking

2. **Vehicle Recognition** (`vehicle`)
   - Cars, trucks, vans
   - Motorcycles, buses
   - Colors, types, positions
   - **Use**: Parking monitoring, traffic analysis

3. **Suspicious Objects** (`suspicious_object`)
   - Weapons, tools
   - Unusual items
   - Security concerns
   - **Use**: Threat detection

4. **Crowd Monitoring** (`crowd`)
   - Crowd density
   - Behavior patterns
   - Safety concerns
   - **Use**: Event monitoring, panic detection

5. **Activity Recognition** (`activity`)
   - Running, fighting
   - Climbing, breaking
   - Unusual behaviors
   - **Use**: Anomaly detection

## 📁 Output Structure

```
alibi/data/hf_training_data/
├── collected_examples.jsonl       # Raw collected data
├── openai_training_dataset.jsonl  # OpenAI fine-tuning format
└── images/
    ├── coco_abc123.jpg
    ├── open_images_def456.jpg
    └── crowd_ghi789.jpg
```

## 🔧 OpenAI Fine-Tuning Format

Each example is formatted for GPT-4 Vision fine-tuning:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a security camera AI assistant..."
    },
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Analyze this security camera image"},
        {"type": "image_url", "image_url": {"url": "file://path/to/image.jpg"}}
      ]
    },
    {
      "role": "assistant",
      "content": "One person visible in frame. Vehicle detected: car. Security Relevance: Useful for person detection..."
    }
  ]
}
```

## 🎓 Fine-Tuning with OpenAI

### Step 1: Upload Dataset

```python
from openai import OpenAI
client = OpenAI()

# Upload training file
with open("training_dataset.jsonl", "rb") as f:
    response = client.files.create(
        file=f,
        purpose="fine-tune"
    )

file_id = response.id
print(f"File ID: {file_id}")
```

### Step 2: Create Fine-Tuning Job

```python
job = client.fine_tuning.jobs.create(
    training_file=file_id,
    model="gpt-4-vision-preview",  # Or latest model
    suffix="alibi-security-v1"
)

print(f"Job ID: {job.id}")
```

### Step 3: Monitor Progress

```python
# Check status
job_status = client.fine_tuning.jobs.retrieve(job.id)
print(f"Status: {job_status.status}")

# List events
events = client.fine_tuning.jobs.list_events(job.id, limit=10)
for event in events.data:
    print(event.message)
```

### Step 4: Use Fine-Tuned Model

```python
response = client.chat.completions.create(
    model="gpt-4-vision-ft:alibi-security-v1",  # Your fine-tuned model
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this security camera image"},
                {"type": "image_url", "image_url": {"url": "your_image_url"}}
            ]
        }
    ]
)

print(response.choices[0].message.content)
```

## 📈 Expected Improvements

With 200+ training examples, you should see:

✅ **Better Object Recognition**
- Improved detection of people, vehicles
- Better classification accuracy
- Fewer false positives

✅ **Security-Focused Language**
- Uses appropriate security terminology
- Consistent description format
- Action-oriented observations

✅ **South African Context** (if you add SA-specific data)
- Recognition of local vehicle types (minibus taxis)
- Understanding of local context
- Better place/landmark recognition

✅ **Confidence & Clarity**
- More confident assessments
- Clearer descriptions
- Better security relevance scoring

## 🔄 Continuous Improvement

### Regular Collection Schedule

Run collection monthly to keep improving:

```python
# Cron job example (monthly)
0 0 1 * * python -m alibi.data_collection.huggingface_collector
```

### Feedback Loop

1. Use the **24/7 Collection Agent** to capture real security events
2. Combine with Hugging Face data
3. Fine-tune quarterly
4. Deploy new version
5. Repeat!

## 💡 Pro Tips

1. **Start Small**: Collect 100-200 examples first, test fine-tuning
2. **Mix Data**: Combine Hugging Face data with your real footage
3. **Quality > Quantity**: 200 good examples > 1000 mediocre ones
4. **Regular Updates**: Fine-tune every 3-6 months as you collect more data
5. **Track Versions**: Use the fine-tuning history feature to track improvements

## 🚨 Important Notes

### Licensing
- COCO: CC BY 4.0 (commercial use OK)
- Open Images: CC BY 4.0 (commercial use OK)
- Check specific dataset licenses before commercial deployment

### Storage
- Each image: ~100-500 KB
- 200 images: ~50-100 MB
- Plan accordingly for large collections

### API Costs
- Fine-tuning costs vary by model
- Check OpenAI pricing: https://openai.com/pricing
- Estimated: $2-10 per 200 examples (as of 2026)

### Time Requirements
- Collection: 10-30 minutes per 200 examples
- Conversion: 1-5 minutes
- Fine-tuning: 1-4 hours (OpenAI side)
- Total: ~2-5 hours start to finish

## 📞 Troubleshooting

### "datasets not installed"
```bash
pip install datasets pillow huggingface-hub
```

### "Out of memory"
- Reduce `num_coco`, `num_open_images`, `num_security`
- Collect in batches (e.g., 50 at a time)

### "Collection stuck"
- Check `/tmp/alibi_api.log` for errors
- Restart API: `./stop_alibi.sh && ./start_alibi.sh`

### "Images not downloading"
- Check internet connection
- Try VPN if Hugging Face is blocked
- Use smaller batch sizes

## 🎯 Next Steps

1. ✅ Collect 200 examples from Hugging Face
2. ✅ Combine with your real camera data
3. ✅ Convert to OpenAI format
4. ✅ Upload and fine-tune
5. ✅ Deploy and test
6. ✅ Collect feedback
7. 🔄 Repeat!

---

**Questions?** Check the Training Data page or API docs at `/docs`
