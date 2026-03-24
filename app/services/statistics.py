"""Statistics utilities for numerical calculations."""
from __future__ import annotations

from typing import List


def calculate_average(numbers: List[float]) -> float:
    """Calculate the mean of a list of numbers.
    
    Args:
        numbers: A list of numeric values
        
    Returns:
        The arithmetic mean of the input numbers
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of an empty list")
    
    return sum(numbers) / len(numbers)
