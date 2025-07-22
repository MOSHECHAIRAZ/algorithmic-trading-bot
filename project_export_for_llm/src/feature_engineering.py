#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
feature_engineering.py
----------------------
תוכנית נפרדת לחישוב פיצ'רים מנתונים שעברו עיבוד ראשוני.
מטרת התוכנית הפרדת שלב יצירת הפיצ'רים משלב האימון.
"""

import os
import sys
import time
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# הוספת ספריית src לPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import load_system_config
from src.feature_calculator import FeatureCalculator

# הגדרות לוגר
log_path = 'all_features_computed.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(log_path, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """
    פונקציה ראשית לחישוב פיצ'רים
    """
    start_time = time.time()
    logging.info("=== תהליך חישוב פיצ'רים החל ===")
    
    try:
        # טעינת קונפיגורציה
        config = load_system_config()
        logging.info("קונפיגורציה נטענה בהצלחה")
        
        # נתיבים לקבצי קלט/פלט
        input_file = Path(config['system_paths'].get('processed_data', 'data/processed/SPY_processed.csv'))
        output_feature_file = Path(config['system_paths'].get('feature_data', 'data/processed/SPY_features.csv'))
        failed_features_report = Path('feature_fail_report.json')
        
        # וידוא שקובץ הקלט קיים
        if not input_file.exists():
            logging.error(f"קובץ קלט {input_file} לא נמצא. יש להפעיל קודם את עיבוד הנתונים.")
            return 1
        
        # טעינת הנתונים המעובדים
        logging.info(f"טוען נתונים מעובדים מ- {input_file}")
        df = pd.read_csv(input_file, index_col=0, parse_dates=True)
        
        # חישוב כל הפיצ'רים האפשריים
        logging.info(f"מחשב פיצ'רים מתוך {len(df)} שורות נתונים...")
        fc = FeatureCalculator()
        
        # קודם חישוב אינדיקטורים קריטיים באופן ישיר
        logging.info("מחשב אינדיקטורים קריטיים באופן ישיר...")
        df = fc.add_critical_indicators(df, verbose=True)
        
        # אחר כך חישוב שאר האינדיקטורים
        logging.info("מחשב שאר האינדיקטורים...")
        features_df, stats = fc.add_all_possible_indicators(df, verbose=True)
        
        # שמירת הנתונים עם הפיצ'רים
        output_feature_file.parent.mkdir(parents=True, exist_ok=True)
        features_df.to_csv(output_feature_file)
        logging.info(f"קובץ פיצ'רים נשמר בהצלחה ב- {output_feature_file}")
        
        # שמירת דוח פיצ'רים שנכשלו
        with open(failed_features_report, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=4)
        
        # סטטיסטיקות חישוב פיצ'רים
        logging.info(f"סיכום: נוצרו {stats['succeeded']} פיצ'רים בהצלחה, נכשלו {stats['failed']} פיצ'רים")
        logging.info(f"מספר כולל של עמודות בדאטאפריים הסופי: {len(features_df.columns)}")
        
        # מידע על זיכרון וזמן ריצה
        memory_usage = features_df.memory_usage(deep=True).sum() / (1024 * 1024)
        logging.info(f"גודל הדאטאפריים הסופי: {memory_usage:.2f} MB")
        logging.info(f"זמן ריצה כולל: {time.time() - start_time:.2f} שניות")
        
        return 0
        
    except Exception as e:
        logging.exception(f"אירעה שגיאה במהלך חישוב הפיצ'רים: {str(e)}")
        # שימוש ב-sys.exit במקום להחזיר קוד
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
