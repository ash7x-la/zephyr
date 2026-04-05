import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    DEEPSEEK_FREE_TOKEN = os.getenv("DEEPSEEK_FREE_TOKEN")
    DEEPSEEK_FREE_URL = os.getenv("DEEPSEEK_FREE_URL", "http://127.0.0.1:8000/v1")
    
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen/qwen3.6-plus:free")
    MAX_TOKENS = 4096
    PROJECTS_DIR = "projects"
