"""
Training Data Review Schema

Lightweight state machine for human validation of training data.
NOTHING becomes fine-tune eligible without explicit human confirmation.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pathlib import Path
import json


class ReviewStatus(Enum):
    """
    Review status for training incidents.
    
    Flow:
    1. Incident created → PENDING_REVIEW
    2. Human reviews:
       - Good data → CONFIRMED (fine-tune eligible)
       - Bad data → REJECTED (not used)
       - Unsure → NEEDS_REVIEW (flag for senior review)
    """
    PENDING_REVIEW = "pending_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class RejectReason(Enum):
    """
    Reasons for rejecting training data.
    
    Used for:
    - Audit trail
    - Understanding rejection patterns
    - Improving data collection
    """
    WRONG_CLASS = "wrong_class"              # Detector misclassified object
    BASELINE_NOISE = "baseline_noise"        # Not security-relevant
    PRIVACY_RISK = "privacy_risk"            # Contains identifiable people without consent
    LOW_QUALITY = "low_quality"              # Blurry, dark, occluded
    DUPLICATE = "duplicate"                  # Already have similar example
    POLICY_VIOLATION = "policy_violation"    # Violates data policy
    OTHER = "other"                          # Other reason (specify in notes)


@dataclass
class HumanReview:
    """
    Human review decision on training data.
    
    This is the GATE for fine-tuning eligibility.
    """
    # Review decision
    status: ReviewStatus
    reject_reason: Optional[RejectReason] = None
    
    # Reviewer info
    reviewer_username: str = ""
    reviewer_role: str = ""
    
    # Timestamps
    reviewed_at: datetime = field(default_factory=datetime.utcnow)
    
    # Notes
    notes: Optional[str] = None
    
    # Privacy handling
    faces_detected: bool = False
    faces_redacted: bool = False
    redaction_method: Optional[str] = None  # "blur", "pixelate", "mask"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage"""
        return {
            "status": self.status.value,
            "reject_reason": self.reject_reason.value if self.reject_reason else None,
            "reviewer_username": self.reviewer_username,
            "reviewer_role": self.reviewer_role,
            "reviewed_at": self.reviewed_at.isoformat(),
            "notes": self.notes,
            "faces_detected": self.faces_detected,
            "faces_redacted": self.faces_redacted,
            "redaction_method": self.redaction_method
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'HumanReview':
        """Create from dict"""
        return HumanReview(
            status=ReviewStatus(data["status"]),
            reject_reason=RejectReason(data["reject_reason"]) if data.get("reject_reason") else None,
            reviewer_username=data.get("reviewer_username", ""),
            reviewer_role=data.get("reviewer_role", ""),
            reviewed_at=datetime.fromisoformat(data["reviewed_at"]) if data.get("reviewed_at") else datetime.utcnow(),
            notes=data.get("notes"),
            faces_detected=data.get("faces_detected", False),
            faces_redacted=data.get("faces_redacted", False),
            redaction_method=data.get("redaction_method")
        )


@dataclass
class TrainingIncident:
    """
    Training data incident with review state.
    
    Combines:
    - VisionIncident (detections, rules, evidence)
    - HumanReview (confirmation, rejection)
    - Provenance (where it came from, when, why)
    """
    # Identity
    incident_id: str
    
    # Source incident data
    incident_data: Dict[str, Any]  # VisionIncident.to_dict()
    
    # Review state
    review: Optional[HumanReview] = None
    
    # Provenance
    source_camera_id: str = ""
    source_timestamp: Optional[datetime] = None
    collection_method: str = "gatekeeper"  # "gatekeeper", "manual", "import"
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_fine_tune_eligible(self) -> bool:
        """
        Is this incident eligible for fine-tuning?
        
        Rules:
        1. MUST be confirmed by human
        2. If privacy_risk, MUST have faces redacted
        3. Must have evidence
        """
        if not self.review:
            return False
        
        if self.review.status != ReviewStatus.CONFIRMED:
            return False
        
        # Check privacy
        if self.review.faces_detected and not self.review.faces_redacted:
            return False
        
        # Check evidence exists
        evidence_frames = self.incident_data.get("evidence_frames", [])
        evidence_clip = self.incident_data.get("evidence_clip")
        if not evidence_frames and not evidence_clip:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage"""
        return {
            "incident_id": self.incident_id,
            "incident_data": self.incident_data,
            "review": self.review.to_dict() if self.review else None,
            "source_camera_id": self.source_camera_id,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "collection_method": self.collection_method,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'TrainingIncident':
        """Create from dict"""
        return TrainingIncident(
            incident_id=data["incident_id"],
            incident_data=data["incident_data"],
            review=HumanReview.from_dict(data["review"]) if data.get("review") else None,
            source_camera_id=data.get("source_camera_id", ""),
            source_timestamp=datetime.fromisoformat(data["source_timestamp"]) if data.get("source_timestamp") else None,
            collection_method=data.get("collection_method", "gatekeeper"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow()
        )


class TrainingDataStore:
    """
    Store for training incidents with review state.
    
    Maintains:
    - JSONL file of all training incidents
    - Review state for each
    - Query by status
    """
    
    def __init__(self, storage_path: str = "alibi/data/training_incidents.jsonl"):
        """
        Initialize store.
        
        Args:
            storage_path: Path to JSONL storage file
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def add_incident(self, incident: TrainingIncident) -> None:
        """Add incident to store"""
        with open(self.storage_path, "a") as f:
            f.write(json.dumps(incident.to_dict()) + "\n")
    
    def get_all(self) -> List[TrainingIncident]:
        """Get all incidents"""
        if not self.storage_path.exists():
            return []
        
        incidents = []
        with open(self.storage_path) as f:
            for line in f:
                if line.strip():
                    incidents.append(TrainingIncident.from_dict(json.loads(line)))
        return incidents
    
    def get_by_status(self, status: ReviewStatus) -> List[TrainingIncident]:
        """Get incidents by review status"""
        all_incidents = self.get_all()
        return [
            inc for inc in all_incidents
            if inc.review and inc.review.status == status
        ]
    
    def get_fine_tune_eligible(self) -> List[TrainingIncident]:
        """Get all fine-tune eligible incidents (confirmed + privacy-safe)"""
        all_incidents = self.get_all()
        return [inc for inc in all_incidents if inc.is_fine_tune_eligible]
    
    def get_counts_by_status(self) -> Dict[str, int]:
        """Get counts by review status"""
        all_incidents = self.get_all()
        counts = {
            "pending_review": 0,
            "confirmed": 0,
            "rejected": 0,
            "needs_review": 0,
            "total": len(all_incidents)
        }
        
        for inc in all_incidents:
            if inc.review:
                counts[inc.review.status.value] += 1
            else:
                counts["pending_review"] += 1
        
        return counts
    
    def update_review(
        self,
        incident_id: str,
        review: HumanReview
    ) -> bool:
        """
        Update review state for an incident.
        
        This is done by rewriting the entire file (inefficient but simple).
        For production, use a proper database.
        
        Args:
            incident_id: Incident ID to update
            review: New review state
            
        Returns:
            True if updated, False if not found
        """
        all_incidents = self.get_all()
        updated = False
        
        for inc in all_incidents:
            if inc.incident_id == incident_id:
                inc.review = review
                inc.updated_at = datetime.utcnow()
                updated = True
                break
        
        if updated:
            # Rewrite file
            with open(self.storage_path, "w") as f:
                for inc in all_incidents:
                    f.write(json.dumps(inc.to_dict()) + "\n")
        
        return updated
