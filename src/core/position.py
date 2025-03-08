"""
Position class for representing and manipulating spatial coordinates.
"""
import math
import random
from src.utils.exceptions import validate_type, ValidationError


class Position:
    """
    Represents a 2D position in the simulation world.
    Handles movement and spatial calculations.
    """
    
    def __init__(self, x, y):
        """
        Initialize a position with x and y coordinates.
        
        Args:
            x (float): The x-coordinate
            y (float): The y-coordinate
            
        Raises:
            ValidationError: If x or y are not numbers
        """
        # Validate input types
        validate_type(x, "x", (int, float))
        validate_type(y, "y", (int, float))
        
        self._x = float(x)
        self._y = float(y)
    
    @property
    def x(self):
        """Get the x-coordinate"""
        return self._x
    
    @x.setter
    def x(self, value):
        """
        Set the x-coordinate.
        
        Args:
            value (float): The new x-coordinate
            
        Raises:
            ValidationError: If value is not a number
        """
        validate_type(value, "x", (int, float))
        self._x = float(value)
    
    @property
    def y(self):
        """Get the y-coordinate"""
        return self._y
    
    @y.setter
    def y(self, value):
        """
        Set the y-coordinate.
        
        Args:
            value (float): The new y-coordinate
            
        Raises:
            ValidationError: If value is not a number
        """
        validate_type(value, "y", (int, float))
        self._y = float(value)
    
    def distance_to(self, other_position):
        """
        Calculate the Euclidean distance to another position.
        
        Args:
            other_position (Position): The position to calculate distance to
            
        Returns:
            float: The distance between the two positions
            
        Raises:
            ValidationError: If other_position is not a Position object
        """
        validate_type(other_position, "other_position", Position)
        return math.sqrt((self._x - other_position.x)**2 + (self._y - other_position.y)**2)
    
    def move_towards(self, target_position, speed):
        """
        Move current position towards target position based on speed.
        
        Args:
            target_position (Position): The target position to move towards
            speed (float): The distance to move
            
        Raises:
            ValidationError: If parameters are invalid
        """
        validate_type(target_position, "target_position", Position)
        validate_type(speed, "speed", (int, float))
        
        if speed < 0:
            raise ValidationError("Speed must be non-negative", "speed", speed)
        
        dist = self.distance_to(target_position)
        if dist <= speed:
            self._x = target_position.x
            self._y = target_position.y
        else:
            ratio = speed / dist
            self._x += (target_position.x - self._x) * ratio
            self._y += (target_position.y - self._y) * ratio
    
    def move_random(self, speed):
        """
        Move in a random direction with the given speed.
        
        Args:
            speed (float): The distance to move
            
        Raises:
            ValidationError: If speed is not a positive number
        """
        validate_type(speed, "speed", (int, float))
        
        if speed < 0:
            raise ValidationError("Speed must be non-negative", "speed", speed)
        
        angle = random.uniform(0, 2 * math.pi)
        self._x += math.cos(angle) * speed
        self._y += math.sin(angle) * speed
    
    def __eq__(self, other):
        """
        Check if this position equals another position.
        
        Args:
            other: The position to compare with
            
        Returns:
            bool: True if positions are equal, False otherwise
        """
        if not isinstance(other, Position):
            return False
        return self._x == other.x and self._y == other.y
    
    def __str__(self):
        """
        Return a string representation of the position.
        
        Returns:
            str: String representation in format (x, y)
        """
        return f"({self._x:.2f}, {self._y:.2f})"
    
    def __repr__(self):
        """
        Return a detailed string representation of the position.
        
        Returns:
            str: Detailed string representation
        """
        return f"Position(x={self._x:.2f}, y={self._y:.2f})"
    
    def copy(self):
        """
        Create a copy of this position.
        
        Returns:
            Position: A new position with the same coordinates
        """
        return Position(self._x, self._y)
