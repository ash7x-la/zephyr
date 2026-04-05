import os
import json

# TIDAK LAGI PAKAI .env — SEMUA DARI config.json
_config_data = {}
_source = "NONE"
if os.path.exists("config.json"):
    try:
        with open("config.json", "r") as f:
            _config_data = json.load(f)
            _source = "config.json"
    except Exception as e:
        print(f"Bermasalah saat membaca config.json: {e}")

def _get(key, default=None):
    """Ambil dari config.json saja. Tidak ada fallback ke env."""
    val = _config_data.get(key, default)
    if isinstance(val, str):
        val = val.strip().replace('"', '').replace("'", "")
    return val

class Config:
    SOURCE = _source
    OPENROUTER_API_KEY = _get("OPENROUTER_API_KEY")
    GEMINI_API_KEY = _get("GEMINI_API_KEY")
    CLAUDE_API_KEY = _get("CLAUDE_API_KEY")
    DEEPSEEK_FREE_TOKEN = _get("DEEPSEEK_FREE_TOKEN")
    DEEPSEEK_FREE_URL = _get("DEEPSEEK_FREE_URL")
    
    # ZERO DEFAULT: Semua harus dari config.json user
    DEFAULT_MODEL = _get("DEFAULT_MODEL")
    MODEL_MAPPING = _get("MODEL_MAPPING", {})
    MODEL_LABELS = _get("MODEL_LABELS", {})
    
    MAX_TOKENS = 4096
    PROJECTS_DIR = "projects"
