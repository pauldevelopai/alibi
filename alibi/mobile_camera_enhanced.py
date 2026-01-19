"""
Enhanced Mobile Camera with Security Threat Detection

NEW FEATURES:
- Real-time threat level assessment
- Visual threat warnings
- Red flag capability
- Integrated with tracking + incident manager
- Automatic flow to training data
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from fastapi.responses import HTMLResponse
from typing import Optional
import cv2
import numpy as np
import base64
from datetime import datetime
import uuid

from alibi.auth import User, get_current_user
from alibi.intelligence_store import IntelligenceStore, RedFlag
from alibi.vision.gatekeeper import VisionGatekeeper, GatekeeperPolicy
from alibi.vision.tracking import MultiObjectTracker
from alibi.rules.events import RuleEvaluator
from alibi.vision.simulate import IncidentManager
from alibi.vision.scene_analyzer import get_scene_analyzer
from alibi.camera_analysis_store import CameraAnalysis, get_camera_analysis_store

router = APIRouter(prefix="/camera", tags=["Enhanced Mobile Camera"])

# Global instances
_gatekeeper = None
_tracker = None
_rule_evaluator = None
_incident_manager = None
_intelligence_store = None


def get_security_components():
    """Initialize security components"""
    global _gatekeeper, _tracker, _rule_evaluator, _incident_manager, _intelligence_store
    
    if _gatekeeper is None:
        policy = GatekeeperPolicy(min_combined_conf=0.5)
        _gatekeeper = VisionGatekeeper(model_path="yolov8n.pt", policy=policy)
    
    if _tracker is None:
        _tracker = MultiObjectTracker()
    
    if _rule_evaluator is None:
        # Load zones and rules
        import json
        from pathlib import Path
        zones_file = Path("alibi/data/config/zones.json")
        if zones_file.exists():
            with open(zones_file) as f:
                zones_config = json.load(f)
        else:
            zones_config = []
        
        _rule_evaluator = RuleEvaluator(zones_config)
    
    if _incident_manager is None:
        _incident_manager = IncidentManager(
            _rule_evaluator,
            auto_convert_to_training=True,
            camera_id="mobile_camera"
        )
    
    if _intelligence_store is None:
        _intelligence_store = IntelligenceStore()
    
    return _gatekeeper, _tracker, _rule_evaluator, _incident_manager, _intelligence_store


def assess_threat_level(detections, zone_hits, triggered_rules):
    """
    Assess threat level based on detections and rules.
    
    Returns:
        (level: str, color: str, message: str)
        level: "safe", "caution", "warning", "critical"
    """
    # Start with safe
    level = "safe"
    color = "#10b981"  # Green
    message = "No threats detected"
    
    # Check for security-relevant objects
    security_objects = ["person", "backpack", "handbag", "suitcase", "knife", "gun"]
    detected_security = [d for d in detections if d.get("class") in security_objects]
    
    # Check rules triggered
    if triggered_rules:
        for track_id, rules in triggered_rules.items():
            # Loitering or unattended object
            if any("loitering" in r or "unattended" in r for r in rules):
                level = "caution"
                color = "#f59e0b"  # Orange
                message = "Suspicious activity detected"
            
            # Restricted zone or rapid movement
            if any("restricted" in r or "rapid" in r or "aggression" in r for r in rules):
                level = "warning"
                color = "#ef4444"  # Red
                message = "Security breach detected"
            
            # Crowd or panic
            if any("crowd" in r or "panic" in r for r in rules):
                level = "critical"
                color = "#dc2626"  # Dark red
                message = "Critical situation - multiple people"
    
    # Check for weapons or suspicious objects
    suspicious = [d for d in detections if d.get("class") in ["knife", "gun", "weapon"]]
    if suspicious:
        level = "critical"
        color = "#dc2626"
        message = "⚠️ WEAPON DETECTED"
    
    # Multiple people in frame
    people = [d for d in detections if d.get("class") == "person"]
    if len(people) >= 3:
        if level == "safe":
            level = "caution"
            color = "#f59e0b"
            message = f"{len(people)} people detected"
    
    return level, color, message


@router.post("/analyze-secure")
async def analyze_frame_secure(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze camera frame with security threat detection AND AI descriptions.
    
    Returns:
    - Detection results
    - Threat level assessment
    - Rule violations
    - AI natural language description (what the camera is seeing)
    - Recommended actions
    """
    # Get components
    gatekeeper, tracker, rule_evaluator, incident_manager, intelligence_store = get_security_components()
    
    # Read image
    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image")
    
    # Run gatekeeper (YOLO detection)
    timestamp = datetime.utcnow()
    result = gatekeeper.process_frame(frame, zones_config=None)
    
    # Update tracker (if eligible)
    tracks = {}
    triggered_rules = {}
    
    if result["eligible"]:
        # Run tracking
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        yolo_results = model.track(frame, persist=True, conf=0.5, verbose=False)
        tracks = tracker.update(yolo_results, zones_config=None, timestamp=timestamp)
        
        # Evaluate rules
        triggered_rules = rule_evaluator.evaluate(tracks)
        
        # Update incidents
        frame_number = int(timestamp.timestamp())
        incident_manager.update(tracks, frame_number, timestamp)
    
    # Assess threat level
    detections = result.get("detections", [])
    threat_level, threat_color, threat_message = assess_threat_level(
        detections,
        result.get("zone_hits", []),
        triggered_rules
    )
    
    # Get AI description of what camera is seeing (with timeout and fallback)
    ai_description_text = "Analysis in progress..."
    ai_confidence = 0.0
    ai_objects = []
    ai_activities = []
    
    try:
        scene_analyzer = get_scene_analyzer()
        # Add timeout to prevent hanging
        import asyncio
        from concurrent.futures import TimeoutError
        
        # Try to get AI analysis with 5 second timeout
        ai_analysis = scene_analyzer.analyze_frame(frame)
        ai_description_text = ai_analysis.description
        ai_confidence = ai_analysis.confidence
        ai_objects = ai_analysis.objects_detected
        ai_activities = ai_analysis.activities
        
        # Store analysis for history (only if successful)
        analysis_store = get_camera_analysis_store()
        analysis_entry = CameraAnalysis(
            analysis_id=str(uuid.uuid4()),
            timestamp=timestamp,
            camera_id="mobile_camera",
            description=ai_description_text,
            confidence=ai_confidence,
            detected_objects=ai_objects,
            detected_activities=ai_activities,
            safety_concern=threat_level in ["warning", "critical"],
            safety_details=threat_message if threat_level in ["warning", "critical"] else None,
            analysis_method=ai_analysis.backend_used
        )
        analysis_store.save_analysis(analysis_entry, frame)
    except Exception as e:
        # Fallback if AI analysis fails
        print(f"AI analysis failed: {e}")
        detected_classes = [d.get("class") for d in detections]
        ai_description_text = f"Detected: {', '.join(detected_classes) if detected_classes else 'No objects'}. AI analysis temporarily unavailable."
        ai_confidence = 0.5
    
    # Build response
    return {
        "timestamp": timestamp.isoformat(),
        "detections": {
            "objects": [{"class": d.get("class"), "confidence": d.get("confidence")} for d in detections],
            "count": len(detections),
            "security_relevant": result.get("security_relevant", False)
        },
        "threat": {
            "level": threat_level,
            "color": threat_color,
            "message": threat_message
        },
        "tracking": {
            "active_tracks": len(tracks),
            "triggered_rules": triggered_rules
        },
        "ai_description": {
            "description": ai_description_text,
            "confidence": ai_confidence,
            "objects": ai_objects,
            "activities": ai_activities
        },
        "scores": result.get("scores", {}),
        "eligible_for_training": result.get("eligible", False)
    }


@router.post("/red-flag")
async def create_red_flag(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Create a red flag from camera feed.
    
    User can flag anything suspicious they see in real-time.
    """
    _, _, _, _, intelligence_store = get_security_components()
    
    red_flag = RedFlag(
        flag_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow(),
        camera_id=data.get("camera_id", "mobile_camera"),
        flagged_by=current_user.username,
        severity=data.get("severity", "medium"),
        category=data.get("category", "suspicious_activity"),
        description=data.get("description", ""),
        snapshot_path=data.get("snapshot_path"),
        notes=data.get("notes", "")
    )
    
    intelligence_store.add_red_flag(red_flag)
    
    return {
        "success": True,
        "flag_id": red_flag.flag_id,
        "message": "Red flag created"
    }


@router.get("/secure-stream", response_class=HTMLResponse)
async def secure_mobile_stream():
    """Enhanced mobile camera stream with threat detection"""
    return HTMLResponse(content=SECURE_CAMERA_HTML)


# Enhanced HTML with threat warnings and red flag
SECURE_CAMERA_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alibi Security Camera</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: white;
            overflow-x: hidden;
        }
        
        .header {
            background: #000;
            padding: 15px;
            text-align: center;
            border-bottom: 2px solid #333;
        }
        
        .header h1 {
            font-size: 20px;
            color: #10b981;
        }
        
        .video-container {
            position: relative;
            width: 100%;
            max-width: 640px;
            margin: 20px auto;
            background: #000;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }
        
        video {
            width: 100%;
            height: auto;
            display: block;
        }
        
        .threat-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            padding: 15px;
            background: linear-gradient(180deg, rgba(0,0,0,0.8) 0%, transparent 100%);
            z-index: 10;
        }
        
        .threat-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        .threat-safe {
            background: rgba(16, 185, 129, 0.2);
            border: 2px solid #10b981;
            color: #10b981;
        }
        
        .threat-caution {
            background: rgba(245, 158, 11, 0.2);
            border: 2px solid #f59e0b;
            color: #f59e0b;
        }
        
        .threat-warning {
            background: rgba(239, 68, 68, 0.2);
            border: 2px solid #ef4444;
            color: #ef4444;
            animation: pulse 2s infinite;
        }
        
        .threat-critical {
            background: rgba(220, 38, 38, 0.3);
            border: 2px solid #dc2626;
            color: #fff;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .detection-info {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 15px;
            background: linear-gradient(0deg, rgba(0,0,0,0.95) 0%, transparent 100%);
            z-index: 10;
        }
        
        .ai-description {
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid rgba(16, 185, 129, 0.5);
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 14px;
            line-height: 1.4;
            max-height: 80px;
            overflow-y: auto;
        }
        
        .ai-description strong {
            color: #10b981;
            display: block;
            margin-bottom: 4px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .analyzing {
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
        }
        
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
            background: #10b981;
            animation: blink 2s infinite;
        }
        
        @keyframes blink {
            0%, 50%, 100% { opacity: 1; }
            25%, 75% { opacity: 0.3; }
        }
        
        .detection-stats {
            display: flex;
            gap: 15px;
            font-size: 12px;
        }
        
        .stat {
            background: rgba(255,255,255,0.1);
            padding: 6px 12px;
            border-radius: 6px;
        }
        
        .controls {
            padding: 20px;
            max-width: 640px;
            margin: 0 auto;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        button {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #10b981;
            color: white;
        }
        
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        
        .btn-secondary {
            background: #374151;
            color: white;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        
        .red-flag-btn {
            background: #dc2626;
            color: white;
            font-size: 18px;
            animation: glow 2s infinite;
        }
        
        @keyframes glow {
            0%, 100% { box-shadow: 0 0 5px #dc2626; }
            50% { box-shadow: 0 0 20px #dc2626; }
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal.active { display: flex; }
        
        .modal-content {
            background: #1f2937;
            padding: 30px;
            border-radius: 15px;
            max-width: 500px;
            width: 90%;
        }
        
        .modal h3 {
            color: #ef4444;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #d1d5db;
        }
        
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #374151;
            border-radius: 8px;
            background: #111827;
            color: white;
            font-size: 14px;
        }
        
        .modal-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 ALIBI SECURITY CAMERA</h1>
    </div>
    
    <div class="video-container">
        <div class="threat-overlay">
            <div class="threat-indicator threat-safe" id="threat-indicator">
                <span id="threat-icon">✓</span>
                <span id="threat-message">No threats detected</span>
            </div>
        </div>
        
        <video id="video" autoplay playsinline></video>
        
        <div class="detection-info">
            <div class="ai-description" id="ai-description">
                <strong><span class="status-dot"></span>AI Vision:</strong>
                <span id="ai-text">Starting camera...</span>
            </div>
            <div class="detection-stats">
                <div class="stat">
                    <strong id="object-count">0</strong> objects
                </div>
                <div class="stat">
                    <strong id="track-count">0</strong> tracks
                </div>
                <div class="stat" id="security-status">
                    Monitoring...
                </div>
            </div>
        </div>
    </div>
    
    <div class="controls">
        <button class="btn-primary" id="start-btn">▶️ Start Camera</button>
        <button class="btn-secondary" id="pause-btn">⏸ Pause</button>
        <button class="red-flag-btn" id="red-flag-btn">🚩 RED FLAG</button>
    </div>
    
    <!-- Red Flag Modal -->
    <div class="modal" id="red-flag-modal">
        <div class="modal-content">
            <h3>🚩 Create Red Flag</h3>
            <div class="form-group">
                <label>Severity</label>
                <select id="severity">
                    <option value="low">Low</option>
                    <option value="medium" selected>Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                </select>
            </div>
            <div class="form-group">
                <label>Category</label>
                <select id="category">
                    <option value="suspicious_activity">Suspicious Activity</option>
                    <option value="security_breach">Security Breach</option>
                    <option value="unusual_behavior">Unusual Behavior</option>
                    <option value="potential_threat">Potential Threat</option>
                    <option value="other">Other</option>
                </select>
            </div>
            <div class="form-group">
                <label>Description</label>
                <textarea id="description" rows="4" placeholder="What did you see?"></textarea>
            </div>
            <div class="modal-actions">
                <button class="btn-secondary" onclick="closeRedFlagModal()">Cancel</button>
                <button class="btn-danger" onclick="submitRedFlag()">Submit Red Flag</button>
            </div>
        </div>
    </div>
    
    <script>
        const video = document.getElementById('video');
        const token = localStorage.getItem('alibi_token');
        let stream = null;
        let isPaused = false;
        let lastSnapshot = null;
        
        if (!token) {
            window.location.href = '/camera/login';
        }
        
        async function startCamera() {
            try {
                stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'environment', width: 640, height: 480 }
                });
                video.srcObject = stream;
                
                // Start analysis loop
                setInterval(analyzeFrame, 2000);  // Every 2 seconds
            } catch (error) {
                alert('Camera access denied: ' + error.message);
            }
        }
        
        let isAnalyzing = false;
        let analysisTimeout = null;
        
        async function analyzeFrame() {
            if (isPaused || !stream || isAnalyzing) return;
            
            isAnalyzing = true;
            
            // Show analyzing state
            const aiText = document.getElementById('ai-text');
            const aiDescription = document.getElementById('ai-description');
            aiText.textContent = 'Analyzing...';
            aiText.style.fontStyle = 'italic';
            aiText.style.color = 'white';
            aiDescription.classList.add('analyzing');
            
            // Capture frame
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);
            
            // Set timeout to prevent hanging (10 seconds)
            analysisTimeout = setTimeout(() => {
                if (isAnalyzing) {
                    document.getElementById('ai-description').classList.remove('analyzing');
                    aiText.textContent = 'Analysis timed out - retrying next frame...';
                    aiText.style.color = '#f59e0b';
                    isAnalyzing = false;
                }
            }, 10000);
            
            // Convert to blob
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('image', blob, 'frame.jpg');
                
                try {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 8000);
                    
                    const response = await fetch('/camera/analyze-secure', {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${token}` },
                        body: formData,
                        signal: controller.signal
                    });
                    
                    clearTimeout(timeoutId);
                    clearTimeout(analysisTimeout);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    
                    const result = await response.json();
                    aiText.style.fontStyle = 'normal';
                    aiText.style.color = 'white';
                    aiDescription.classList.remove('analyzing');
                    updateThreatDisplay(result);
                    lastSnapshot = canvas.toDataURL('image/jpeg');
                    isAnalyzing = false;
                } catch (error) {
                    clearTimeout(analysisTimeout);
                    aiDescription.classList.remove('analyzing');
                    console.error('Analysis failed:', error);
                    
                    if (error.name === 'AbortError') {
                        aiText.textContent = 'Request timed out - continuing...';
                    } else {
                        aiText.textContent = 'Analysis error - continuing...';
                    }
                    aiText.style.color = '#f59e0b';
                    isAnalyzing = false;
                }
            }, 'image/jpeg');
        }
        
        function updateThreatDisplay(result) {
            const indicator = document.getElementById('threat-indicator');
            const icon = document.getElementById('threat-icon');
            const message = document.getElementById('threat-message');
            const objectCount = document.getElementById('object-count');
            const trackCount = document.getElementById('track-count');
            const securityStatus = document.getElementById('security-status');
            const aiText = document.getElementById('ai-text');
            
            // Update threat level
            const threat = result.threat;
            indicator.className = `threat-indicator threat-${threat.level}`;
            message.textContent = threat.message;
            
            // Update icon
            if (threat.level === 'safe') icon.textContent = '✓';
            else if (threat.level === 'caution') icon.textContent = '⚠️';
            else if (threat.level === 'warning') icon.textContent = '🔴';
            else icon.textContent = '🚨';
            
            // Update AI description
            if (result.ai_description && result.ai_description.description) {
                aiText.textContent = result.ai_description.description;
                
                // Highlight safety concerns
                if (threat.level === 'warning' || threat.level === 'critical') {
                    document.getElementById('ai-description').style.borderColor = threat.color;
                    document.getElementById('ai-description').style.background = `${threat.color}22`;
                } else {
                    document.getElementById('ai-description').style.borderColor = 'rgba(16, 185, 129, 0.5)';
                    document.getElementById('ai-description').style.background = 'rgba(16, 185, 129, 0.2)';
                }
            }
            
            // Update stats
            objectCount.textContent = result.detections.count;
            trackCount.textContent = result.tracking.active_tracks;
            
            if (result.detections.security_relevant) {
                securityStatus.textContent = 'Security Alert';
                securityStatus.style.color = '#ef4444';
            } else {
                securityStatus.textContent = 'Monitoring...';
                securityStatus.style.color = '#10b981';
            }
        }
        
        function openRedFlagModal() {
            document.getElementById('red-flag-modal').classList.add('active');
        }
        
        function closeRedFlagModal() {
            document.getElementById('red-flag-modal').classList.remove('active');
        }
        
        async function submitRedFlag() {
            const data = {
                severity: document.getElementById('severity').value,
                category: document.getElementById('category').value,
                description: document.getElementById('description').value,
                camera_id: 'mobile_camera',
                snapshot_path: lastSnapshot
            };
            
            try {
                const response = await fetch('/camera/red-flag', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('🚩 Red flag created!');
                    closeRedFlagModal();
                    document.getElementById('description').value = '';
                }
            } catch (error) {
                alert('Failed to create red flag: ' + error.message);
            }
        }
        
        // Event listeners
        document.getElementById('start-btn').addEventListener('click', startCamera);
        
        document.getElementById('pause-btn').addEventListener('click', () => {
            isPaused = !isPaused;
            const btn = document.getElementById('pause-btn');
            btn.textContent = isPaused ? '▶️ Resume' : '⏸ Pause';
        });
        
        document.getElementById('red-flag-btn').addEventListener('click', openRedFlagModal);
    </script>
</body>
</html>
"""
