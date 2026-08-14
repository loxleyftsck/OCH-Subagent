import uvicorn
import argparse
import sys
from src.config import settings

def start_server():
    print(f"🚀 Starting OCH-Subagent System on http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
    print(f"🔒 Shared-Team Safety Mode: {'ENABLED' if settings.TEAM_SHARED_MODE else 'DISABLED'}")
    print(f"⏱️ OCR Interval: {settings.OCR_INTERVAL_SECONDS}s | Concurrency: {settings.MAX_CONCURRENT_REQUESTS}")
    uvicorn.run(
        "src.server.app:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=False
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCH-Subagent System")
    parser.add_argument("--server", action="store_true", default=True, help="Start the FastAPI server & Web UI")
    args = parser.parse_args()
    start_server()
