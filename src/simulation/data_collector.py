"""
DataCollector module for collecting and analyzing simulation data.
"""
import csv
import os
import pandas as pd
from datetime import datetime
from src.utils.exceptions import validate_type, DataCollectionError, safe_operation


class DataCollector:
    """
    Collects and manages simulation data.
    Provides tools for recording metrics and generating reports.
    """
    
    def __init__(self, data_dir="data"):
        """
        Initialize the data collector.
        
        Args:
            data_dir (str): Directory for storing collected data (default: "data")
            
        Raises:
            DataCollectionError: If the data directory cannot be created
        """
        self._metrics = {}
        self._time_series = []
        self._data_dir = data_dir
        
        # Create data directory if it doesn't exist
        try:
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
        except Exception as e:
            raise DataCollectionError(f"Failed to create data directory: {str(e)}")
        
        # Generate a unique ID for this simulation run
        self._simulation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @property
    def metrics(self):
        """Get the collected metrics"""
        return self._metrics.copy()
    
    @property
    def time_series(self):
        """Get the time series data"""
        return list(self._time_series)
    
    @property
    def simulation_id(self):
        """Get the unique simulation ID"""
        return self._simulation_id
    
    @property
    def data_dir(self):
        """Get the data directory"""
        return self._data_dir
    
    def record_metrics(self, time, metrics):
        """
        Record metrics at a specific time point.
        
        Args:
            time (float): The simulation time
            metrics (dict): Dictionary of metrics to record
            
        Returns:
            bool: True if recording was successful
            
        Raises:
            DataCollectionError: If metrics are invalid
            ValidationError: If parameters are invalid
        """
        validate_type(time, "time", (int, float))
        validate_type(metrics, "metrics", dict)
        
        try:
            time_point = {"time": time}
            time_point.update(metrics)
            self._time_series.append(time_point)
            
            # Update latest metrics
            self._metrics = metrics.copy()
            
            return True
        except Exception as e:
            raise DataCollectionError(f"Failed to record metrics: {str(e)}")
    
    def export_data(self, filename=None):
        """
        Export collected data to CSV file.
        
        Args:
            filename (str, optional): Output filename
            
        Returns:
            str: Path to the exported CSV file
            
        Raises:
            DataCollectionError: If export fails
        """
        if filename is None:
            filename = f"{self._data_dir}/simulation_{self._simulation_id}.csv"
        
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            with open(filename, 'w', newline='') as csvfile:
                if self._time_series:
                    fieldnames = self._time_series[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for data_point in self._time_series:
                        writer.writerow(data_point)
            
            return filename
        except Exception as e:
            raise DataCollectionError(f"Failed to export data: {str(e)}")
    
    def get_dataframe(self):
        """
        Convert time series data to a pandas DataFrame.
        
        Returns:
            pandas.DataFrame: DataFrame containing time series data
            
        Raises:
            DataCollectionError: If conversion fails
        """
        try:
            if not self._time_series:
                return pd.DataFrame()
            
            return pd.DataFrame(self._time_series)
        except Exception as e:
            raise DataCollectionError(f"Failed to create DataFrame: {str(e)}")
    
    def generate_report(self):
        """
        Generate a summary report from collected data.
        
        Returns:
            str: Summary report text
            
        Raises:
            DataCollectionError: If report generation fails
        """
        if not self._time_series:
            return "No data collected yet."
        
        try:
            # Convert to pandas DataFrame for analysis
            df = self.get_dataframe()
            
            # Calculate basic statistics
            report = "Simulation Summary Report\n"
            report += "=======================\n\n"
            
            # Time span
            report += f"Simulation duration: {df['time'].max()} time units\n"
            report += f"Data points collected: {len(df)}\n\n"
            
            # Population statistics
            if 'predator_count' in df.columns:
                report += f"Predator population - Initial: {df['predator_count'].iloc[0]}, "
                report += f"Final: {df['predator_count'].iloc[-1]}, "
                report += f"Max: {df['predator_count'].max()}, "
                report += f"Min: {df['predator_count'].min()}\n"
            
            if 'prey_count' in df.columns:
                report += f"Prey population - Initial: {df['prey_count'].iloc[0]}, "
                report += f"Final: {df['prey_count'].iloc[-1]}, "
                report += f"Max: {df['prey_count'].max()}, "
                report += f"Min: {df['prey_count'].min()}\n"
            
            if 'invasive_count' in df.columns:
                report += f"Invasive population - Initial: {df['invasive_count'].iloc[0]}, "
                report += f"Final: {df['invasive_count'].iloc[-1]}, "
                report += f"Max: {df['invasive_count'].max()}, "
                report += f"Min: {df['invasive_count'].min()}\n"
            
            # Additional analyses could be added here
            
            return report
        except Exception as e:
            safe_operation(
                lambda: print(f"Error generating report: {str(e)}"),
                "Failed to print error message"
            )
            return "Error generating report. See logs for details."
    
    def clear_data(self):
        """
        Clear all collected data.
        
        Returns:
            bool: True if data was cleared successfully
        """
        self._time_series.clear()
        self._metrics.clear()
        return True
    
    def get_latest_metrics(self):
        """
        Get the most recently recorded metrics.
        
        Returns:
            dict: The latest metrics
        """
        return self._metrics.copy()
    
    def analyze_population_dynamics(self):
        """
        Analyze population dynamics based on collected data.
        
        Returns:
            dict: Analysis results
            
        Raises:
            DataCollectionError: If analysis fails
        """
        if not self._time_series:
            return {"error": "No data available for analysis"}
        
        try:
            df = self.get_dataframe()
            
            # Population trends
            results = {"population_trends": {}}
            
            for species in ["predator_count", "prey_count", "invasive_count"]:
                if species in df.columns:
                    # Calculate trends
                    start_pop = df[species].iloc[0]
                    end_pop = df[species].iloc[-1]
                    max_pop = df[species].max()
                    min_pop = df[species].min()
                    avg_pop = df[species].mean()
                    
                    # Calculate growth rate
                    if start_pop > 0:
                        growth_rate = (end_pop - start_pop) / start_pop
                    else:
                        growth_rate = float('inf') if end_pop > 0 else 0
                    
                    # Store results
                    species_name = species.replace("_count", "")
                    results["population_trends"][species_name] = {
                        "initial": start_pop,
                        "final": end_pop,
                        "max": max_pop,
                        "min": min_pop,
                        "average": avg_pop,
                        "growth_rate": growth_rate
                    }
            
            # Population balance
            if "predator_count" in df.columns and "prey_count" in df.columns:
                predator_prey_ratio = df["predator_count"] / df["prey_count"].replace(0, 1)
                results["predator_prey_ratio"] = {
                    "initial": predator_prey_ratio.iloc[0],
                    "final": predator_prey_ratio.iloc[-1],
                    "average": predator_prey_ratio.mean(),
                    "max": predator_prey_ratio.max(),
                    "min": predator_prey_ratio.min()
                }
            
            # Stability analysis
            if len(df) > 10:  # Need enough data points
                for species in ["predator_count", "prey_count", "invasive_count"]:
                    if species in df.columns:
                        # Calculate volatility (standard deviation / mean)
                        volatility = df[species].std() / df[species].mean() if df[species].mean() > 0 else 0
                        
                        # Store stability metrics
                        if "stability" not in results:
                            results["stability"] = {}
                        
                        species_name = species.replace("_count", "")
                        results["stability"][species_name] = {
                            "volatility": volatility
                        }
            
            return results
        except Exception as e:
            raise DataCollectionError(f"Failed to analyze population dynamics: {str(e)}")
