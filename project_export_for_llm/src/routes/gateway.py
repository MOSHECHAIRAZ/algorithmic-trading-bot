"""
קובץ זה מכיל את כל הנתיבים הקשורים לניהול ה-Gateway של IBKR
"""

from flask import Blueprint, jsonify, request
import logging
import os
import sys
import subprocess
import time
import json
from dotenv import load_dotenv
from pathlib import Path

# יצירת Blueprint עבור ניהול Gateway
gateway_bp = Blueprint('gateway', __name__, url_prefix='/api/gateway')

# טעינת משתני סביבה (מבוצע פעם נוספת למקרה שהם השתנו)
load_dotenv()

# בדיקה אם pyautogui זמין
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    # הגדרת השהייה בטיחותית בין פעולות
    pyautogui.PAUSE = 0.5
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logging.warning("pyautogui not available - some gateway operations will be limited")

# טעינת קובץ תצורת המערכת
def load_system_config():
    """טוען את קובץ תצורת המערכת"""
    try:
        config_path = Path('system_config.json')
        if not config_path.exists():
            logging.error(f"Config file not found at {config_path}")
            return {}
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading system config: {e}")
        return {}

@gateway_bp.route('/start', methods=['POST'])
def start_gateway():
    """מפעיל את ה-Gateway של IBKR"""
    try:
        # בדיקה אם ה-Gateway כבר פועל
        # TODO: יש להוסיף בדיקה אמיתית אם ה-Gateway פועל
        
        # שימוש בסקריפט הפעלה נפרד
        result = subprocess.run(
            [sys.executable, 'start_ibkr.py'], 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            return jsonify({
                "status": "success", 
                "message": "IBKR Gateway startup initiated"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": f"Gateway failed to start: {result.stderr}"
            }), 500
            
    except Exception as e:
        logging.error(f"Error starting gateway: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"שגיאה בהפעלת Gateway: {str(e)}"
        }), 500

@gateway_bp.route('/login', methods=['POST'])
def login_to_gateway():
    """מבצע התחברות ל-Gateway"""
    try:
        # אם אין pyautogui, לא ניתן להתחבר
        if not PYAUTOGUI_AVAILABLE:
            return jsonify({
                "status": "error", 
                "message": "pyautogui not available - cannot perform login"
            }), 400
            
        # קבלת נתוני התחברות
        data = request.json or {}
        auto_fill = data.get('auto_fill', True)
        
        # קבלת פרטי התחברות מהסביבה
        username = os.getenv("IBKR_USERNAME")
        password = os.getenv("IBKR_PASSWORD")
        
        if not username or not password:
            # אם אין פרטים בסביבה, ננסה לקבל מהתצורה
            config = load_system_config()
            username = config.get('ibkr_settings', {}).get('username')
            password = config.get('ibkr_settings', {}).get('password')
            
        if not username or not password:
            return jsonify({
                "status": "error", 
                "message": "Missing login credentials"
            }), 400
            
        if auto_fill:
            logging.info("Auto-fill is enabled, attempting to fill login data...")
            success = auto_fill_login_data(username, password)
            
            if success:
                return jsonify({
                    "status": "success", 
                    "message": "Login data filled successfully"
                })
            else:
                return jsonify({
                    "status": "error", 
                    "message": "Failed to fill login data"
                }), 500
        else:
            return jsonify({
                "status": "warning", 
                "message": "Auto-fill disabled, user must login manually"
            })
            
    except Exception as e:
        logging.error(f"Error during gateway login: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"שגיאה בהתחברות ל-Gateway: {str(e)}"
        }), 500

def auto_fill_login_data(username, password):
    """מזין נתוני התחברות אוטומטית לחלון Gateway באמצעות מאקרו או שיטה ישירה"""
    try:
        if not PYAUTOGUI_AVAILABLE:
            logging.warning("pyautogui not available for auto-fill")
            return False
            
        # בדיקה אם קיים מאקרו התחברות מוקלט
        try:
            import login_recorder
            recording_exists = os.path.exists(login_recorder.DEFAULT_RECORDING_PATH)
            
            if recording_exists:
                # השתמש במאקרו המוקלט
                logging.info("Using recorded login macro...")
                success = login_recorder.run_login_macro()
                if success:
                    logging.info("Login macro played successfully")
                    return True
                else:
                    logging.warning("Login macro failed, falling back to direct method")
            else:
                logging.info("No login macro found, using direct method")
        except ImportError:
            logging.warning("login_recorder module not available, using direct method")
        
        # אם לא קיים מאקרו או שהמאקרו נכשל, השתמש בשיטה הישירה
        logging.info("Starting simplified Gateway login process...")
        
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 1.0  # המתנה ארוכה יותר בין פעולות
        
        # המתנה לטעינת חלון Gateway
        logging.info("Waiting for Gateway window to load...")
        time.sleep(5)  # המתנה לטעינת החלון
        
        # גישה פשוטה - ללא חיפוש חלון ספציפי
        # קליק במרכז המסך להתמקדות
        screen_width, screen_height = pyautogui.size()
        center_x, center_y = screen_width // 2, screen_height // 2
        
        logging.info("Using direct simplified login method")
        
        # ודא שהמקלדת באנגלית
        pyautogui.hotkey('alt', 'shift')
        time.sleep(1)
        
        # קליק במרכז המסך להתמקדות
        pyautogui.click(center_x, center_y)
        time.sleep(1)
        
        # גישה ישירה - הקלדת שם משתמש
        logging.info(f"Direct typing of username: {username}")
        # הקלד שם משתמש מקובץ .env
        pyautogui.write(username, interval=0.25)
        time.sleep(1)
        
        # Tab לשדה הבא
        pyautogui.press('tab')
        time.sleep(1)
        
        # הקלד סיסמה מקובץ .env
        logging.info("Direct typing of password")
        pyautogui.write(password, interval=0.25)
        time.sleep(1)
        
        # Enter להגשה
        pyautogui.press('enter')
        
        logging.info("Login form submitted with direct typing")
        return True
            
    except Exception as e:
        logging.error(f"Critical error in auto_fill_login_data: {str(e)}")
        return False

@gateway_bp.route('/status', methods=['GET'])
def check_gateway_status():
    """בודק אם ה-Gateway פעיל ומחובר"""
    # TODO: יש לממש בדיקה אמיתית של סטטוס ה-Gateway
    
    # גישה זמנית - הפעלת סקריפט בדיקה
    try:
        result = subprocess.run(
            [sys.executable, 'test_ib_connection.py'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return jsonify({
                "status": "connected",
                "message": "Gateway is running and connected"
            })
        else:
            return jsonify({
                "status": "disconnected",
                "message": "Gateway is not connected",
                "details": result.stderr
            })
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "unknown",
            "message": "Gateway status check timed out"
        })
    except Exception as e:
        logging.error(f"Error checking gateway status: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error checking gateway status: {str(e)}"
        }), 500
