# Computer Vision Tools for Alibi

**Advanced object detection and annotation tools for security applications**

---

## ✅ What's Installed

### 1. **OpenCV** ✅ WORKING
- **Version**: 4.13.0
- **Status**: ✅ Fully installed and tested
- **Capabilities**:
  - Motion detection (already in use)
  - Face detection (DNN-based)
  - Object tracking
  - Image preprocessing
  - Video analysis
  
### 2. **PyTorch** ✅ WORKING
- **Version**: 2.9.1
- **Status**: ✅ Installed
- **Use**: Required for deep learning models
- **Hardware**: CPU (Metal acceleration on macOS)

### 3. **Detectron2** ⚠️ OPTIONAL
- **Status**: Not installed (installation can be tricky on macOS)
- **Alternative**: OpenCV provides good object detection
- **When needed**: For state-of-the-art person/vehicle detection

### 4. **CVAT** (Annotation Tool)
- **Status**: Available via Docker
- **Purpose**: Annotate your camera footage to create custom training data
- **Setup**: Run `./setup_cvat.sh`

---

## 🚀 What You Can Do Now

### 1. **Enhanced Object Detection** (Using OpenCV DNN)

OpenCV can use pre-trained models for detecting:
- **People**: For suspect tracking, crowd monitoring
- **Vehicles**: Cars, trucks, motorcycles, buses
- **Faces**: For watchlist matching (already implemented)
- **Motion**: Background subtraction, optical flow

**No additional installation needed - OpenCV is already working!**

### 2. **Annotate Your Data** (Using CVAT)

CVAT lets you:
1. Upload camera snapshots from Alibi (you have 189 ready!)
2. Draw bounding boxes around people, weapons, vehicles
3. Label suspicious activities
4. Export in COCO format for training
5. Create South African-specific datasets

**Setup CVAT**:
```bash
./setup_cvat.sh
```

Then access at: `http://localhost:8080`

### 3. **Train Custom Models** (Advanced)

With annotated data from CVAT, you can:
1. Fine-tune models for:
   - Minibus taxis (SA-specific)
   - Township scenarios
   - Local weapon types
   - South African police uniforms
2. Improve detection accuracy for your specific use case
3. Deploy models back into Alibi

---

## 📋 Quick Start Guide

### Step 1: Use What's Already Working

OpenCV is installed and working. You can immediately add:

**Enhanced Person Detection**:
```python
import cv2

# Load OpenCV's DNN model
net = cv2.dnn.readNetFromCaffe(
    'deploy.prototxt',
    'mobilenet_ssd.caffemodel'
)

# Detect people in camera frames
blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)
net.setInput(blob)
detections = net.forward()
```

**Vehicle Detection**:
- Use YOLO models (OpenCV DNN supports them)
- Detect cars, trucks, motorcycles, buses
- Track vehicles across frames

### Step 2: Annotate Your Camera Footage

1. **Setup CVAT**:
   ```bash
   ./setup_cvat.sh
   ```

2. **Upload snapshots**:
   - Your camera snapshots are at: `alibi/data/camera_snapshots/`
   - You have 189 snapshots ready to annotate!
   - Upload them to CVAT

3. **Create a task**:
   - Task name: "South African Security Scenarios"
   - Labels: person, weapon, vehicle, suspicious_object, crowd

4. **Annotate**:
   - Draw boxes around people, weapons, vehicles
   - Label activities (loitering, aggression, etc.)
   - Export in COCO format

5. **Use for training**:
   - Your annotations become training data
   - Fine-tune OpenAI Vision or other models
   - Improve Alibi's detection accuracy

### Step 3: Integrate with Alibi's Training System

Your annotated data feeds into:
1. **OpenAI Vision fine-tuning** (already set up)
2. **Custom detector training** (for local models)
3. **Feedback loop** (improve over time)

---

## 🎯 Recommended Workflow

### For Immediate Value:

1. ✅ **Use OpenCV DNN** (already installed)
   - Add person/vehicle detection to existing detectors
   - Use pre-trained models (no training needed)
   - Fast, runs on CPU

2. ✅ **Collect annotations with CVAT**
   - Annotate 100-500 snapshots
   - Focus on South African scenarios
   - Create custom training dataset

3. ✅ **Fine-tune OpenAI Vision** (already implemented)
   - Use CVAT annotations + Hugging Face data
   - Improve scene understanding
   - Better text descriptions

### For Advanced Detection:

4. ⚠️ **Try Detectron2** (optional, may fail on macOS)
   ```bash
   ./install_cv_tools.sh
   ```
   - State-of-the-art detection
   - Better accuracy than OpenCV DNN
   - Requires more resources

---

## 📊 Your Current Status

```
✅ OpenCV: INSTALLED & WORKING
   - 189 camera snapshots available
   - Can read/process images (1280x720)
   - Ready for enhanced detection

✅ PyTorch: INSTALLED
   - Version 2.9.1
   - CPU acceleration ready
   - Foundation for deep learning

⚠️  Detectron2: NOT INSTALLED (optional)
   - Can be added later if needed
   - OpenCV DNN is sufficient for most use cases

📦 CVAT: AVAILABLE
   - Run: ./setup_cvat.sh
   - Annotate your 189 snapshots
   - Create custom training data
```

---

## 💡 Next Steps

### Option 1: Quick Win (10 minutes)
1. Add OpenCV DNN person/vehicle detection
2. Improve existing detectors
3. No additional installation needed

### Option 2: Build Custom Dataset (1-2 hours)
1. Run `./setup_cvat.sh`
2. Annotate 100 snapshots in CVAT
3. Export COCO format
4. Use for OpenAI Vision fine-tuning

### Option 3: Advanced AI (2-4 hours)
1. Try Detectron2 installation
2. Train custom South African models
3. Deploy back into Alibi
4. Achieve state-of-the-art detection

---

## 🛠️ Commands Reference

```bash
# Test what's working
python3 test_detectron2.py

# Setup CVAT for annotation
./setup_cvat.sh

# Install advanced detection (optional)
./install_cv_tools.sh

# Start CVAT
cd cvat && docker compose up -d

# Stop CVAT
cd cvat && docker compose down

# View CVAT logs
cd cvat && docker compose logs -f
```

---

## 📚 Resources

### OpenCV DNN Models
- **MobileNet-SSD**: Fast person detection
- **YOLO**: Vehicle detection
- **ResNet**: Face recognition
- Download from: https://github.com/opencv/opencv/wiki/TensorFlow-Object-Detection-API

### CVAT Documentation
- **Setup guide**: https://opencv.github.io/cvat/docs/
- **Annotation tips**: https://opencv.github.io/cvat/docs/manual/
- **Export formats**: COCO, YOLO, Pascal VOC

### Detectron2 (Optional)
- **Models**: https://github.com/facebookresearch/detectron2/blob/main/MODEL_ZOO.md
- **Training guide**: https://detectron2.readthedocs.io/

---

## 🎉 Summary

**You have everything you need to enhance Alibi's computer vision!**

- ✅ OpenCV is working (basic + advanced detection)
- ✅ 189 camera snapshots ready to annotate
- ✅ CVAT available for creating custom datasets
- ✅ PyTorch installed for future deep learning
- ✅ Integration with existing Alibi training system

**Start with OpenCV DNN or CVAT annotation - both are ready to use!**
