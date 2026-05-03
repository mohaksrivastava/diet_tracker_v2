# schedulers/fill_recipes.py
# Entry point for Windows Task Scheduler (02:00 daily).
# Calls the recipe fill agent and logs results.
#
# Windows Task Scheduler setup:
#   Program:   python
#   Arguments: D:\path\to\diet_tracker_py\schedulers\fill_recipes.py
#   Start in:  D:\path\to\diet_tracker_py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime
from agents.recipe_fill_agent import run_recipe_fill

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(LOG_DIR, f"fill_recipes_{datetime.now().strftime('%Y%m')}.log")
        ),
        logging.StreamHandler(sys.stdout),
    ]
)

if __name__ == "__main__":
    logging.info("fill_recipes scheduler invoked")
    result = run_recipe_fill()
    logging.info(f"Result: {result}")
