"""
Template-based behavior system for entity actions and decision-making.
This module provides reusable behavior templates that can be applied to different entities.
"""
from abc import ABC, abstractmethod
import random
import math


class BehaviorAction(ABC):
    """Abstract base class for entity behavior actions"""
    
    def __init__(self, entity):
        """Initialize the action with an entity"""
        self._entity = entity
    
    @property
    def entity(self):
        """Get the entity associated with this action"""
        return self._entity
    
    @abstractmethod
    def can_perform(self, world):
        """Check if the action can be performed in the current state"""
        pass
    
    @abstractmethod
    def perform(self, world):
        """Execute the action"""
        pass
    
    @abstractmethod
    def calculate_utility(self, world):
        """Calculate the utility value of this action in the current state"""
        pass


class MoveAction(BehaviorAction):
    """Template for movement-based actions"""
    
    def __init__(self, entity, target_position=None):
        super().__init__(entity)
        self._target_position = target_position
    
    @property
    def target_position(self):
        """Get the target position for movement"""
        return self._target_position
    
    @target_position.setter
    def target_position(self, value):
        """Set the target position for movement"""
        self._target_position = value
    
    def can_perform(self, world):
        """Check if movement is possible"""
        return self.entity.energy > 0 and self.entity.is_alive
    
    def perform(self, world):
        """Execute the movement"""
        if self.target_position:
            self.entity.position.move_towards(self.target_position, self.entity.attributes.speed)
        else:
            self.entity.position.move_random(self.entity.attributes.speed)
        
        # Ensure entity stays within world boundaries
        world.enforce_boundaries(self.entity)
        
        # Energy cost for movement
        energy_cost = 0.1 * self.entity.attributes.energy_consumption
        self.entity.energy -= energy_cost
        
        return True
    
    def calculate_utility(self, world):
        """Calculate movement utility (template method)"""
        # Base utility
        base_utility = 0.5
        
        # Subclasses should override this to provide specific utility calculation
        return base_utility


class FleeAction(MoveAction):
    """Template for fleeing from threats"""
    
    def __init__(self, entity, threat):
        super().__init__(entity)
        self._threat = threat
        
        # Calculate direction away from threat
        flee_x = entity.position.x + (entity.position.x - threat.position.x)
        flee_y = entity.position.y + (entity.position.y - threat.position.y)
        
        from src.core.position import Position
        self.target_position = Position(flee_x, flee_y)
    
    @property
    def threat(self):
        """Get the threat entity"""
        return self._threat
    
    def calculate_utility(self, world):
        """Calculate fleeing utility based on threat proximity and energy"""
        # Base utility from parent
        base_utility = super().calculate_utility(world)
        
        # Distance to threat factor (closer = higher utility)
        distance = self.entity.position.distance_to(self.threat.position)
        perception_range = getattr(self.entity.attributes, 'perception_range', 100.0)
        distance_factor = 1.0 - min(1.0, distance / perception_range)
        
        # Energy factor (lower energy = lower utility to flee)
        energy_factor = self.entity.energy / self.entity.attributes.max_energy
        
        # Health factor (lower health = higher utility to flee)
        health_factor = 1.0 - (self.entity.health / 100.0)
        
        # Combined utility
        return base_utility + (3.0 * distance_factor * energy_factor) + health_factor


class ForageAction(MoveAction):
    """Template for foraging behavior"""
    
    def perform(self, world):
        """Execute foraging behavior"""
        # Move while foraging
        super().perform(world)
        
        # Calculate energy gained
        efficiency = getattr(self.entity.attributes, 'foraging_efficiency', 10.0)
        energy_gained = efficiency * random.uniform(0.5, 1.0)
        
        # Add energy
        self.entity.energy = min(self.entity.attributes.max_energy, 
                                self.entity.energy + energy_gained)
        
        return True
    
    def calculate_utility(self, world):
        """Calculate foraging utility based on energy needs"""
        # Base utility from parent
        base_utility = super().calculate_utility(world)
        
        # Energy need factor (lower energy = higher utility)
        energy_factor = 1.0 - (self.entity.energy / self.entity.attributes.max_energy)
        
        # Energy threshold factor (higher utility when below 60% energy)
        threshold_factor = 2.0 if self.entity.energy < 0.6 * self.entity.attributes.max_energy else 0.5
        
        return base_utility + (energy_factor * threshold_factor)


class HuntAction(MoveAction):
    """Template for hunting behavior"""
    
    def __init__(self, entity, prey):
        super().__init__(entity, prey.position)
        self._prey = prey
    
    @property
    def prey(self):
        """Get the prey target"""
        return self._prey
    
    def can_perform(self, world):
        """Check if hunting is possible"""
        return (super().can_perform(world) and 
                self.prey.is_alive and 
                self.entity.energy < 0.9 * self.entity.attributes.max_energy)
    
    def perform(self, world):
        """Execute hunting behavior"""
        # Move towards prey
        super().perform(world)
        
        # Check if close enough to attack
        attack_range = getattr(self.entity.attributes, 'interaction_range', 10.0)
        if self.entity.position.distance_to(self.prey.position) < attack_range:
            # Attack success probability based on health and energy
            attack_success = random.random() < (self.entity.health / 100) * (self.entity.energy / self.entity.attributes.max_energy)
            
            if attack_success:
                # Successful hunt
                prey_energy = self.prey.energy
                self.prey.health = 0  # Kill the prey
                
                # Gain energy from prey
                digest_efficiency = getattr(self.entity.attributes, 'digest_efficiency', 0.5)
                energy_gained = prey_energy * digest_efficiency
                self.entity.energy = min(self.entity.attributes.max_energy, 
                                        self.entity.energy + energy_gained)
                
                return True
        
        return False
    
    def calculate_utility(self, world):
        """Calculate hunting utility based on hunger and prey vulnerability"""
        # Base utility from parent
        base_utility = super().calculate_utility(world)
        
        # Hunger factor (lower energy = higher utility)
        hunger_factor = 1.0 - (self.entity.energy / self.entity.attributes.max_energy)
        
        # Prey vulnerability factor (lower health/energy = higher utility)
        prey_vulnerability = 1.0 - ((self.prey.health / 100.0) * (self.prey.energy / self.prey.attributes.max_energy))
        
        # Distance factor (closer = higher utility)
        distance = self.entity.position.distance_to(self.prey.position)
        hunting_range = getattr(self.entity.attributes, 'hunting_range', 50.0)
        distance_factor = 1.0 - min(1.0, distance / hunting_range)
        
        return base_utility + (2.0 * hunger_factor) + (prey_vulnerability * 0.5) + distance_factor


class BehaviorSystem:
    """Template-based behavior system for entity decision-making"""
    
    def __init__(self, entity):
        """Initialize the behavior system for an entity"""
        self._entity = entity
        self._available_actions = []
    
    @property
    def entity(self):
        """Get the entity associated with this behavior system"""
        return self._entity
    
    def add_action(self, action):
        """Add an action to the available actions list"""
        self._available_actions.append(action)
    
    def clear_actions(self):
        """Clear all available actions"""
        self._available_actions.clear()
    
    def select_action(self, world):
        """Select the best action based on utility calculations"""
        # Filter actions that can be performed
        valid_actions = [action for action in self._available_actions if action.can_perform(world)]
        
        if not valid_actions:
            return None
        
        # Calculate utility for each action
        action_utilities = [(action, action.calculate_utility(world)) for action in valid_actions]
        
        # Convert utilities to selection probabilities using softmax
        total = sum(math.exp(utility) for _, utility in action_utilities)
        probabilities = [math.exp(utility) / total for _, utility in action_utilities]
        
        # Select action based on probabilities
        selected_index = random.choices(range(len(valid_actions)), weights=probabilities, k=1)[0]
        
        return valid_actions[selected_index]
    
    def update(self, world):
        """Update the behavior system and execute selected action"""
        # Generate available actions based on entity state and surroundings
        self.generate_actions(world)
        
        # Select the best action
        selected_action = self.select_action(world)
        
        # Perform the selected action
        if selected_action:
            return selected_action.perform(world)
        
        return False
    
    def generate_actions(self, world):
        """Generate available actions based on current state"""
        # This should be implemented by specific behavior systems
        pass


class PreyBehaviorSystem(BehaviorSystem):
    """Behavior system for prey entities"""
    
    def generate_actions(self, world):
        """Generate prey-specific actions"""
        self.clear_actions()
        
        # Add basic movement action
        self.add_action(MoveAction(self.entity))
        
        # Add foraging action
        self.add_action(ForageAction(self.entity))
        
        # Check for nearby predators
        from src.entities.predator import Predator
        perception_range = getattr(self.entity.attributes, 'perception_range', 80.0)
        predators_nearby = [
            entity for entity in world.get_entities_in_range(
                self.entity.position, perception_range
            )
            if isinstance(entity, Predator) and entity.is_alive
        ]
        
        # Add flee actions for each nearby predator
        for predator in predators_nearby:
            self.add_action(FleeAction(self.entity, predator))


class PredatorBehaviorSystem(BehaviorSystem):
    """Behavior system for predator entities"""
    
    def generate_actions(self, world):
        """Generate predator-specific actions"""
        self.clear_actions()
        
        # Add basic movement action
        self.add_action(MoveAction(self.entity))
        
        # Check for nearby prey
        from src.entities.prey import Prey
        hunting_range = getattr(self.entity.attributes, 'hunting_range', 75.0)
        prey_in_range = [
            entity for entity in world.get_entities_in_range(
                self.entity.position, hunting_range
            )
            if isinstance(entity, Prey) and entity.is_alive
        ]
        
        # Add hunt actions for each nearby prey
        for prey in prey_in_range:
            self.add_action(HuntAction(self.entity, prey))


class InvasiveSpeciesBehaviorSystem(BehaviorSystem):
    """Behavior system for invasive species entities"""
    
    def generate_actions(self, world):
        """Generate invasive species-specific actions"""
        self.clear_actions()
        
        # Add basic movement action
        self.add_action(MoveAction(self.entity))
        
        # Add foraging action (more efficient than prey)
        self.add_action(ForageAction(self.entity))
        
        # Add competition action for nearby native species
        from src.entities.predator import Predator
        from src.entities.prey import Prey
        
        competition_range = getattr(self.entity.attributes, 'interaction_range', 60.0)
        natives = [
            entity for entity in world.get_entities_in_range(
                self.entity.position, competition_range
            )
            if (isinstance(entity, Prey) or isinstance(entity, Predator)) and entity.is_alive
        ]
        
        # Add competition actions for native species
        for native in natives:
            self.add_action(CompeteAction(self.entity, native))


class CompeteAction(MoveAction):
    """Template for competition behavior"""
    
    def __init__(self, entity, competitor):
        super().__init__(entity, competitor.position)
        self._competitor = competitor
    
    @property
    def competitor(self):
        """Get the competitor entity"""
        return self._competitor
    
    def perform(self, world):
        """Execute competition behavior"""
        # Move towards competitor
        super().perform(world)
        
        # Check if close enough to compete
        competition_range = self.entity.attributes.interaction_range * 0.5
        if self.entity.position.distance_to(self.competitor.position) < competition_range:
            # Calculate competition strength
            adaptation_level = getattr(self.entity, 'adaptation_level', 0)
            competition_factor = getattr(self.entity.attributes, 'competition_factor', 1.0)
            competition_strength = competition_factor * (1.0 + adaptation_level)
            
            # Reduce the native's energy based on competition strength
            energy_depletion = min(
                self.competitor.energy * 0.1 * competition_strength,
                self.competitor.energy * 0.3  # Cap at 30% of current energy
            )
            self.competitor.energy -= energy_depletion
            
            # The invasive species gains a portion of this energy
            self.entity.energy = min(self.entity.attributes.max_energy, 
                                    self.entity.energy + energy_depletion * 0.5)
            
            return True
        
        return False
    
    def calculate_utility(self, world):
        """Calculate competition utility based on competitor vulnerability"""
        # Base utility from parent
        base_utility = super().calculate_utility(world)
        
        # Competitor vulnerability factor
        competitor_vulnerability = 1.0 - (self.competitor.energy / self.competitor.attributes.max_energy)
        
        # Distance factor
        distance = self.entity.position.distance_to(self.competitor.position)
        interaction_range = self.entity.attributes.interaction_range
        distance_factor = 1.0 - min(1.0, distance / interaction_range)
        
        # Energy need factor
        energy_need = 1.0 - (self.entity.energy / self.entity.attributes.max_energy)
        
        return base_utility + competitor_vulnerability + distance_factor + energy_need
