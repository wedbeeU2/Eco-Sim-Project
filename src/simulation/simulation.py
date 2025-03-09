"""
Simulation controller module for the ecosystem simulation.
"""
import time
import os
import random
from datetime import datetime
from src.simulation.world import World
from src.simulation.clock import SimulationClock
from src.simulation.data_collector import DataCollector
from src.core.position import Position
from src.core.enums import Gender, SeasonType
from src.utils.exceptions import (
    validate_positive, validate_non_negative, SimulationConfigError, 
    safe_operation, validate_type
)


class Simulation:
    """
    Main simulation controller.
    Manages the world, entities, time, and data collection.
    """
    
    def __init__(self, world_width=1000, world_height=800, data_dir="data"):
        """
        Initialize the simulation.
        
        Args:
            world_width (float): Width of the world (default: 1000)
            world_height (float): Height of the world (default: 800)
            data_dir (str): Directory for data output (default: "data")
            
        Raises:
            SimulationConfigError: If initialization fails
        """
        try:
            # Validate parameters
            validate_positive(world_width, "world_width")
            validate_positive(world_height, "world_height")
            
            self._world = World(world_width, world_height)
            self._clock = SimulationClock()
            self._data_collector = DataCollector(data_dir)
            
            self._running = False
            self._last_update_time = 0
            self._data_collection_interval = 1.0  # Collect data every second of simulation time
            self._last_data_collection = 0
            
            # Season management
            self._season_duration = 90 * 86400  # 90 days in seconds
            self._current_season = SeasonType.SPRING
            
            # Performance metrics
            self._frame_count = 0
            self._last_fps_check = 0
            self._current_fps = 0
            
            # Custom events
            self._event_queue = []
            self._event_handlers = {}
            
            # Register default event handlers
            self._register_default_event_handlers()
        except Exception as e:
            raise SimulationConfigError(f"Failed to initialize simulation: {str(e)}")
    
    @property
    def world(self):
        """Get the simulation world"""
        return self._world
    
    @property
    def clock(self):
        """Get the simulation clock"""
        return self._clock
    
    @property
    def data_collector(self):
        """Get the data collector"""
        return self._data_collector
    
    def _register_default_event_handlers(self):
        """Register default event handlers"""
        # Season change handler
        self._register_event_handler("season_change", self._handle_season_change)
        
        # Population threshold handlers
        self._register_event_handler("predator_extinction", self._handle_predator_extinction)
        self._register_event_handler("prey_extinction", self._handle_prey_extinction)
    
    def _register_event_handler(self, event_type, handler):
        """
        Register an event handler.
        
        Args:
            event_type (str): The type of event
            handler (callable): The event handler function
            
        Returns:
            bool: True if registration was successful
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        return True
    
    def _trigger_event(self, event_type, **kwargs):
        """
        Trigger an event.
        
        Args:
            event_type (str): The type of event
            **kwargs: Event parameters
            
        Returns:
            bool: True if event was triggered successfully
        """
        # Add event to queue
        self._event_queue.append({
            "type": event_type,
            "time": self._clock.get_time(),
            "params": kwargs
        })
        
        return True
    
    def _process_events(self):
        """
        Process all pending events.
        
        Returns:
            bool: True if event processing was successful
        """
        if not self._event_queue:
            return True
        
        # Process all events in queue
        events_to_process = list(self._event_queue)
        self._event_queue.clear()
        
        for event in events_to_process:
            # Call handlers for this event type
            if event["type"] in self._event_handlers:
                for handler in self._event_handlers[event["type"]]:
                    try:
                        handler(**event["params"])
                    except Exception as e:
                        from src.utils.exceptions import logger
                        logger.error(f"Error in event handler for {event['type']}: {e}")
        
        return True
    
    def _handle_season_change(self, old_season, new_season):
        """
        Handle season change event.
        
        Args:
            old_season (SeasonType): The previous season
            new_season (SeasonType): The new season
            
        Returns:
            bool: True if handling was successful
        """
        # Update world season
        self._world.current_season = new_season
        
        # Log season change
        from src.utils.exceptions import logger
        logger.info(f"Season changed from {old_season.name} to {new_season.name} at time {self._clock.get_formatted_time()}")
        
        return True
    
    def _handle_predator_extinction(self):
        """
        Handle predator extinction event.
        
        Returns:
            bool: True if handling was successful
        """
        from src.utils.exceptions import logger
        logger.warning(f"Predator extinction at time {self._clock.get_formatted_time()}")
        
        # Could add recovery mechanisms here
        return True
    
    def _handle_prey_extinction(self):
        """
        Handle prey extinction event.
        
        Returns:
            bool: True if handling was successful
        """
        from src.utils.exceptions import logger
        logger.warning(f"Prey extinction at time {self._clock.get_formatted_time()}")
        
        # Could add recovery mechanisms here
        return True
    
    def _update_season(self):
        """
        Update the current season based on simulation time.
        
        Returns:
            bool: True if update was successful
        """
        # Calculate the current season based on time
        season_index = int((self._clock.get_time() % (4 * self._season_duration)) / self._season_duration)
        
        # Convert index to season
        new_season = list(SeasonType)[season_index]
        
        # If season changed, trigger event
        if new_season != self._current_season:
            self._trigger_event("season_change", old_season=self._current_season, new_season=new_season)
            self._current_season = new_season
        
        return True
    
    def _check_population_thresholds(self):
        """
        Check population thresholds and trigger events if needed.
        
        Returns:
            bool: True if check was successful
        """
        # Get current statistics
        stats = self._world.get_statistics()
        
        # Check predator extinction
        if stats["predator_count"] == 0 and not self._event_queue:
            self._trigger_event("predator_extinction")
        
        # Check prey extinction
        if stats["prey_count"] == 0 and not self._event_queue:
            self._trigger_event("prey_extinction")
        
        return True
    
    def _update_performance_metrics(self):
        """
        Update performance metrics.
        
        Returns:
            bool: True if update was successful
        """
        self._frame_count += 1
        
        # Update FPS every second
        current_time = time.time()
        if current_time - self._last_fps_check >= 1.0:
            self._current_fps = self._frame_count / (current_time - self._last_fps_check)
            self._frame_count = 0
            self._last_fps_check = current_time
        
        return True
    
    def initialize(self, predator_count=25, prey_count=75, invasive_count=0):
        """
        Initialize the simulation with entities.
        
        Args:
            predator_count (int): Number of predators to create (default: 10)
            prey_count (int): Number of prey to create (default: 100)
            invasive_count (int): Number of invasive species to create (default: 0)
            
        Returns:
            bool: True if initialization was successful
            
        Raises:
            SimulationConfigError: If initialization fails
        """
        try:
            # Validate parameters
            validate_non_negative(predator_count, "predator_count")
            validate_non_negative(prey_count, "prey_count")
            validate_non_negative(invasive_count, "invasive_count")
            
            # Clear any existing entities
            self._world.clear()
            
            # Reset clock and data collection
            self._clock.reset()
            self._data_collector.clear_data()
            
            # Reset internal state
            self._last_update_time = 0
            self._last_data_collection = 0
            self._current_season = SeasonType.SPRING
            self._world.current_season = SeasonType.SPRING
            
            # Create initial predators
            from src.entities.predator import Predator
            for _ in range(predator_count):
                position = Position(
                    random.uniform(0, self._world.width),
                    random.uniform(0, self._world.height)
                )
                gender = random.choice(list(Gender))
                predator = Predator(position, gender)
                self._world.add_entity(predator)
            
            # Create initial prey
            from src.entities.prey import Prey
            for _ in range(prey_count):
                position = Position(
                    random.uniform(0, self._world.width),
                    random.uniform(0, self._world.height)
                )
                gender = random.choice(list(Gender))
                prey = Prey(position, gender)
                self._world.add_entity(prey)
            
            # Create initial invasive species
            from src.entities.invasive_species import InvasiveSpecies
            for _ in range(invasive_count):
                position = Position(
                    random.uniform(0, self._world.width),
                    random.uniform(0, self._world.height)
                )
                gender = random.choice(list(Gender))
                invasive = InvasiveSpecies(position, gender)
                self._world.add_entity(invasive)
            
            # Start the clock
            self._clock.start()
            
            # Collect initial data
            self._collect_data()
            
            return True
        except Exception as e:
            raise SimulationConfigError(f"Failed to initialize simulation: {str(e)}")
    
    def update(self):
        """
        Update the simulation state.
        
        Returns:
            bool: True if update was successful
            
        Raises:
            SimulationConfigError: If update fails
        """
        if not self._running:
            return False
        
        try:
            current_time = time.time()
            
            if self._last_update_time == 0:
                real_time_delta = 0.001  # Small non-zero value for first update
            else:
                real_time_delta = max(0.001, current_time - self._last_update_time)  # Ensure non-zero
            
            # Tick the clock
            simulation_time_delta = self._clock.tick(real_time_delta)
            
            # Update the world
            self._world.update(simulation_time_delta)
            
            # Update season
            self._update_season()
            
            # Process events
            self._process_events()
            
            # Check population thresholds
            self._check_population_thresholds()
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Check if it's time to collect data
            if self._clock.get_time() - self._last_data_collection >= self._data_collection_interval:
                self._collect_data()
                self._last_data_collection = self._clock.get_time()
            
            self._last_update_time = current_time
            
            return True
        except Exception as e:
            raise SimulationConfigError(f"Failed to update simulation: {str(e)}")
    
    def _collect_data(self):
        """
        Collect current simulation data.
        
        Returns:
            bool: True if data collection was successful
            
        Raises:
            SimulationConfigError: If data collection fails
        """
        try:
            # Get statistics from world
            metrics = self._world.get_statistics()
            
            # Record metrics
            self._data_collector.record_metrics(self._clock.get_time(), metrics)
            
            return True
        except Exception as e:
            raise SimulationConfigError(f"Failed to collect data: {str(e)}")
    
    def run(self):
        """
        Start the simulation.
        
        Returns:
            bool: True if the simulation was started
        """
        if self._running:
            return False
        
        self._running = True
        
        if self._last_update_time == 0:
            self._last_update_time = time.time()
            self._last_fps_check = time.time()
        
        return True
    
    def pause(self):
        """
        Pause the simulation.
        
        Returns:
            bool: True if the simulation was paused
        """
        if not self._running:
            return False
        
        self._running = False
        return True
    
    def reset(self):
        """
        Reset the simulation.
    
        Returns:
            bool: True if reset was successful
        """
        try:
            # Stop the simulation before resetting
            was_running = self._running
            self._running = False
        
            # Clear the world
            self._world.clear()
        
            # Reset clock and data collection
            self._clock.reset()
            self._data_collector.clear_data()
        
            # Reset internal state
            self._last_update_time = 0
            self._last_data_collection = 0
            self._current_season = SeasonType.SPRING
            self._world.current_season = SeasonType.SPRING
        
            # Create entities same as initialize
            from src.entities.predator import Predator
            from src.entities.prey import Prey
            from src.core.position import Position
            from src.core.enums import Gender
        
            # Get values from last initialization
            predator_count = sum(1 for entity in self._world.entities if isinstance(entity, Predator))
            prey_count = sum(1 for entity in self._world.entities if isinstance(entity, Prey))
        
            # Use default values if empty
            if predator_count == 0:
                predator_count = 10
            if prey_count == 0:
                prey_count = 100
            
            # Create predators
            for _ in range(predator_count):
                position = Position(
                    random.uniform(0, self._world.width),
                    random.uniform(0, self._world.height)
                )
                gender = random.choice(list(Gender))
                predator = Predator(position, gender)
                self._world.add_entity(predator)
        
            # Create prey
            for _ in range(prey_count):
                position = Position(
                    random.uniform(0, self._world.width),
                    random.uniform(0, self._world.height)
                )
                gender = random.choice(list(Gender))
                prey = Prey(position, gender)
                self._world.add_entity(prey)
        
            # Start the clock
            self._clock.start()
        
            # Collect initial data
            self._collect_data()
        
            # Restore running state if it was running
            if was_running:
                self._running = True
        
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error resetting simulation: {str(e)}")
            return False
    
    def is_running(self):
        """
        Check if the simulation is running.
        
        Returns:
            bool: True if the simulation is running
        """
        return self._running
    
    def get_simulation_time(self):
        """
        Get the current simulation time as a formatted string.
        
        Returns:
            str: Formatted simulation time
        """
        return self._clock.get_formatted_time()
    
    def get_simulation_time_seconds(self):
        """
        Get the current simulation time in seconds.
        
        Returns:
            float: Simulation time in seconds
        """
        return self._clock.get_time()
    
    def set_time_scale(self, scale):
        """
        Set the simulation time scale.
        
        Args:
            scale (float): The new time scale
            
        Returns:
            float: The new time scale
            
        Raises:
            SimulationConfigError: If time scale setting fails
        """
        try:
            validate_positive(scale, "scale")
            return self._clock.set_time_scale(scale)
        except Exception as e:
            raise SimulationConfigError(f"Failed to set time scale: {str(e)}")
    
    def get_time_scale(self):
        """
        Get the current simulation time scale.
        
        Returns:
            float: The current time scale
        """
        return self._clock.time_scale
    
    def get_fps(self):
        """
        Get the current frames per second.
        
        Returns:
            float: The current FPS
        """
        return self._current_fps
    
    def introduce_invasive_species(self, count=5):
        """
        Introduce invasive species into the ecosystem.
        
        Args:
            count (int): Number of invasive species to introduce
            
        Returns:
            bool: True if introduction was successful
            
        Raises:
            SimulationConfigError: If introduction fails
        """
        try:
            validate_positive(count, "count")
            
            from src.entities.invasive_species import InvasiveSpecies
            for _ in range(count):
                position = Position(
                    random.uniform(0, self._world.width),
                    random.uniform(0, self._world.height)
                )
                gender = random.choice(list(Gender))
                invasive = InvasiveSpecies(position, gender)
                self._world.add_entity(invasive)
            
            from src.utils.exceptions import logger
            logger.info(f"Introduced {count} invasive species at time {self.get_simulation_time()}")
            
            return True
        except Exception as e:
            raise SimulationConfigError(f"Failed to introduce invasive species: {str(e)}")
    
    def export_data(self, filename=None):
        """
        Export collected data.
        
        Args:
            filename (str, optional): Output filename
            
        Returns:
            str: Path to the exported data file
            
        Raises:
            SimulationConfigError: If export fails
        """
        try:
            return self._data_collector.export_data(filename)
        except Exception as e:
            raise SimulationConfigError(f"Failed to export data: {str(e)}")
    
    def generate_report(self):
        """
        Generate a report of the simulation results.
        
        Returns:
            str: Simulation report
            
        Raises:
            SimulationConfigError: If report generation fails
        """
        try:
            return self._data_collector.generate_report()
        except Exception as e:
            raise SimulationConfigError(f"Failed to generate report: {str(e)}")
    
    def analyze_population_dynamics(self):
        """
        Analyze population dynamics.
        
        Returns:
            dict: Analysis results
            
        Raises:
            SimulationConfigError: If analysis fails
        """
        try:
            return self._data_collector.analyze_population_dynamics()
        except Exception as e:
            raise SimulationConfigError(f"Failed to analyze population dynamics: {str(e)}")
