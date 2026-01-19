"""
Rule-Based Event Detection from Tracks

Time-based rules that trigger incidents:
- Restricted zone entry (person in restricted area)
- Loitering (person stationary in zone > threshold)
- Object left unattended (stationary object)

These rules replace LLM guessing with deterministic logic.
"""

from typing import Dict, List, Optional
from datetime import datetime
from alibi.vision.tracking import TrackState


def restricted_zone_entry(
    track: TrackState,
    zones_config: List[Dict],
    restricted_zone_types: Optional[List[str]] = None
) -> bool:
    """
    Check if track has entered a restricted zone.
    
    Rule: Track is currently in a zone marked as "restricted"
    
    Args:
        track: TrackState to check
        zones_config: List of zone configurations
        restricted_zone_types: Zone types considered restricted (default: ["restricted"])
        
    Returns:
        True if track is in restricted zone
    """
    if restricted_zone_types is None:
        restricted_zone_types = ["restricted"]
    
    # Check each zone the track is currently in
    for zone_id in track.current_zones:
        # Find zone config
        zone_config = next(
            (z for z in zones_config if z["id"] == zone_id),
            None
        )
        
        if zone_config and zone_config.get("type") in restricted_zone_types:
            return True
    
    return False


def loitering(
    track: TrackState,
    zone_id: str,
    dwell_seconds_threshold: float = 30.0
) -> bool:
    """
    Check if track is loitering in a zone.
    
    Rule: Track has been in zone for > threshold seconds
    
    Args:
        track: TrackState to check
        zone_id: Zone ID to check
        dwell_seconds_threshold: Minimum dwell time to trigger (default: 30s)
        
    Returns:
        True if track is loitering in zone
    """
    # Must be currently in the zone
    if not track.is_in_zone(zone_id):
        return False
    
    # Check dwell time
    dwell_time = track.dwell_time_in_zone(zone_id)
    return dwell_time >= dwell_seconds_threshold


def object_left_unattended(
    track: TrackState,
    stationary_threshold_seconds: float = 60.0,
    person_classes: Optional[List[str]] = None
) -> bool:
    """
    Check if an object has been left unattended.
    
    Rule: Non-person object is stationary for > threshold seconds
    
    Simple heuristic:
    - Object must not be a person
    - Object must be stationary
    - Stationary duration > threshold
    
    Args:
        track: TrackState to check
        stationary_threshold_seconds: Minimum time stationary (default: 60s)
        person_classes: Classes considered "person" (default: ["person"])
        
    Returns:
        True if object left unattended
    """
    if person_classes is None:
        person_classes = ["person"]
    
    # Must not be a person
    if track.class_name in person_classes:
        return False
    
    # Must be stationary
    if not track.is_stationary:
        return False
    
    # Must be stationary for long enough
    return track.stationary_duration_seconds >= stationary_threshold_seconds


def rapid_movement(
    track: TrackState,
    speed_threshold_pixels_per_second: float = 100.0,
    frame_window: int = 10
) -> bool:
    """
    Check if track is moving rapidly.
    
    Rule: Average displacement over recent frames exceeds threshold
    
    Args:
        track: TrackState to check
        speed_threshold_pixels_per_second: Speed threshold
        frame_window: Number of recent frames to analyze
        
    Returns:
        True if track is moving rapidly
    """
    if len(track.displacement_history) < frame_window:
        return False
    
    # Get recent displacements
    recent_displacements = list(track.displacement_history)[-frame_window:]
    avg_displacement_per_frame = sum(recent_displacements) / len(recent_displacements)
    
    # Assuming 30 FPS (adjust if needed)
    fps = 30.0
    speed = avg_displacement_per_frame * fps
    
    return speed >= speed_threshold_pixels_per_second


def multiple_tracks_in_zone(
    tracks: Dict[int, TrackState],
    zone_id: str,
    min_count: int = 3,
    class_filter: Optional[List[str]] = None
) -> bool:
    """
    Check if multiple tracks are in a zone.
    
    Rule: Count of tracks in zone >= threshold
    
    Useful for:
    - Crowd formation
    - Multiple people in restricted area
    
    Args:
        tracks: Dict of all active tracks
        zone_id: Zone ID to check
        min_count: Minimum number of tracks to trigger
        class_filter: Optional list of classes to count (e.g., ["person"])
        
    Returns:
        True if enough tracks in zone
    """
    count = 0
    for track in tracks.values():
        if not track.is_in_zone(zone_id):
            continue
        
        if class_filter and track.class_name not in class_filter:
            continue
        
        count += 1
    
    return count >= min_count


def zone_violation_duration(
    track: TrackState,
    zone_id: str,
    min_duration_seconds: float = 5.0
) -> bool:
    """
    Check if track has been in zone for minimum duration.
    
    Similar to loitering but with lower threshold for immediate violations.
    
    Args:
        track: TrackState to check
        zone_id: Zone ID to check
        min_duration_seconds: Minimum duration (default: 5s)
        
    Returns:
        True if track has been in zone long enough
    """
    if not track.is_in_zone(zone_id):
        return False
    
    dwell_time = track.dwell_time_in_zone(zone_id)
    return dwell_time >= min_duration_seconds


class RuleEvaluator:
    """
    Evaluates multiple rules on tracks to determine incident triggers.
    
    Usage:
        evaluator = RuleEvaluator(zones_config, rules_config)
        incidents = evaluator.evaluate(tracker.get_active_tracks())
    """
    
    def __init__(
        self,
        zones_config: List[Dict],
        rules_config: Optional[Dict] = None
    ):
        """
        Initialize rule evaluator.
        
        Args:
            zones_config: Zone configurations
            rules_config: Rule thresholds (or use defaults)
        """
        self.zones_config = zones_config
        self.rules_config = rules_config or self._default_rules_config()
    
    def _default_rules_config(self) -> Dict:
        """Default rule thresholds"""
        return {
            "loitering_threshold_seconds": 30.0,
            "unattended_threshold_seconds": 60.0,
            "rapid_movement_threshold_pps": 100.0,
            "crowd_threshold": 3,
            "zone_violation_duration_seconds": 5.0
        }
    
    def evaluate(
        self,
        tracks: Dict[int, TrackState]
    ) -> Dict[int, List[str]]:
        """
        Evaluate all rules on all tracks.
        
        Args:
            tracks: Active tracks from tracker
            
        Returns:
            Dict of track_id -> list of triggered rule names
        """
        results = {}
        
        for track_id, track in tracks.items():
            triggered_rules = []
            
            # Check restricted zone entry
            if restricted_zone_entry(track, self.zones_config):
                triggered_rules.append("restricted_zone_entry")
            
            # Check loitering in each zone
            for zone_id in track.current_zones:
                if loitering(
                    track,
                    zone_id,
                    self.rules_config["loitering_threshold_seconds"]
                ):
                    triggered_rules.append(f"loitering_in_{zone_id}")
            
            # Check object left unattended
            if object_left_unattended(
                track,
                self.rules_config["unattended_threshold_seconds"]
            ):
                triggered_rules.append("object_left_unattended")
            
            # Check rapid movement
            if rapid_movement(
                track,
                self.rules_config["rapid_movement_threshold_pps"]
            ):
                triggered_rules.append("rapid_movement")
            
            if triggered_rules:
                results[track_id] = triggered_rules
        
        # Check crowd formation in each zone
        for zone in self.zones_config:
            zone_id = zone["id"]
            if multiple_tracks_in_zone(
                tracks,
                zone_id,
                self.rules_config["crowd_threshold"],
                class_filter=["person"]
            ):
                # Add to all tracks in zone
                for track_id, track in tracks.items():
                    if track.is_in_zone(zone_id):
                        if track_id not in results:
                            results[track_id] = []
                        results[track_id].append(f"crowd_formation_in_{zone_id}")
        
        return results
    
    def get_incident_reason(
        self,
        track: TrackState,
        triggered_rules: List[str]
    ) -> str:
        """
        Generate human-readable incident reason from triggered rules.
        
        Args:
            track: TrackState
            triggered_rules: List of rule names that triggered
            
        Returns:
            Formatted reason string
        """
        reasons = []
        
        for rule in triggered_rules:
            if rule == "restricted_zone_entry":
                zones = ", ".join(track.current_zones)
                reasons.append(f"{track.class_name} in restricted zone ({zones})")
            
            elif rule.startswith("loitering_in_"):
                zone_id = rule.replace("loitering_in_", "")
                dwell = track.dwell_time_in_zone(zone_id)
                reasons.append(f"{track.class_name} loitering in {zone_id} for {dwell:.0f}s")
            
            elif rule == "object_left_unattended":
                duration = track.stationary_duration_seconds
                reasons.append(f"{track.class_name} left unattended for {duration:.0f}s")
            
            elif rule == "rapid_movement":
                reasons.append(f"{track.class_name} moving rapidly")
            
            elif rule.startswith("crowd_formation_in_"):
                zone_id = rule.replace("crowd_formation_in_", "")
                reasons.append(f"Part of crowd in {zone_id}")
        
        return "; ".join(reasons) if reasons else f"{track.class_name} detected"
