"""
Prey entity module for the ecosystem simulation.
"""
import random
from src.core.entity import Entity
from src.core.enums import Gender
from src.core.attributes import PreyAttributes
from src.utils.exceptions import validate_type, EntityError, safe_operation


class Prey(Entity):
    """
    Prey entity in the ecosystem.
    Forages for resources, flees from predators, and reproduces with other prey.
    """
    
    # Class-level attributes shared by all prey
    _attributes = PreyAttributes()
    
    @property
    def attributes(self):
        """Return the entity's attributes"""
        return Prey._attributes
    
    def __init__(self, position, gender=None, energy=None, age=0, health=100):
        """
        Initialize a prey entity.
        
        Args:
            position (Position): The initial position
            gender (Gender, optional): The gender (random if None)
            energy (float, optional): Initial energy level (max if None)
            age (float, optional): Initial age in days (default: 0)
            health (float, optional): Initial health (default: 100)
        """
        super().__init__(position, gender, energy, age, health)
        self._time_since_last_reproduction = 0
        self._foraging_cooldown = 0
    
    @property
    def time_since_last_reproduction(self):
        """Get time since last reproduction"""
        return self._time_since_last_reproduction
    
    @time_since_last_reproduction.setter
    def time_since_last_reproduction(self, value):
        """Set time since last reproduction"""
        self._time_since_last_reproduction = max(0, value)
    
    @property
    def foraging_cooldown(self):
        """Get the foraging cooldown timer"""
        return self._foraging_cooldown
    
    @foraging_cooldown.setter
    def foraging_cooldown(self, value):
        """Set the foraging cooldown timer"""
        self._foraging_cooldown = max(0, value)
    
    def update(self, world, time_delta):
        """
        Update the prey's state.
        
        Args:
            world (World): The world environment
            time_delta (float): Time elapsed since last update
            
        Returns:
            bool: True if update was successful
        """
        # Update base entity state
        super().update(world, time_delta)
        
        if not self.is_alive:
            return False
        
        # Update reproduction timer
        self._time_since_last_reproduction += time_delta
        
        # Update foraging cooldown
        if self._foraging_cooldown > 0:
            self._foraging_cooldown = max(0, self._foraging_cooldown - time_delta)
        
        # Use behavior system if available
        behavior_system = getattr(self, '_behavior_system', None)
        if behavior_system is not None:
            return behavior_system.update(world)
        
        # Basic behavior when no behavior system is attached
        return self._basic_behavior(world)
    
    def _basic_behavior(self, world):
        """
        Execute basic prey behavior when no behavior system is available.
        
        Args:
            world (World): The world environment
            
        Returns:
            bool: True if behavior execution was successful
        """
        try:
            # Check for nearby predators
            from src.entities.predator import Predator
            predators_nearby = [
                entity for entity in world.get_entities_in_range(
                    self.position, self.attributes.perception_range
                )
                if isinstance(entity, Predator) and entity.is_alive
            ]
            
            if predators_nearby:
                # Flee from the closest predator
                closest_predator = min(
                    predators_nearby,
                    key=lambda p: self.position.distance_to(p.position)
                )
                return self.flee(closest_predator)
            else:
                # No immediate danger, focus on other activities
                
                # Forage if hungry
                if self.energy < 0.7 * self.attributes.max_energy and self._foraging_cooldown <= 0:
                    return self.forage(world)
                
                # Try to reproduce if it's time
                elif self.can_reproduce():
                    # Find potential mates
                    potential_mates = [
                        entity for entity in world.get_entities_in_range(
                            self.position, self.attributes.interaction_range
                        )
                        if isinstance(entity, Prey) 
                        and entity.is_alive 
                        and entity.gender != self.gender
                        and entity.can_reproduce()
                    ]
                    
                    if potential_mates:
                        # Reproduce with a random mate
                        return bool(self.reproduce(random.choice(potential_mates), world))
                    else:
                        # Move randomly looking for mates
                        self.move()
                else:
                    # Move randomly
                    self.move()
            
            return True
        except Exception as e:
            # Log error and continue
            from src.utils.exceptions import logger
            logger.error(f"Error in prey basic behavior: {e}")
            return False
    
    def flee(self, predator):
        """
        Flee from a predator.
        
        Args:
            predator: The predator to flee from
            
        Returns:
            bool: True if fleeing was successful
            
        Raises:
            EntityError: If fleeing fails
        """
        try:
            validate_type(predator, "predator", object)  # Just check it's an object
            
            # Calculate direction away from predator
            flee_x = self.position.x + (self.position.x - predator.position.x)
            flee_y = self.position.y + (self.position.y - predator.position.y)
            
            from src.core.position import Position
            flee_position = Position(flee_x, flee_y)
            
            # Move away at maximum speed
            self.move(flee_position)
            
            # Energy cost for fleeing (higher than normal movement)
            energy_cost = 0.4 * self.attributes.energy_consumption
            self.energy -= energy_cost
            
            return True
        except Exception as e:
            raise EntityError(f"Fleeing failed: {str(e)}", entity=self)
    
    def forage(self, world):
        """
        Forage for food in the environment.
        
        Args:
            world: The world environment
            
        Returns:
            bool: True if foraging was successful
            
        Raises:
            EntityError: If foraging fails
        """
        try:
            # Apply foraging cooldown
            self._foraging_cooldown = 3.0  # 3 seconds cooldown
            
            # Simple implementation - prey gains energy from the environment
            energy_gained = self.attributes.foraging_efficiency * random.uniform(0.5, 1.0)
            self.energy = min(self.attributes.max_energy, self.energy + energy_gained)
            
            # Move while foraging
            self.move()
            
            return True
        except Exception as e:
            raise EntityError(f"Foraging failed: {str(e)}", entity=self)
    
    def interact(self, other, world):
        """
        Interact with another entity.
        
        Args:
            other: The entity to interact with
            world: The world environment
            
        Returns:
            bool: True if interaction was successful
        """
        try:
            # Basic implementation - more complex interactions could be added
            if not self.can_interact_with(other):
                return False
            
            # Different interaction based on entity type
            from src.entities.predator import Predator
            if isinstance(other, Predator) and other.is_alive:
                return self.flee(other)
            
            return False
        except Exception as e:
            # Log error and continue
            return False
    
    def can_reproduce(self):
        """
        Check if the prey can reproduce.
        
        Returns:
            bool: True if reproduction is possible
        """
        return (
            self.is_mature() and
            self._time_since_last_reproduction >= self.attributes.breeding_cycle and
            self.energy > 0.6 * self.attributes.max_energy and
            self.health > 50
        )
    
    def reproduce(self, partner, world):
        """
        Reproduce with another prey.
        
        Args:
            partner: The partner prey
            world: The world environment
            
        Returns:
            list: List of offspring entities
            
        Raises:
            EntityError: If reproduction fails
        """
        try:
            validate_type(partner, "partner", Prey)
            
            if not (self.can_reproduce() and partner.can_reproduce()):
                return []
            
            # Reset reproduction timers
            self._time_since_last_reproduction = 0
            partner.time_since_last_reproduction = 0
            
            # Energy cost for reproduction
            reproduction_cost = 0.3 * self.attributes.max_energy
            self.energy -= reproduction_cost
            partner.energy -= reproduction_cost
            
            # Generate offspring
            num_offspring = random.randint(
                self.attributes.min_offspring, 
                self.attributes.max_offspring
            )
            
            offspring = []
            for _ in range(num_offspring):
                # Create a new prey at a position near the parents
                from src.core.position import Position
                offspring_position = Position(
                    self.position.x + random.uniform(-10, 10),
                    self.position.y + random.uniform(-10, 10)
                )
                
                # Apply random gender
                offspring_gender = random.choice(list(Gender))
                
                new_prey = Prey(
                    position=offspring_position,
                    gender=offspring_gender,
                    energy=0.5 * self.attributes.max_energy,
                    age=0
                )
                
                offspring.append(new_prey)
                
                # Add to world safely
                safe_operation(
                    lambda: world.add_entity(new_prey),
                    f"Failed to add offspring {new_prey.id} to world"
                )
            
            return offspring
        except Exception as e:
            raise EntityError(f"Reproduction failed: {str(e)}", entity=self)
    
    def attach_behavior_system(self, behavior_system):
        """
        Attach a behavior system to this prey.
        
        Args:
            behavior_system: The behavior system to attach
            
        Returns:
            bool: True if attachment was successful
        """
        try:
            self._behavior_system = behavior_system
            return True
        except Exception:
            return False
