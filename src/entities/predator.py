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
        Update the predator's state with balanced hunting and reproduction priorities.
    
        Args:
            world (World): The world environment
            time_delta (float): Time elapsed since last update
        """
        # Ensure time_delta is positive
        effective_time_delta = max(0.001, time_delta)
    
        # Update base entity state
        super().update(world, effective_time_delta)
    
        if not self.is_alive:
            return False
    
        # Update reproduction timer
        self._time_since_last_reproduction += effective_time_delta
    
        # Update hunting cooldown
        if self._hunting_cooldown > 0:
            self._hunting_cooldown = max(0, self._hunting_cooldown - effective_time_delta)
    
        # MAJOR CHANGE: Check reproduction readiness first
        # This gives reproduction priority over hunting when possible
        if self.can_reproduce():
            # Log reproduction attempt for debugging
            from src.utils.exceptions import logger
            logger.info(f"Predator {self.id} attempting to reproduce")
        
            # Find potential mates
            potential_mates = [
                entity for entity in world.get_entities_in_range(
                    self.position, self.attributes.interaction_range * 1.5  # Increased range
                )
                if isinstance(entity, type(self)) 
                and entity.is_alive 
                and entity.gender != self.gender
                and entity.can_reproduce()
            ]
        
            if potential_mates:
                # Reproduce with a random mate
                mate = random.choice(potential_mates)

                # Move towards mate if not already close
                if self.position.distance_to(mate.position) > self.attributes.interaction_range:
                    self.move(mate.position)
                else:
                    # Attempt reproduction
                    offspring = self.reproduce(mate, world)
                    if offspring:
                        from src.utils.exceptions import logger
                        logger.info(f"Predator {self.id} successfully reproduced, creating {len(offspring)} offspring")
            
                return True
            else:
                # Look for mates - move to a random location to find mates
                # This makes predators actively search for mates
                self.move()
                return True
    
        # If not reproducing, check if hungry
        if self.energy < 0.7 * self.attributes.max_energy:
            # Find prey to hunt
            from src.entities.prey import Prey
            prey_in_range = [
                entity for entity in world.get_entities_in_range(
                    self.position, self.attributes.hunting_range
                )
                if isinstance(entity, Prey) and entity.is_alive
            ]
        
            if prey_in_range and self._hunting_cooldown <= 0:
                # Hunt a random prey
                target_prey = random.choice(prey_in_range)
                self.move(target_prey.position)
                hunt_result = self.hunt(target_prey, world)
            
                # Log successful hunts for debugging
                if hunt_result:
                    from src.utils.exceptions import logger
                    logger.info(f"Predator {self.id} successfully hunted prey")
            
                return True
            else:
                # Move randomly looking for prey
                self.move()
                return True
        else:
            # Not hungry or reproducing - move randomly
            # This adds more exploration to find mates
            self.move()
            return True

    
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
        Hunt a prey entity - enhanced for better success rate.
    
        Args:
            prey: The prey entity to hunt
            world: The world environment
        
        Returns:
            bool: True if hunt was successful
        """
        try:
            validate_type(prey, "prey", object)
        
            # Check if prey is valid
            if not hasattr(prey, 'is_alive') or not prey.is_alive:
                return False
        
            # Move towards prey
            self.move(prey.position)
        
            # Check if close enough to attack
            if self.position.distance_to(prey.position) < self.attributes.interaction_range:
                # Apply hunting cooldown
                self._hunting_cooldown = 5.0  # Reduced from 5.0
            
                # Calculate base attack success probability
                # Enhanced formula that factors in predator's adaptation
                base_success_prob = 0.5  # Base 50% chance
            
                # Modify by health and energy ratios
                health_factor = self.health / 100.0
                energy_factor = self.energy / self.attributes.max_energy
            
                # NEW: Consider prey's health and energy too
                prey_health_factor = 1.0 - (prey.health / 100.0) * 0.5  # Weaker prey easier to catch
                prey_energy_factor = 1.0 - (prey.energy / prey.attributes.max_energy) * 0.5  # Tired prey easier to catch
            
                # Calculate final success probability
                attack_success_prob = base_success_prob * health_factor * energy_factor * prey_health_factor * prey_energy_factor
            
                # Ensure reasonable bounds
                attack_success_prob = max(0.2, min(0.9, attack_success_prob))
            
                # Check for success
                attack_success = random.random() < attack_success_prob
            
                if attack_success:
                    # Successful hunt
                    prey_energy = prey.energy
                    prey.health = 0  # Kill the prey

                    # Gain energy from prey - more efficient
                    energy_gained = prey_energy * self.attributes.digest_efficiency
                    self.energy = min(self.attributes.max_energy, self.energy + energy_gained)

                    return True
        
            return False
        except Exception as e:
            # Log error and ensure predator keeps moving
            from src.utils.exceptions import logger
            logger.error(f"Error during hunting: {str(e)}")
            self.move()
            return False
    
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
        Check if the predator can reproduce with improved criteria.
    
        Returns:
            bool: True if reproduction is possible
        """
        # Energy threshold reduced from 0.6 to 0.5
        energy_threshold = 0.5 * self.attributes.max_energy
    
        reproduction_ready = (
            self.is_mature() and
            self._time_since_last_reproduction >= self.attributes.breeding_cycle and
            self.energy > energy_threshold and
            self.health > 40  # Reduced from 50 to make reproduction more likely
        )
    
        # Log reproduction readiness for debugging
        if reproduction_ready:
            from src.utils.exceptions import logger
            logger.debug(f"Predator {self.id} is ready to reproduce")
    
        return reproduction_ready
    
    def reproduce(self, partner, world):
        """
        Reproduce with another predator. Enhanced to ensure successful reproduction.
    
        Args:
            partner: The partner predator
            world: The world environment
        
        Returns:
            list: List of offspring entities
        """
        try:
            # Check partner type
            if not isinstance(partner, type(self)):
                from src.utils.exceptions import logger
                logger.error(f"Invalid partner type for reproduction: {type(partner)}")
                return []
        
            # Check reproduction readiness for both
            if not (self.can_reproduce() and partner.can_reproduce()):
                return []
        
            # Reset reproduction timers
            self._time_since_last_reproduction = 0
            partner._time_since_last_reproduction = 0
        
            # Energy cost for reproduction - REDUCED to 25%
            reproduction_cost = 0.25 * self.attributes.max_energy
            self.energy -= reproduction_cost
            partner.energy -= reproduction_cost
        
            # Generate offspring
            num_offspring = random.randint(
                self.attributes.min_offspring, 
                self.attributes.max_offspring
            )
        
            # Ensure at least minimum offspring
            num_offspring = max(num_offspring, self.attributes.min_offspring)
        
            offspring = []
            for _ in range(num_offspring):
                # Create a new predator at a position near the parents
                from src.core.position import Position
                offspring_position = Position(
                    self.position.x + random.uniform(-10, 10),
                    self.position.y + random.uniform(-10, 10)
                )
            
                # Apply random gender with equal probability
                from src.core.enums import Gender
                offspring_gender = random.choice(list(Gender))
            
                # Create new predator with higher initial energy
                new_predator = type(self)(
                    position=offspring_position,
                    gender=offspring_gender,
                    energy=0.6 * self.attributes.max_energy,  # Increased from 0.5
                    age=0,
                    health=100
                )
            
                offspring.append(new_predator)
            
                # Add to world
                world.add_entity(new_predator)
        
            # Log successful reproduction
            from src.utils.exceptions import logger
            logger.info(f"Created {num_offspring} predator offspring")
        
            return offspring
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error during reproduction: {str(e)}")
            return []
    
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
