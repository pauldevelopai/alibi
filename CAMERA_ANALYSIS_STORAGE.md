# 📊 Camera Analysis Storage & Insights

**All camera analysis results are now automatically stored for historical review, pattern analysis, and reporting.**

---

## ✅ What Gets Stored

Every time the camera analyzes a frame, this data is saved:

- **Description**: Natural language description of what AI sees
- **Detected Objects**: List of objects (person, car, cat, dog, etc.)
- **Detected Activities**: List of activities (walking, fighting, entering, etc.)
- **Safety Concern**: Boolean flag if potential safety issue detected
- **Confidence Score**: AI confidence level (0.0 to 1.0)
- **User**: Who requested the analysis
- **Timestamp**: When analysis occurred
- **Camera Source**: Which camera/device (webcam, mobile, IP cam, etc.)
- **Analysis Method**: Which AI was used (OpenAI Vision, Google Vision, Basic CV)
- **Metadata**: Additional context

**Storage Location**: `alibi/data/camera_analysis.jsonl`

**Format**: JSONL (JSON Lines) - one JSON object per line, append-only for audit trail

---

## 📡 API Endpoints

### Get Recent Analyses

```
GET /camera/analysis/recent?hours=24&limit=100
```

**Parameters**:
- `hours` - How many hours back to look (default: 24)
- `limit` - Maximum number of records (default: 100)

**Returns**: List of camera analysis records

**Example**:
```bash
curl http://localhost:8000/camera/analysis/recent?hours=8
```

---

### Get Statistics

```
GET /camera/analysis/statistics?hours=24
```

**Parameters**:
- `hours` - Time window for statistics (default: 24)

**Returns**:
```json
{
  "total_analyses": 450,
  "safety_concerns": 12,
  "most_common_objects": [
    {"object": "person", "count": 234},
    {"object": "car", "count": 89},
    {"object": "cat", "count": 45}
  ],
  "most_common_activities": [
    {"activity": "walking", "count": 156},
    {"activity": "standing", "count": 78}
  ],
  "analysis_methods": {
    "openai_vision": 445,
    "basic_cv": 5
  },
  "unique_users": 3,
  "unique_cameras": 2
}
```

**Use Cases**:
- Daily/weekly summary reports
- Pattern detection
- System performance monitoring
- Operator activity tracking

---

### Get Safety Concerns

```
GET /camera/analysis/safety-concerns?hours=24
```

**Parameters**:
- `hours` - Time window (default: 24)

**Returns**: Only analyses where `safety_concern=True`

**Example**:
```bash
curl http://localhost:8000/camera/analysis/safety-concerns?hours=48
```

---

## 💡 Use Cases

### 1. **Daily Summary Reports**

Generate a report of what cameras detected today:

```python
from alibi.camera_analysis_store import get_camera_analysis_store
from datetime import datetime, timedelta

store = get_camera_analysis_store()
start = datetime.utcnow() - timedelta(days=1)
end = datetime.utcnow()

report = store.export_for_report(start, end)
print(report)  # Markdown formatted report
```

### 2. **Pattern Detection**

Find unusual patterns:

```python
stats = store.get_statistics(hours=168)  # Last week

# Check for spikes in safety concerns
if stats['safety_concerns'] > threshold:
    alert_supervisor()

# Check for unusual objects
unusual_objects = ['weapon', 'fire', 'smoke']
for obj in stats['most_common_objects']:
    if obj['object'] in unusual_objects:
        create_incident()
```

### 3. **Training Data**

Export analyses for training or validation:

```python
analyses = store.get_recent(limit=1000, hours=720)  # Last month
training_data = [
    {
        'image': a.snapshot_path,
        'label': a.description,
        'objects': a.detected_objects
    }
    for a in analyses
]
```

### 4. **Audit Trail**

Review what operators were monitoring:

```python
analyses = store.get_by_date_range(start, end)
operator_activity = {}

for analysis in analyses:
    user = analysis.user
    operator_activity[user] = operator_activity.get(user, 0) + 1

print(f"Operator activity: {operator_activity}")
```

---

## 📊 Integration with Reports

Camera analysis data is automatically included in shift reports:

```
POST /reports/shift
{
  "range": "8h",
  "include_sections": ["camera_analysis", "incidents", "decisions"]
}
```

The report will include:
- Summary of camera activity
- Safety concerns detected
- Most common objects/activities
- Timestamps of key events

---

## 🔍 Querying Data

### Python API

```python
from alibi.camera_analysis_store import get_camera_analysis_store
from datetime import datetime, timedelta

store = get_camera_analysis_store()

# Get last 24 hours
recent = store.get_recent(hours=24)

# Get specific date range
start = datetime(2026, 1, 19, 8, 0)
end = datetime(2026, 1, 19, 16, 0)
shift_data = store.get_by_date_range(start, end)

# Get statistics
stats = store.get_statistics(hours=24)

# Get only safety concerns
concerns = store.get_safety_concerns(hours=24)
```

### REST API

```bash
# Get recent analyses
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/camera/analysis/recent?hours=24

# Get statistics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/camera/analysis/statistics?hours=168

# Get safety concerns
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/camera/analysis/safety-concerns?hours=24
```

---

## 🎯 Dashboard Ideas

### Real-Time Monitoring

- Live feed of latest analyses
- Safety concern alerts
- Object/activity counters
- Operator activity tracker

### Historical Analysis

- Graphs of detected objects over time
- Heatmap of safety concerns by hour/day
- Comparison across cameras/locations
- Trend detection

### Reporting

- Daily summary emails
- Weekly pattern reports
- Monthly statistics
- Annual audit reports

---

## 🔐 Security & Privacy

- ✅ **Authentication Required**: All endpoints require valid JWT token
- ✅ **Role-Based Access**: Operators, supervisors, admins can all access
- ✅ **Audit Trail**: Append-only storage preserves complete history
- ✅ **Data Retention**: Configure retention policy in production
- ✅ **Privacy**: No images stored by default (only descriptions)

**Optional**: Enable snapshot storage:
```python
camera_analysis = CameraAnalysis(
    ...
    snapshot_path="/evidence/snapshots/abc123.jpg"  # Store image path
)
```

---

## 📁 File Format

**Example JSONL entry**:

```json
{
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-19T10:15:30.123456",
  "user": "operator1",
  "camera_source": "webcam_upload",
  "description": "Person walking through hallway",
  "confidence": 0.85,
  "detected_objects": ["person", "door"],
  "detected_activities": ["walking"],
  "safety_concern": false,
  "method": "openai_vision",
  "metadata": {
    "prompt": "describe_scene",
    "user_role": "operator",
    "source": "mobile_camera_api"
  },
  "snapshot_path": null
}
```

---

## 🚀 Future Enhancements

Possible additions:

- **Incident Correlation**: Link analyses to incidents
- **Alert Rules**: Trigger alerts on specific patterns
- **ML Training**: Use data to train custom models
- **Advanced Analytics**: Predictive analysis, anomaly detection
- **Export Formats**: CSV, Excel, PDF reports
- **Data Visualization**: Built-in charts and graphs
- **Real-Time Dashboard**: Live monitoring interface

---

## ✅ Summary

✨ **Camera analysis storage is production-ready!**

- All analyses automatically saved
- Rich API for querying and insights
- Integrated with reporting system
- Audit trail for accountability
- Pattern detection capabilities
- Ready for Namibia pilot deployment

**Access it now**: `http://localhost:8000/docs` → Camera Analysis endpoints
