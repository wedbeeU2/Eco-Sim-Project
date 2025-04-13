"""
Food resource module for the ecosystem simulation.
"""
import uuid
import random
import math
from src.core.position import Position
from src.utils.exceptions import validate_positive, validate_non_negative

class FoodResource:
    """
    Represents a food resource in the ecosystem that prey can forage.
    """
    
    def __init__(self, position, energy_value=30.0, size=1.0):
        """
        Initialize a food resource.
        
        Args:
            position (Position): The position of the resource
            energy_value (float): The base energy value of the resource
            size (float): The size of the resource, affects visibility and energy
        """
        self._id = uuid.uuid4()
        self._position = position
        self._base_energy = validate_positive(energy_value, "energy_value")
        self._size = validate_positive(size, "size")
        self._depletion = 0.0  # 0.0 = full, 1.0 = depleted
        self._max_depletion = 1.0
        self._is_active = True
        self._consumers = set()  # Track entities currently consuming this resource
        self._last_growth = 0.0  # Time tracker for regrowth
    
    @property
    def id(self):
        """Get the resource's unique identifier"""
        return self._id
    
    @property
    def position(self):
        """Get the resource's position"""
        return self._position
    
    @property
    def size(self):
        """Get the resource's size"""
        return self._size
    
    @property
    def is_active(self):
        """Check if the resource is active (not fully depleted)"""
        return self._is_active and self._depletion < self._max_depletion
    
    @property
    def depletion(self):
        """Get the resource's depletion level (0.0-1.0)"""
        return self._depletion
    
    @property
    def remaining_energy(self):
        """Get the remaining energy available in the resource"""
        if not self.is_active:
            return 0.0
        return self._base_energy * self._size * (1.0 - self._depletion)
    
    @property
    def consumer_count(self):
        """Get the number of entities currently consuming this resource"""
        return len(self._consumers)
    
    def update(self, world, time_delta):
        """
        Update the resource state.
        
        Args:
            world: The world environment
            time_delta (float): Time elapsed since last update
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Skip if inactive
            if not self._is_active:
                return False
            
            # Update growth timer
            self._last_growth += time_delta
            
            # Regrow resources gradually if not being consumed
            if self._consumers and self._last_growth >= 5.0:  # Every 5 seconds
                # Only regrow if not heavily consumed and partially depleted
                if self._depletion > 0.2 and self._depletion < 0.9:
                    # Small regrowth when being consumed
                    self._depletion = max(0.0, self._depletion - 0.05)
                
                self._last_growth = 0.0
            elif not self._consumers and self._last_growth >= 3.0:  # Faster regrowth when not consumed
                # Regrow faster when not being consumed
                regrowth_rate = 0.1 * time_delta  # 10% per second
                self._depletion = max(0.0, self._depletion - regrowth_rate)
                
                # If it was depleted and has regrown, make it active again
                if self._depletion < self._max_depletion:
                    self._is_active = True
                
                self._last_growth = 0.0
            
            # Clean up consumer list (remove any that moved away)
            self._consumers = {
                consumer for consumer in self._consumers
                if consumer.is_alive and 
                consumer.position.distance_to(self._position) < consumer.attributes.interaction_range
            }
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error updating food resource: {str(e)}")
            return False
    
    def consume(self, consumer, consumption_rate=0.1):
        """
        Consume energy from the resource.
        
        Args:
            consumer: The entity consuming the resource
            consumption_rate (float): Rate at which the resource is consumed
            
        Returns:
            float: Amount of energy gained by the consumer
        """
        try:
            # Skip if inactive or fully depleted
            if not self.is_active:
                return 0.0
            
            # Add to consumers set
            self._consumers.add(consumer)
            
            # Calculate base consumption
            base_consumption = consumption_rate * self._size * consumer.attributes.foraging_efficiency
            
            # Adjust for multiple consumers (competition)
            if self.consumer_count > 1:
                # Reduce consumption when multiple entities are feeding
                competition_factor = 1.0 / self.consumer_count
                actual_consumption = base_consumption * competition_factor
            else:
                actual_consumption = base_consumption
            
            # Calculate energy gain for consumer
            energy_gain = min(self.remaining_energy, actual_consumption)
            
            # Update depletion
            if self._base_energy * self._size > 0:
                depletion_increase = energy_gain / (self._base_energy * self._size)
                self._depletion = min(self._max_depletion, self._depletion + depletion_increase)
                
                # Check if fully depleted
                if self._depletion >= self._max_depletion:
                    self._is_active = False
            
            return energy_gain
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error consuming food resource: {str(e)}")
            return 0.0
