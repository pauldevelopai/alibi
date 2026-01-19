"""
Video Simulation for Track-Level Incidents

Processes a video file to demonstrate:
- Track-level incidents (not frame-level)
- Incident open/update/close lifecycle
- Rule-based triggers
- Duration and "why" based on rules

Usage:
    python -m alibi.vision.simulate --video path/to/sample.mp4
"""

import argparse
import cv2
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

from alibi.vision.tracking import MultiObjectTracker, TrackState
from alibi.rules.events import RuleEvaluator
from alibi.training import get_converter


class IncidentManager:
    """
    Manages lifecycle of track-level incidents.
    
    Incidents:
    - OPEN when rule becomes true
    - UPDATE while rule remains true
    - CLOSE when rule becomes false or track ends
    """
    
    def __init__(
        self,
        rule_evaluator: RuleEvaluator,
        auto_convert_to_training: bool = True,
        camera_id: str = "unknown"
    ):
        """
        Initialize incident manager.
        
        Args:
            rule_evaluator: RuleEvaluator instance
            auto_convert_to_training: Automatically convert closed incidents to TrainingIncidents
            camera_id: Source camera ID for training data
        """
        self.rule_evaluator = rule_evaluator
        self.auto_convert_to_training = auto_convert_to_training
        self.camera_id = camera_id
        
        # Active incidents: track_id -> incident dict
        self.active_incidents: Dict[int, Dict] = {}
        
        # Closed incidents
        self.closed_incidents: List[Dict] = []
        
        # Incident counter
        self.incident_counter = 0
        
        # Training converter (if enabled)
        self.converter = get_converter() if auto_convert_to_training else None
    
    def update(
        self,
        tracks: Dict[int, TrackState],
        frame_number: int,
        timestamp: datetime
    ) -> Dict[str, List[Dict]]:
        """
        Update incidents based on current tracks and rules.
        
        Args:
            tracks: Active tracks from tracker
            frame_number: Current frame number
            timestamp: Current timestamp
            
        Returns:
            Dict with "opened", "updated", "closed" incidents
        """
        # Evaluate rules on all tracks
        rule_triggers = self.rule_evaluator.evaluate(tracks)
        
        opened = []
        updated = []
        closed = []
        
        # Check each track with rule triggers
        for track_id, triggered_rules in rule_triggers.items():
            track = tracks[track_id]
            
            if track_id not in self.active_incidents:
                # OPEN new incident
                self.incident_counter += 1
                incident = {
                    "incident_id": f"inc_{self.incident_counter:04d}",
                    "track_id": track_id,
                    "class_name": track.class_name,
                    "triggered_rules": triggered_rules,
                    "reason": self.rule_evaluator.get_incident_reason(track, triggered_rules),
                    "start_frame": frame_number,
                    "start_time": timestamp,
                    "last_frame": frame_number,
                    "last_time": timestamp,
                    "duration_seconds": 0.0,
                    "max_confidence": track.max_confidence,
                    "zone_presence": track.zone_presence.copy(),
                    "status": "open"
                }
                self.active_incidents[track_id] = incident
                opened.append(incident.copy())
            else:
                # UPDATE existing incident
                incident = self.active_incidents[track_id]
                incident["last_frame"] = frame_number
                incident["last_time"] = timestamp
                incident["duration_seconds"] = (timestamp - incident["start_time"]).total_seconds()
                incident["triggered_rules"] = triggered_rules
                incident["reason"] = self.rule_evaluator.get_incident_reason(track, triggered_rules)
                incident["max_confidence"] = max(incident["max_confidence"], track.max_confidence)
                incident["zone_presence"] = track.zone_presence.copy()
                updated.append(incident.copy())
        
        # Check for incidents to close (tracks that no longer trigger rules)
        tracks_to_close = []
        for track_id, incident in self.active_incidents.items():
            if track_id not in rule_triggers:
                # Rules no longer triggered - close incident
                incident["status"] = "closed"
                incident["end_frame"] = frame_number
                incident["end_time"] = timestamp
                incident["duration_seconds"] = (
                    incident["last_time"] - incident["start_time"]
                ).total_seconds()
                
                closed_incident = incident.copy()
                closed.append(closed_incident)
                self.closed_incidents.append(closed_incident)
                tracks_to_close.append(track_id)
                
                # Auto-convert to TrainingIncident for human review
                if self.converter:
                    try:
                        self.converter.convert_incident(
                            closed_incident,
                            camera_id=self.camera_id
                        )
                    except Exception as e:
                        print(f"⚠️  Failed to convert incident {incident['incident_id']} to training: {e}")
        
        # Remove closed incidents from active
        for track_id in tracks_to_close:
            del self.active_incidents[track_id]
        
        return {
            "opened": opened,
            "updated": updated,
            "closed": closed
        }
    
    def get_summary(self) -> Dict:
        """Get summary of incident management"""
        return {
            "total_incidents": self.incident_counter,
            "active_incidents": len(self.active_incidents),
            "closed_incidents": len(self.closed_incidents)
        }


def load_zones_config(zones_file: str) -> List[Dict]:
    """Load zones configuration from JSON file"""
    with open(zones_file) as f:
        return json.load(f)


def load_rules_config(rules_file: str) -> Dict:
    """Load rules configuration from YAML file"""
    with open(rules_file) as f:
        return yaml.safe_load(f)


def simulate_video(
    video_path: str,
    zones_file: Optional[str] = None,
    rules_file: Optional[str] = None,
    model_path: str = "yolov8n.pt",
    show_video: bool = False,
    max_frames: Optional[int] = None
):
    """
    Simulate track-level incidents on a video.
    
    Args:
        video_path: Path to video file
        zones_file: Path to zones.json (optional)
        rules_file: Path to rules.yaml (optional)
        model_path: YOLO model path
        show_video: Whether to show annotated video
        max_frames: Maximum frames to process (None = all)
    """
    if not YOLO_AVAILABLE:
        print("❌ ultralytics not installed. Install with: pip install ultralytics")
        return
    
    print("\n" + "="*70)
    print("TRACK-LEVEL INCIDENT SIMULATION")
    print("="*70)
    
    # Load video
    print(f"\n📹 Loading video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Failed to open video: {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"   ✅ Loaded: {total_frames} frames, {fps:.1f} FPS, {duration:.1f}s")
    
    if max_frames:
        total_frames = min(total_frames, max_frames)
        print(f"   ⏭️  Processing first {max_frames} frames only")
    
    # Load configs
    zones_config = None
    if zones_file and Path(zones_file).exists():
        zones_config = load_zones_config(zones_file)
        print(f"\n🎯 Loaded {len(zones_config)} zones from {zones_file}")
    else:
        print("\n⚠️  No zones config - using default")
        zones_config = []
    
    rules_config = None
    if rules_file and Path(rules_file).exists():
        rules_config = load_rules_config(rules_file)
        print(f"📋 Loaded rules from {rules_file}")
    else:
        print("⚠️  No rules config - using defaults")
    
    # Initialize YOLO with tracking
    print(f"\n🤖 Initializing YOLO: {model_path}")
    model = YOLO(model_path)
    print("   ✅ Model loaded")
    
    # Initialize tracker
    print("\n🎯 Initializing tracker...")
    tracker = MultiObjectTracker(max_age=30, min_hits=3)
    print("   ✅ Tracker ready")
    
    # Initialize rule evaluator
    print("\n📐 Initializing rule evaluator...")
    evaluator = RuleEvaluator(zones_config, rules_config)
    print("   ✅ Rules ready")
    
    # Initialize incident manager
    print("\n🚨 Initializing incident manager...")
    incident_manager = IncidentManager(evaluator)
    print("   ✅ Manager ready")
    
    # Process video
    print(f"\n▶️  Processing video...")
    print("="*70)
    
    frame_count = 0
    start_time = datetime.utcnow()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if max_frames and frame_count >= max_frames:
            break
        
        frame_count += 1
        timestamp = start_time + timedelta(seconds=frame_count / fps)
        
        # Run YOLO with tracking
        results = model.track(frame, persist=True, conf=0.5, verbose=False)
        
        # Update tracker
        tracks = tracker.update(results, zones_config, timestamp)
        
        # Update incidents
        incident_updates = incident_manager.update(tracks, frame_count, timestamp)
        
        # Print incident events
        for incident in incident_updates["opened"]:
            print(f"\n🟢 OPEN  | Frame {frame_count:04d} | "
                  f"ID: {incident['incident_id']} | "
                  f"Track: {incident['track_id']} | "
                  f"{incident['class_name']}")
            print(f"         Reason: {incident['reason']}")
        
        for incident in incident_updates["closed"]:
            print(f"\n🔴 CLOSE | Frame {frame_count:04d} | "
                  f"ID: {incident['incident_id']} | "
                  f"Duration: {incident['duration_seconds']:.1f}s")
            print(f"         Final reason: {incident['reason']}")
        
        # Show video (if requested)
        if show_video:
            # Annotate frame with tracks
            annotated = frame.copy()
            for track_id, track in tracks.items():
                x, y, w, h = track.current_bbox
                
                # Color based on incident status
                if track_id in incident_manager.active_incidents:
                    color = (0, 0, 255)  # Red for active incident
                else:
                    color = (0, 255, 0)  # Green for normal track
                
                cv2.rectangle(annotated, (x, y), (x+w, y+h), color, 2)
                label = f"T{track_id}: {track.class_name}"
                cv2.putText(annotated, label, (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            cv2.imshow("Track-Level Incidents", annotated)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    # Cleanup
    cap.release()
    if show_video:
        cv2.destroyAllWindows()
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    summary = incident_manager.get_summary()
    print(f"\n📊 Incident Statistics:")
    print(f"   Total incidents: {summary['total_incidents']}")
    print(f"   Still active: {summary['active_incidents']}")
    print(f"   Closed: {summary['closed_incidents']}")
    
    print(f"\n🎬 Processing Statistics:")
    print(f"   Frames processed: {frame_count}")
    print(f"   Active tracks: {len(tracker.get_active_tracks())}")
    
    if incident_manager.closed_incidents:
        print(f"\n📋 Closed Incidents:")
        for incident in incident_manager.closed_incidents:
            print(f"\n   {incident['incident_id']}:")
            print(f"      Class: {incident['class_name']}")
            print(f"      Duration: {incident['duration_seconds']:.1f}s")
            print(f"      Frames: {incident['start_frame']} → {incident['end_frame']}")
            print(f"      Reason: {incident['reason']}")
            print(f"      Rules: {', '.join(incident['triggered_rules'])}")
    
    print("\n" + "="*70)
    print("✅ Simulation complete!")
    print("="*70)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Simulate track-level incidents on video"
    )
    parser.add_argument(
        "--video",
        required=True,
        help="Path to video file"
    )
    parser.add_argument(
        "--zones",
        default="alibi/data/config/zones.json",
        help="Path to zones.json"
    )
    parser.add_argument(
        "--rules",
        default="alibi/data/config/rules.yaml",
        help="Path to rules.yaml"
    )
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="YOLO model path"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show annotated video"
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        help="Maximum frames to process"
    )
    
    args = parser.parse_args()
    
    simulate_video(
        video_path=args.video,
        zones_file=args.zones,
        rules_file=args.rules,
        model_path=args.model,
        show_video=args.show,
        max_frames=args.max_frames
    )


if __name__ == "__main__":
    main()
