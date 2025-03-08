"""
Predator entity module for the ecosystem simulation.
"""
import random
from src.core.entity import Entity
from src.core.enums import Gender
from src.core.attributes import PredatorAttributes
from src.utils.exceptions import validate_type, EntityError, safe_operation


class Predator(Entity):
    """
    Predator entity in the ecosystem.
    Hunts prey entities and reproduces with other predators.
    """
    
    # Class-level attributes shared by all predators
    _attributes = PredatorAttributes()
    
    @property
    def attributes(self):
        """Return the entity's attributes"""
        return Predator._attributes
    
    def __init__(self, position, gender=None, energy=None, age=0, health=100):
        """
        Initialize a predator entity.
        
        Args:
            position (Position): The initial position
            gender (Gender, optional): The gender (random if None)
            energy (float, optional): Initial energy level (max if None)
            age (float, optional): Initial age in days (default: 0)
            health (float, optional): Initial health (default: 100)
        """
        super().__init__(position, gender, energy, age, health)
        self._time_since_last_reproduction = 0
        self._hunting_cooldown = 0
    
    @property
    def time_since_last_reproduction(self):
        """Get time since last reproduction"""
        return self._time_since_last_reproduction
    
    @time_since_last_reproduction.setter
    def time_since_last_reproduction(self, value):
        """Set time since last reproduction"""
        self._time_since_last_reproduction = max(0, value)
    
    @property
    def hunting_cooldown(self):
        """Get the hunting cooldown timer"""
        return self._hunting_cooldown
    
    @hunting_cooldown.setter
    def hunting_cooldown(self, value):
        """Set the hunting cooldown timer"""
        self._hunting_cooldown = max(0, value)
    
    def update(self, world, time_delta):
        """
        Update the predator's state.
        
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
        
        # Update hunting cooldown
        if self._hunting_cooldown > 0:
            self._hunting_cooldown = max(0, self._hunting_cooldown - time_delta)
        
        # Use behavior system if available
        behavior_system = getattr(self, '_behavior_system', None)
        if behavior_system is not None:
            return behavior_system.update(world)
        
        # Basic behavior when no behavior system is attached
        return self._basic_behavior(world)
    
    def _basic_behavior(self, world):
        """
        Execute basic predator behavior when no behavior system is available.
        
        Args:
            world (World): The world environment
            
        Returns:
            bool: True if behavior execution was successful
        """
        try:
            # Find and hunt prey if hungry
            if self.energy < 0.7 * self.attributes.max_energy:
                # Find prey in hunting range
                from src.entities.prey import Prey
                prey_in_range = [
                    entity for entity in world.get_entities_in_range(
                        self.position, self.attributes.hunting_range
                    )
                    if isinstance(entity, Prey) and entity.is_alive
                ]
                
                if prey_in_range and self._hunting_cooldown <= 0:
                    # Hunt a random prey
                    return self.hunt(random.choice(prey_in_range), world)
                else:
                    # Move randomly looking for prey
                    self.move()
            else:
                # Try to reproduce if it's time
                if self.can_reproduce():
                    # Find potential mates
                    potential_mates = [
                        entity for entity in world.get_entities_in_range(
                            self.position, self.attributes.interaction_range
                        )
                        if isinstance(entity, Predator) 
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
                    # Rest to conserve energy
                    pass
            
            return True
        except Exception as e:
            # Log error and continue
            from src.utils.exceptions import logger
            logger.error(f"Error in predator basic behavior: {e}")
            return False
    
    def hunt(self, prey, world):
        """
        Hunt a prey entity.
        
        Args:
            prey: The prey entity to hunt
            world: The world environment
            
        Returns:
            bool: True if hunt was successful
            
        Raises:
            EntityError: If hunting fails
        """
        try:
            validate_type(prey, "prey", object)  # Just check it's an object, more specific check below
            
            # Check if prey is valid
            if not hasattr(prey, 'is_alive') or not prey.is_alive:
                return False
            
            # Move towards prey
            self.move(prey.position)
            
            # Check if close enough to attack
            if self.position.distance_to(prey.position) < self.attributes.interaction_range:
                # Apply hunting cooldown
                self._hunting_cooldown = 5.0  # 5 seconds cooldown
                
                # Attack success probability based on health and energy
                attack_success = random.random() < (self.health / 100) * (self.energy / self.attributes.max_energy)
                
                if attack_success:
                    # Successful hunt
                    prey_energy = prey.energy
                    prey.health = 0  # Kill the prey
                    
                    # Gain energy from prey
                    energy_gained = prey_energy * self.attributes.digest_efficiency
                    self.energy = min(self.attributes.max_energy, self.energy + energy_gained)
                    
                    return True
            
            return False
        except Exception as e:
            raise EntityError(f"Hunting failed: {str(e)}", entity=self)
    
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
            from src.entities.prey import Prey
            if isinstance(other, Prey) and other.is_alive:
                return self.hunt(other, world)
            
            return False
        except Exception as e:
            # Log error and continue
            return False
    
    def can_reproduce(self):
        """
        Check if the predator can reproduce.
        
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
        Reproduce with another predator.
        
        Args:
            partner: The partner predator
            world: The world environment
            
        Returns:
            list: List of offspring entities
            
        Raises:
            EntityError: If reproduction fails
        """
        try:
            validate_type(partner, "partner", Predator)
            
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
                # Create a new predator at a position near the parents
                from src.core.position import Position
                offspring_position = Position(
                    self.position.x + random.uniform(-10, 10),
                    self.position.y + random.uniform(-10, 10)
                )
                
                # Apply random gender
                offspring_gender = random.choice(list(Gender))
                
                new_predator = Predator(
                    position=offspring_position,
                    gender=offspring_gender,
                    energy=0.5 * self.attributes.max_energy,
                    age=0
                )
                
                offspring.append(new_predator)
                
                # Add to world safely
                safe_operation(
                    lambda: world.add_entity(new_predator),
                    f"Failed to add offspring {new_predator.id} to world"
                )
            
            return offspring
        except Exception as e:
            raise EntityError(f"Reproduction failed: {str(e)}", entity=self)
    
    def attach_behavior_system(self, behavior_system):
        """
        Attach a behavior system to this predator.
        
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
