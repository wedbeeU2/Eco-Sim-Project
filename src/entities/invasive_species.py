"""
InvasiveSpecies entity module for the ecosystem simulation.
"""
import random
from src.core.entity import Entity
from src.core.enums import Gender
from src.core.attributes import InvasiveSpeciesAttributes
from src.utils.exceptions import validate_type, EntityError, safe_operation, validate_range


class InvasiveSpecies(Entity):
    """
    Invasive species entity that can disrupt the ecosystem.
    Competes with native species and adapts to the environment.
    """
    
    # Class-level attributes shared by all invasive species
    _attributes = InvasiveSpeciesAttributes()
    
    @property
    def attributes(self):
        """Return the entity's attributes"""
        return InvasiveSpecies._attributes
    
    def __init__(self, position, gender=None, energy=None, age=0, health=100):
        """
        Initialize an invasive species entity.
        
        Args:
            position (Position): The initial position
            gender (Gender, optional): The gender (random if None)
            energy (float, optional): Initial energy level (max if None)
            age (float, optional): Initial age in days (default: 0)
            health (float, optional): Initial health (default: 100)
        """
        super().__init__(position, gender, energy, age, health)
        self._time_since_last_reproduction = 0
        self._adaptation_level = 0  # Increases over time
        self._competition_cooldown = 0
    
    @property
    def time_since_last_reproduction(self):
        """Get time since last reproduction"""
        return self._time_since_last_reproduction
    
    @time_since_last_reproduction.setter
    def time_since_last_reproduction(self, value):
        """Set time since last reproduction"""
        self._time_since_last_reproduction = max(0, value)
    
    @property
    def adaptation_level(self):
        """Get the adaptation level"""
        return self._adaptation_level
    
    @adaptation_level.setter
    def adaptation_level(self, value):
        """
        Set the adaptation level, ensuring it stays within valid range.
        
        Args:
            value (float): The new adaptation level
        """
        self._adaptation_level = validate_range(value, "adaptation_level", 0, 1)
    
    @property
    def competition_cooldown(self):
        """Get the competition cooldown timer"""
        return self._competition_cooldown
    
    @competition_cooldown.setter
    def competition_cooldown(self, value):
        """Set the competition cooldown timer"""
        self._competition_cooldown = max(0, value)
    
    def update(self, world, time_delta):
        """
        Update the invasive species' state.
        
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
        
        # Update adaptation level over time
        self._adaptation_level += self.attributes.adaptation_rate * time_delta
        self._adaptation_level = min(1.0, self._adaptation_level)  # Cap at 1.0
        
        # Update competition cooldown
        if self._competition_cooldown > 0:
            self._competition_cooldown = max(0, self._competition_cooldown - time_delta)
        
        # Use behavior system if available
        behavior_system = getattr(self, '_behavior_system', None)
        if behavior_system is not None:
            return behavior_system.update(world)
        
        # Basic behavior when no behavior system is attached
        return self._basic_behavior(world)
    
    def _basic_behavior(self, world):
        """
        Execute basic invasive species behavior when no behavior system is available.
        
        Args:
            world (World): The world environment
            
        Returns:
            bool: True if behavior execution was successful
        """
        try:
            # Forage more efficiently than natives if hungry
            if self.energy < 0.8 * self.attributes.max_energy:
                return self.forage(world)
            
            # Try to reproduce if it's time
            if self.can_reproduce():
                # Find potential mates
                potential_mates = [
                    entity for entity in world.get_entities_in_range(
                        self.position, self.attributes.interaction_range
                    )
                    if isinstance(entity, InvasiveSpecies) 
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
            elif self._competition_cooldown <= 0:
                # Compete with natives in the area
                return self.compete(world)
            else:
                # Move randomly
                self.move()
            
            return True
        except Exception as e:
            # Log error and continue
            from src.utils.exceptions import logger
            logger.error(f"Error in invasive species basic behavior: {e}")
            return False
    
    def forage(self, world):
        """
        Forage more efficiently than native species.
        
        Args:
            world: The world environment
            
        Returns:
            bool: True if foraging was successful
            
        Raises:
            EntityError: If foraging fails
        """
        try:
            # Enhanced foraging ability that increases with adaptation
            efficiency_bonus = 1.0 + (self._adaptation_level * 0.5)
            energy_gained = self.attributes.resource_consumption * efficiency_bonus * random.uniform(0.5, 1.0)
            self.energy = min(self.attributes.max_energy, self.energy + energy_gained)
            
            # Move while foraging
            self.move()
            
            return True
        except Exception as e:
            raise EntityError(f"Foraging failed: {str(e)}", entity=self)
    
    def compete(self, world):
        """
        Compete with native species for resources.
        
        Args:
            world: The world environment
            
        Returns:
            bool: True if competition was successful
            
        Raises:
            EntityError: If competition fails
        """
        try:
            # Apply competition cooldown
            self._competition_cooldown = 5.0  # 5 seconds cooldown
            
            # Find nearby native species
            from src.entities.prey import Prey
            from src.entities.predator import Predator
            natives = [
                entity for entity in world.get_entities_in_range(
                    self.position, self.attributes.interaction_range
                )
                if (isinstance(entity, Prey) or isinstance(entity, Predator)) and entity.is_alive
            ]
            
            if natives:
                # Move towards a random native
                target = random.choice(natives)
                self.move(target.position)
                
                # If close enough, compete for resources
                if self.position.distance_to(target.position) < self.attributes.interaction_range * 0.5:
                    competition_strength = self.attributes.competition_factor * (1.0 + self._adaptation_level)
                    
                    # Reduce the native's energy based on competition strength
                    energy_depletion = min(
                        target.energy * 0.1 * competition_strength,
                        target.energy * 0.3  # Cap at 30% of current energy
                    )
                    target.energy -= energy_depletion
                    
                    # The invasive species gains a portion of this energy
                    self.energy = min(self.attributes.max_energy, self.energy + energy_depletion * 0.5)
                    
                    return True
            else:
                # No natives nearby, move randomly
                self.move()
            
            return False
        except Exception as e:
            raise EntityError(f"Competition failed: {str(e)}", entity=self)
    
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
            from src.entities.predator import Predator
            if (isinstance(other, Prey) or isinstance(other, Predator)) and other.is_alive:
                return self.compete(world)
            
            return False
        except Exception as e:
            # Log error and continue
            return False
    
    def can_reproduce(self):
        """
        Check if the invasive species can reproduce.
        
        Returns:
            bool: True if reproduction is possible
        """
        # Adaptation level helps reproduction efficiency
        reproduction_threshold = 0.6 - (self._adaptation_level * 0.2)
        return (
            self.is_mature() and
            self._time_since_last_reproduction >= self.attributes.breeding_cycle and
            self.energy > reproduction_threshold * self.attributes.max_energy and
            self.health > 40  # Can reproduce at lower health levels
        )
    
    def reproduce(self, partner, world):
        """
        Reproduce with another invasive species.
        
        Args:
            partner: The partner invasive species
            world: The world environment
            
        Returns:
            list: List of offspring entities
            
        Raises:
            EntityError: If reproduction fails
        """
        try:
            validate_type(partner, "partner", InvasiveSpecies)
            
            if not (self.can_reproduce() and partner.can_reproduce()):
                return []
            
            # Reset reproduction timers
            self._time_since_last_reproduction = 0
            partner.time_since_last_reproduction = 0
            
            # Energy cost for reproduction (reduced by adaptation)
            reproduction_cost = 0.3 * self.attributes.max_energy * (1.0 - self._adaptation_level * 0.2)
            self.energy -= reproduction_cost
            partner.energy -= reproduction_cost
            
            # Generate offspring with possible adaptation boost
            adaptation_boost = max(self._adaptation_level, partner.adaptation_level) * 0.1
            num_offspring = random.randint(
                self.attributes.min_offspring, 
                self.attributes.max_offspring
            )
            
            # Additional offspring based on adaptation level
            num_offspring += int(adaptation_boost * 5)
            
            offspring = []
            for _ in range(num_offspring):
                # Create a new invasive species at a position near the parents
                from src.core.position import Position
                offspring_position = Position(
                    self.position.x + random.uniform(-10, 10),
                    self.position.y + random.uniform(-10, 10)
                )
                
                # Apply random gender
                offspring_gender = random.choice(list(Gender))
                
                new_invasive = InvasiveSpecies(
                    position=offspring_position,
                    gender=offspring_gender,
                    energy=0.6 * self.attributes.max_energy,  # More starting energy
                    age=0
                )
                
                # Inherit adaptation level from parents with a small boost
                inherited_adaptation = (self._adaptation_level + partner.adaptation_level) / 2.0
                new_invasive.adaptation_level = min(1.0, inherited_adaptation + random.uniform(0, 0.05))
                
                offspring.append(new_invasive)
                
                # Add to world safely
                safe_operation(
                    lambda: world.add_entity(new_invasive),
                    f"Failed to add offspring {new_invasive.id} to world"
                )
            
            return offspring
        except Exception as e:
            raise EntityError(f"Reproduction failed: {str(e)}", entity=self)
    
    def attach_behavior_system(self, behavior_system):
        """
        Attach a behavior system to this invasive species.
        
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
