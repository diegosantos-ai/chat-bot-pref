import sys
from pathlib import Path

# Ajuste de path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.settings import settings  # noqa: E402
print(f"TOKEN_CARREGADO: '{settings.META_WEBHOOK_VERIFY_TOKEN}'")
