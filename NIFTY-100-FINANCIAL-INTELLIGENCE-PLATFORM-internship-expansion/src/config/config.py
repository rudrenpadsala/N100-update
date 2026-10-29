from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Project Root
BASE_DIR = Path(__file__).resolve().parents[2]

# Paths
RAW_DATA_PATH = BASE_DIR / "data" / "raw"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed"
DATABASE_PATH = BASE_DIR / "db" / "nifty100.db"
OUTPUT_PATH = BASE_DIR / "output"

# Project Name
PROJECT_NAME = os.getenv("PROJECT_NAME")

print("Project Loaded Successfully")