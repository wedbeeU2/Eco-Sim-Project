"""
World environment module for the ecosystem simulation.
"""
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
            self._resources = {}  # Resource distribution in the world
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
            # Validate input parameters
            validate_positive(time_delta, "time_delta")
            
            # Update world time
            self._current_time += time_delta
            
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
    
    def get_resources_in_range(self, resource_type, position, radius):
        """
        Get resources of a specific type in range of a position.
        
        Args:
            resource_type (str): The type of resource
            position (Position): Center position
            radius (float): Search radius
            
        Returns:
            list: Resources in range
            
        Raises:
            WorldError: If resource search fails
        """
        try:
            validate_type(position, "position", Position)
            validate_positive(radius, "radius")
            
            # Check if resource type exists
            if resource_type not in self._resources:
                return []
            
            # Filter resources by distance
            return [
                resource for resource in self._resources[resource_type]
                if position.distance_to(resource["position"]) <= radius
            ]
        except Exception as e:
            raise WorldError(f"Failed to get resources in range: {str(e)}")
