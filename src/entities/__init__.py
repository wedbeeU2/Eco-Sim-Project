"""
Entity classes for the ecosystem simulation.
Provides specialized implementations of predators, prey, and invasive species.
"""

from src.entities.predator import Predator
from src.entities.prey import Prey
from src.entities.invasive_species import InvasiveSpecies

__all__ = ['Predator', 'Prey', 'InvasiveSpecies']