"""
Red Light Violation Detector

Combines traffic light detection, vehicle tracking, and stop line monitoring
to detect red light violations.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List
from datetime import datetime
from pathlib import Path

from alibi.traffic.light_state import TrafficLightDetector, LightState
from alibi.traffic.vehicle_detect import VehicleDetector, TrackedVehicle
from alibi.traffic.stop_line import StopLineMonitor, CrossingEvent
from alibi.traffic.config import TrafficCameraConfig


class RedLightViolationDetector:
    """
    Detects red light violations by combining:
    - Traffic light state detection
    - Vehicle tracking
    - Stop line crossing detection
    
    Emits violation events with annotated evidence.
    """
    
    def __init__(
        self,
        camera_config: TrafficCameraConfig,
        evidence_dir: str = "alibi/data/evidence"
    ):
        """
        Initialize red light violation detector.
        
        Args:
            camera_config: Traffic camera configuration
            evidence_dir: Directory for evidence files
        """
        self.camera_config = camera_config
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize sub-detectors
        self.light_detector = TrafficLightDetector(smoothing_window=5)
        self.vehicle_detector = VehicleDetector(
            min_contour_area=1000,
            max_contour_area=50000
        )
        self.stop_line_monitor = StopLineMonitor(
            stop_line=camera_config.stop_line,
            traffic_direction=camera_config.traffic_direction
        )
        
        # State
        self.current_light_state = LightState.UNKNOWN
        self.current_light_confidence = 0.0
    
    def process_frame(
        self,
        frame: np.ndarray,
        timestamp: float
    ) -> Optional[dict]:
        """
        Process a frame and detect violations.
        
        Args:
            frame: Input frame (BGR)
            timestamp: Frame timestamp
            
        Returns:
            Violation event dict if detected, None otherwise
        """
        # 1. Detect traffic light state
        light_state, light_confidence = self.light_detector.detect(
            frame,
            self.camera_config.traffic_light_roi
        )
        
        self.current_light_state = light_state
        self.current_light_confidence = light_confidence
        
        # 2. Detect vehicles in intersection
        vehicles = self.vehicle_detector.detect(
            frame,
            timestamp,
            roi=self.camera_config.intersection_roi
        )
        
        # 3. Check for stop line crossings
        crossings = self.stop_line_monitor.check_crossings(vehicles, timestamp)
        
        # 4. Generate violation events if light is RED
        if light_state == LightState.RED and crossings:
            for crossing in crossings:
                # Find the vehicle that crossed
                vehicle = next(
                    (v for v in vehicles if v.vehicle_id == crossing.vehicle_id),
                    None
                )
                
                if vehicle:
                    return self._create_violation_event(
                        frame,
                        timestamp,
                        vehicle,
                        crossing,
                        light_state,
                        light_confidence
                    )
        
        return None
    
    def _create_violation_event(
        self,
        frame: np.ndarray,
        timestamp: float,
        vehicle: TrackedVehicle,
        crossing: CrossingEvent,
        light_state: LightState,
        light_confidence: float
    ) -> dict:
        """
        Create a violation event with evidence.
        
        Args:
            frame: Current frame
            timestamp: Timestamp
            vehicle: Vehicle that crossed
            crossing: Crossing event
            light_state: Traffic light state
            light_confidence: Light detection confidence
            
        Returns:
            Event dictionary
        """
        # Calculate combined confidence
        # Confidence = min(light_confidence, tracking_confidence)
        # For now, use light confidence as baseline
        combined_confidence = light_confidence
        
        # Determine severity based on confidence
        if combined_confidence >= 0.8:
            severity = 4  # High confidence violation
        else:
            severity = 3  # Medium confidence, needs review
        
        # Create annotated snapshot
        snapshot_path = self._create_annotated_snapshot(
            frame,
            vehicle,
            light_state
        )
        
        # Create event
        event = {
            "event_type": "red_light_violation",
            "confidence": combined_confidence,
            "severity": severity,
            "snapshot_url": f"/evidence/{snapshot_path}" if snapshot_path else None,
            "metadata": {
                "light_state": light_state.value,
                "light_confidence": round(light_confidence, 3),
                "crossing_ts": crossing.crossing_timestamp,
                "vehicle_id": vehicle.vehicle_id,
                "centroid": crossing.centroid_at_crossing,
                "bbox": crossing.bbox_at_crossing,
                "direction": crossing.direction,
                "camera_location": self.camera_config.location,
                "requires_verification": True,
                "warning": "POSSIBLE RED LIGHT VIOLATION - VERIFY"
            }
        }
        
        return event
    
    def _create_annotated_snapshot(
        self,
        frame: np.ndarray,
        vehicle: TrackedVehicle,
        light_state: LightState
    ) -> Optional[str]:
        """
        Create annotated snapshot with vehicle bbox, stop line, and light state.
        
        Args:
            frame: Input frame
            vehicle: Tracked vehicle
            light_state: Current light state
            
        Returns:
            Relative path to snapshot file
        """
        try:
            # Create annotated copy
            annotated = frame.copy()
            
            # Draw stop line
            for i in range(len(self.camera_config.stop_line) - 1):
                pt1 = self.camera_config.stop_line[i]
                pt2 = self.camera_config.stop_line[i + 1]
                cv2.line(annotated, pt1, pt2, (0, 0, 255), 3)  # Red line
            
            # Draw vehicle bbox
            x, y, w, h = vehicle.bbox
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 255), 2)  # Yellow box
            
            # Draw vehicle ID
            cv2.putText(
                annotated,
                f"Vehicle {vehicle.vehicle_id}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )
            
            # Draw light state indicator
            light_color = {
                LightState.RED: (0, 0, 255),
                LightState.AMBER: (0, 165, 255),
                LightState.GREEN: (0, 255, 0),
                LightState.UNKNOWN: (128, 128, 128)
            }
            
            color = light_color.get(light_state, (255, 255, 255))
            
            cv2.putText(
                annotated,
                f"LIGHT: {light_state.value.upper()}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                color,
                3
            )
            
            # Draw traffic light ROI box
            lx, ly, lw, lh = self.camera_config.traffic_light_roi
            cv2.rectangle(annotated, (lx, ly), (lx + lw, ly + lh), color, 2)
            
            # Generate filename
            dt = datetime.fromtimestamp(vehicle.last_seen)
            filename = f"red_light_{self.camera_config.camera_id}_{dt.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
            
            # Save snapshot
            snapshots_dir = self.evidence_dir / "snapshots"
            snapshots_dir.mkdir(exist_ok=True)
            filepath = snapshots_dir / filename
            
            cv2.imwrite(str(filepath), annotated, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            # Return relative path
            return f"snapshots/{filename}"
        
        except Exception as e:
            print(f"[RedLightDetector] Error creating annotated snapshot: {e}")
            return None
    
    def reset(self):
        """Reset detector state"""
        self.light_detector.reset()
        self.vehicle_detector.reset()
        self.stop_line_monitor.reset()
        self.current_light_state = LightState.UNKNOWN
        self.current_light_confidence = 0.0
