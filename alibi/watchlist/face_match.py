"""
Face Matching

Cosine similarity-based face matching against watchlist.
"""

import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class MatchCandidate:
    """A potential match from the watchlist"""
    person_id: str
    label: str
    score: float  # Cosine similarity (0-1)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "person_id": self.person_id,
            "label": self.label,
            "score": round(self.score, 4)
        }


class FaceMatcher:
    """
    Face matcher using cosine similarity.
    
    Compares face embeddings against watchlist embeddings.
    """
    
    def __init__(
        self,
        match_threshold: float = 0.6,
        top_k: int = 3
    ):
        """
        Initialize matcher.
        
        Args:
            match_threshold: Minimum similarity score to consider a match
            top_k: Number of top candidates to return
        """
        self.match_threshold = match_threshold
        self.top_k = top_k
    
    def cosine_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1, where 1 is identical)
        """
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        
        # Clip to [0, 1] range (sometimes numerical errors can cause values slightly outside)
        similarity = np.clip(similarity, 0.0, 1.0)
        
        return float(similarity)
    
    def match(
        self,
        query_embedding: np.ndarray,
        watchlist_embeddings: Dict[str, np.ndarray],
        watchlist_labels: Dict[str, str]
    ) -> Tuple[bool, List[MatchCandidate], float]:
        """
        Match query embedding against watchlist.
        
        Args:
            query_embedding: Embedding to match
            watchlist_embeddings: Dict of person_id -> embedding
            watchlist_labels: Dict of person_id -> label
            
        Returns:
            Tuple of (is_match, top_candidates, best_score)
        """
        if not watchlist_embeddings:
            return False, [], 0.0
        
        # Calculate similarities for all watchlist entries
        similarities = []
        
        for person_id, watchlist_embedding in watchlist_embeddings.items():
            similarity = self.cosine_similarity(query_embedding, watchlist_embedding)
            
            label = watchlist_labels.get(person_id, person_id)
            
            similarities.append(
                MatchCandidate(
                    person_id=person_id,
                    label=label,
                    score=similarity
                )
            )
        
        # Sort by score (descending)
        similarities.sort(key=lambda x: x.score, reverse=True)
        
        # Get top-k candidates
        top_candidates = similarities[:self.top_k]
        
        # Check if best match exceeds threshold
        best_score = top_candidates[0].score if top_candidates else 0.0
        is_match = best_score >= self.match_threshold
        
        return is_match, top_candidates, best_score
    
    def batch_match(
        self,
        query_embeddings: List[np.ndarray],
        watchlist_embeddings: Dict[str, np.ndarray],
        watchlist_labels: Dict[str, str]
    ) -> List[Tuple[bool, List[MatchCandidate], float]]:
        """
        Match multiple embeddings against watchlist.
        
        Args:
            query_embeddings: List of embeddings to match
            watchlist_embeddings: Dict of person_id -> embedding
            watchlist_labels: Dict of person_id -> label
            
        Returns:
            List of match results
        """
        results = []
        
        for embedding in query_embeddings:
            result = self.match(embedding, watchlist_embeddings, watchlist_labels)
            results.append(result)
        
        return results
