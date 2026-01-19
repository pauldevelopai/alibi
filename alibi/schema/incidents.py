"""
Vision-First Incident Schema

Structured incident objects created from computer vision detections.
These replace LLM-generated captions as the primary source of truth.

PHILOSOPHY:
- Incidents are vision-based, not language-based
- They exist independent of LLM availability
- LLM captions are OPTIONAL enrichment, not required data
- Training data is based on detections, not descriptions
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class IncidentCategory(Enum):
    """
    Vision-first categories based on DETECTIONS, not LLM interpretation.
    """
    # People
    PERSON_DETECTED = "person_detected"
    PERSON_LOITERING = "person_loitering"
    MULTIPLE_PEOPLE = "multiple_people"
    
    # Vehicles
    VEHICLE_DETECTED = "vehicle_detected"
    VEHICLE_PARKED = "vehicle_parked"
    MULTIPLE_VEHICLES = "multiple_vehicles"
    
    # Zone violations
    RESTRICTED_ZONE_ENTRY = "restricted_zone_entry"
    AFTER_HOURS_PRESENCE = "after_hours_presence"
    
    # Objects
    OBJECT_LEFT_UNATTENDED = "object_left_unattended"
    SUSPICIOUS_OBJECT = "suspicious_object"
    WEAPON_DETECTED = "weapon_detected"
    
    # Activity (derived from motion/tracking)
    RAPID_MOVEMENT = "rapid_movement"
    CROWD_FORMATION = "crowd_formation"
    
    # Fallback
    UNKNOWN = "unknown"


@dataclass
class DetectionSummary:
    """Summary of YOLO detections for this incident"""
    classes: List[str]              # List of detected class names
    counts: Dict[str, int]          # Count per class
    avg_confidence: float           # Average detection confidence
    total_detections: int           # Total number of detections
    security_relevant: bool         # Contains security-relevant objects
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "classes": self.classes,
            "counts": self.counts,
            "avg_confidence": self.avg_confidence,
            "total_detections": self.total_detections,
            "security_relevant": self.security_relevant
        }


@dataclass
class ZoneHitSummary:
    """Summary of zone violations"""
    zone_ids: List[str]
    zone_names: List[str]
    zone_types: List[str]           # restricted, monitored, public, private
    restricted_violations: int       # Count of restricted zone hits
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_ids": self.zone_ids,
            "zone_names": self.zone_names,
            "zone_types": self.zone_types,
            "restricted_violations": self.restricted_violations
        }


@dataclass
class IncidentScores:
    """Confidence scores for this incident"""
    vision_conf: float      # YOLO detection confidence (0-1)
    rule_conf: float        # Rule-based relevance score (0-1)
    combined_conf: float    # Final combined score (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vision_conf": self.vision_conf,
            "rule_conf": self.rule_conf,
            "combined_conf": self.combined_conf
        }


@dataclass
class IncidentFlags:
    """Flags for incident processing"""
    privacy_risk: bool = False          # Contains people in public areas
    needs_human_review: bool = False    # Requires manual review
    llm_optional: bool = True           # LLM caption is optional
    training_eligible: bool = False     # Can be used for training
    baseline_noise: bool = False        # Stored as noise, not training
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "privacy_risk": self.privacy_risk,
            "needs_human_review": self.needs_human_review,
            "llm_optional": self.llm_optional,
            "training_eligible": self.training_eligible,
            "baseline_noise": self.baseline_noise
        }


@dataclass
class VisionIncident:
    """
    A vision-first incident created by the Gatekeeper.
    
    KEY PRINCIPLE:
    This incident exists BEFORE any LLM is called.
    The LLM may enrich it later, but it is NOT required for the incident to exist.
    
    TRAINING ELIGIBILITY:
    Only incidents with training_eligible=True are used for training.
    The rest are stored as baseline/noise for metrics.
    """
    
    # Identity
    id: str
    camera_id: str
    
    # Timing
    ts_start: datetime
    ts_end: datetime
    duration_seconds: float
    
    # Category (vision-based)
    category: IncidentCategory
    
    # Detections (the source of truth)
    detections: DetectionSummary
    
    # Zone hits (spatial context)
    zone_hits: Optional[ZoneHitSummary] = None
    
    # Evidence (frames/clips)
    evidence_frames: List[str] = field(default_factory=list)  # Frame paths
    evidence_clip: Optional[str] = None                        # Clip path
    
    # Scores (gatekeeper decision)
    scores: Optional[IncidentScores] = None
    
    # Flags (processing state)
    flags: IncidentFlags = field(default_factory=IncidentFlags)
    
    # LLM enrichment (OPTIONAL - may be None)
    llm_caption: Optional[str] = None
    llm_confidence: Optional[float] = None
    llm_timestamp: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage"""
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "ts_start": self.ts_start.isoformat(),
            "ts_end": self.ts_end.isoformat(),
            "duration_seconds": self.duration_seconds,
            "category": self.category.value,
            "detections": self.detections.to_dict(),
            "zone_hits": self.zone_hits.to_dict() if self.zone_hits else None,
            "evidence_frames": self.evidence_frames,
            "evidence_clip": self.evidence_clip,
            "scores": self.scores.to_dict() if self.scores else None,
            "flags": self.flags.to_dict(),
            "llm_caption": self.llm_caption,
            "llm_confidence": self.llm_confidence,
            "llm_timestamp": self.llm_timestamp.isoformat() if self.llm_timestamp else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @staticmethod
    def from_gatekeeper_result(
        camera_id: str,
        result: Dict[str, Any],
        evidence_frames: List[str],
        evidence_clip: Optional[str] = None
    ) -> 'VisionIncident':
        """
        Create an incident from gatekeeper pipeline output.
        
        Args:
            camera_id: Camera identifier
            result: Output from VisionGatekeeper.process_frame()
            evidence_frames: List of frame paths
            evidence_clip: Optional clip path
            
        Returns:
            VisionIncident ready to store
        """
        import uuid
        from datetime import datetime
        
        # Determine category based on detections
        detections = result['detections']
        zone_hits = result['zone_hits']
        
        category = IncidentCategory.UNKNOWN
        if detections:
            class_names = [d.class_name for d in detections]
            
            # People
            person_count = class_names.count("person")
            if person_count > 3:
                category = IncidentCategory.MULTIPLE_PEOPLE
            elif person_count >= 1:
                category = IncidentCategory.PERSON_DETECTED
            
            # Vehicles
            vehicle_classes = ["car", "motorcycle", "bus", "truck"]
            vehicle_count = sum(class_names.count(vc) for vc in vehicle_classes)
            if vehicle_count > 2:
                category = IncidentCategory.MULTIPLE_VEHICLES
            elif vehicle_count >= 1 and person_count == 0:
                category = IncidentCategory.VEHICLE_DETECTED
            
            # Weapons
            weapon_classes = ["knife", "scissors"]
            if any(wc in class_names for wc in weapon_classes):
                category = IncidentCategory.WEAPON_DETECTED
            
            # Zone violations
            restricted_hits = [
                zh for zh in zone_hits
                if zh.zone_type == "restricted"
            ]
            if restricted_hits:
                category = IncidentCategory.RESTRICTED_ZONE_ENTRY
        
        # Build detection summary
        class_counts = {}
        for d in detections:
            class_counts[d.class_name] = class_counts.get(d.class_name, 0) + 1
        
        security_classes = ["person", "car", "motorcycle", "bus", "truck", "knife", "scissors", "backpack", "handbag", "suitcase"]
        security_relevant = any(d.class_name in security_classes for d in detections)
        
        detection_summary = DetectionSummary(
            classes=list(set(d.class_name for d in detections)),
            counts=class_counts,
            avg_confidence=result['detection_summary']['avg_confidence'],
            total_detections=len(detections),
            security_relevant=security_relevant
        )
        
        # Build zone hit summary
        zone_hit_summary = None
        if zone_hits:
            zone_hit_summary = ZoneHitSummary(
                zone_ids=[zh.zone_id for zh in zone_hits],
                zone_names=[zh.zone_name for zh in zone_hits],
                zone_types=[zh.zone_type for zh in zone_hits],
                restricted_violations=len([
                    zh for zh in zone_hits if zh.zone_type == "restricted"
                ])
            )
        
        # Build scores
        score = result['score']
        incident_scores = IncidentScores(
            vision_conf=score.vision_conf,
            rule_conf=score.rule_conf,
            combined_conf=score.combined_conf
        )
        
        # Build flags
        flags = IncidentFlags(
            privacy_risk="person" in detection_summary.classes,
            needs_human_review=False,
            llm_optional=True,
            training_eligible=result['eligible'],
            baseline_noise=not result['eligible']
        )
        
        # Create incident
        now = datetime.utcnow()
        return VisionIncident(
            id=f"inc_{uuid.uuid4().hex[:12]}",
            camera_id=camera_id,
            ts_start=now,
            ts_end=now,
            duration_seconds=0.0,
            category=category,
            detections=detection_summary,
            zone_hits=zone_hit_summary,
            evidence_frames=evidence_frames,
            evidence_clip=evidence_clip,
            scores=incident_scores,
            flags=flags
        )
