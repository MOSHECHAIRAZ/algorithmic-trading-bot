"""
start_ibkr.py - סקריפט להפעלת ה-Gateway של Interactive Brokers

סקריפט זה מפעיל את ה-Gateway של Interactive Brokers ומנסה להתחבר באופן אוטומטי.
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
    פונקציה ראשית להפעלת ה-Gateway
    """
    try:
        logger.info("Starting IB Gateway...")
        
        # יבוא מנהל ה-Gateway
        from src.gateway_manager import gateway_manager
        
        # הפעלת ה-Gateway
        result = gateway_manager.start_gateway()
        
        if result["status"] in ["success", "warning"]:
            logger.info(f"Gateway startup: {result['message']}")
            
            # המתנה לטעינת ה-Gateway
            logger.info("Waiting for Gateway to initialize...")
            time.sleep(5)
            
            # ניסיון להתחבר
            login_result = gateway_manager.login_to_gateway()
            logger.info(f"Gateway login: {login_result['message']}")
            
            # בדיקת סטטוס ה-Gateway
            time.sleep(3)  # המתנה לסיום ההתחברות
            status_result = gateway_manager.check_gateway_status()
            logger.info(f"Gateway status: {status_result['status']} - {status_result['message']}")
            
            return 0
        else:
            logger.error(f"Failed to start Gateway: {result['message']}")
            return 1
            
    except Exception as e:
        logger.error(f"Error in start_ibkr.py: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
