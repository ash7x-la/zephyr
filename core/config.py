import os
import json
from dotenv import load_dotenv

load_dotenv()

def _get_config(data, key, default=None):
    val = data.get(key, os.getenv(key, default))
    if isinstance(val, str):
        # Bersihkan spasi, newline, dan kutipan berlebih (Sering terjadi di Termux)
        val = val.strip().replace('"', '').replace("'", "")
    return val

_config_data = {}
_source = "OS Environment"
if os.path.exists("config.json"):
    try:
        with open("config.json", "r") as f:
            _config_data = json.load(f)
            _source = "config.json"
    except Exception as e:
        print(f"Bermasalah saat membaca config.json: {e}")

class Config:
    SOURCE = _source
    OPENROUTER_API_KEY = _get_config(_config_data, "OPENROUTER_API_KEY")
    GEMINI_API_KEY = _get_config(_config_data, "GEMINI_API_KEY")
    CLAUDE_API_KEY = _get_config(_config_data, "CLAUDE_API_KEY")
    DEEPSEEK_FREE_TOKEN = _get_config(_config_data, "DEEPSEEK_FREE_TOKEN")
    DEEPSEEK_FREE_URL = _get_config(_config_data, "DEEPSEEK_FREE_URL", "http://127.0.0.1:8000/v1")
    
    DEFAULT_MODEL = _get_config(_config_data, "DEFAULT_MODEL", "qwen/qwen3.6-plus:free")
    MAX_TOKENS = 4096
    PROJECTS_DIR = "projects"
