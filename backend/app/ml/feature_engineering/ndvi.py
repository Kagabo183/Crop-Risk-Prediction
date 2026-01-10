"""
Feature engineering utilities for NDVI trend and anomaly calculations.
Assumes NDVI values are precomputed and available for each date/region.
"""
from typing import List, Dict
import numpy as np
from datetime import date

def ndvi_trend(ndvi_series: List[float]) -> float:
    """
    Calculate the linear trend (slope) of NDVI over time.
    Args:
        ndvi_series: List of NDVI values ordered by date.
    Returns:
        Slope of the linear fit (trend).
    """
    if len(ndvi_series) < 2:
        return 0.0
    x = np.arange(len(ndvi_series))
    y = np.array(ndvi_series)
    slope, _ = np.polyfit(x, y, 1)
    return float(slope)

def ndvi_anomaly(current_ndvi: float, historical_mean: float) -> float:
    """
    Calculate NDVI anomaly (current - historical mean).
    """
    return current_ndvi - historical_mean
