"""
Feature engineering utilities for rainfall deficit and heat stress calculations.
Assumes daily/periodic weather data is available.
"""
from typing import List
import numpy as np

def rainfall_deficit(rainfall_series: List[float], normal_rainfall_series: List[float]) -> float:
    """
    Calculate rainfall deficit as the difference between observed and normal rainfall.
    Args:
        rainfall_series: Observed rainfall values for the period.
        normal_rainfall_series: Long-term mean rainfall values for the same period.
    Returns:
        Total rainfall deficit (negative means deficit).
    """
    return float(np.sum(rainfall_series) - np.sum(normal_rainfall_series))

def heat_stress_days(temperature_series: List[float], threshold: float = 30.0) -> int:
    """
    Count the number of days with temperature above the heat stress threshold.
    Args:
        temperature_series: List of daily mean temperatures.
        threshold: Temperature threshold for heat stress (default 30°C).
    Returns:
        Number of heat stress days.
    """
    return int(np.sum(np.array(temperature_series) > threshold))
