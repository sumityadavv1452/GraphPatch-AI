"""Root launcher for GraphPatch-AI Web Dashboard.

Provides backward-compatible CLI execution: `python app.py`
Delegates directly to dashboard/app.py.
"""

import sys
from pathlib import Path
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dashboard.app import app

if __name__ == "__main__":
    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=8000, reload=True)
