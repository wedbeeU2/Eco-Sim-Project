"""
SimulationClock module for managing time in the simulation.
"""
import time
from src.utils.exceptions import validate_non_negative, validate_positive, SimulationConfigError


class SimulationClock:
    """
    Manages time in the simulation.
    Provides utilities for controlling simulation speed and tracking time.
    """
    
    def __init__(self, time_scale=1.0):
        """
        Initialize the simulation clock.
        
        Args:
            time_scale (float): Multiplier for simulation speed (default: 1.0)
            
        Raises:
            ValidationError: If time_scale is not positive
        """
        self._current_time = 0.0
        self._time_scale = validate_positive(time_scale, "time_scale")
        self._real_start_time = None
        self._is_running = False
    
    @property
    def current_time(self):
        """Get the current simulation time"""
        return self._current_time
    
    @current_time.setter
    def current_time(self, value):
        """
        Set the current simulation time.
        
        Args:
            value (float): The new simulation time
            
        Raises:
            ValidationError: If value is negative
        """
        self._current_time = validate_non_negative(value, "current_time")
    
    @property
    def time_scale(self):
        """Get the time scale (simulation speed multiplier)"""
        return self._time_scale
    
    @property
    def is_running(self):
        """Check if the clock is running"""
        return self._is_running
    
    @property
    def real_elapsed_time(self):
        """
        Get the elapsed real time since the clock was started.
        
        Returns:
            float: Elapsed time in seconds, or 0 if clock hasn't started
            
        Raises:
            SimulationConfigError: If the clock hasn't been started
        """
        if self._real_start_time is None:
            raise SimulationConfigError("Clock has not been started yet")
        
        return time.time() - self._real_start_time
    
    def start(self):
        """
        Start the simulation clock.
        
        Returns:
            bool: True if clock was started, False if it was already running
        """
        if self._is_running:
            return False
        
        self._real_start_time = time.time()
        self._is_running = True
        return True
    
    def stop(self):
        """
        Stop the simulation clock.
        
        Returns:
            bool: True if clock was stopped, False if it wasn't running
        """
        if not self._is_running:
            return False
        
        self._is_running = False
        return True
    
    def reset(self):
        """
        Reset the simulation clock to zero.
        Stops the clock if it's running.
        
        Returns:
            bool: True if reset was successful
        """
        self._current_time = 0.0
        self._real_start_time = None
        self._is_running = False
        return True
    
    def tick(self, real_time_delta):
        """
        Update the simulation time based on real time delta.
        
        Args:
            real_time_delta (float): The elapsed real time since last update
            
        Returns:
            float: The simulation time delta that was applied
            
        Raises:
            ValidationError: If real_time_delta is negative
            SimulationConfigError: If the clock isn't running
        """
        validate_non_negative(real_time_delta, "real_time_delta")
        
        if not self._is_running:
            raise SimulationConfigError("Cannot tick a clock that isn't running")
        
        simulation_time_delta = real_time_delta * self._time_scale
        self._current_time += simulation_time_delta
        return simulation_time_delta
    
    def get_time(self):
        """
        Get the current simulation time.
        
        Returns:
            float: The current simulation time
        """
        return self._current_time
    
    def set_time_scale(self, scale):
        """
        Set the time scale (speed) of the simulation.
        
        Args:
            scale (float): The new time scale
            
        Returns:
            float: The new time scale after adjustment
            
        Raises:
            ValidationError: If scale is not positive
        """
        try:
            scale = validate_positive(scale, "scale")
        except Exception:
            # Ensure scale doesn't get too small
            scale = 0.1
        
        self._time_scale = scale
        return self._time_scale
    
    def get_formatted_time(self):
        """
        Get a formatted string of the current simulation time.
        
        Returns:
            str: Formatted time string (e.g., "Day 5, 12:30")
        """
        # Convert to days, hours, minutes
        total_seconds = self._current_time
        days = int(total_seconds / 86400)  # 86400 seconds in a day
        hours = int((total_seconds % 86400) / 3600)
        minutes = int((total_seconds % 3600) / 60)
        
        return f"Day {days}, {hours:02d}:{minutes:02d}"
