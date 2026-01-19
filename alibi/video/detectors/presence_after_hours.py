"""
Presence After Hours Detector

Detects motion during after-hours time windows (e.g., perimeter breaches).
"""

from datetime import datetime, time
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

from alibi.video.detectors.base import Detector, DetectionResult
from alibi.video.detectors.motion_detector import MotionDetector
from alibi.video.zones import Zone


class PresenceAfterHoursDetector(Detector):
    """
    Detects presence/motion during after-hours time windows.
    
    Uses motion detector as base, but:
    - Only triggers during configured time windows
    - Emits "perimeter_breach" event type
    - Higher severity and confidence
    """
    
    def __init__(
        self,
        name: str = "after_hours",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Config options:
        - after_hours_start: Start time (HH:MM), default "22:00"
        - after_hours_end: End time (HH:MM), default "06:00"
        - base_confidence: Base confidence score, default 0.85
        - base_severity: Base severity level, default 4
        - motion_config: Config passed to underlying motion detector
        """
        super().__init__(name, config)
        
        # Parse time windows
        start_str = self.config.get('after_hours_start', '22:00')
        end_str = self.config.get('after_hours_end', '06:00')
        
        self.after_hours_start = self._parse_time(start_str)
        self.after_hours_end = self._parse_time(end_str)
        
        self.base_confidence = self.config.get('base_confidence', 0.85)
        self.base_severity = self.config.get('base_severity', 4)
        
        # Create underlying motion detector
        motion_config = self.config.get('motion_config', {})
        self.motion_detector = MotionDetector(name=f"{name}_motion", config=motion_config)
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string (HH:MM)"""
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)
    
    def is_after_hours(self, timestamp: float) -> bool:
        """
        Check if timestamp is within after-hours window.
        
        Args:
            timestamp: Unix timestamp
        
        Returns:
            True if after hours
        """
        dt = datetime.fromtimestamp(timestamp)
        current_time = dt.time()
        
        # Handle overnight windows (e.g., 22:00 - 06:00)
        if self.after_hours_start > self.after_hours_end:
            return current_time >= self.after_hours_start or current_time <= self.after_hours_end
        else:
            return self.after_hours_start <= current_time <= self.after_hours_end
    
    def detect(
        self,
        frame: np.ndarray,
        timestamp: float,
        zone: Optional[Zone] = None,
        **kwargs
    ) -> Optional[DetectionResult]:
        """
        Detect presence during after-hours.
        
        Args:
            frame: Input frame
            timestamp: Frame timestamp
            zone: Optional zone for masking
        
        Returns:
            DetectionResult if presence detected after hours, None otherwise
        """
        # Check if after hours
        if not self.is_after_hours(timestamp):
            # Still update motion detector state
            self.motion_detector.detect(frame, timestamp, zone=zone)
            return None
        
        # Run motion detection
        motion_result = self.motion_detector.detect(frame, timestamp, zone=zone)
        
        if not motion_result or not motion_result.detected:
            return None
        
        # Convert to perimeter_breach event
        # Increase confidence and severity
        confidence = min(self.base_confidence + (motion_result.confidence - 0.75) * 0.1, 1.0)
        severity = max(self.base_severity, motion_result.severity + 1)
        severity = min(severity, 5)  # Cap at 5
        
        # Enhance metadata
        metadata = motion_result.metadata.copy()
        metadata['after_hours'] = True
        metadata['breach_type'] = 'after_hours_motion'
        metadata['time_detected'] = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
        
        return DetectionResult(
            detected=True,
            event_type="perimeter_breach",
            confidence=confidence,
            severity=severity,
            metadata=metadata,
            zone_id=zone.zone_id if zone else None,
        )
    
    def reset(self):
        """Reset detector state"""
        self.motion_detector.reset()
