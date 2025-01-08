import sys
import os

# Default Configuration Constants
DEFAULT_CONFIG = {
    "DIFFERENCE_THRESHOLD": 0.5,
    "CIRCULARITY_THRESHOLD": 0.0,
    "UNIFORMITY_THRESHOLD": 0.0,
    "ODD_CENTER": "Both",  # Changed to string for selection
    "MIN_RADIUS": 1.0,
    "MAX_RADIUS": 200.0,
    "MIN_DIAMETER": 1,
    "MAX_DIAMETER": 400,
    "MAX_WIDTH": 8
}

# Database path constant
def get_resource_path(relative_path):  # For dev and packaging
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

DATABASE_PATH = get_resource_path("results.db")
