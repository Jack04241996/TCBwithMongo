from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent  # .../app/core
APP_DIR = CORE_DIR.parent                   # .../app
BACKEND_DIR = APP_DIR.parent                # .../backend
PROJECT_ROOT = BACKEND_DIR.parent           # .../TCB-Mongo

STATIC_DIR = PROJECT_ROOT / "static"
IMAGE_DIR = PROJECT_ROOT / "image"