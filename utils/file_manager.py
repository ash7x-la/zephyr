import os
from core.config import Config
from core.logger import Logger

def save_file(project_name, filename, content):
    try:
        base_dir = os.path.join(Config.PROJECTS_DIR, project_name)
        os.makedirs(base_dir, exist_ok=True)
        file_path = os.path.join(base_dir, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path
    except Exception as e:
        Logger.error(f"Gagal menyimpan file {filename}: {e}")
        return None
