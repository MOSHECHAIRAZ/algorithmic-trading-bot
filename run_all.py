import logging
import sys
import subprocess
from src.utils import archive_existing_file

# הגדרת לוגינג בסיסי
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

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
        subprocess.run([sys.executable, "run_preprocessing.py"], check=True)
        logging.info("Data preprocessing completed.")
    except Exception as e:
        logging.error(f"Data preprocessing failed: {e}")
        raise

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
        subprocess.run([
            sys.executable, "main_trainer.py"
            # אין צורך בפרמטרים נוספים, הכל נקבע בקונפיגורציה
        ], check=True)
        logging.info("Model training completed.")
    except Exception as e:
        logging.error(f"Model training failed: {e}")
        raise

if __name__ == "__main__":
    run_data_collection()
    run_preprocessing()
    run_feature_engineering()  # תוסף חדש - חישוב פיצ'רים בנפרד
    run_model_training()
    logging.info("All steps completed successfully.")
