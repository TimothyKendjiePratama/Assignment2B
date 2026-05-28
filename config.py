# config.py
"""
Configuration settings for TBRGS
All settings in one place - no JSON files
"""

# Traffic prediction settings
SEQ_LENGTH = 12  # Number of past 15-min intervals (12 = 3 hours)
TEST_SPLIT = 0.2  # 20% test data

# Travel time settings (from PDF v1.0)
SPEED_LIMIT_KPH = 60
INTERSECTION_DELAY_SEC = 30
CAPACITY_FLOW = 1500  # vehicles per hour
FREE_FLOW_THRESHOLD = 351  # vehicles per hour

# Quadratic coefficients for flow-speed relationship (from PDF)
FLOW_TO_SPEED_A = -1.4648375
FLOW_TO_SPEED_B = 93.75

# Pathfinding settings
DEFAULT_K_ROUTES = 5
MAX_VISITS_PER_NODE = 5

# GUI settings
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 750

# File paths
TRAFFIC_FILE = 'Scats Data October 2006.xls'