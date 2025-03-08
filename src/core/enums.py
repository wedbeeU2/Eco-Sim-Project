"""
Enumeration types used throughout the ecosystem simulation.
"""
from enum import Enum, auto


class Gender(Enum):
    """Gender enumeration for entities"""
    MALE = auto()
    FEMALE = auto()


class EntityType(Enum):
    """Entity type enumeration"""
    PREDATOR = auto()
    PREY = auto()
    INVASIVE = auto()


class BehaviorType(Enum):
    """Behavior type enumeration"""
    HUNT = auto()
    FLEE = auto()
    FORAGE = auto()
    REPRODUCE = auto()
    COMPETE = auto()
    IDLE = auto()


class SeasonType(Enum):
    """Season type enumeration for environmental effects"""
    SPRING = auto()
    SUMMER = auto()
    FALL = auto()
    WINTER = auto()
