import os
import shutil
from datetime import datetime
import logging
import json

def archive_existing_file(filepath):
    """
    אם קובץ קיים - מעביר אותו לארכיון עם חותמת זמן כדי למנוע דריסה.
    אם הקובץ תפוס ע"י תהליך אחר (PermissionError), מדלג ומדפיס אזהרה.
    """
    if os.path.exists(filepath):
        archive_dir = os.path.join(os.path.dirname(filepath), 'archive')
        os.makedirs(archive_dir, exist_ok=True)
        base = os.path.basename(filepath)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archived_file = os.path.join(archive_dir, f"{base}.{timestamp}")
        try:
            shutil.move(filepath, archived_file)
        except PermissionError:
            logging.warning(f"Could not archive {filepath} (file is in use). Skipping archive.")
        except Exception as e:
            logging.warning(f"Could not archive {filepath}: {e}")

def load_system_config():
    """Loads the main system configuration file."""
    with open('system_config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_system_config(config_data):
    """Saves data to the main system configuration file."""
    with open('system_config.json', 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
