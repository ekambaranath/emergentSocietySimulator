"""
main.py — entry point. Runs the FastAPI server.
Usage: python main.py
"""

import uvicorn
from config import CONFIG

if __name__ == "__main__":
    uvicorn.run(
        "dashboard.api.main:app",
        host    = CONFIG.server.host,
        port    = CONFIG.server.port,
        reload  = True,
        log_level = "info",
    )
