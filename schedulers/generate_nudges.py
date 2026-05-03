# schedulers/generate_nudges.py
# Entry point for Windows Task Scheduler (04:00 daily).
# Calls the nudge agent and logs results.
#
# Windows Task Scheduler setup:
#   Program:   python
#   Arguments: D:\path\to\diet_tracker_py\schedulers\generate_nudges.py
#   Start in:  D:\path\to\diet_tracker_py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime
from agents.nudge_agent import run_nudge_agent

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(LOG_DIR, f"generate_nudges_{datetime.now().strftime('%Y%m')}.log")
        ),
        logging.StreamHandler(sys.stdout),
    ]
)

if __name__ == "__main__":
    logging.info("generate_nudges scheduler invoked")
    result = run_nudge_agent()
    logging.info(f"Result: {result}")
