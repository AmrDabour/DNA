"""
Serialization Utilities - Functions for converting data types for JSON
"""
import numpy as np


def convert_to_serializable(obj):
    """
    Convert NumPy types to regular Python types for JSON serialization.
    This handles things like int64, float32, etc.
    """
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return convert_to_serializable(obj.tolist())
    elif isinstance(obj, (np.bool_)):
        return bool(obj)
    elif obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        return str(obj)


def ensure_string_items(items):
    """Convert all items in a list to strings, including nested lists"""
    if isinstance(items, list):
        return [
            ensure_string_items(item) if isinstance(item, (list, dict)) else str(item)
            for item in items
        ]
    elif isinstance(items, dict):
        return {
            k: ensure_string_items(v) if isinstance(v, (list, dict)) else str(v)
            for k, v in items.items()
        }
    else:
        return str(items)
