"""
Stop Line Crossing Detection

Detects when vehicles cross a defined stop line in a specific direction.
"""

import numpy as np
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass

from alibi.traffic.vehicle_detect import TrackedVehicle


@dataclass
class CrossingEvent:
    """A stop line crossing event"""
    vehicle_id: int
    crossing_timestamp: float
    centroid_at_crossing: Tuple[int, int]
    bbox_at_crossing: Tuple[int, int, int, int]
    direction: str  # "forward" or "backward" relative to stop line


class StopLineMonitor:
    """
    Monitors vehicles crossing a stop line.
    
    Uses line intersection detection to determine when a vehicle's
    trajectory crosses the stop line.
    """
    
    def __init__(
        self,
        stop_line: List[Tuple[int, int]],
        traffic_direction: str = "up"
    ):
        """
        Initialize stop line monitor.
        
        Args:
            stop_line: List of (x, y) points defining the stop line
            traffic_direction: Expected traffic direction ("up", "down", "left", "right")
        """
        self.stop_line = stop_line
        self.traffic_direction = traffic_direction
        
        # Track which vehicles have crossed
        self.crossed_vehicles: Set[int] = set()
        
        # Convert stop line to simple line for intersection testing
        # For now, use first two points or endpoints
        if len(stop_line) >= 2:
            self.line_start = stop_line[0]
            self.line_end = stop_line[-1]
        else:
            raise ValueError("Stop line must have at least 2 points")
    
    def check_crossings(
        self,
        vehicles: List[TrackedVehicle],
        timestamp: float
    ) -> List[CrossingEvent]:
        """
        Check if any vehicles have crossed the stop line.
        
        Args:
            vehicles: List of tracked vehicles
            timestamp: Current timestamp
            
        Returns:
            List of new crossing events
        """
        crossings = []
        
        for vehicle in vehicles:
            # Skip if already crossed
            if vehicle.vehicle_id in self.crossed_vehicles:
                continue
            
            # Need at least 2 points in trajectory
            if len(vehicle.trajectory) < 2:
                continue
            
            # Check if trajectory segment crosses stop line
            prev_point = vehicle.trajectory[-2]
            curr_point = vehicle.trajectory[-1]
            
            if self._segments_intersect(
                prev_point, curr_point,
                self.line_start, self.line_end
            ):
                # Determine direction
                direction = self._get_crossing_direction(prev_point, curr_point)
                
                # Only count as violation if crossing in expected traffic direction
                if self._is_expected_direction(direction):
                    crossing = CrossingEvent(
                        vehicle_id=vehicle.vehicle_id,
                        crossing_timestamp=timestamp,
                        centroid_at_crossing=curr_point,
                        bbox_at_crossing=vehicle.bbox,
                        direction=direction
                    )
                    
                    crossings.append(crossing)
                    self.crossed_vehicles.add(vehicle.vehicle_id)
        
        return crossings
    
    def _segments_intersect(
        self,
        p1: Tuple[int, int],
        p2: Tuple[int, int],
        p3: Tuple[int, int],
        p4: Tuple[int, int]
    ) -> bool:
        """
        Check if line segment p1-p2 intersects with line segment p3-p4.
        
        Uses cross product method.
        """
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)
    
    def _get_crossing_direction(
        self,
        prev_point: Tuple[int, int],
        curr_point: Tuple[int, int]
    ) -> str:
        """
        Determine direction of crossing relative to stop line.
        
        Returns "forward" or "backward" based on movement direction.
        """
        # Calculate movement vector
        dx = curr_point[0] - prev_point[0]
        dy = curr_point[1] - prev_point[1]
        
        # Determine primary movement direction
        if abs(dy) > abs(dx):
            # Primarily vertical movement
            if dy < 0:
                return "up"
            else:
                return "down"
        else:
            # Primarily horizontal movement
            if dx > 0:
                return "right"
            else:
                return "left"
    
    def _is_expected_direction(self, direction: str) -> bool:
        """
        Check if crossing direction matches expected traffic direction.
        
        Returns True if it's a violation (crossing in the direction
        where vehicles shouldn't be crossing on red).
        """
        # Simplification: for now, just check if it matches the configured direction
        return direction == self.traffic_direction
    
    def reset(self):
        """Reset crossing history"""
        self.crossed_vehicles.clear()
    
    def clear_vehicle(self, vehicle_id: int):
        """Clear a specific vehicle from crossing history"""
        self.crossed_vehicles.discard(vehicle_id)
