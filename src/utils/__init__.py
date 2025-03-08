"""
Utility functions and classes for the ecosystem simulation.
Includes error handling, configuration, and helper functions.
"""

from src.utils.exceptions import (
    SimulationError, EntityError, WorldError, 
    ValidationError, ErrorSeverity
)

__all__ = [
    'SimulationError', 'EntityError', 'WorldError', 
    'ValidationError', 'ErrorSeverity'
]