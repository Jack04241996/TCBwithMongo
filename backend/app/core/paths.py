from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent  # .../app/core
APP_DIR = CORE_DIR.parent                   # .../app
BACKEND_DIR = APP_DIR.parent   
            # .../backend
PROJECT_ROOT = BACKEND_DIR.parent           # .../TCB-Mongo
FRONTEND_DIR = PROJECT_ROOT / "frontend" 
STATIC_DIR = FRONTEND_DIR / "static"
IMAGE_DIR = FRONTEND_DIR / "image"