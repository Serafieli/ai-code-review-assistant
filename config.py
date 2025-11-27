import os
from dotenv import load_dotenv

# -------------------------------------------------------
# LOAD ENV
# -------------------------------------------------------
load_dotenv()

def require_env(name: str) -> str:
    """ Бросает понятную ошибку, если переменная не найдена. """
    value = os.getenv(name)
    if not value or value.strip() == "":
        raise ValueError(f"❌ Missing environment variable: {name}")
    return value


# -------------------------------------------------------
# OPENAI
# -------------------------------------------------------
OPENAI_API_KEY = require_env("OPENAI_API_KEY")


# -------------------------------------------------------
# GITLAB CONFIG
# -------------------------------------------------------
GITLAB_TOKEN = require_env("GITLAB_TOKEN")

# Можно оставить default gitlab.com
GITLAB_BASE_URL = os.getenv("GITLAB_BASE_URL", "https://gitlab.com").rstrip("/")


# -------------------------------------------------------
# WEBHOOK SECRET
# -------------------------------------------------------
WEBHOOK_SECRET = require_env("WEBHOOK_SECRET")


# -------------------------------------------------------
# STORE LIMIT (с валидной int-конверсией)
# -------------------------------------------------------
_store_limit_raw = os.getenv("STORE_LIMIT", "100")

try:
    STORE_LIMIT = int(_store_limit_raw)
except ValueError:
    print(f"⚠ WARNING: STORE_LIMIT '{_store_limit_raw}' is not a number. Default = 100")
    STORE_LIMIT = 100


# -------------------------------------------------------
# DEBUG MODE
# -------------------------------------------------------
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("1", "true", "yes")


# -------------------------------------------------------
# BASE PATH (если понадобится)
# -------------------------------------------------------
BASE_PATH = os.path.dirname(os.path.abspath(__file__))


# -------------------------------------------------------
# PRINT CONFIG SUMMARY FOR STARTUP
# -------------------------------------------------------
print("""
==================== CONFIG LOADED ====================
GitLab URL:        {}
Store Limit:       {}
Debug Mode:        {}
=======================================================
""".format(
    GITLAB_BASE_URL,
    STORE_LIMIT,
    DEBUG_MODE
))
