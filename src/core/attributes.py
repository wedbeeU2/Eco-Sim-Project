"""
Entity attributes classes for different species in the ecosystem simulation.
"""
from src.utils.exceptions import validate_positive, validate_non_negative, validate_range


class EntityAttributes:
    """
    Base class for species-specific attributes.
    Provides common attribute storage and validation.
    """
    
    def __init__(self, max_energy, energy_consumption, speed, interaction_range, maturity_age):
        """
        Initialize entity attributes with basic parameters.
        
        Args:
            max_energy (float): Maximum energy capacity
            energy_consumption (float): Base energy consumption rate
            speed (float): Movement speed
            interaction_range (float): Range for entity interactions
            maturity_age (float): Age at which entity becomes mature
            
        Raises:
            ValidationError: If any parameter is invalid
        """
        self._max_energy = validate_positive(max_energy, "max_energy")
        self._energy_consumption = validate_positive(energy_consumption, "energy_consumption")
        self._speed = validate_positive(speed, "speed")
        self._interaction_range = validate_positive(interaction_range, "interaction_range")
        self._maturity_age = validate_positive(maturity_age, "maturity_age")
    
    @property
    def max_energy(self):
        """Get the maximum energy capacity"""
        return self._max_energy
    
    @property
    def energy_consumption(self):
        """Get the base energy consumption rate"""
        return self._energy_consumption
    
    @property
    def speed(self):
        """Get the movement speed"""
        return self._speed
    
    @property
    def interaction_range(self):
        """Get the range for entity interactions"""
        return self._interaction_range
    
    @property
    def maturity_age(self):
        """Get the age at which entity becomes mature"""
        return self._maturity_age
    
    def __str__(self):
        """
        Return a string representation of the attributes.
        
        Returns:
            str: String representation
        """
        return (f"{self.__class__.__name__}("
                f"max_energy={self._max_energy}, "
                f"energy_consumption={self._energy_consumption}, "
                f"speed={self._speed}, "
                f"interaction_range={self._interaction_range}, "
                f"maturity_age={self._maturity_age})")


class PredatorAttributes(EntityAttributes):
    """Attributes specific to predator entities"""
    
    def __init__(self):
        """Initialize predator-specific attributes"""
        # Predator-specific parameters
        super().__init__(
            max_energy=1000,
            energy_consumption=0.5,
            speed=2.0,
            interaction_range=50.0,
            maturity_age=730  # 2 years in days
        )
        
        self._hunting_range = validate_positive(75.0, "hunting_range")
        self._attack_strength = validate_positive(25.0, "attack_strength")
        self._breeding_cycle = validate_positive(180, "breeding_cycle")  # 6 months in days
        self._min_offspring = validate_positive(4, "min_offspring")
        self._max_offspring = validate_positive(7, "max_offspring")
        self._digest_efficiency = validate_range(0.7, "digest_efficiency", 0, 1)  # 70% of prey energy is converted
    
    @property
    def hunting_range(self):
        """Get the hunting range"""
        return self._hunting_range
    
    @property
    def attack_strength(self):
        """Get the attack strength"""
        return self._attack_strength
    
    @property
    def breeding_cycle(self):
        """Get the breeding cycle duration"""
        return self._breeding_cycle
    
    @property
    def min_offspring(self):
        """Get the minimum number of offspring"""
        return self._min_offspring
    
    @property
    def max_offspring(self):
        """Get the maximum number of offspring"""
        return self._max_offspring
    
    @property
    def digest_efficiency(self):
        """Get the digest efficiency"""
        return self._digest_efficiency


class PreyAttributes(EntityAttributes):
    """Attributes specific to prey entities"""
    
    def __init__(self):
        """Initialize prey-specific attributes"""
        # Prey-specific parameters
        super().__init__(
            max_energy=500,
            energy_consumption=0.3,
            speed=2.5,  # Slightly faster than predators
            interaction_range=30.0,
            maturity_age=180  # 6 months in days
        )
        
        self._flee_range = validate_positive(100.0, "flee_range")
        self._foraging_efficiency = validate_positive(15.0, "foraging_efficiency")
        self._breeding_cycle = validate_positive(30, "breeding_cycle")  # 30 days
        self._min_offspring = validate_positive(4, "min_offspring")
        self._max_offspring = validate_positive(12, "max_offspring")
        self._perception_range = validate_positive(80.0, "perception_range")  # Range to detect predators
    
    @property
    def flee_range(self):
        """Get the flee range"""
        return self._flee_range
    
    @property
    def foraging_efficiency(self):
        """Get the foraging efficiency"""
        return self._foraging_efficiency
    
    @property
    def breeding_cycle(self):
        """Get the breeding cycle duration"""
        return self._breeding_cycle
    
    @property
    def min_offspring(self):
        """Get the minimum number of offspring"""
        return self._min_offspring
    
    @property
    def max_offspring(self):
        """Get the maximum number of offspring"""
        return self._max_offspring
    
    @property
    def perception_range(self):
        """Get the perception range"""
        return self._perception_range


class InvasiveSpeciesAttributes(EntityAttributes):
    """Attributes specific to invasive species entities"""
    
    def __init__(self):
        """Initialize invasive species-specific attributes"""
        # Invasive species-specific parameters - more adaptable and competitive
        super().__init__(
            max_energy=800,
            energy_consumption=0.2,  # More efficient energy use
            speed=3.0,  # Faster than natives
            interaction_range=60.0,  # Larger interaction range
            maturity_age=120  # 4 months - faster maturity
        )
        
        self._competition_factor = validate_positive(2.0, "competition_factor")  # How strongly it competes
        self._adaptation_rate = validate_range(0.1, "adaptation_rate", 0, 1)  # How quickly it adapts
        self._breeding_cycle = validate_positive(25, "breeding_cycle")  # 25 days - faster breeding
        self._min_offspring = validate_positive(6, "min_offspring")
        self._max_offspring = validate_positive(15, "max_offspring")  # More offspring
        self._resource_consumption = validate_positive(1.5, "resource_consumption")  # Consumes more resources
    
    @property
    def competition_factor(self):
        """Get the competition factor"""
        return self._competition_factor
    
    @property
    def adaptation_rate(self):
        """Get the adaptation rate"""
        return self._adaptation_rate
    
    @property
    def breeding_cycle(self):
        """Get the breeding cycle duration"""
        return self._breeding_cycle
    
    @property
    def min_offspring(self):
        """Get the minimum number of offspring"""
        return self._min_offspring
    
    @property
    def max_offspring(self):
        """Get the maximum number of offspring"""
        return self._max_offspring
    
    @property
    def resource_consumption(self):
        """Get the resource consumption rate"""
        return self._resource_consumption
