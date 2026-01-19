"""
24/7 Training Data Collection Agent

Automatically collects security-relevant data from camera footage
to continuously improve OpenAI Vision model for security applications.
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from collections import Counter
import hashlib

# Storage paths
TRAINING_AGENT_DATA = Path("alibi/data/training_agent.jsonl")
SECURITY_PATTERNS_DATA = Path("alibi/data/security_patterns.json")
FINE_TUNING_HISTORY = Path("alibi/data/fine_tuning_history.jsonl")

# Ensure directories exist
TRAINING_AGENT_DATA.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class SecurityTrainingExample:
    """A training example focused on security applications"""
    example_id: str
    timestamp: str
    category: str  # "suspicious_activity", "safety_concern", "security_object", etc.
    scene_description: str
    objects_detected: List[str]
    activities: List[str]
    security_relevance: str  # Why this is relevant for security
    confidence_score: float
    image_hash: str
    metadata: Dict
    
    def to_openai_format(self) -> Dict:
        """Convert to OpenAI fine-tuning format"""
        return {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a security-focused AI vision system. Analyze footage for safety concerns, suspicious activities, and security-relevant events. Provide clear, actionable descriptions suitable for security personnel."
                },
                {
                    "role": "user",
                    "content": f"Analyze this security camera footage. Focus on: safety concerns, suspicious behavior, unauthorized access, unusual objects, potential threats."
                },
                {
                    "role": "assistant",
                    "content": f"{self.scene_description}\n\nSecurity Assessment: {self.security_relevance}"
                }
            ],
            "metadata": {
                "category": self.category,
                "confidence": self.confidence_score,
                "timestamp": self.timestamp
            }
        }


@dataclass
class FineTuningJob:
    """Record of a fine-tuning job"""
    job_id: str
    created_at: str
    status: str  # "pending", "running", "completed", "failed"
    model_name: str  # "gpt-4-vision-2024-01-turbo-ft:custom-001"
    base_model: str  # "gpt-4-vision-preview"
    training_examples: int
    version: str  # "v1", "v2", etc.
    improvements: List[str]  # What this version improved
    performance_metrics: Dict  # Accuracy, loss, etc.
    deployed: bool
    notes: str


class TrainingDataCollectionAgent:
    """
    24/7 agent that automatically collects training data
    focused on security applications
    """
    
    def __init__(self):
        self.running = False
        self.security_categories = {
            "suspicious_activity": {
                "keywords": ["loitering", "running", "fighting", "climbing", "breaking"],
                "min_confidence": 0.7
            },
            "safety_concern": {
                "keywords": ["fire", "smoke", "weapon", "injury", "fall", "accident"],
                "min_confidence": 0.8
            },
            "unauthorized_access": {
                "keywords": ["fence", "door", "window", "gate", "barrier", "climbing"],
                "min_confidence": 0.7
            },
            "security_object": {
                "keywords": ["bag", "package", "vehicle", "person", "weapon", "tool"],
                "min_confidence": 0.6
            },
            "crowd_behavior": {
                "keywords": ["crowd", "gathering", "group", "running", "panic"],
                "min_confidence": 0.7
            }
        }
        
    def should_collect(self, analysis: Dict) -> tuple[bool, str, str]:
        """
        Determine if an analysis should be collected for training.
        
        Returns: (should_collect, category, reason)
        """
        description = analysis.get("description", "").lower()
        safety_concerns = analysis.get("safety_concerns", [])
        objects = analysis.get("objects", [])
        activities = analysis.get("activities", [])
        
        # High priority: Safety concerns
        if safety_concerns:
            return True, "safety_concern", f"Safety concern detected: {', '.join(safety_concerns)}"
        
        # Check each category
        for category, config in self.security_categories.items():
            keywords = config["keywords"]
            
            # Check if any keyword matches
            for keyword in keywords:
                if keyword in description or \
                   any(keyword in str(obj).lower() for obj in objects) or \
                   any(keyword in str(act).lower() for act in activities):
                    
                    confidence = analysis.get("confidence", 0.5)
                    if confidence >= config["min_confidence"]:
                        reason = f"Matched security pattern: {keyword} (category: {category})"
                        return True, category, reason
        
        # Collect diverse examples (10% of normal footage for baseline)
        import random
        if random.random() < 0.1:
            return True, "baseline", "Diversity sample for context"
        
        return False, "", ""
    
    def collect_example(self, analysis: Dict, category: str, reason: str) -> SecurityTrainingExample:
        """Create a training example from an analysis"""
        
        # Generate unique ID
        content = f"{analysis.get('timestamp')}_{analysis.get('description')}"
        example_id = hashlib.md5(content.encode()).hexdigest()[:12]
        
        # Create security-focused training example
        example = SecurityTrainingExample(
            example_id=example_id,
            timestamp=analysis.get("timestamp", datetime.utcnow().isoformat()),
            category=category,
            scene_description=analysis.get("description", ""),
            objects_detected=analysis.get("objects", []),
            activities=analysis.get("activities", []),
            security_relevance=reason,
            confidence_score=analysis.get("confidence", 0.5),
            image_hash=analysis.get("image_hash", ""),
            metadata={
                "safety_concerns": analysis.get("safety_concerns", []),
                "analysis_duration_ms": analysis.get("analysis_duration_ms", 0)
            }
        )
        
        return example
    
    def save_example(self, example: SecurityTrainingExample):
        """Save training example to storage"""
        with open(TRAINING_AGENT_DATA, 'a') as f:
            f.write(json.dumps(asdict(example)) + "\n")
    
    def load_examples(self, min_confidence: float = 0.0) -> List[SecurityTrainingExample]:
        """Load all collected examples"""
        if not TRAINING_AGENT_DATA.exists():
            return []
        
        examples = []
        with open(TRAINING_AGENT_DATA, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("confidence_score", 0) >= min_confidence:
                        examples.append(SecurityTrainingExample(**data))
                except:
                    continue
        
        return examples
    
    def _save_example(self, example: SecurityTrainingExample):
        """Save a single example to storage"""
        with open(TRAINING_AGENT_DATA, 'a') as f:
            f.write(json.dumps(asdict(example)) + '\n')
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about collected training data"""
        examples = self.load_examples()
        
        if not examples:
            return {
                "total_examples": 0,
                "by_category": {},
                "avg_confidence": 0,
                "date_range": {"start": None, "end": None},
                "ready_for_training": False
            }
        
        # Calculate stats
        categories = Counter(ex.category for ex in examples)
        confidences = [ex.confidence_score for ex in examples]
        timestamps = [ex.timestamp for ex in examples]
        
        return {
            "total_examples": len(examples),
            "by_category": dict(categories),
            "avg_confidence": sum(confidences) / len(confidences),
            "date_range": {
                "start": min(timestamps),
                "end": max(timestamps)
            },
            "ready_for_training": len(examples) >= 50,
            "high_confidence_examples": len([ex for ex in examples if ex.confidence_score >= 0.8])
        }
    
    def export_training_dataset(self, output_path: Optional[Path] = None, min_confidence: float = 0.7) -> Dict:
        """
        Export collected data as OpenAI fine-tuning dataset
        
        Args:
            output_path: Where to save the dataset
            min_confidence: Minimum confidence score to include
            
        Returns:
            Dict with export info
        """
        if output_path is None:
            output_path = Path("alibi/data/security_training_dataset.jsonl")
        
        examples = self.load_examples(min_confidence=min_confidence)
        
        if not examples:
            return {
                "success": False,
                "error": "No examples collected yet",
                "examples_exported": 0
            }
        
        if len(examples) < 50:
            return {
                "success": False,
                "error": f"Need at least 50 examples, only have {len(examples)}",
                "examples_exported": 0
            }
        
        # Convert to OpenAI format
        with open(output_path, 'w') as f:
            for example in examples:
                f.write(json.dumps(example.to_openai_format()) + "\n")
        
        # Calculate category distribution
        categories = Counter(ex.category for ex in examples)
        
        return {
            "success": True,
            "dataset_file": str(output_path),
            "examples_exported": len(examples),
            "by_category": dict(categories),
            "avg_confidence": sum(ex.confidence_score for ex in examples) / len(examples),
            "ready_for_openai": True
        }


class FineTuningHistoryManager:
    """Manages fine-tuning job history and versions"""
    
    def __init__(self):
        self.history_file = FINE_TUNING_HISTORY
    
    def record_job(self, job: FineTuningJob):
        """Record a new fine-tuning job"""
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(asdict(job)) + "\n")
    
    def get_history(self) -> List[FineTuningJob]:
        """Get all fine-tuning jobs"""
        if not self.history_file.exists():
            return []
        
        jobs = []
        with open(self.history_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    jobs.append(FineTuningJob(**data))
                except:
                    continue
        
        return sorted(jobs, key=lambda x: x.created_at, reverse=True)
    
    def get_deployed_version(self) -> Optional[FineTuningJob]:
        """Get currently deployed model version"""
        jobs = self.get_history()
        deployed = [job for job in jobs if job.deployed]
        return deployed[0] if deployed else None
    
    def get_latest_version(self) -> str:
        """Get next version number"""
        jobs = self.get_history()
        if not jobs:
            return "v1"
        
        versions = [int(job.version.replace('v', '')) for job in jobs if job.version.startswith('v')]
        next_version = max(versions) + 1 if versions else 1
        return f"v{next_version}"
    
    def mark_deployed(self, job_id: str):
        """Mark a job as deployed and unmark others"""
        jobs = self.get_history()
        
        # Rewrite history with updated deployment status
        with open(self.history_file, 'w') as f:
            for job in jobs:
                if job.job_id == job_id:
                    job.deployed = True
                else:
                    job.deployed = False
                f.write(json.dumps(asdict(job)) + "\n")


# Global agent instance
_agent = TrainingDataCollectionAgent()
_history_manager = FineTuningHistoryManager()


def get_training_agent() -> TrainingDataCollectionAgent:
    """Get the global training agent"""
    return _agent


def get_history_manager() -> FineTuningHistoryManager:
    """Get the fine-tuning history manager"""
    return _history_manager


async def run_collection_agent():
    """
    Background task that monitors camera analyses and collects training data.
    This should be run as a FastAPI background task or separate process.
    """
    from alibi.camera_analysis_store import CameraAnalysisStore
    
    agent = get_training_agent()
    store = CameraAnalysisStore()
    
    print("🤖 Training Data Collection Agent started")
    print("   Monitoring camera analyses for security-relevant patterns...")
    
    last_check = datetime.utcnow()
    seen_hashes: Set[str] = set()
    
    while True:
        try:
            # Get new analyses since last check
            analyses = store.get_recent_analyses(since_ts=last_check, limit=100)
            
            for analysis in analyses:
                image_hash = analysis.get("image_hash", "")
                
                # Skip if already processed
                if image_hash in seen_hashes:
                    continue
                
                seen_hashes.add(image_hash)
                
                # Check if should collect
                should_collect, category, reason = agent.should_collect(analysis)
                
                if should_collect:
                    example = agent.collect_example(analysis, category, reason)
                    agent.save_example(example)
                    print(f"   📊 Collected: {category} - {reason[:50]}")
            
            last_check = datetime.utcnow()
            
            # Clean old seen hashes (keep last 1000)
            if len(seen_hashes) > 1000:
                seen_hashes.clear()
            
            # Sleep for 30 seconds
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"   ⚠️  Collection agent error: {e}")
            await asyncio.sleep(60)
