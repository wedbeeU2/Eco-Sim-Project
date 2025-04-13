"""
World environment module for the ecosystem simulation.
"""
import random
from src.systems.spatial_grid import SpatialPartitioning
from src.core.position import Position
from src.utils.exceptions import (
    validate_positive, validate_type, WorldError, 
    safe_operation, validate_non_negative
)


class World:
    """
    Represents the environment where entities exist and interact.
    Manages all entities and provides spatial query capabilities.
    """
    
    def __init__(self, width, height):
        """
        Initialize the world environment.
        
        Args:
            width (float): The width of the world
            height (float): The height of the world
            
        Raises:
            WorldError: If initialization fails
        """
        try:
            self._width = validate_positive(width, "width")
            self._height = validate_positive(height, "height")
            self._entities = []
            self._spatial_index = SpatialPartitioning(width, height)
            self._current_time = 0.0
            self._current_season = None  # Will be set by simulation

            # NEW: Add food resources management
            self._food_resources = []
            self._food_spawn_timer = 0.0
            self._target_food_density = 0.0002  # Target food per square unit
            self._max_food_count = int(width * height * self._target_food_density)
            self._min_food_count = int(self._max_food_count * 0.3)  # Minimum 30% of max
        
            # Initialize starting food
            self._initialize_food_resources()
        except Exception as e:
            raise WorldError(f"Failed to initialize world: {str(e)}")
    
    @property
    def width(self):
        """Get the world width"""
        return self._width
    
    @property
    def height(self):
        """Get the world height"""
        return self._height
    
    @property
    def entities(self):
        """Get a copy of the entities list"""
        return list(self._entities)
    
    @property
    def current_time(self):
        """Get the current world time"""
        return self._current_time
    
    @current_time.setter
    def current_time(self, value):
        """Set the current world time"""
        self._current_time = validate_non_negative(value, "current_time")
    
    @property
    def current_season(self):
        """Get the current season"""
        return self._current_season
    
    @current_season.setter
    def current_season(self, value):
        """Set the current season"""
        from src.core.enums import SeasonType
        if value is not None and not isinstance(value, SeasonType):
            raise ValueError(f"current_season must be a SeasonType or None, got {type(value)}")
        self._current_season = value
    
    def add_entity(self, entity):
        """
        Add an entity to the world.
        
        Args:
            entity: The entity to add
            
        Returns:
            bool: True if addition was successful
            
        Raises:
            WorldError: If addition fails
        """
        try:
            # Validate entity has required attributes
            if not hasattr(entity, 'position') or not hasattr(entity, 'is_alive'):
                raise WorldError(f"Entity missing required attributes", entity=entity)
            
            # Enforce world boundaries
            self.enforce_boundaries(entity)
            
            # Add to entities list
            self._entities.append(entity)
            
            # Add to spatial index
            self._spatial_index.add_entity(entity)
            
            return True
        except Exception as e:
            raise WorldError(f"Failed to add entity to world: {str(e)}")
    
    def remove_entity(self, entity):
        """
        Remove an entity from the world.
        
        Args:
            entity: The entity to remove
            
        Returns:
            bool: True if removal was successful
            
        Raises:
            WorldError: If removal fails
        """
        try:
            # Check if entity is in the world
            if entity not in self._entities:
                return False
            
            # Remove from entities list
            self._entities.remove(entity)
            
            # Remove from spatial index
            self._spatial_index.remove_entity(entity)
            
            return True
        except Exception as e:
            raise WorldError(f"Failed to remove entity from world: {str(e)}")
    
    def get_entities_in_range(self, position, range_radius):
        """
        Get all entities within a certain range of a position.
        
        Args:
            position (Position): The center position
            range_radius (float): The search radius
            
        Returns:
            list: Entities within the specified range
            
        Raises:
            WorldError: If search fails
        """
        try:
            validate_type(position, "position", Position)
            validate_positive(range_radius, "range_radius")
            
            return self._spatial_index.get_entities_in_range(position, range_radius)
        except Exception as e:
            raise WorldError(f"Failed to get entities in range: {str(e)}")
    
    def update(self, time_delta):
        """
        Update all entities in the world.
        
        Args:
            time_delta (float): Time elapsed since last update
            
        Returns:
            bool: True if update was successful
            
        Raises:
            WorldError: If update fails
        """
        try:
            # Ensure time_delta is positive
            effective_time_delta = max(0.001, time_delta)
            
            # Update world time
            self._current_time += effective_time_delta

            # NEW: Update food resources
            self.manage_food_resources(effective_time_delta)
            
            # Make a copy of the entities list to avoid issues if list changes during iteration
            entities_to_update = list(self._entities)
            
            for entity in entities_to_update:
                try:
                    if entity.is_alive:
                        # Store old position for spatial index update
                        old_position = Position(entity.position.x, entity.position.y)
                        
                        # Update entity with error handling
                        safe_operation(
                            lambda: entity.update(self, time_delta),
                            f"Error updating entity {entity.id}"
                        )
                        
                        # Enforce world boundaries
                        self.enforce_boundaries(entity)
                        
                        # Update spatial index if position changed
                        if (old_position.x != entity.position.x or old_position.y != entity.position.y):
                            safe_operation(
                                lambda: self._spatial_index.update_entity_position(entity, old_position),
                                f"Error updating spatial index for entity {entity.id}"
                            )
                    else:
                        # Remove dead entities
                        self.remove_entity(entity)
                except Exception as e:
                    from src.utils.exceptions import logger
                    logger.error(f"Error processing entity {entity.id}: {str(e)}")
                    # Try to remove the problematic entity
                    try:
                        self.remove_entity(entity)
                    except:
                        pass
                        
            return True
            
        except Exception as e:
            # Handle unexpected errors
            raise WorldError(f"Failed to update world: {str(e)}")
    
    def get_statistics(self):
        """
        Get statistics about the world.
        
        Returns:
            dict: Statistics about the world and entities
            
        Raises:
            WorldError: If statistics collection fails
        """
        try:
            # Count entities by type
            from src.entities.predator import Predator
            from src.entities.prey import Prey
            from src.entities.invasive_species import InvasiveSpecies
            
            predator_count = sum(1 for entity in self._entities if isinstance(entity, Predator) and entity.is_alive)
            prey_count = sum(1 for entity in self._entities if isinstance(entity, Prey) and entity.is_alive)
            invasive_count = sum(1 for entity in self._entities if isinstance(entity, InvasiveSpecies) and entity.is_alive)
            
            # Calculate gender distribution
            from src.core.enums import Gender
            male_count = sum(1 for entity in self._entities if entity.is_alive and entity.gender == Gender.MALE)
            female_count = sum(1 for entity in self._entities if entity.is_alive and entity.gender == Gender.FEMALE)
            
            # Calculate maturity distribution
            mature_count = sum(1 for entity in self._entities if entity.is_alive and entity.is_mature())
            immature_count = sum(1 for entity in self._entities if entity.is_alive and not entity.is_mature())
            
            # Calculate average health and energy
            total_health = sum(entity.health for entity in self._entities if entity.is_alive)
            total_energy = sum(entity.energy for entity in self._entities if entity.is_alive)
            
            live_entity_count = sum(1 for entity in self._entities if entity.is_alive)
            
            avg_health = total_health / live_entity_count if live_entity_count > 0 else 0
            avg_energy = total_energy / live_entity_count if live_entity_count > 0 else 0
            
            return {
                "time": self._current_time,
                "predator_count": predator_count,
                "prey_count": prey_count,
                "invasive_count": invasive_count,
                "total_entities": live_entity_count,
                "male_count": male_count,
                "female_count": female_count,
                "mature_count": mature_count,
                "immature_count": immature_count,
                "avg_health": avg_health,
                "avg_energy": avg_energy,
                "season": self._current_season.name if self._current_season else "None"
            }
        except Exception as e:
            raise WorldError(f"Failed to get world statistics: {str(e)}")
    
    def contains_position(self, position):
        """
        Check if a position is within the world boundaries.
        
        Args:
            position (Position): The position to check
            
        Returns:
            bool: True if the position is within boundaries
            
        Raises:
            WorldError: If check fails
        """
        try:
            validate_type(position, "position", Position)
            return 0 <= position.x < self._width and 0 <= position.y < self._height
        except Exception as e:
            raise WorldError(f"Failed to check position boundaries: {str(e)}")
    
    def enforce_boundaries(self, entity):
        """
        Ensure an entity stays within world boundaries.
        
        Args:
            entity: The entity to check and adjust
            
        Returns:
            bool: True if boundaries were enforced
            
        Raises:
            WorldError: If enforcement fails
        """
        try:
            if not hasattr(entity, 'position'):
                raise WorldError(f"Entity missing position attribute", entity=entity)
            
            # Adjust position to stay within boundaries
            if entity.position.x < 0:
                entity.position.x = 0
            elif entity.position.x >= self._width:
                entity.position.x = self._width - 1
                
            if entity.position.y < 0:
                entity.position.y = 0
            elif entity.position.y >= self._height:
                entity.position.y = self._height - 1
            
            return True
        except Exception as e:
            raise WorldError(f"Failed to enforce entity boundaries: {str(e)}")
    
    def clear(self):
        """
        Clear all entities from the world.
        
        Returns:
            bool: True if clearing was successful
        """
        self._entities.clear()
        self._spatial_index.clear()
        return True
    
    def get_entity_density(self, position, radius):
        """
        Get the entity density in a specific area.
        
        Args:
            position (Position): Center position
            radius (float): Search radius
            
        Returns:
            float: Entity density (entities per unit area)
            
        Raises:
            WorldError: If density calculation fails
        """
        try:
            validate_type(position, "position", Position)
            validate_positive(radius, "radius")
            
            # Get entities in the area
            entities = self.get_entities_in_range(position, radius)
            
            # Calculate area
            area = 3.14159 * radius * radius
            
            # Calculate density
            return len(entities) / area
        except Exception as e:
            raise WorldError(f"Failed to calculate entity density: {str(e)}")
    
    def add_resource(self, resource_type, position, amount):
        """
        Add a resource to the world at a specific position.
        
        Args:
            resource_type (str): The type of resource
            position (Position): The position of the resource
            amount (float): The amount of resource
            
        Returns:
            bool: True if resource addition was successful
            
        Raises:
            WorldError: If resource addition fails
        """
        try:
            validate_type(position, "position", Position)
            validate_positive(amount, "amount")
            
            # Add resource to resources dictionary
            if resource_type not in self._resources:
                self._resources[resource_type] = []
            
            self._resources[resource_type].append({
                "position": position,
                "amount": amount
            })
            
            return True
        except Exception as e:
            raise WorldError(f"Failed to add resource: {str(e)}")
        
    def _initialize_food_resources(self):
        """
        Initialize food resources in the world.
    
        Returns:
            bool: True if initialization was successful
        """
        try:
            from src.core.food_resource import FoodResource
        
            # Calculate initial food count - start with 50% of max
            initial_food_count = int(self._max_food_count * 0.5)
        
            # Create food resources with random positions
            for _ in range(initial_food_count):
                self.spawn_food_resource()
        
            from src.utils.exceptions import logger
            logger.info(f"Initialized {initial_food_count} food resources")
        
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Failed to initialize food resources: {str(e)}")
            return False

    def spawn_food_resource(self, position=None, energy_value=None, size=None):
        """
        Spawn a new food resource at a specific or random position.
    
        Args:
            position (Position, optional): Position for the new resource, random if None
            energy_value (float, optional): Energy value for the resource, random if None
            size (float, optional): Size of the resource, random if None
        
        Returns:
            FoodResource: The newly spawned food resource
        """
        try:
            from src.core.position import Position
            from src.core.food_resource import FoodResource
        
            # Generate random position if not provided
            if position is None:
                position = Position(
                    random.uniform(0, self._width),
                    random.uniform(0, self._height)
                )
        
            # Generate random energy value if not provided (15-45)
            if energy_value is None:
                energy_value = random.uniform(15.0, 45.0)
        
            # Generate random size if not provided (0.5-1.5)
            if size is None:
                size = random.uniform(0.5, 1.5)
        
            # Create and add the food resource
            food = FoodResource(position, energy_value, size)
            self._food_resources.append(food)
        
            return food
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Failed to spawn food resource: {str(e)}")
            return None
    
    def get_food_resources_in_range(self, position, range_radius):
        """
        Get all food resources within a certain range of a position.
    
        Args:
            position (Position): The center position
            range_radius (float): The search radius
        
        Returns:
            list: Food resources within the specified range, sorted by distance
        """
        try:
            validate_type(position, "position", Position)
            validate_positive(range_radius, "range_radius")
        
            # Find food resources in range
            resources_in_range = [
                resource for resource in self._food_resources
                if resource.is_active and position.distance_to(resource.position) <= range_radius
            ]
        
            # Sort by distance (closest first)
            resources_in_range.sort(key=lambda r: position.distance_to(r.position))
        
            return resources_in_range
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Failed to get food resources in range: {str(e)}")
            return []

    def manage_food_resources(self, time_delta):
        """
        Manage food resources in the world (update, spawn, remove).
    
        Args:
            time_delta (float): Time elapsed since last update
        
        Returns:
            bool: True if management was successful
        """
        try:
            # Update each food resource
            for food in list(self._food_resources):
                food.update(self, time_delta)
        
            # Remove inactive (fully depleted) resources that haven't regrown
            self._food_resources = [food for food in self._food_resources if food.is_active]
        
            # Update spawn timer
            self._food_spawn_timer += time_delta
        
            # Check if it's time to spawn new food
            if self._food_spawn_timer >= 5.0:  # Every 5 seconds
                self._food_spawn_timer = 0.0
            
                # Count active food resources
                active_food_count = len(self._food_resources)
            
                # Spawn food if below minimum count
                if active_food_count < self._min_food_count:
                    # Calculate how many to spawn - up to 10% of max at once
                    spawn_count = min(
                        int(self._max_food_count * 0.1),
                        self._min_food_count - active_food_count
                    )
                
                    # Spawn new food resources
                    for _ in range(spawn_count):
                        self.spawn_food_resource()
                
                    from src.utils.exceptions import logger
                    logger.info(f"Spawned {spawn_count} new food resources. Total: {len(self._food_resources)}")
        
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Failed to manage food resources: {str(e)}")
            return False
