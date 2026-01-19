"""
Training Data Pipeline

Converts real camera incidents to training data for human review.
"""

from alibi.training.incident_converter import (
    IncidentToTrainingConverter,
    get_converter
)

__all__ = [
    "IncidentToTrainingConverter",
    "get_converter"
]
