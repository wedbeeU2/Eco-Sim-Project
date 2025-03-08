from abc import ABC, abstractmethod
import uuid
from enum import Enum
import math
import random

class Gender(Enum):
    MALE = 1
    FEMALE = 2

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def distance_to(self, other_position):
        return math.sqrt((self.x - other_position.x)**2 + (self.y - other_position.y)**2)
    
    def move_towards(self, target_position, speed):
        """Move current position towards target position based on speed"""
        dist = self.distance_to(target_position)
        if dist <= speed:
            self.x = target_position.x
            self.y = target_position.y
        else:
            ratio = speed / dist
            self.x += (target_position.x - self.x) * ratio
            self.y += (target_position.y - self.y) * ratio
    
    def move_random(self, speed):
        """Move in a random direction with the given speed"""
        angle = random.uniform(0, 2 * math.pi)
        self.x += math.cos(angle) * speed
        self.y += math.sin(angle) * speed

class EntityAttributes:
    """Holds species-specific attributes"""
    def __init__(self, max_energy, energy_consumption, speed, interaction_range, maturity_age):
        self.max_energy = max_energy
        self.energy_consumption = energy_consumption
        self.speed = speed
        self.interaction_range = interaction_range
        self.maturity_age = maturity_age

class Entity(ABC):
    """Abstract base class for all entities in the ecosystem"""
    
    def __init__(self, position, gender=None, energy=None, age=0, health=100):
        self._id = uuid.uuid4()
        self._position = position
        self._gender = gender if gender else random.choice(list(Gender))
        self._energy = energy if energy is not None else self.attributes.max_energy
        self._age = age
        self._health = health
        self._is_alive = True
        
    @property
    def id(self):
        """Get the entity's unique identifier"""
        return self._id
        
    @property
    def position(self):
        """Get the entity's position"""
        return self._position
        
    @position.setter
    def position(self, value):
        """Set the entity's position"""
        self._position = value
        
    @property
    def gender(self):
        """Get the entity's gender"""
        return self._gender
        
    @property
    def energy(self):
        """Get the entity's current energy level"""
        return self._energy
        
    @energy.setter
    def energy(self, value):
        """Set the entity's energy level, ensuring it stays within valid range"""
        self._energy = max(0, min(value, self.attributes.max_energy))
        
    @property
    def age(self):
        """Get the entity's age"""
        return self._age
        
    @age.setter
    def age(self, value):
        """Set the entity's age"""
        self._age = max(0, value)
        
    @property
    def health(self):
        """Get the entity's health"""
        return self._health
        
    @health.setter
    def health(self, value):
        """Set the entity's health, ensuring it stays within valid range"""
        self._health = max(0, min(value, 100))
        # Update alive status if health reaches zero
        if self._health <= 0:
            self._is_alive = False
            
    @property
    def is_alive(self):
        """Check if the entity is alive"""
        return self._is_alive
        
    @is_alive.setter
    def is_alive(self, value):
        """Set whether the entity is alive"""
        self._is_alive = value
    
    @property
    @abstractmethod
    def attributes(self):
        """Return the entity's attributes"""
        pass
    
    @abstractmethod
    def update(self, world, time_delta):
        """Update the entity's state"""
        from src.utils.exceptions import validate_positive, EntityError, safe_operation
        
        try:
            # Validate input parameters
            validate_positive(time_delta, "time_delta")
            
            # Base implementation for common behaviors
            self._age += time_delta
            self._energy -= self.attributes.energy_consumption * time_delta
            
            # Check vital signs
            if self._energy <= 0 or self._health <= 0:
                self._is_alive = False
                
            # Enforce world boundaries
            safe_operation(
                lambda: world.enforce_boundaries(self),
                f"Error enforcing world boundaries for entity {self.id}",
                log_error=True
            )
            
        except Exception as e:
            # Handle unexpected errors
            raise EntityError(f"Failed to update entity: {str(e)}", entity=self)
    
    @abstractmethod
    def interact(self, other, world):
        """Interact with another entity"""
        pass
    
    def move(self, target_position=None):
        """Move the entity"""
        if target_position:
            self.position.move_towards(target_position, self.attributes.speed)
        else:
            self.position.move_random(self.attributes.speed)
    
    def is_mature(self):
        """Check if the entity is mature enough to reproduce"""
        return self.age >= self.attributes.maturity_age
    
    def can_interact_with(self, other):
        """Check if this entity can interact with the other entity"""
        return self.position.distance_to(other.position) <= self.attributes.interaction_range