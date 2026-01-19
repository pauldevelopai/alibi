"""
Real Training Data Collection System
Scrapes and processes data from Hugging Face and the web
"""
from .huggingface_collector import HuggingFaceCollector, collect_training_data

__all__ = ['HuggingFaceCollector', 'collect_training_data']
