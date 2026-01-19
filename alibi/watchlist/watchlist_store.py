"""
Watchlist Store

JSONL storage for City Police wanted list.
Stores person_id, label, embeddings, and metadata.
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class WatchlistEntry:
    """Entry in the watchlist"""
    person_id: str
    label: str  # Name/alias (for operator reference only)
    embedding: List[float]  # Face embedding vector
    added_ts: str  # ISO timestamp
    source_ref: str  # Reference to source document/case
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return {
            "person_id": self.person_id,
            "label": self.label,
            "embedding": self.embedding,
            "added_ts": self.added_ts,
            "source_ref": self.source_ref,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WatchlistEntry':
        """Create from dictionary"""
        return cls(
            person_id=data["person_id"],
            label=data["label"],
            embedding=data["embedding"],
            added_ts=data["added_ts"],
            source_ref=data["source_ref"],
            metadata=data.get("metadata", {})
        )
    
    def get_embedding_array(self) -> np.ndarray:
        """Get embedding as numpy array"""
        return np.array(self.embedding, dtype=np.float32)


class WatchlistStore:
    """
    JSONL-based storage for watchlist entries.
    
    Append-only for audit trail.
    """
    
    def __init__(self, storage_path: str = "alibi/data/watchlist.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file if it doesn't exist
        if not self.storage_path.exists():
            self.storage_path.touch()
            print(f"[WatchlistStore] Created new watchlist file: {self.storage_path}")
    
    def add_entry(self, entry: WatchlistEntry) -> None:
        """
        Add entry to watchlist.
        
        Args:
            entry: WatchlistEntry to add
        """
        with open(self.storage_path, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')
        
        print(f"[WatchlistStore] Added entry: {entry.person_id} - {entry.label}")
    
    def load_all(self) -> List[WatchlistEntry]:
        """
        Load all watchlist entries.
        
        Returns:
            List of WatchlistEntry objects
        """
        entries = []
        
        if not self.storage_path.exists():
            return entries
        
        with open(self.storage_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    entries.append(WatchlistEntry.from_dict(data))
                except Exception as e:
                    print(f"[WatchlistStore] Error loading entry: {e}")
        
        return entries
    
    def get_by_person_id(self, person_id: str) -> Optional[WatchlistEntry]:
        """
        Get entry by person_id (returns most recent if multiple).
        
        Args:
            person_id: Person ID to search for
            
        Returns:
            WatchlistEntry or None
        """
        entries = self.load_all()
        
        # Return most recent entry with matching person_id
        for entry in reversed(entries):
            if entry.person_id == person_id:
                return entry
        
        return None
    
    def get_all_embeddings(self) -> Dict[str, np.ndarray]:
        """
        Get all embeddings as dictionary.
        
        Returns:
            Dict mapping person_id to embedding array
        """
        entries = self.load_all()
        
        # Use most recent entry for each person_id
        embeddings = {}
        for entry in entries:
            embeddings[entry.person_id] = entry.get_embedding_array()
        
        return embeddings
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """
        Get all entries without embeddings (for API responses).
        
        Returns:
            List of entry metadata (no embeddings)
        """
        entries = self.load_all()
        
        metadata_list = []
        for entry in entries:
            metadata_list.append({
                "person_id": entry.person_id,
                "label": entry.label,
                "added_ts": entry.added_ts,
                "source_ref": entry.source_ref,
                "metadata": entry.metadata
            })
        
        return metadata_list
    
    def count(self) -> int:
        """Get total number of entries"""
        return len(self.load_all())
