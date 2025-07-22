"""
stop_ibkr.py - סקריפט לעצירת ה-Gateway של Interactive Brokers

סקריפט זה עוצר את ה-Gateway של Interactive Brokers.
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

# הגדרת לוגר
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/ibkr_gateway_{time.strftime('%Y%m%d')}.log", encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# יצירת תיקיית לוגים אם לא קיימת
os.makedirs("logs", exist_ok=True)

# טעינת משתני סביבה
load_dotenv()

def main():
    """
    פונקציה ראשית לעצירת ה-Gateway
    """
    try:
        logger.info("Stopping IB Gateway...")
        
        # יבוא מנהל ה-Gateway
        from src.gateway_manager import gateway_manager
        
        # עצירת ה-Gateway
        result = gateway_manager.stop_gateway()
        
        if result["status"] in ["success", "warning"]:
            logger.info(f"Gateway shutdown: {result['message']}")
            return 0
        else:
            logger.error(f"Failed to stop Gateway: {result['message']}")
            return 1
            
    except Exception as e:
        logger.error(f"Error in stop_ibkr.py: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
