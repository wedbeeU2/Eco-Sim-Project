"""
Custom exceptions and error handling utilities for the ecosystem simulation.
This module defines exception classes specific to simulation errors and provides
utility functions for graceful error handling.
"""
import logging
import sys
from enum import Enum


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simulation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create a logger
logger = logging.getLogger('ecosystem_simulation')


class ErrorSeverity(Enum):
    """Enumeration for error severity levels"""
    WARNING = 1
    ERROR = 2
    CRITICAL = 3


class SimulationError(Exception):
    """Base class for all simulation-related exceptions"""
    
    def __init__(self, message, severity=ErrorSeverity.ERROR):
        super().__init__(message)
        self.severity = severity
        
        # Log the error based on severity
        if severity == ErrorSeverity.WARNING:
            logger.warning(message)
        elif severity == ErrorSeverity.ERROR:
            logger.error(message)
        elif severity == ErrorSeverity.CRITICAL:
            logger.critical(message)


class EntityError(SimulationError):
    """Exception raised for errors related to entity operations"""
    
    def __init__(self, message, entity=None, severity=ErrorSeverity.ERROR):
        if entity:
            entity_info = f"Entity ID: {entity.id}, Type: {entity.__class__.__name__}"
            message = f"{message} [{entity_info}]"
        super().__init__(message, severity)


class WorldError(SimulationError):
    """Exception raised for errors related to world operations"""
    
    def __init__(self, message, world=None, severity=ErrorSeverity.ERROR):
        if world:
            world_info = f"World size: {world.width}x{world.height}, Entities: {len(world.entities)}"
            message = f"{message} [{world_info}]"
        super().__init__(message, severity)


class SimulationConfigError(SimulationError):
    """Exception raised for simulation configuration errors"""
    
    def __init__(self, message, severity=ErrorSeverity.ERROR):
        super().__init__(message, severity)


class DataCollectionError(SimulationError):
    """Exception raised for errors in data collection and export"""
    
    def __init__(self, message, severity=ErrorSeverity.ERROR):
        super().__init__(message, severity)


class RenderingError(SimulationError):
    """Exception raised for rendering-related errors"""
    
    def __init__(self, message, severity=ErrorSeverity.ERROR):
        super().__init__(message, severity)


class ValidationError(SimulationError):
    """Exception raised for parameter validation errors"""
    
    def __init__(self, message, parameter=None, value=None, severity=ErrorSeverity.ERROR):
        if parameter and value is not None:
            message = f"{message} [Parameter: {parameter}, Value: {value}]"
        super().__init__(message, severity)


def handle_error(error, should_raise=True):
    """
    Handle an error based on severity
    
    Args:
        error: The exception to handle
        should_raise: Whether to raise the exception after handling
        
    Returns:
        bool: True if operation should continue, False if it should abort
    """
    if isinstance(error, SimulationError):
        # Already logged during initialization
        pass
    else:
        # Log unexpected errors
        logger.error(f"Unexpected error: {error}")
    
    # Determine if operation should continue based on severity
    if isinstance(error, SimulationError) and error.severity == ErrorSeverity.WARNING:
        # For warnings, continue execution
        if should_raise:
            raise error
        return True
    else:
        # For errors and critical issues, abort if not explicitly handling
        if should_raise:
            raise error
        return False


def validate_positive(value, name, min_value=0.0001):
    """
    Validate that a value is positive
    
    Args:
        value: The value to validate
        name: The parameter name for error reporting
        
    Returns:
        float or int: The validated value
        
    Raises:
        ValidationError: If validation fails
    """
    if value < min_value:
        raise ValidationError(
            f"Parameter must be positive (at least {min_value})", 
            parameter=name, 
            value=value
        )
    return value


def validate_non_negative(value, name):
    """
    Validate that a value is non-negative
    
    Args:
        value: The value to validate
        name: The parameter name for error reporting
        
    Returns:
        float or int: The validated value
        
    Raises:
        ValidationError: If validation fails
    """
    if value < 0:
        raise ValidationError(
            f"Parameter must be non-negative", 
            parameter=name, 
            value=value
        )
    return value


def validate_range(value, name, min_value=None, max_value=None):
    """
    Validate that a value is within a specified range
    
    Args:
        value: The value to validate
        name: The parameter name for error reporting
        min_value: The minimum allowed value (inclusive)
        max_value: The maximum allowed value (inclusive)
        
    Returns:
        float or int: The validated value
        
    Raises:
        ValidationError: If validation fails
    """
    if min_value is not None and value < min_value:
        raise ValidationError(
            f"Parameter must be at least {min_value}", 
            parameter=name, 
            value=value
        )
    
    if max_value is not None and value > max_value:
        raise ValidationError(
            f"Parameter must not exceed {max_value}", 
            parameter=name, 
            value=value
        )
    
    return value


def validate_type(value, name, expected_type):
    """
    Validate that a value is of the expected type
    
    Args:
        value: The value to validate
        name: The parameter name for error reporting
        expected_type: The expected type or tuple of types
        
    Returns:
        Any: The validated value
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Parameter must be of type {expected_type.__name__}", 
            parameter=name, 
            value=value
        )
    
    return value


def validate_not_none(value, name):
    """
    Validate that a value is not None
    
    Args:
        value: The value to validate
        name: The parameter name for error reporting
        
    Returns:
        Any: The validated value
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        raise ValidationError(
            f"Parameter cannot be None", 
            parameter=name
        )
    
    return value


def safe_operation(operation, error_message, default_value=None, log_error=True):
    """
    Execute an operation safely, handling exceptions
    
    Args:
        operation: A callable to execute
        error_message: Message to log if an exception occurs
        default_value: Value to return if an exception occurs
        log_error: Whether to log the error
        
    Returns:
        Any: The result of the operation or default_value if an exception occurs
    """
    try:
        return operation()
    except Exception as e:
        if log_error:
            logger.error(f"{error_message}: {str(e)}")
        return default_value


def apply_error_handling(world_update):
    """
    Decorator for applying error handling to the world update method
    
    Args:
        world_update: The original world update method
        
    Returns:
        function: Decorated update method with error handling
    """
    def decorated_update(self, time_delta):
        try:
            # Make a copy of the entities list to avoid issues if list changes during iteration
            entities_to_update = list(self.entities)
            
            for entity in entities_to_update:
                try:
                    if entity.is_alive:
                        # Update entity with error handling
                        safe_operation(
                            lambda: entity.update(self, time_delta),
                            f"Error updating entity {entity.id}"
                        )
                    else:
                        # Remove dead entities
                        self.remove_entity(entity)
                except Exception as e:
                    logger.error(f"Error processing entity {entity.id}: {str(e)}")
                    # Try to remove the problematic entity
                    try:
                        self.remove_entity(entity)
                    except:
                        pass
            
            return True
        except Exception as e:
            logger.critical(f"Critical error during world update: {str(e)}")
            return False
    
    return decorated_update
