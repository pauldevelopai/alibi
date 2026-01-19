"""
Simulator Manager

Manages running simulator instances and event generation.
"""

import asyncio
import json
from typing import Optional, Dict, Any
from datetime import datetime

from alibi.sim.event_simulator import EventSimulator, Scenario, SimulatorConfig


class SimulatorManager:
    """
    Manages event simulator lifecycle.
    
    Singleton pattern - only one simulator runs at a time.
    """
    
    def __init__(self):
        self.simulator: Optional[EventSimulator] = None
        self.task: Optional[asyncio.Task] = None
        self.is_running = False
        self.incidents_created = 0
        self.event_callback = None
    
    async def start(
        self,
        scenario: Scenario,
        rate_per_min: float,
        seed: Optional[int] = None,
        event_callback = None
    ):
        """
        Start simulator.
        
        Args:
            scenario: Scenario preset
            rate_per_min: Events per minute
            seed: Random seed for determinism
            event_callback: Async function to call with each generated event
        """
        if self.is_running:
            raise ValueError("Simulator already running")
        
        config = SimulatorConfig(
            scenario=scenario,
            rate_per_min=rate_per_min,
            seed=seed
        )
        
        self.simulator = EventSimulator(config)
        self.event_callback = event_callback
        self.is_running = True
        self.incidents_created = 0
        
        # Start generation task
        self.task = asyncio.create_task(self._generation_loop())
    
    async def stop(self):
        """Stop simulator"""
        self.is_running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        
        self.simulator = None
        self.event_callback = None
    
    async def _generation_loop(self):
        """Generate events at specified rate"""
        if not self.simulator:
            return
        
        interval = 60.0 / self.simulator.config.rate_per_min
        
        try:
            while self.is_running:
                # Generate event
                event = self.simulator.generate_event()
                
                # Validate
                is_valid, error = self.simulator.validate_event(event)
                
                if not is_valid:
                    print(f"[Simulator] Invalid event generated: {error}")
                    print(f"[Simulator] Event: {json.dumps(event, indent=2)}")
                    # Do NOT silently fix - log and skip
                    await asyncio.sleep(interval)
                    continue
                
                # Call callback if provided
                if self.event_callback:
                    try:
                        result = await self.event_callback(event)
                        if result.get("incident_id"):
                            # Track unique incidents created
                            self.incidents_created += 1
                    except Exception as e:
                        print(f"[Simulator] Event callback failed: {e}")
                
                # Wait for next event
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            print("[Simulator] Generation loop cancelled")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current simulator status"""
        if not self.is_running or not self.simulator:
            return {
                "running": False,
                "events_generated": 0,
                "incidents_created": 0,
            }
        
        stats = self.simulator.get_stats()
        
        return {
            "running": True,
            "events_generated": stats["events_generated"],
            "incidents_created": self.incidents_created,
            "rate_actual": stats["rate_actual"],
            "rate_target": stats["rate_target"],
            "scenario": stats["scenario"],
            "seed": stats["seed"],
            "elapsed_seconds": stats["elapsed_seconds"],
        }


# Global singleton instance
_manager_instance = None


def get_simulator_manager() -> SimulatorManager:
    """Get or create global simulator manager"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SimulatorManager()
    return _manager_instance
