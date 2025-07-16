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

        merged_df.to_csv(out_path, index=False)
        logging.info(f"✅ Preprocessing complete. Saved merged data to {out_path} (rows: {len(merged_df)})")

    except Exception as e:
        logging.error(f"An error occurred during preprocessing: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    preprocess_data()
