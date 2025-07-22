"""
סקריפט ייעודי לעיבוד נתונים: ממזג את קובצי ה-CSV הגולמיים
מ-data/raw/ לקובץ מאוחד ב-data/processed/SPY_processed.csv.
"""
import pandas as pd
import os
import logging
import sys

# הגדרת לוגינג
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def preprocess_data():
    """
    ממזג את נתוני SPY ו-VIX, יוצר SPY_processed.csv כולל vix_close
    """
    logging.info("--- Starting Data Preprocessing ---")
    raw_dir = os.path.join('data', 'raw')
    processed_dir = os.path.join('data', 'processed')
    
    try:
        os.makedirs(processed_dir, exist_ok=True)
        spy_path = os.path.join(raw_dir, 'SPY_ibkr.csv')
        vix_path = os.path.join(raw_dir, 'VIX_ibkr.csv')
        out_path = os.path.join(processed_dir, 'SPY_processed.csv')

        if not os.path.exists(spy_path):
            logging.error(f"SPY raw data not found at {spy_path}. Cannot preprocess.")
            return

        logging.info(f"Reading SPY data from {spy_path}")
        spy = pd.read_csv(spy_path, parse_dates=['date'])
        
        merged_df = spy.copy()

        if os.path.exists(vix_path):
            logging.info(f"Reading and merging VIX data from {vix_path}")
            vix = pd.read_csv(vix_path, parse_dates=['date'])
            vix = vix[['date', 'close']].rename(columns={'close': 'vix_close'})
            # מיזוג ששומר על כל נתוני ה-SPY גם אם אין VIX תואם
            merged_df = pd.merge(spy, vix, on='date', how='left')
            # מילוי ערכי VIX חסרים (בגלל חגים וכו') עם הערך האחרון הידוע
            merged_df['vix_close'] = merged_df['vix_close'].ffill()
        else:
            logging.warning(f"VIX data not found at {vix_path}. Preprocessing without VIX.")
            merged_df['vix_close'] = None
            
        # דרוש מיון לפי תאריך לפני שמירה
        merged_df.sort_values('date', inplace=True)
        
        # שמירת הקובץ המאוחד
        logging.info(f"Saving merged data to {out_path}")
        merged_df.to_csv(out_path, index=False)
        logging.info(f"Successfully saved {len(merged_df)} rows to {out_path}")
        
        # תמצית סטטיסטית
        logging.info(f"Data summary: Range {merged_df['date'].min()} to {merged_df['date'].max()}")
        logging.info(f"VIX data available: {(~merged_df['vix_close'].isna()).sum()} rows")
        logging.info("--- Data Preprocessing Completed ---")
        
    except Exception as e:
        logging.error(f"Error in preprocessing: {str(e)}")
        # שימוש ב-sys.exit במקום להעלות שגיאה
        sys.exit(1)

if __name__ == "__main__":
    preprocess_data()
