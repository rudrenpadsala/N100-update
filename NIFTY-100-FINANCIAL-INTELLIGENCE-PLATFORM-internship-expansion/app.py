"""
Root entrypoint for cloud deployment platforms (Streamlit Community Cloud, Hugging Face Spaces, etc.)
Automatically sets up the environment and delegates to src/dashboard/app.py.
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
DASHBOARD_DIR = REPO_ROOT / "src" / "dashboard"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

# Run the dashboard app
app_file = DASHBOARD_DIR / "app.py"
with open(app_file, encoding="utf-8") as f:
    exec(f.read(), globals())
