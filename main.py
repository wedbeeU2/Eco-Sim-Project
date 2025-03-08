#!/usr/bin/env python3
"""
Ecosystem Simulation: Predator-Prey Dynamics with Invasive Species
Main entry point for the simulation
"""

import sys
import argparse
import os
import logging
from src.simulation.simulation import Simulation
from src.visualization.renderer import Renderer
from src.utils.exceptions import SimulationError, ErrorSeverity


def setup_logging(log_level=logging.INFO, log_file="simulation.log"):
    """
    Setup logging configuration.
    
    Args:
        log_level: The logging level (default: INFO)
        log_file: Path to log file (default: "simulation.log")
        
    Returns:
        logger: Configured logger
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.dirname(log_file)
    if logs_dir and not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create a logger
    logger = logging.getLogger('ecosystem_simulation')
    
    return logger


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        args: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Ecosystem Simulation')
    
    parser.add_argument(
        '--width', type=int, default=1000,
        help='Width of the simulation world (default: 1000)'
    )
    parser.add_argument(
        '--height', type=int, default=800,
        help='Height of the simulation world (default: 800)'
    )
    parser.add_argument(
        '--predators', type=int, default=10,
        help='Initial number of predators (default: 10)'
    )
    parser.add_argument(
        '--prey', type=int, default=100,
        help='Initial number of prey (default: 100)'
    )
    parser.add_argument(
        '--invasive', type=int, default=0,
        help='Initial number of invasive species (default: 0)'
    )
    parser.add_argument(
        '--headless', action='store_true',
        help='Run in headless mode without visualization'
    )
    parser.add_argument(
        '--duration', type=float, default=0,
        help='Duration to run the simulation in days (default: 0, runs indefinitely)'
    )
    parser.add_argument(
        '--seed', type=int, default=None,
        help='Random seed for reproducible results (default: None)'
    )
    parser.add_argument(
        '--time-scale', type=float, default=1.0,
        help='Time scale for the simulation (default: 1.0)'
    )
    parser.add_argument(
        '--output-dir', type=str, default='data',
        help='Directory for output data (default: "data")'
    )
    parser.add_argument(
        '--log-level', type=str, default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--log-file', type=str, default='logs/simulation.log',
        help='Path to log file (default: "logs/simulation.log")'
    )
    
    return parser.parse_args()


def main():
    """
    Main function to run the simulation.
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Setup logging
        log_level = getattr(logging, args.log_level)
        logger = setup_logging(log_level, args.log_file)
        
        # Set random seed if specified
        if args.seed is not None:
            import random
            random.seed(args.seed)
            logger.info(f"Using random seed: {args.seed}")
        
        # Create simulation
        simulation = Simulation(args.width, args.height)
        
        # Set time scale
        simulation.set_time_scale(args.time_scale)
        
        # Ensure output directory exists
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Initialize with entities
        logger.info(f"Initializing simulation with {args.predators} predators, "
                    f"{args.prey} prey, and {args.invasive} invasive species")
        
        simulation.initialize(
            predator_count=args.predators,
            prey_count=args.prey,
            invasive_count=args.invasive
        )
        
        if args.headless:
            # Run in headless mode
            logger.info("Running in headless mode...")
            simulation.run()
            
            # Convert duration from days to seconds
            duration_seconds = args.duration * 86400
            
            # Run for specified duration
            if duration_seconds > 0:
                import time
                
                start_time = time.time()
                logger.info(f"Running for {args.duration} simulation days")
                
                last_day = 0
                while simulation.is_running():
                    simulation.update()
                    
                    # Check if duration has elapsed
                    if simulation.get_simulation_time_seconds() >= duration_seconds:
                        simulation.pause()
                    
                    # Print progress every simulation day
                    current_day = int(simulation.get_simulation_time_seconds() / 86400)
                    if current_day > last_day:
                        last_day = current_day
                        stats = simulation.world.get_statistics()
                        logger.info(f"Day {current_day}: "
                                    f"Predators: {stats['predator_count']}, "
                                    f"Prey: {stats['prey_count']}, "
                                    f"Invasive: {stats['invasive_count']}")
                
                real_time = time.time() - start_time
                logger.info(f"Simulation completed in {real_time:.2f} seconds of real time")
            else:
                logger.warning("No duration specified in headless mode. Exiting.")
            
            # Export data
            data_file = simulation.export_data()
            logger.info(f"Data exported to {data_file}")
            
            # Generate and print report
            report = simulation.generate_report()
            logger.info("\n" + report)
        else:
            # Run with visualization
            logger.info("Starting visualization...")
            renderer = Renderer(args.width, args.height, simulation)
            
            # Start the simulation
            simulation.run()
            
            # Main loop
            try:
                while True:
                    # Process events
                    renderer.process_events()
                    
                    # Update simulation
                    simulation.update()
                    
                    # Render frame
                    renderer.render()
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt. Exiting.")
            finally:
                # On exit, export data
                data_file = simulation.export_data()
                logger.info(f"Data exported to {data_file}")
                
                # Generate and print report
                report = simulation.generate_report()
                logger.info("\n" + report)
        
        return 0
    
    except SimulationError as e:
        # Handle simulation-specific errors
        if e.severity == ErrorSeverity.WARNING:
            logging.warning(f"Warning: {str(e)}")
            return 0
        else:
            logging.error(f"Error: {str(e)}")
            return 1
    
    except Exception as e:
        # Handle unexpected errors
        logging.critical(f"Unexpected error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
