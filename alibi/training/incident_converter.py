"""
Incident to Training Data Converter

Automatically converts closed incidents to TrainingIncidents for human review.
This is the bridge between the incident manager and the training data pipeline.
"""

from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

from alibi.schema.training import (
    TrainingDataStore,
    TrainingIncident,
    ReviewStatus
)
from alibi.privacy import check_privacy_risk


class IncidentToTrainingConverter:
    """
    Converts closed incidents to TrainingIncidents.
    
    This is the missing link that connects:
    - Camera detections → Incidents → TrainingIncidents → Human review → Export
    """
    
    def __init__(self, training_store: Optional[TrainingDataStore] = None):
        """
        Initialize converter.
        
        Args:
            training_store: TrainingDataStore instance (creates new if None)
        """
        self.training_store = training_store or TrainingDataStore()
        self.converted_count = 0
    
    def convert_incident(
        self,
        incident: Dict,
        camera_id: str = "unknown",
        evidence_frames: Optional[list] = None,
        evidence_clip: Optional[str] = None
    ) -> Optional[TrainingIncident]:
        """
        Convert a closed incident to a TrainingIncident.
        
        Args:
            incident: Closed incident dict from IncidentManager
            camera_id: Source camera ID
            evidence_frames: Optional list of evidence frame paths
            evidence_clip: Optional clip path
            
        Returns:
            TrainingIncident if successful, None otherwise
        """
        # Ensure incident is closed
        if incident.get("status") != "closed":
            return None
        
        # Build incident data structure
        incident_data = {
            "category": self._infer_category(incident["triggered_rules"]),
            "reason": incident["reason"],
            "duration_seconds": incident["duration_seconds"],
            "max_confidence": incident["max_confidence"],
            "triggered_rules": incident["triggered_rules"],
            "zone_presence": incident["zone_presence"],
            "class_name": incident["class_name"],
            "start_time": incident["start_time"].isoformat() if isinstance(incident["start_time"], datetime) else incident["start_time"],
            "end_time": incident["end_time"].isoformat() if isinstance(incident["end_time"], datetime) else incident["end_time"],
            "evidence_frames": evidence_frames or [],
            "evidence_clip": evidence_clip
        }
        
        # Check for privacy risks
        faces_detected = False
        if evidence_frames:
            for frame_path in evidence_frames[:1]:  # Check first frame
                frame_path = Path(frame_path)
                if frame_path.exists():
                    has_faces, num_faces = check_privacy_risk(str(frame_path))
                    if has_faces:
                        faces_detected = True
                        break
        
        # Create TrainingIncident
        training_incident = TrainingIncident(
            incident_id=incident["incident_id"],
            incident_data=incident_data,
            review=None,  # Pending review
            source_camera_id=camera_id,
            source_timestamp=incident["start_time"] if isinstance(incident["start_time"], datetime) else datetime.fromisoformat(incident["start_time"]),
            collection_method="gatekeeper"
        )
        
        # Store it
        self.training_store.add_incident(training_incident)
        self.converted_count += 1
        
        return training_incident
    
    def _infer_category(self, triggered_rules: list) -> str:
        """
        Infer incident category from triggered rules.
        
        Args:
            triggered_rules: List of rule names
            
        Returns:
            Category string
        """
        rules_str = " ".join(triggered_rules).lower()
        
        if "loitering" in rules_str:
            return "loitering"
        elif "restricted_zone" in rules_str:
            return "restricted_zone_entry"
        elif "unattended" in rules_str:
            return "object_left_unattended"
        elif "rapid_movement" in rules_str or "aggression" in rules_str:
            return "rapid_movement"
        elif "crowd" in rules_str:
            return "crowd_formation"
        elif "person" in rules_str:
            return "person_detected"
        elif "vehicle" in rules_str:
            return "vehicle_detected"
        else:
            return "unknown"
    
    def process_closed_incidents(
        self,
        closed_incidents: list,
        camera_id: str = "unknown",
        evidence_dir: Optional[Path] = None
    ) -> int:
        """
        Process a batch of closed incidents.
        
        Args:
            closed_incidents: List of closed incident dicts
            camera_id: Source camera ID
            evidence_dir: Directory containing evidence files
            
        Returns:
            Number of incidents converted
        """
        converted = 0
        
        for incident in closed_incidents:
            # Look for evidence files if directory provided
            evidence_frames = []
            evidence_clip = None
            
            if evidence_dir:
                incident_id = incident["incident_id"]
                
                # Look for frames
                frame_pattern = f"{incident_id}_frame_*.jpg"
                evidence_frames = [
                    str(p) for p in evidence_dir.glob(frame_pattern)
                ]
                
                # Look for clip
                clip_path = evidence_dir / f"{incident_id}_clip.mp4"
                if clip_path.exists():
                    evidence_clip = str(clip_path)
            
            # Convert
            training_incident = self.convert_incident(
                incident,
                camera_id=camera_id,
                evidence_frames=evidence_frames,
                evidence_clip=evidence_clip
            )
            
            if training_incident:
                converted += 1
        
        return converted
    
    def get_stats(self) -> Dict:
        """Get conversion statistics"""
        return {
            "converted_count": self.converted_count,
            "pending_review": len(self.training_store.get_by_status(ReviewStatus.PENDING_REVIEW)),
            "confirmed": len(self.training_store.get_by_status(ReviewStatus.CONFIRMED)),
            "rejected": len(self.training_store.get_by_status(ReviewStatus.REJECTED))
        }


# Global converter instance
_converter = None


def get_converter() -> IncidentToTrainingConverter:
    """Get global converter instance"""
    global _converter
    if _converter is None:
        _converter = IncidentToTrainingConverter()
    return _converter
