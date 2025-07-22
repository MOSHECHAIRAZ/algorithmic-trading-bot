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
    """
    Loads the main system configuration file.
    
    Returns:
        dict: Configuration data from system_config.json
        
    Raises:
        FileNotFoundError: If the configuration file is missing
        json.JSONDecodeError: If the configuration file has invalid JSON
    """
    config_path = 'system_config.json'
    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Basic validation of required sections
        required_sections = ['training_params', 'backtest_params', 'contract', 'api_settings']
        missing_sections = [section for section in required_sections if section not in config_data]
        
        if missing_sections:
            logging.warning(f"Configuration is missing required sections: {', '.join(missing_sections)}")
        
        return config_data
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in configuration file: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error loading configuration: {str(e)}")
        raise


def save_system_config(config_data):
    """
    Saves data to the main system configuration file.
    
    Args:
        config_data: The configuration data to save
        
    Raises:
        TypeError: If config_data is not a dictionary
        IOError: If there's an error writing to the file
    """
    if not isinstance(config_data, dict):
        raise TypeError("Configuration data must be a dictionary")
        
    config_path = 'system_config.json'
    
    # Create a backup of the current config before modifying
    if os.path.exists(config_path):
        archive_existing_file(config_path)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        logging.info(f"Configuration saved successfully to {config_path}")
    except IOError as e:
        logging.error(f"Failed to write configuration file: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error saving configuration: {str(e)}")
        raise

def get_system_path(path_key):
    """
    מחזיר את הנתיב הנכון מתוך הגדרות המערכת.
    יוצר את התיקייה אם היא לא קיימת.
    
    Args:
        path_key: המפתח של הנתיב בתוך system_paths
        
    Returns:
        הנתיב המלא
    """
    config = load_system_config()
    paths = config.get('system_paths', {})
    
    if path_key not in paths:
        # אם המפתח לא קיים, החזר ערך ברירת מחדל לפי המפתח
        default_paths = {
            "raw_data": "data/raw/SPY_ibkr.csv",
            "vix_data": "data/raw/VIX_ibkr.csv",
            "processed_data": "data/processed/SPY_processed.csv",
            "feature_data": "data/processed/SPY_features.csv",
            "champion_model": "models/champion_model.pkl",
            "champion_scaler": "models/champion_scaler.pkl",
            "champion_config": "models/champion_model_config.json",
            "backtest_results": "reports/backtest_results",
            "logs_dir": "logs",
            "archive_dir": "archive"
        }
        path = default_paths.get(path_key, "")
    else:
        path = paths[path_key]
    
    # יצירת התיקייה אם מדובר בתיקייה
    if not path.endswith(('.csv', '.json', '.pkl', '.txt')):
        os.makedirs(path, exist_ok=True)
    else:
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)
    
    return path
