"""
Vehicle Sighting Detector

Continuously detects and indexes vehicle sightings.
NOT an alert system - creates searchable database of vehicle activity.
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import time
import uuid

from alibi.video.detectors.base import Detector, DetectionResult
from alibi.video.zones import Zone
from alibi.vehicles.vehicle_detect import VehicleDetector
from alibi.vehicles.vehicle_attrs import VehicleAttributeExtractor
from alibi.vehicles.sightings_store import VehicleSightingsStore, VehicleSighting


class VehicleSightingDetector(Detector):
    """
    Detects vehicles and records sightings for search/indexing.
    
    This is NOT an alert system - it continuously indexes vehicle activity
    to enable operator searches like "Find all White Mazda Demio".
    """
    
    def __init__(
        self,
        name: str = "vehicle_sighting",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Config options:
        - sightings_path: Path to vehicle_sightings.jsonl
        - check_interval_seconds: How often to detect vehicles (default 3.0)
        - min_confidence: Minimum detection confidence (default 0.3)
        - evidence_dir: Directory for evidence files
        """
        super().__init__(name, config)
        
        # Configuration
        self.sightings_path = self.config.get(
            'sightings_path',
            'alibi/data/vehicle_sightings.jsonl'
        )
        self.check_interval = self.config.get('check_interval_seconds', 3.0)
        self.min_confidence = self.config.get('min_confidence', 0.3)
        self.evidence_dir = Path(self.config.get('evidence_dir', 'alibi/data/evidence'))
        
        # Initialize components
        self.vehicle_detector = VehicleDetector()
        self.attr_extractor = VehicleAttributeExtractor()
        self.sightings_store = VehicleSightingsStore(self.sightings_path)
        
        # State
        self.last_check_time = 0
        self.frame_count = 0
        
        print(f"[VehicleSightingDetector] Initialized - continuous vehicle indexing active")
    
    def detect(
        self,
        frame: np.ndarray,
        timestamp: float,
        camera_id: Optional[str] = None,
        zone: Optional[Zone] = None,
        **kwargs
    ) -> Optional[DetectionResult]:
        """
        Detect vehicles and record sightings.
        
        Args:
            frame: Input frame
            timestamp: Frame timestamp
            camera_id: Camera ID
            zone: Optional zone
            
        Returns:
            DetectionResult for each vehicle sighting (not an alert)
        """
        if not self.enabled:
            return None
        
        self.frame_count += 1
        
        # Rate limiting: only check every N seconds
        if timestamp - self.last_check_time < self.check_interval:
            return None
        
        self.last_check_time = timestamp
        
        # Detect vehicles
        detected_vehicles = self.vehicle_detector.detect(frame, max_vehicles=3)
        
        if not detected_vehicles:
            return None
        
        # Process first vehicle (can be extended to handle multiple)
        vehicle = detected_vehicles[0]
        
        if vehicle.confidence < self.min_confidence:
            return None
        
        try:
            # Extract attributes
            attrs = self.attr_extractor.extract_attributes(vehicle.vehicle_crop)
            
            # Save vehicle snapshot
            snapshot_path = self._save_vehicle_snapshot(vehicle.vehicle_crop, timestamp)
            
            # Generate sighting ID
            sighting_id = f"sighting_{uuid.uuid4().hex[:12]}"
            
            # Create sighting record
            sighting = VehicleSighting(
                sighting_id=sighting_id,
                camera_id=camera_id or "unknown",
                ts=datetime.fromtimestamp(timestamp).isoformat(),
                bbox=vehicle.bbox,
                color=attrs.color,
                make=attrs.make,
                model=attrs.model,
                confidence=vehicle.confidence,
                snapshot_url=f"/evidence/{snapshot_path}" if snapshot_path else None,
                clip_url=None,  # Optional: can add clip later
                metadata={
                    "color_confidence": round(attrs.color_confidence, 3),
                    "make_model_confidence": round(attrs.make_model_confidence, 3)
                }
            )
            
            # Store sighting
            self.sightings_store.add_sighting(sighting)
            
            # Return detection result (informational, not an alert)
            return DetectionResult(
                detected=True,
                event_type="vehicle_sighting",
                confidence=vehicle.confidence,
                severity=1,  # Low severity - not an alert
                zone_id=zone.zone_id if zone else None,
                metadata={
                    "sighting_id": sighting_id,
                    "color": attrs.color,
                    "make": attrs.make,
                    "model": attrs.model,
                    "bbox": {
                        "x": vehicle.bbox[0],
                        "y": vehicle.bbox[1],
                        "w": vehicle.bbox[2],
                        "h": vehicle.bbox[3]
                    },
                    "snapshot_url": sighting.snapshot_url,
                    "indexing": True  # Mark as indexing, not alerting
                }
            )
        
        except Exception as e:
            print(f"[VehicleSightingDetector] Error processing vehicle: {e}")
            return None
    
    def _save_vehicle_snapshot(
        self,
        vehicle_crop: np.ndarray,
        timestamp: float
    ) -> Optional[str]:
        """
        Save vehicle snapshot to evidence directory.
        
        Args:
            vehicle_crop: Vehicle crop image
            timestamp: Detection timestamp
            
        Returns:
            Relative path for URL, or None if failed
        """
        try:
            # Create vehicle_snapshots subdirectory
            snapshots_dir = self.evidence_dir / "vehicle_snapshots"
            snapshots_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            dt = datetime.fromtimestamp(timestamp)
            filename = f"vehicle_{dt.strftime('%Y%m%d_%H%M%S_%f')}.jpg"
            filepath = snapshots_dir / filename
            
            # Save with high quality
            cv2.imwrite(str(filepath), vehicle_crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            # Return relative path
            return f"vehicle_snapshots/{filename}"
        
        except Exception as e:
            print(f"[VehicleSightingDetector] Error saving vehicle snapshot: {e}")
            return None
    
    def reset(self):
        """Reset detector state"""
        self.last_check_time = 0
        self.frame_count = 0
        self.vehicle_detector.reset()
