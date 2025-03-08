"""
Renderer module for visualizing the simulation using PyGame.
"""
import pygame
import sys
import math
from datetime import datetime
from src.utils.exceptions import validate_type, RenderingError, safe_operation
from src.core.enums import SeasonType


class Renderer:
    """
    Handles rendering of the simulation using PyGame.
    Provides visualization and user interface components.
    """
    
    def __init__(self, width, height, simulation):
        """
        Initialize the renderer with the given parameters.
        
        Args:
            width (int): Screen width
            height (int): Screen height
            simulation: The simulation to render
            
        Raises:
            RenderingError: If initialization fails
        """
        try:
            self._width = width
            self._height = height
            self._simulation = simulation
            
            # Initialize PyGame
            pygame.init()
            pygame.display.set_caption("Ecosystem Simulation")
            self._screen = pygame.display.set_mode((width, height))
            self._clock = pygame.time.Clock()
            
            # FPS settings
            self._target_fps = 60
            self._show_fps = True
            
            # Font initialization
            self._font = pygame.font.SysFont("Arial", 16)
            self._title_font = pygame.font.SysFont("Arial", 20, bold=True)
            self._large_font = pygame.font.SysFont("Arial", 24, bold=True)
            
            # Initialize colors
            self._init_colors()
            
            # Create UI elements
            self._buttons = []
            self._sliders = []
            self._create_ui()
            
            # Visualization settings
            self._grid_visible = False
            self._grid_size = 50
            self._entity_size_multiplier = 1.0
            self._show_stats = True
            self._show_detailed_stats = False
            
            # Animation frame counter
            self._frame_count = 0
            
            # Screenshot functionality
            self._screenshot_path = "screenshots/"
            import os
            os.makedirs(self._screenshot_path, exist_ok=True)
            
            # Tracking
            self._selected_entity = None
            self._tracked_entity = None
            self._tracking_active = False
        except Exception as e:
            raise RenderingError(f"Failed to initialize renderer: {str(e)}")
    
    def _init_colors(self):
        """
        Initialize color definitions.
        
        Returns:
            bool: True if initialization was successful
        """
        # Basic colors
        self._colors = {
            "white": (255, 255, 255),
            "black": (10, 10, 10),
            "gray": (128, 128, 128),
            "light_gray": (200, 200, 200),
            "dark_gray": (50, 50, 50),
            
            # Entity colors
            "predator": (220, 60, 60),      # Red
            "prey": (60, 180, 60),          # Green
            "invasive": (180, 60, 180),     # Purple
            
            # UI colors
            "background": (240, 240, 240),
            "ui_background": (200, 200, 200),
            "ui_border": (100, 100, 100),
            "ui_text": (10, 10, 10),
            "button": (100, 100, 100),
            "button_hover": (120, 120, 120),
            "button_text": (255, 255, 255),
            "slider_track": (150, 150, 150),
            "slider_handle": (80, 80, 80),
            
            # Seasonal colors
            "spring_bg": (230, 250, 230),
            "summer_bg": (250, 250, 230),
            "fall_bg": (250, 230, 200),
            "winter_bg": (230, 240, 250),
            
            # Status colors
            "healthy": (60, 180, 60),
            "warning": (220, 180, 60),
            "danger": (220, 60, 60),
            "info": (60, 140, 220),
        }
        
        # Season background colors
        self._season_colors = {
            SeasonType.SPRING: self._colors["spring_bg"],
            SeasonType.SUMMER: self._colors["summer_bg"],
            SeasonType.FALL: self._colors["fall_bg"],
            SeasonType.WINTER: self._colors["winter_bg"],
        }
        
        return True
    
    def _create_ui(self):
        """
        Create UI elements.
        
        Returns:
            bool: True if creation was successful
        """
        # Main control buttons
        self._buttons = [
            {
                "rect": pygame.Rect(20, self._height - 60, 100, 40),
                "text": "Start/Pause",
                "action": self._toggle_simulation,
                "tooltip": "Start or pause the simulation",
            },
            {
                "rect": pygame.Rect(130, self._height - 60, 100, 40),
                "text": "Reset",
                "action": self._reset_simulation,
                "tooltip": "Reset the simulation to initial state",
            },
            {
                "rect": pygame.Rect(240, self._height - 60, 150, 40),
                "text": "Add Invasive",
                "action": self._add_invasive_species,
                "tooltip": "Add invasive species to the simulation",
            },
            {
                "rect": pygame.Rect(400, self._height - 60, 120, 40),
                "text": "Export Data",
                "action": self._export_data,
                "tooltip": "Export simulation data to a CSV file",
            },
            {
                "rect": pygame.Rect(530, self._height - 60, 120, 40),
                "text": "Screenshot",
                "action": self._take_screenshot,
                "tooltip": "Take a screenshot of the current view",
            },
            {
                "rect": pygame.Rect(660, self._height - 60, 120, 40),
                "text": "Toggle Grid",
                "action": self._toggle_grid,
                "tooltip": "Show/hide the spatial grid",
            },
            {
                "rect": pygame.Rect(790, self._height - 60, 120, 40),
                "text": "Toggle Stats",
                "action": self._toggle_stats,
                "tooltip": "Show/hide detailed statistics",
            },
        ]
        
        # Sliders for simulation parameters
        slider_y = self._height - 120
        self._sliders = [
            {
                "rect": pygame.Rect(20, slider_y, 200, 20),
                "handle_rect": pygame.Rect(120, slider_y - 5, 10, 30),
                "label": "Time Scale",
                "min_value": 0.1,
                "max_value": 5.0,
                "current_value": 1.0,
                "format_func": lambda x: f"{x:.1f}x",
                "action": self._set_time_scale,
                "tooltip": "Adjust simulation speed",
            },
            {
                "rect": pygame.Rect(250, slider_y, 200, 20),
                "handle_rect": pygame.Rect(350, slider_y - 5, 10, 30),
                "label": "Entity Size",
                "min_value": 0.5,
                "max_value": 2.0,
                "current_value": 1.0,
                "format_func": lambda x: f"{x:.1f}x",
                "action": self._set_entity_size,
                "tooltip": "Adjust entity display size",
            },
        ]
        
        return True
    
    def _toggle_simulation(self):
        """
        Toggle the simulation between running and paused.
        
        Returns:
            bool: True if the toggle was successful
        """
        try:
            if self._simulation.is_running():
                self._simulation.pause()
            else:
                self._simulation.run()
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error toggling simulation: {e}")
            return False
    
    def _reset_simulation(self):
        """
        Reset the simulation.
        
        Returns:
            bool: True if reset was successful
        """
        try:
            return self._simulation.reset()
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error resetting simulation: {e}")
            return False
    
    def _add_invasive_species(self):
        """
        Add invasive species to the simulation.
        
        Returns:
            bool: True if addition was successful
        """
        try:
            return self._simulation.introduce_invasive_species(5)
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error adding invasive species: {e}")
            return False
    
    def _export_data(self):
        """
        Export simulation data.
        
        Returns:
            bool: True if export was successful
        """
        try:
            filename = self._simulation.export_data()
            from src.utils.exceptions import logger
            logger.info(f"Data exported to {filename}")
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error exporting data: {e}")
            return False
    
    def _take_screenshot(self):
        """
        Take a screenshot of the current simulation view.
        
        Returns:
            bool: True if screenshot was successful
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self._screenshot_path}screenshot_{timestamp}.png"
            pygame.image.save(self._screen, filename)
            from src.utils.exceptions import logger
            logger.info(f"Screenshot saved to {filename}")
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error taking screenshot: {e}")
            return False
    
    def _toggle_grid(self):
        """
        Toggle grid visibility.
        
        Returns:
            bool: True if toggle was successful
        """
        self._grid_visible = not self._grid_visible
        return True
    
    def _toggle_stats(self):
        """
        Toggle between basic and detailed statistics display.
        
        Returns:
            bool: True if toggle was successful
        """
        self._show_detailed_stats = not self._show_detailed_stats
        return True
    
    def _set_time_scale(self, value):
        """
        Set the simulation time scale.
        
        Args:
            value (float): The new time scale
            
        Returns:
            bool: True if setting was successful
        """
        try:
            self._simulation.set_time_scale(value)
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error setting time scale: {e}")
            return False
    
    def _set_entity_size(self, value):
        """
        Set the entity size multiplier.
        
        Args:
            value (float): The new entity size multiplier
            
        Returns:
            bool: True if setting was successful
        """
        self._entity_size_multiplier = value
        return True
    
    def _handle_slider(self, slider, mouse_pos):
        """
        Handle slider interaction.
        
        Args:
            slider (dict): The slider to handle
            mouse_pos (tuple): Current mouse position
            
        Returns:
            bool: True if handling was successful
        """
        # Check if mouse is within slider rect
        if slider["rect"].collidepoint(mouse_pos):
            # Calculate new value based on mouse position
            x_ratio = (mouse_pos[0] - slider["rect"].left) / slider["rect"].width
            new_value = slider["min_value"] + x_ratio * (slider["max_value"] - slider["min_value"])
            
            # Clamp to valid range
            new_value = max(slider["min_value"], min(slider["max_value"], new_value))
            
            # Update slider value
            slider["current_value"] = new_value
            
            # Update handle position
            slider["handle_rect"].centerx = mouse_pos[0]
            
            # Call action function
            if "action" in slider:
                slider["action"](new_value)
            
            return True
        
        return False
    
    def process_events(self):
        """
        Process PyGame events.
        
        Returns:
            bool: True if processing was successful, False if the program should exit
        """
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return False
                    elif event.key == pygame.K_SPACE:
                        self._toggle_simulation()
                    elif event.key == pygame.K_r:
                        self._reset_simulation()
                    elif event.key == pygame.K_i:
                        self._add_invasive_species()
                    elif event.key == pygame.K_g:
                        self._toggle_grid()
                    elif event.key == pygame.K_s:
                        self._toggle_stats()
                    elif event.key == pygame.K_p:
                        self._take_screenshot()
                    elif event.key == pygame.K_t:
                        # Toggle tracking
                        self._tracking_active = not self._tracking_active
                        if not self._tracking_active:
                            self._tracked_entity = None
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Handle button clicks
                    for button in self._buttons:
                        if button["rect"].collidepoint(mouse_pos):
                            button["action"]()
                    
                    # Handle slider clicks
                    for slider in self._sliders:
                        self._handle_slider(slider, mouse_pos)
                    
                    # Handle entity selection
                    if event.button == 1 and mouse_pos[1] < self._height - 150:  # Not in UI area
                        self._select_entity_at_position(mouse_pos)
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    pass
                
                elif event.type == pygame.MOUSEMOTION:
                    # Handle slider dragging
                    if pygame.mouse.get_pressed()[0]:  # Left button pressed
                        mouse_pos = pygame.mouse.get_pos()
                        for slider in self._sliders:
                            self._handle_slider(slider, mouse_pos)
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error processing events: {e}")
            return True  # Continue despite error
    
    def _select_entity_at_position(self, position):
        """
        Select an entity at the given position.
        
        Args:
            position (tuple): The position to check
            
        Returns:
            bool: True if selection was successful
        """
        try:
            from src.core.position import Position
            world_pos = Position(position[0], position[1])
            
            # Get entities near the position
            entities = self._simulation.world.get_entities_in_range(world_pos, 20)
            
            if entities:
                # Select the closest entity
                closest = min(entities, key=lambda e: world_pos.distance_to(e.position))
                self._selected_entity = closest
                
                # If tracking is active, set tracked entity
                if self._tracking_active:
                    self._tracked_entity = closest
                
                return True
            else:
                self._selected_entity = None
                return False
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error selecting entity: {e}")
            return False
    
    def _render_background(self):
        """
        Render the background.
        
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Get current season
            season = self._simulation.world.current_season
            
            # Set background color based on season
            if season in self._season_colors:
                bg_color = self._season_colors[season]
            else:
                bg_color = self._colors["background"]
            
            # Fill background
            self._screen.fill(bg_color)
            
            # Draw grid if visible
            if self._grid_visible:
                self._draw_grid()
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering background: {e}")
            return False
    
    def _draw_grid(self):
        """
        Draw the spatial grid.
        
        Returns:
            bool: True if drawing was successful
        """
        try:
            grid_color = self._colors["gray"] + (50,)  # Semi-transparent
            
            # Draw vertical lines
            for x in range(0, self._width, self._grid_size):
                pygame.draw.line(
                    self._screen,
                    grid_color,
                    (x, 0),
                    (x, self._height - 150),  # Stop at UI area
                    1
                )
            
            # Draw horizontal lines
            for y in range(0, self._height - 150, self._grid_size):
                pygame.draw.line(
                    self._screen,
                    grid_color,
                    (0, y),
                    (self._width, y),
                    1
                )
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error drawing grid: {e}")
            return False
    
    def _render_entities(self):
        """
        Render all entities.
        
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Get all entities
            entities = self._simulation.world.entities
            
            # First pass - draw entity bodies
            for entity in entities:
                if not entity.is_alive:
                    continue
                
                self._render_entity(entity)
            
            # Second pass - draw selection indicator and tracking info
            if self._selected_entity and self._selected_entity.is_alive:
                self._render_selection(self._selected_entity)
            
            if self._tracked_entity and self._tracked_entity.is_alive:
                self._render_tracking(self._tracked_entity)
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering entities: {e}")
            return False
    
    def _render_entity(self, entity):
        """
        Render a single entity.
        
        Args:
            entity: The entity to render
            
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Determine entity type and color
            from src.entities.predator import Predator
            from src.entities.prey import Prey
            from src.entities.invasive_species import InvasiveSpecies
            
            if isinstance(entity, Predator):
                base_color = self._colors["predator"]
            elif isinstance(entity, Prey):
                base_color = self._colors["prey"]
            elif isinstance(entity, InvasiveSpecies):
                base_color = self._colors["invasive"]
            else:
                base_color = self._colors["gray"]
            
            # Adjust color based on health
            health_factor = entity.health / 100.0
            color = (
                int(base_color[0] * health_factor),
                int(base_color[1] * health_factor),
                int(base_color[2] * health_factor)
            )
            
            # Calculate size based on age and maturity
            if entity.is_mature():
                base_size = 6.0
            else:
                # Gradually increase size as entity approaches maturity
                base_size = 3.0 + (3.0 * entity.age / entity.attributes.maturity_age)
            
            # Apply size multiplier
            size = base_size * self._entity_size_multiplier
            
            # Draw entity
            pygame.draw.circle(
                self._screen,
                color,
                (int(entity.position.x), int(entity.position.y)),
                int(size)
            )
            
            # Draw gender indicator
            from src.core.enums import Gender
            if entity.gender == Gender.MALE:
                gender_color = (100, 100, 255)  # Blue for male
            else:
                gender_color = (255, 100, 255)  # Pink for female
            
            pygame.draw.circle(
                self._screen,
                gender_color,
                (int(entity.position.x), int(entity.position.y)),
                int(size / 3)
            )
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering entity: {e}")
            return False
    
    def _render_selection(self, entity):
        """
        Render selection indicator for the selected entity.
        
        Args:
            entity: The selected entity
            
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Draw selection circle
            pygame.draw.circle(
                self._screen,
                self._colors["white"],
                (int(entity.position.x), int(entity.position.y)),
                int(10 * self._entity_size_multiplier),
                1
            )
            
            # Draw entity info tooltip
            self._render_entity_tooltip(entity)
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering selection: {e}")
            return False
    
    def _render_entity_tooltip(self, entity):
        """
        Render tooltip with entity information.
        
        Args:
            entity: The entity to render tooltip for
            
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Determine entity type
            from src.entities.predator import Predator
            from src.entities.prey import Prey
            from src.entities.invasive_species import InvasiveSpecies
            
            if isinstance(entity, Predator):
                entity_type = "Predator"
            elif isinstance(entity, Prey):
                entity_type = "Prey"
            elif isinstance(entity, InvasiveSpecies):
                entity_type = "Invasive"
            else:
                entity_type = "Entity"
            
            # Create tooltip text
            from src.core.enums import Gender
            gender_text = "Male" if entity.gender == Gender.MALE else "Female"
            tooltip_lines = [
                f"{entity_type} ({gender_text})",
                f"Health: {entity.health:.0f}%",
                f"Energy: {entity.energy:.0f}/{entity.attributes.max_energy:.0f}",
                f"Age: {entity.age:.1f} days",
                f"Mature: {'Yes' if entity.is_mature() else 'No'}"
            ]
            
            # Add reproduction info if available
            if hasattr(entity, "time_since_last_reproduction"):
                tooltip_lines.append(
                    f"Breeding: {entity.time_since_last_reproduction:.1f}/{entity.attributes.breeding_cycle:.1f}"
                )
            
            # Add adaptation level for invasive species
            if isinstance(entity, InvasiveSpecies):
                tooltip_lines.append(f"Adaptation: {entity.adaptation_level:.2f}")
            
            # Calculate tooltip dimensions
            line_height = 20
            tooltip_width = max(len(line) * 7, 150)
            tooltip_height = len(tooltip_lines) * line_height + 10
            
            # Position tooltip near entity but within screen
            tooltip_x = int(entity.position.x) + 20
            tooltip_y = int(entity.position.y) - tooltip_height // 2
            
            # Ensure tooltip stays within screen bounds
            if tooltip_x + tooltip_width > self._width:
                tooltip_x = int(entity.position.x) - tooltip_width - 20
            
            if tooltip_y < 0:
                tooltip_y = 0
            elif tooltip_y + tooltip_height > self._height - 150:
                tooltip_y = self._height - 150 - tooltip_height
            
            # Draw tooltip background
            pygame.draw.rect(
                self._screen,
                self._colors["ui_background"],
                pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height),
                border_radius=5
            )
            
            pygame.draw.rect(
                self._screen,
                self._colors["ui_border"],
                pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height),
                width=1,
                border_radius=5
            )
            
            # Draw tooltip text
            for i, line in enumerate(tooltip_lines):
                text = self._font.render(line, True, self._colors["ui_text"])
                self._screen.blit(text, (tooltip_x + 10, tooltip_y + 5 + i * line_height))
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering entity tooltip: {e}")
            return False
    
    def _render_tracking(self, entity):
        """
        Render tracking information for the tracked entity.
        
        Args:
            entity: The tracked entity
            
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Draw tracking indicator
            pygame.draw.circle(
                self._screen,
                (255, 255, 0),  # Yellow
                (int(entity.position.x), int(entity.position.y)),
                int(15 * self._entity_size_multiplier),
                2
            )
            
            # Draw "camera tracking" text in bottom left
            text = self._font.render(f"Tracking: {entity.__class__.__name__}", True, (255, 255, 0))
            self._screen.blit(text, (20, self._height - 150 - 30))
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering tracking: {e}")
            return False
    
    def _render_ui(self):
        """
        Render the user interface.
        
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Draw UI panel background
            ui_rect = pygame.Rect(0, self._height - 150, self._width, 150)
            pygame.draw.rect(self._screen, self._colors["ui_background"], ui_rect)
            pygame.draw.line(self._screen, self._colors["ui_border"], (0, self._height - 150), (self._width, self._height - 150), 2)
            
            # Draw statistics
            self._render_statistics()
            
            # Draw buttons
            self._render_buttons()
            
            # Draw sliders
            self._render_sliders()
            
            # Draw simulation info
            self._render_simulation_info()
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering UI: {e}")
            return False
    
    def _render_statistics(self):
        """
        Render simulation statistics.
        
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Get statistics
            stats = self._simulation.world.get_statistics()
            
            # Position for stats
            stats_x = 20
            stats_y = self._height - 145
            
            # Draw title
            title_text = self._title_font.render("Population Statistics", True, self._colors["ui_text"])
            self._screen.blit(title_text, (stats_x, stats_y))
            
            # Basic stats - always displayed
            basic_stats = [
                f"Predators: {stats['predator_count']}",
                f"Prey: {stats['prey_count']}",
                f"Invasive: {stats['invasive_count']}",
                f"Total: {stats['total_entities']}",
            ]
            
            for i, text in enumerate(basic_stats):
                color = self._colors["ui_text"]
                
                # Highlight extinction warnings
                if "Predators: 0" in text:
                    color = self._colors["danger"]
                elif "Prey: 0" in text:
                    color = self._colors["danger"]
                
                rendered_text = self._font.render(text, True, color)
                self._screen.blit(rendered_text, (stats_x, stats_y + 25 + i * 20))
            
            # Detailed stats - only if enabled
            if self._show_detailed_stats:
                detailed_stats = [
                    f"Males: {stats['male_count']} | Females: {stats['female_count']}",
                    f"Mature: {stats['mature_count']} | Immature: {stats['immature_count']}",
                    f"Avg Health: {stats['avg_health']:.1f}% | Avg Energy: {stats['avg_energy']:.1f}",
                    f"Season: {stats['season']}",
                ]
                
                for i, text in enumerate(detailed_stats):
                    rendered_text = self._font.render(text, True, self._colors["ui_text"])
                    self._screen.blit(rendered_text, (stats_x + 200, stats_y + 25 + i * 20))
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering statistics: {e}")
            return False
    
    def _render_buttons(self):
        """
        Render UI buttons.
        
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Get mouse position for hover effects
            mouse_pos = pygame.mouse.get_pos()
            
            for button in self._buttons:
                # Check if mouse is hovering over button
                if button["rect"].collidepoint(mouse_pos):
                    color = self._colors["button_hover"]
                    
                    # Draw tooltip if defined
                    if "tooltip" in button:
                        self._render_tooltip(button["tooltip"], mouse_pos)
                else:
                    color = self._colors["button"]
                
                # Draw button
                pygame.draw.rect(
                    self._screen,
                    color,
                    button["rect"],
                    border_radius=5
                )
                
                # Draw button text
                text = self._font.render(button["text"], True, self._colors["button_text"])
                text_rect = text.get_rect(center=button["rect"].center)
                self._screen.blit(text, text_rect)
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering buttons: {e}")
            return False
    
    def _render_sliders(self):
        """
        Render UI sliders.
        
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Get mouse position for hover effects
            mouse_pos = pygame.mouse.get_pos()
            
            for slider in self._sliders:
                # Draw slider label
                label_text = self._font.render(slider["label"], True, self._colors["ui_text"])
                self._screen.blit(label_text, (slider["rect"].left, slider["rect"].top - 20))
                
                # Draw slider value
                value_text = self._font.render(
                    slider["format_func"](slider["current_value"]),
                    True,
                    self._colors["ui_text"]
                )
                self._screen.blit(value_text, (slider["rect"].right + 10, slider["rect"].top - 5))
                
                # Draw slider track
                pygame.draw.rect(
                    self._screen,
                    self._colors["slider_track"],
                    slider["rect"],
                    border_radius=3
                )
                
                # Update handle position based on current value
                value_ratio = (slider["current_value"] - slider["min_value"]) / (slider["max_value"] - slider["min_value"])
                handle_x = slider["rect"].left + value_ratio * slider["rect"].width
                slider["handle_rect"].centerx = handle_x
                
                # Draw slider handle
                pygame.draw.rect(
                    self._screen,
                    self._colors["slider_handle"],
                    slider["handle_rect"],
                    border_radius=5
                )
                
                # Draw tooltip if mouse is hovering over slider and tooltip is defined
                if slider["rect"].collidepoint(mouse_pos) and "tooltip" in slider:
                    self._render_tooltip(slider["tooltip"], mouse_pos)
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering sliders: {e}")
            return False
    
    def _render_tooltip(self, text, position):
        """
        Render a tooltip at the given position.
        
        Args:
            text (str): The tooltip text
            position (tuple): The position to render at
            
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Create tooltip surface
            tooltip_text = self._font.render(text, True, self._colors["ui_text"])
            tooltip_width = tooltip_text.get_width() + 20
            tooltip_height = tooltip_text.get_height() + 10
            
            # Position tooltip above mouse
            tooltip_x = position[0] - tooltip_width // 2
            tooltip_y = position[1] - tooltip_height - 10
            
            # Ensure tooltip stays within screen bounds
            if tooltip_x < 0:
                tooltip_x = 0
            elif tooltip_x + tooltip_width > self._width:
                tooltip_x = self._width - tooltip_width
            
            if tooltip_y < 0:
                tooltip_y = position[1] + 20
            
            # Draw tooltip background
            pygame.draw.rect(
                self._screen,
                self._colors["light_gray"],
                pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height),
                border_radius=3
            )
            
            # Draw tooltip border
            pygame.draw.rect(
                self._screen,
                self._colors["dark_gray"],
                pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height),
                width=1,
                border_radius=3
            )
            
            # Draw tooltip text
            self._screen.blit(tooltip_text, (tooltip_x + 10, tooltip_y + 5))
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering tooltip: {e}")
            return False
    
    def _render_simulation_info(self):
        """
        Render simulation information.
        
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Position for info
            info_x = self._width - 300
            info_y = self._height - 145
            
            # Draw title
            title_text = self._title_font.render("Simulation Info", True, self._colors["ui_text"])
            self._screen.blit(title_text, (info_x, info_y))
            
            # Draw simulation time
            time_text = self._font.render(
                f"Time: {self._simulation.get_simulation_time()}",
                True,
                self._colors["ui_text"]
            )
            self._screen.blit(time_text, (info_x, info_y + 25))
            
            # Draw simulation status
            status_text = self._font.render(
                f"Status: {'Running' if self._simulation.is_running() else 'Paused'}",
                True,
                self._colors["healthy"] if self._simulation.is_running() else self._colors["warning"]
            )
            self._screen.blit(status_text, (info_x, info_y + 45))
            
            # Draw time scale
            scale_text = self._font.render(
                f"Time Scale: {self._simulation.get_time_scale():.1f}x",
                True,
                self._colors["ui_text"]
            )
            self._screen.blit(scale_text, (info_x, info_y + 65))
            
            # Draw FPS
            fps_text = self._font.render(
                f"FPS: {self._simulation.get_fps():.1f}",
                True,
                self._colors["ui_text"]
            )
            self._screen.blit(fps_text, (info_x, info_y + 85))
            
            # Draw current season
            season = self._simulation.world.current_season
            season_text = self._font.render(
                f"Season: {season.name if season else 'None'}",
                True,
                self._colors["ui_text"]
            )
            self._screen.blit(season_text, (info_x, info_y + 105))
            
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error rendering simulation info: {e}")
            return False
    
    def render(self):
        """
        Render the current state of the simulation.
        
        Returns:
            bool: True if rendering was successful
        """
        try:
            # Render background
            self._render_background()
            
            # Render entities
            self._render_entities()
            
            # Render UI
            self._render_ui()
            
            # Update the display
            pygame.display.flip()
            
            # Limit frame rate
            self._clock.tick(self._target_fps)
            
            # Increment frame counter
            self._frame_count += 1
            
            return True
        except Exception as e:
            raise RenderingError(f"Rendering failed: {str(e)}")
    
    def cleanup(self):
        """
        Clean up resources used by the renderer.
        
        Returns:
            bool: True if cleanup was successful
        """
        try:
            pygame.quit()
            return True
        except Exception as e:
            from src.utils.exceptions import logger
            logger.error(f"Error during renderer cleanup: {e}")
            return False
