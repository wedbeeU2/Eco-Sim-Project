"""
Reproduction system for entities in the ecosystem simulation.
"""
import random
from src.core.enums import Gender, SeasonType
from src.utils.exceptions import validate_type, EntityError, validate_positive, safe_operation


class ReproductionSystem:
    """
    Manages reproduction for ecosystem entities.
    Handles mating, offspring generation, and genetic inheritance.
    """
    
    def __init__(self, entity, breeding_cycle=None, maturity_age=None, offspring_range=None):
        """
        Initialize a reproduction system for an entity.
        
        Args:
            entity: The entity this system belongs to
            breeding_cycle (float, optional): Override breeding cycle duration
            maturity_age (float, optional): Override maturity age
            offspring_range (tuple, optional): Override (min, max) offspring range
            
        Raises:
            EntityError: If initialization fails
        """
        self._entity = entity
        
        # Use attributes from entity if not overridden
        try:
            self._breeding_cycle = breeding_cycle if breeding_cycle is not None else entity.attributes.breeding_cycle
            self._maturity_age = maturity_age if maturity_age is not None else entity.attributes.maturity_age
            
            # Determine offspring range
            if offspring_range is not None:
                self._min_offspring, self._max_offspring = offspring_range
            else:
                self._min_offspring = getattr(entity.attributes, 'min_offspring', 1)
                self._max_offspring = getattr(entity.attributes, 'max_offspring', 5)
                
            # Validate parameters
            validate_positive(self._breeding_cycle, "breeding_cycle")
            validate_positive(self._maturity_age, "maturity_age")
            validate_positive(self._min_offspring, "min_offspring")
            validate_positive(self._max_offspring, "max_offspring")
            
            # Ensure min_offspring <= max_offspring
            if self._min_offspring > self._max_offspring:
                self._min_offspring, self._max_offspring = self._max_offspring, self._min_offspring
            
            # Initialize reproductive state
            self._time_since_last_reproduction = getattr(entity, '_time_since_last_reproduction', 0)
            
            # Seasonal influence
            self._season_modifiers = {
                SeasonType.SPRING: 1.2,  # Increased reproduction in spring
                SeasonType.SUMMER: 1.0,  # Normal reproduction in summer
                SeasonType.FALL: 0.8,    # Decreased reproduction in fall
                SeasonType.WINTER: 0.6   # Greatly decreased reproduction in winter
            }
            
        except Exception as e:
            raise EntityError(f"Failed to initialize reproduction system: {str(e)}", entity=entity)
    
    @property
    def entity(self):
        """Get the entity this system belongs to"""
        return self._entity
    
    @property
    def breeding_cycle(self):
        """Get the breeding cycle duration"""
        return self._breeding_cycle
    
    @property
    def maturity_age(self):
        """Get the maturity age"""
        return self._maturity_age
    
    @property
    def min_offspring(self):
        """Get the minimum number of offspring"""
        return self._min_offspring
    
    @property
    def max_offspring(self):
        """Get the maximum number of offspring"""
        return self._max_offspring
    
    @property
    def time_since_last_reproduction(self):
        """Get the time since last reproduction"""
        return self._time_since_last_reproduction
    
    @time_since_last_reproduction.setter
    def time_since_last_reproduction(self, value):
        """Set the time since last reproduction"""
        self._time_since_last_reproduction = max(0, value)
        
        # Update the entity's reproduction timer if available
        if hasattr(self._entity, '_time_since_last_reproduction'):
            self._entity._time_since_last_reproduction = self._time_since_last_reproduction
    
    def update(self, time_delta):
        """
        Update the reproduction system.
        
        Args:
            time_delta (float): Time elapsed since last update
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Update time since last reproduction
            self._time_since_last_reproduction += time_delta
            
            # Update entity's reproduction timer if available
            if hasattr(self._entity, '_time_since_last_reproduction'):
                self._entity._time_since_last_reproduction = self._time_since_last_reproduction
            
            return True
        except Exception as e:
            # Log error and continue
            from src.utils.exceptions import logger
            logger.error(f"Error updating reproduction system: {e}")
            return False
    
    def can_reproduce(self, current_season=None):
        """
        Check if the entity can reproduce.
        
        Args:
            current_season (SeasonType, optional): Current season to apply modifiers
            
        Returns:
            bool: True if reproduction is possible
        """
        # Check if entity is mature
        if not self._entity.is_mature():
            return False
        
        # Check if breeding cycle has elapsed
        if self._time_since_last_reproduction < self._breeding_cycle:
            return False
        
        # Check energy level (entity should have at least 60% energy)
        if self._entity.energy < 0.6 * self._entity.attributes.max_energy:
            return False
        
        # Check health level (entity should have at least 50% health)
        if self._entity.health < 50:
            return False
        
        # Apply seasonal modifiers if specified
        if current_season is not None and isinstance(current_season, SeasonType):
            # Get seasonal modifier
            season_modifier = self._season_modifiers.get(current_season, 1.0)
            
            # Apply random chance based on season
            if random.random() > season_modifier:
                return False
        
        return True
    
    def find_mate(self, world):
        """
        Find a suitable mate in the vicinity.
        
        Args:
            world: The world environment
            
        Returns:
            entity or None: A suitable mate, or None if none found
            
        Raises:
            EntityError: If mate finding fails
        """
        try:
            # Get entity type
            entity_type = self._entity.__class__
            
            # Get entity's interaction range
            interaction_range = self._entity.attributes.interaction_range
            
            # Find potential mates of the same type but opposite gender
            potential_mates = [
                entity for entity in world.get_entities_in_range(
                    self._entity.position, interaction_range
                )
                if isinstance(entity, entity_type) 
                and entity.is_alive 
                and entity.gender != self._entity.gender
                and entity.can_reproduce()
            ]
            
            # Return a random mate if any found
            if potential_mates:
                return random.choice(potential_mates)
            
            return None
        except Exception as e:
            raise EntityError(f"Failed to find mate: {str(e)}", entity=self._entity)
    
    def calculate_num_offspring(self, mate=None, current_season=None):
        """
        Calculate the number of offspring to produce.
        
        Args:
            mate (entity, optional): The mate entity
            current_season (SeasonType, optional): Current season to apply modifiers
            
        Returns:
            int: Number of offspring to produce
        """
        # Base number of offspring
        num_offspring = random.randint(self._min_offspring, self._max_offspring)
        
        # Apply health and energy modifiers
        health_factor = self._entity.health / 100.0
        energy_factor = self._entity.energy / self._entity.attributes.max_energy
        vitality_modifier = (health_factor + energy_factor) / 2.0
        
        # Apply mate's vitality if available
        if mate is not None:
            mate_health_factor = mate.health / 100.0
            mate_energy_factor = mate.energy / mate.attributes.max_energy
            mate_vitality = (mate_health_factor + mate_energy_factor) / 2.0
            vitality_modifier = (vitality_modifier + mate_vitality) / 2.0
        
        # Apply seasonal modifiers if specified
        season_modifier = 1.0
        if current_season is not None and isinstance(current_season, SeasonType):
            season_modifier = self._season_modifiers.get(current_season, 1.0)
        
        # Calculate adjusted number of offspring
        adjusted_offspring = int(num_offspring * vitality_modifier * season_modifier)
        
        # Ensure at least one offspring if both parents are healthy enough
        if vitality_modifier > 0.5 and adjusted_offspring < 1:
            adjusted_offspring = 1
        
        # Cap at max_offspring
        return min(adjusted_offspring, self._max_offspring)
    
    def generate_offspring(self, mate, world, current_season=None):
        """
        Generate offspring with a mate.
        
        Args:
            mate: The mate entity
            world: The world environment
            current_season (SeasonType, optional): Current season to apply modifiers
            
        Returns:
            list: Generated offspring entities
            
        Raises:
            EntityError: If offspring generation fails
        """
        try:
            # Validate mate
            validate_type(mate, "mate", self._entity.__class__)
            
            # Check if both entities can reproduce
            if not (self.can_reproduce(current_season) and mate.can_reproduce(current_season)):
                return []
            
            # Reset reproduction timers
            self.time_since_last_reproduction = 0
            
            # Reset mate's reproduction timer if available
            if hasattr(mate, '_time_since_last_reproduction'):
                mate._time_since_last_reproduction = 0
            elif hasattr(mate, 'time_since_last_reproduction'):
                mate.time_since_last_reproduction = 0
            
            # Energy cost for reproduction (30% of max energy)
            reproduction_cost = 0.3 * self._entity.attributes.max_energy
            self._entity.energy -= reproduction_cost
            mate.energy -= reproduction_cost
            
            # Calculate number of offspring
            num_offspring = self.calculate_num_offspring(mate, current_season)
            
            # Generate offspring
            offspring = []
            for _ in range(num_offspring):
                # Create a new entity at a position near the parents
                from src.core.position import Position
                offspring_position = Position(
                    self._entity.position.x + random.uniform(-10, 10),
                    self._entity.position.y + random.uniform(-10, 10)
                )
                
                # Randomly assign gender
                offspring_gender = random.choice(list(Gender))
                
                # Create new entity of the same type
                entity_class = self._entity.__class__
                new_entity = entity_class(
                    position=offspring_position,
                    gender=offspring_gender,
                    energy=0.5 * self._entity.attributes.max_energy,
                    age=0,
                    health=100
                )
                
                # Special handling for invasive species
                if hasattr(self._entity, '_adaptation_level') and hasattr(mate, '_adaptation_level'):
                    # Inherit adaptation level from parents with a small boost
                    inherited_adaptation = (self._entity._adaptation_level + mate._adaptation_level) / 2.0
                    new_entity._adaptation_level = min(1.0, inherited_adaptation + random.uniform(0, 0.05))
                
                offspring.append(new_entity)
                
                # Add to world safely
                safe_operation(
                    lambda: world.add_entity(new_entity),
                    f"Failed to add offspring to world"
                )
            
            return offspring
        except Exception as e:
            raise EntityError(f"Failed to generate offspring: {str(e)}", entity=self._entity)
    
    def attempt_reproduction(self, world, current_season=None):
        """
        Attempt to find a mate and reproduce.
        
        Args:
            world: The world environment
            current_season (SeasonType, optional): Current season to apply modifiers
            
        Returns:
            list: Generated offspring entities, or empty list if reproduction failed
        """
        try:
            # Check if entity can reproduce
            if not self.can_reproduce(current_season):
                return []
            
            # Find a mate
            mate = self.find_mate(world)
            if mate is None:
                return []
            
            # Generate offspring
            return self.generate_offspring(mate, world, current_season)
        except Exception as e:
            # Log error and continue
            from src.utils.exceptions import logger
            logger.error(f"Error attempting reproduction: {e}")
            return []
