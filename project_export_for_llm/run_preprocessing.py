"""
סקריפט ייעודי לעיבוד נתונים: ממזג את קובצי ה-CSV הגולמיים
מ-data/raw/ לקובץ מאוחד ב-data/processed/SPY_processed.csv.
"""
import logging
import sys

# הגדרת לוגינג
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# ייבוא פונקציית עיבוד נתונים מהמודול src
from src.run_preprocessing import preprocess_data

if __name__ == "__main__":
    try:
        logging.info("Starting preprocessing from wrapper script")
        preprocess_data()
        logging.info("Preprocessing completed successfully")
    except Exception as e:
        logging.error(f"Error during preprocessing: {e}")
        sys.exit(1)
