"""
Spatial partitioning system for efficient proximity queries.
"""
import math
from collections import defaultdict
from src.utils.exceptions import validate_positive, WorldError, validate_type


class SpatialPartitioning:
    """
    Efficient spatial partitioning for entity proximity queries.
    Uses a grid-based approach to optimize spatial searches.
    """
    
    def __init__(self, world_width, world_height, cell_size=50):
        """
        Initialize the spatial partitioning system.
        
        Args:
            world_width (float): Width of the world
            world_height (float): Height of the world
            cell_size (float): Size of each grid cell (default: 50)
            
        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate parameters
        self._cell_size = validate_positive(cell_size, "cell_size")
        world_width = validate_positive(world_width, "world_width")
        world_height = validate_positive(world_height, "world_height")
        
        self._grid_width = math.ceil(world_width / cell_size)
        self._grid_height = math.ceil(world_height / cell_size)
        self._grid = defaultdict(list)
        
        # Track entity positions for quick lookups
        self._entity_cells = {}
    
    @property
    def cell_size(self):
        """Get the grid cell size"""
        return self._cell_size
    
    @property
    def grid_width(self):
        """Get the grid width in cells"""
        return self._grid_width
    
    @property
    def grid_height(self):
        """Get the grid height in cells"""
        return self._grid_height
    
    def get_cell_coords(self, position):
        """
        Get the grid cell coordinates for a position.
        
        Args:
            position (Position): The position to get cell coordinates for
            
        Returns:
            tuple: (cell_x, cell_y) coordinates
            
        Raises:
            ValidationError: If position is invalid
        """
        from src.core.position import Position
        validate_type(position, "position", Position)
        
        cell_x = min(max(int(position.x // self._cell_size), 0), self._grid_width - 1)
        cell_y = min(max(int(position.y // self._cell_size), 0), self._grid_height - 1)
        return cell_x, cell_y
    
    def add_entity(self, entity):
        """
        Add an entity to the spatial grid.
        
        Args:
            entity: The entity to add
            
        Returns:
            bool: True if addition was successful
            
        Raises:
            WorldError: If addition fails
        """
        try:
            # Get cell coordinates for the entity
            cell_coords = self.get_cell_coords(entity.position)
            
            # Add to the grid
            self._grid[cell_coords].append(entity)
            
            # Store entity's cell for quick lookups
            self._entity_cells[entity.id] = cell_coords
            
            return True
        except Exception as e:
            raise WorldError(f"Failed to add entity to spatial grid: {str(e)}")
    
    def remove_entity(self, entity):
        """
        Remove an entity from the spatial grid.
        
        Args:
            entity: The entity to remove
            
        Returns:
            bool: True if removal was successful
            
        Raises:
            WorldError: If removal fails
        """
        try:
            # Check if entity is in the grid
            if entity.id not in self._entity_cells:
                return False
            
            # Get entity's cell
            cell_coords = self._entity_cells[entity.id]
            
            # Remove from the grid
            if entity in self._grid[cell_coords]:
                self._grid[cell_coords].remove(entity)
            
            # Remove from entity cells dictionary
            del self._entity_cells[entity.id]
            
            return True
        except Exception as e:
            raise WorldError(f"Failed to remove entity from spatial grid: {str(e)}")
    
    def update_entity_position(self, entity, old_position):
        """
        Update entity position in the spatial grid.
        
        Args:
            entity: The entity to update
            old_position (Position): The entity's previous position
            
        Returns:
            bool: True if update was successful
            
        Raises:
            WorldError: If update fails
        """
        try:
            # Get old and new cell coordinates
            from src.core.position import Position
            validate_type(old_position, "old_position", Position)
            
            old_cell = self.get_cell_coords(old_position)
            new_cell = self.get_cell_coords(entity.position)
            
            # If cell hasn't changed, no update needed
            if old_cell == new_cell:
                return False
            
            # Remove from old cell
            if entity in self._grid[old_cell]:
                self._grid[old_cell].remove(entity)
            
            # Add to new cell
            self._grid[new_cell].append(entity)
            
            # Update entity cells dictionary
            self._entity_cells[entity.id] = new_cell
            
            return True
        except Exception as e:
            raise WorldError(f"Failed to update entity position in spatial grid: {str(e)}")
    
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
            from src.core.position import Position
            validate_type(position, "position", Position)
            validate_positive(range_radius, "range_radius")
            
            # Calculate the cells that intersect with the range
            min_cell_x = max(0, int((position.x - range_radius) // self._cell_size))
            max_cell_x = min(self._grid_width - 1, int((position.x + range_radius) // self._cell_size))
            min_cell_y = max(0, int((position.y - range_radius) // self._cell_size))
            max_cell_y = min(self._grid_height - 1, int((position.y + range_radius) // self._cell_size))
            
            entities_in_range = []
            
            # Gather entities from all cells that intersect with the range
            for cell_x in range(min_cell_x, max_cell_x + 1):
                for cell_y in range(min_cell_y, max_cell_y + 1):
                    entities_in_cell = self._grid[(cell_x, cell_y)]
                    entities_in_range.extend(entities_in_cell)
            
            # Filter entities based on actual distance
            return [
                entity for entity in entities_in_range
                if entity.position.distance_to(position) <= range_radius
            ]
        except Exception as e:
            raise WorldError(f"Failed to get entities in range: {str(e)}")
    
    def get_entity_count(self):
        """
        Get the total number of entities in the spatial grid.
        
        Returns:
            int: Number of entities
        """
        return len(self._entity_cells)
    
    def get_cell_entity_counts(self):
        """
        Get a map of cell coordinates to entity counts.
        Useful for debugging and visualization.
        
        Returns:
            dict: Map of (cell_x, cell_y) to entity count
        """
        return {cell: len(entities) for cell, entities in self._grid.items() if entities}
    
    def clear(self):
        """
        Clear all entities from the grid.
        
        Returns:
            bool: True if the operation was successful
        """
        self._grid.clear()
        self._entity_cells.clear()
        return True
    
    def get_nearby_entities(self, entity, max_distance=None):
        """
        Get entities near a specific entity.
        
        Args:
            entity: The reference entity
            max_distance (float, optional): Maximum distance to search
                                           (defaults to entity's interaction range)
            
        Returns:
            list: Nearby entities
            
        Raises:
            WorldError: If search fails
        """
        try:
            # Determine search radius
            if max_distance is None:
                max_distance = getattr(entity.attributes, 'interaction_range', 50.0)
            
            # Get entities in range
            nearby = self.get_entities_in_range(entity.position, max_distance)
            
            # Remove the entity itself from results
            if entity in nearby:
                nearby.remove(entity)
            
            return nearby
        except Exception as e:
            raise WorldError(f"Failed to get nearby entities: {str(e)}")
