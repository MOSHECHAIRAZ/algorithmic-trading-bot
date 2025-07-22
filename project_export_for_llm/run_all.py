import logging
import sys
import subprocess
import os
from pathlib import Path
from src.utils import archive_existing_file

# יצירת ספריית לוגים אם לא קיימת
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# הגדרת לוגינג בסיסי
log_file = log_dir / "run_all.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

def check_environment():
    """
    בודק שהסביבה מוכנה להרצת המערכת.
    """
    try:
        # בדיקה שקובץ התצורה קיים
        if not os.path.exists("system_config.json"):
            logging.error("system_config.json file is missing!")
            return False
            
        # בדיקה שספריות הנתונים קיימות
        for dir_path in ["data/raw", "data/processed", "models"]:
            os.makedirs(dir_path, exist_ok=True)
            
        # בדיקה שיש גישה לקובץ .env אם הוא קיים
        if os.path.exists(".env"):
            try:
                with open(".env", "r") as f:
                    env_content = f.read()
                    if "IBKR_USERNAME" not in env_content or "IBKR_PASSWORD" not in env_content:
                        logging.warning(".env file exists but may be missing required credentials")
            except Exception as e:
                logging.warning(f"Could not verify .env file contents: {e}")
                
        logging.info("Environment check completed")
        return True
        
    except Exception as e:
        logging.error(f"Environment check failed: {e}")
        return False

def run_data_collection():
    try:
        from src.data_collector import fetch_all_historical_data
        logging.info("Collecting data (fetch_all_historical_data from IBKR)...")
        fetch_all_historical_data()
        logging.info("Data collection completed.")
    except Exception as e:
        logging.error(f"Data collection failed: {e}")
        raise

def run_preprocessing():
    """
    מריץ את סקריפט העיבוד המקדים הייעודי.
    """
    try:
        logging.info("Running data preprocessing script...")
        from src.run_preprocessing import preprocess_data
        preprocess_data()
        logging.info("Data preprocessing completed.")
    except Exception as e:
        logging.error(f"Data preprocessing failed: {str(e)}", exc_info=True)
        raise  # העלאת השגיאה כדי שיטופל ברמה גבוהה יותר

def run_feature_engineering():
    """
    מריץ את תהליך חישוב הפיצ'רים בנפרד מתהליך האימון.
    """
    try:
        logging.info("Running feature engineering script...")
        subprocess.run([sys.executable, "src/feature_engineering.py"], check=True)
        logging.info("Feature engineering completed.")
    except Exception as e:
        logging.error(f"Feature engineering failed: {e}")
        raise

def run_model_training():
    try:
        logging.info("Training new champion model...")
        from src.main_trainer import main
        main()
        logging.info("Model training completed.")
    except Exception as e:
        logging.error(f"Model training failed: {e}")
        raise

if __name__ == "__main__":
    try:
        # בדיקת סביבה לפני הרצה
        if not check_environment():
            logging.error("Environment check failed. Exiting.")
            sys.exit(1)
            
        run_data_collection()
        run_preprocessing()
        run_feature_engineering()  # תוסף חדש - חישוב פיצ'רים בנפרד
        run_model_training()
        logging.info("All steps completed successfully.")
    except Exception as e:
        logging.error(f"Process failed with error: {e}")
        sys.exit(1)
