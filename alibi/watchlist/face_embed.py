"""
Face Embedding Generator

Generates face embeddings for matching.
Uses lightweight approach with available libraries.
"""

import cv2
import numpy as np
from typing import Optional, Tuple


class FaceEmbedder:
    """
    Face embedding generator.
    
    Uses a simple but effective approach:
    - Resize face to fixed size
    - Normalize
    - Flatten to create embedding vector
    
    For production, consider using:
    - face_recognition library (dlib-based)
    - DeepFace with lightweight models
    - ONNX models for face recognition
    """
    
    def __init__(
        self,
        embedding_size: int = 128,
        face_size: Tuple[int, int] = (96, 96)
    ):
        """
        Initialize embedder.
        
        Args:
            embedding_size: Size of embedding vector
            face_size: Size to resize faces to
        """
        self.embedding_size = embedding_size
        self.face_size = face_size
        
        # Check if face_recognition is available
        try:
            import face_recognition
            self.face_recognition = face_recognition
            self.method = "face_recognition"
            print("[FaceEmbedder] Using face_recognition library (dlib-based)")
        except ImportError:
            self.face_recognition = None
            self.method = "simple"
            print("[FaceEmbedder] Using simple embedding (install face_recognition for better accuracy)")
            print("[FaceEmbedder] Install with: pip install face-recognition")
    
    def generate_embedding(self, face_image: np.ndarray) -> np.ndarray:
        """
        Generate embedding for face image.
        
        Args:
            face_image: Face crop image (BGR format)
            
        Returns:
            Embedding vector (normalized)
        """
        if self.method == "face_recognition":
            return self._generate_with_face_recognition(face_image)
        else:
            return self._generate_simple(face_image)
    
    def _generate_with_face_recognition(self, face_image: np.ndarray) -> np.ndarray:
        """Generate embedding using face_recognition library"""
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        
        # Generate encoding (128-d vector)
        encodings = self.face_recognition.face_encodings(rgb_image)
        
        if len(encodings) == 0:
            # Fall back to simple method if no face detected
            print("[FaceEmbedder] Warning: No face detected by face_recognition, using simple method")
            return self._generate_simple(face_image)
        
        # Return first encoding
        embedding = encodings[0]
        
        # Normalize
        embedding = embedding / (np.linalg.norm(embedding) + 1e-7)
        
        return embedding.astype(np.float32)
    
    def _generate_simple(self, face_image: np.ndarray) -> np.ndarray:
        """
        Generate simple embedding (fallback method).
        
        This is a basic approach for when face_recognition is not available.
        Uses HOG (Histogram of Oriented Gradients) features.
        """
        # Resize to fixed size
        resized = cv2.resize(face_image, self.face_size)
        
        # Convert to grayscale
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization
        gray = cv2.equalizeHist(gray)
        
        # Calculate HOG features
        win_size = self.face_size
        block_size = (16, 16)
        block_stride = (8, 8)
        cell_size = (8, 8)
        nbins = 9
        
        hog = cv2.HOGDescriptor(
            win_size,
            block_size,
            block_stride,
            cell_size,
            nbins
        )
        
        features = hog.compute(gray)
        
        # Flatten and normalize
        embedding = features.flatten()
        
        # Reduce dimensionality if needed
        if len(embedding) > self.embedding_size:
            # Simple dimensionality reduction: average pooling
            factor = len(embedding) // self.embedding_size
            embedding = embedding[:self.embedding_size * factor].reshape(self.embedding_size, factor).mean(axis=1)
        elif len(embedding) < self.embedding_size:
            # Pad with zeros
            embedding = np.pad(embedding, (0, self.embedding_size - len(embedding)))
        
        # Normalize to unit length
        embedding = embedding / (np.linalg.norm(embedding) + 1e-7)
        
        return embedding.astype(np.float32)
