"""
gateway_manager.py - מודול לניהול ה-Gateway של Interactive Brokers

מודול זה מרכז את כל הפונקציונליות הקשורה להפעלה וניהול של Gateway של Interactive Brokers,
כולל התחברות, בדיקת סטטוס, וניתוק.
"""

import os
import sys
import subprocess
import time
import logging
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any, Union
from dotenv import load_dotenv

# טעינת משתני סביבה
load_dotenv()

# הגדרת הלוגר
logger = logging.getLogger(__name__)

# בדיקה אם pyautogui זמין (אופציונלי - לשימוש זמני בלבד)
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    # הגדרת השהייה בטיחותית בין פעולות
    pyautogui.PAUSE = 0.5
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not available - some gateway operations will be limited")

class GatewayManager:
    """
    מנהל ה-Gateway של Interactive Brokers
    """
    
    def __init__(self, config_path: str = "system_config.json"):
        """
        אתחול מנהל ה-Gateway
        
        Args:
            config_path: נתיב לקובץ הקונפיגורציה
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # הגדרות מהקונפיגורציה
        self.gateway_path = self.config.get('ibkr_settings', {}).get('gateway_path', '')
        self.port = self.config.get('ibkr_settings', {}).get('port', 4001)
        self.client_id = self.config.get('ibkr_settings', {}).get('clientId', 1)
        
        # פרטי התחברות מסביבת העבודה
        self.username = os.getenv("IBKR_USERNAME")
        self.password = os.getenv("IBKR_PASSWORD")
        
        # אם אין פרטים בסביבה, ננסה לקבל מהתצורה (לא מומלץ)
        if not self.username or not self.password:
            self.username = self.config.get('ibkr_settings', {}).get('username')
            self.password = self.config.get('ibkr_settings', {}).get('password')
            
        # התהליך הנוכחי
        self.process = None
        
    def _load_config(self) -> Dict:
        """
        טוען את קובץ הקונפיגורציה
        
        Returns:
            מילון עם הקונפיגורציה
        """
        try:
            if not os.path.exists(self.config_path):
                logger.error(f"קובץ תצורה לא נמצא בנתיב: {self.config_path}")
                return {}
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"שגיאה בטעינת קובץ תצורה: {e}")
            return {}
            
    def start_gateway(self) -> Dict[str, Any]:
        """
        מפעיל את ה-Gateway
        
        Returns:
            מילון עם סטטוס ההפעלה
        """
        if not self.gateway_path:
            return {
                "status": "error", 
                "message": "Gateway path not configured"
            }
            
        if not os.path.exists(self.gateway_path):
            return {
                "status": "error", 
                "message": f"Gateway executable not found at {self.gateway_path}"
            }
            
        try:
            # הפעלת תהליך ה-Gateway
            logger.info(f"Starting IB Gateway from {self.gateway_path}")
            
            # בדיקה אם ה-Gateway כבר פועל
            if self.is_gateway_running():
                return {
                    "status": "warning", 
                    "message": "IB Gateway is already running"
                }
                
            # שימוש בסקריפט הפעלה נפרד אם קיים
            if os.path.exists('start_ibkr.py'):
                self.process = subprocess.Popen(
                    [sys.executable, 'start_ibkr.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # המתנה קצרה לתחילת ההפעלה
                time.sleep(2)
                
                return {
                    "status": "success", 
                    "message": "IB Gateway startup initiated"
                }
            else:
                # הפעלה ישירה של ה-Gateway
                self.process = subprocess.Popen(
                    [self.gateway_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # המתנה קצרה לתחילת ההפעלה
                time.sleep(5)
                
                return {
                    "status": "success", 
                    "message": "IB Gateway started directly"
                }
                
        except Exception as e:
            error_msg = f"Error starting IB Gateway: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error", 
                "message": error_msg
            }
            
    def login_to_gateway(self, use_macro: bool = True) -> Dict[str, Any]:
        """
        מתחבר ל-Gateway
        
        Args:
            use_macro: האם להשתמש במאקרו מוקלט (אם קיים)
            
        Returns:
            מילון עם סטטוס ההתחברות
        """
        if not PYAUTOGUI_AVAILABLE:
            return {
                "status": "error", 
                "message": "pyautogui not available - cannot perform login"
            }
            
        if not self.username or not self.password:
            return {
                "status": "error", 
                "message": "Missing login credentials"
            }
            
        try:
            logger.info("Starting Gateway login process...")
            
            if use_macro:
                # בדיקה אם קיים מאקרו התחברות מוקלט
                try:
                    import login_recorder
                    recording_exists = os.path.exists(login_recorder.DEFAULT_RECORDING_PATH)
                    
                    if recording_exists:
                        # השתמש במאקרו המוקלט
                        logger.info("Using recorded login macro...")
                        success = login_recorder.run_login_macro()
                        if success:
                            logger.info("Login macro played successfully")
                            return {
                                "status": "success", 
                                "message": "Login macro played successfully"
                            }
                        else:
                            logger.warning("Login macro failed, falling back to direct method")
                    else:
                        logger.info("No login macro found, using direct method")
                except ImportError:
                    logger.warning("login_recorder module not available, using direct method")
            
            # שיטה ישירה להתחברות
            return self._direct_login()
                
        except Exception as e:
            error_msg = f"Error during gateway login: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error", 
                "message": error_msg
            }
            
    def _direct_login(self) -> Dict[str, Any]:
        """
        שיטה ישירה להתחברות ל-Gateway
        
        Returns:
            מילון עם סטטוס ההתחברות
        """
        try:
            logger.info("Starting simplified Gateway login process...")
            
            import pyautogui
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 1.0  # המתנה ארוכה יותר בין פעולות
            
            # המתנה לטעינת חלון Gateway
            logger.info("Waiting for Gateway window to load...")
            time.sleep(5)  # המתנה לטעינת החלון
            
            # גישה פשוטה - ללא חיפוש חלון ספציפי
            # קליק במרכז המסך להתמקדות
            screen_width, screen_height = pyautogui.size()
            center_x, center_y = screen_width // 2, screen_height // 2
            
            logger.info("Using direct simplified login method")
            
            # ודא שהמקלדת באנגלית
            pyautogui.hotkey('alt', 'shift')
            time.sleep(1)
            
            # קליק במרכז המסך להתמקדות
            pyautogui.click(center_x, center_y)
            time.sleep(1)
            
            # גישה ישירה - הקלדת שם משתמש
            logger.info(f"Direct typing of username: {self.username}")
            pyautogui.write(self.username, interval=0.25)
            time.sleep(1)
            
            # Tab לשדה הבא
            pyautogui.press('tab')
            time.sleep(1)
            
            # הקלד סיסמה
            logger.info("Direct typing of password")
            pyautogui.write(self.password, interval=0.25)
            time.sleep(1)
            
            # Enter להגשה
            pyautogui.press('enter')
            
            logger.info("Login form submitted with direct typing")
            return {
                "status": "success", 
                "message": "Login form submitted"
            }
                
        except Exception as e:
            error_msg = f"Critical error in direct login: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error", 
                "message": error_msg
            }
            
    def check_gateway_status(self) -> Dict[str, Any]:
        """
        בודק את סטטוס ה-Gateway
        
        Returns:
            מילון עם סטטוס ה-Gateway
        """
        try:
            # גישה זמנית - הפעלת סקריפט בדיקה
            if os.path.exists('test_ib_connection.py'):
                result = subprocess.run(
                    [sys.executable, 'test_ib_connection.py'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    return {
                        "status": "connected",
                        "message": "Gateway is running and connected"
                    }
                else:
                    return {
                        "status": "disconnected",
                        "message": "Gateway is not connected",
                        "details": result.stderr
                    }
            else:
                # בדיקה חלופית - אם ה-Gateway רץ
                if self.is_gateway_running():
                    return {
                        "status": "running",
                        "message": "Gateway process is running, but connection status is unknown"
                    }
                else:
                    return {
                        "status": "stopped",
                        "message": "Gateway is not running"
                    }
        except subprocess.TimeoutExpired:
            return {
                "status": "unknown",
                "message": "Gateway status check timed out"
            }
        except Exception as e:
            error_msg = f"Error checking gateway status: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
            
    def is_gateway_running(self) -> bool:
        """
        בודק אם תהליך ה-Gateway רץ
        
        Returns:
            האם התהליך רץ
        """
        # בדיקה אם יש תהליך פעיל
        if self.process and self.process.poll() is None:
            return True
            
        # ניסיון להתחבר לפורט ה-Gateway
        import socket
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        
        try:
            # נסה להתחבר לפורט של ה-Gateway
            s.connect(('127.0.0.1', self.port))
            s.close()
            return True
        except:
            return False
            
    def stop_gateway(self) -> Dict[str, Any]:
        """
        עוצר את ה-Gateway
        
        Returns:
            מילון עם סטטוס העצירה
        """
        try:
            if not self.is_gateway_running():
                return {
                    "status": "warning", 
                    "message": "Gateway is not running"
                }
                
            # אם יש תהליך פעיל, עצור אותו
            if self.process and self.process.poll() is None:
                logger.info("Stopping Gateway process...")
                
                # נסה לסגור בעדינות תחילה
                self.process.terminate()
                
                # המתנה לסיום
                for _ in range(50):  # המתנה של עד 5 שניות
                    if self.process.poll() is not None:
                        break
                    time.sleep(0.1)
                    
                # אם התהליך עדיין רץ, הרוג אותו
                if self.process.poll() is None:
                    logger.warning("Gateway process did not terminate gracefully, killing it")
                    self.process.kill()
                    
                return {
                    "status": "success", 
                    "message": "Gateway process stopped"
                }
            else:
                # שימוש בסקריפט לסגירת ה-Gateway
                if os.path.exists('stop_ibkr.py'):
                    subprocess.run(
                        [sys.executable, 'stop_ibkr.py'],
                        timeout=10
                    )
                    
                    return {
                        "status": "success", 
                        "message": "Gateway stop script executed"
                    }
                else:
                    logger.warning("No stop script found and no active process to terminate")
                    return {
                        "status": "warning", 
                        "message": "No method available to stop Gateway"
                    }
                    
        except Exception as e:
            error_msg = f"Error stopping Gateway: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error", 
                "message": error_msg
            }

# יצירת מופע גלובלי של מנהל ה-Gateway
gateway_manager = GatewayManager()
