"""
מודול להקלטה ושחזור של מהלכי התחברות ל-IB Gateway
משתמש ב-pyautogui כדי להקליט ולשחזר פעולות עכבר ומקלדת
"""

import os
import json
import time
import logging
from datetime import datetime

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

# הגדרת לוגר
logger = logging.getLogger(__name__)

# נתיב לשמירת ההקלטות
RECORDINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# נתיב ברירת מחדל להקלטה אחרונה
DEFAULT_RECORDING_PATH = os.path.join(RECORDINGS_DIR, "ibkr_login_macro.json")

class LoginMacroRecorder:
    """מקליט ומשחזר פעולות התחברות ל-IB Gateway"""
    
    def __init__(self):
        """אתחול המקליט"""
        self.actions = []
        self.is_recording = False
        self.start_time = None
        self.prev_action_time = None
        self.screen_size = None
        if PYAUTOGUI_AVAILABLE:
            self.screen_size = pyautogui.size()
    
    def start_recording(self):
        """התחלת הקלטה"""
        if not PYAUTOGUI_AVAILABLE:
            logger.error("pyautogui לא מותקן - לא ניתן להקליט")
            return False
        
        # נקה הקלטות קודמות
        self.actions = []
        self.is_recording = True
        self.start_time = datetime.now()
        self.prev_action_time = self.start_time
        
        # הקלט את גודל המסך
        self.screen_size = pyautogui.size()
        
        logger.info(f"התחלת הקלטת מאקרו התחברות בשעה {self.start_time.strftime('%H:%M:%S')}")
        logger.info("יש לבצע עכשיו את תהליך ההתחברות. כל הפעולות יוקלטו.")
        
        # הוסף פעולת השהייה ראשונית כדי לתת זמן למשתמש להתחיל את הפעולות
        self._add_delay_action(3)
        
        # אנחנו לא נוסיף פעולת העברת מקלדת לאנגלית - נשאיר את זה למשתמש
        
        return True
    
    def record_click(self, x, y, button='left'):
        """הקלט פעולת קליק"""
        if not self.is_recording:
            return
        
        # המר לאחוזים מגודל המסך (כדי שיעבוד על מסכים בגדלים שונים)
        x_percent = x / self.screen_size[0]
        y_percent = y / self.screen_size[1]
        
        self._add_action("click", {
            "x_percent": x_percent,
            "y_percent": y_percent,
            "button": button
        })
    
    def record_key(self, key):
        """הקלט לחיצת מקש"""
        if not self.is_recording:
            return
        
        self._add_action("key", {"key": key})
    
    def record_write(self, text):
        """הקלט כתיבת טקסט"""
        if not self.is_recording:
            return
        
        self._add_action("write", {"text": text})
    
    def record_hotkey(self, *keys):
        """הקלט לחיצת קיצור מקשים"""
        if not self.is_recording:
            return
        
        self._add_action("hotkey", {"keys": list(keys)})
    
    def _add_action(self, action_type, params):
        """הוסף פעולה להקלטה"""
        now = datetime.now()
        delay = (now - self.prev_action_time).total_seconds()
        
        # הוסף השהייה לפני הפעולה הנוכחית
        if delay > 0.1:  # רק אם ההשהייה משמעותית
            self._add_delay_action(delay)
        
        self.actions.append({
            "type": action_type,
            "params": params,
            "time": now.strftime("%H:%M:%S.%f")[:-3]
        })
        
        self.prev_action_time = now
    
    def _add_delay_action(self, seconds):
        """הוסף פעולת השהייה"""
        self.actions.append({
            "type": "delay",
            "params": {"seconds": seconds},
            "time": datetime.now().strftime("%H:%M:%S.%f")[:-3]
        })
    
    def stop_recording(self):
        """סיום הקלטה"""
        if not self.is_recording:
            return False
        
        self.is_recording = False
        duration = (datetime.now() - self.start_time).total_seconds()
        
        logger.info(f"סיום הקלטת מאקרו. משך ההקלטה: {duration:.1f} שניות. {len(self.actions)} פעולות הוקלטו.")
        return True
    
    def save_recording(self, file_path=DEFAULT_RECORDING_PATH):
        """שמירת ההקלטה לקובץ"""
        if not self.actions:
            logger.warning("אין הקלטה לשמירה")
            return False
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "recorded_at": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "screen_size": self.screen_size,
                    "actions": self.actions
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"הקלטה נשמרה בהצלחה: {file_path}")
            return True
        except Exception as e:
            logger.error(f"שגיאה בשמירת ההקלטה: {str(e)}")
            return False
    
    def load_recording(self, file_path=DEFAULT_RECORDING_PATH):
        """טעינת הקלטה מקובץ"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"קובץ הקלטה לא קיים: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.actions = data["actions"]
            self.screen_size = tuple(data["screen_size"])
            
            logger.info(f"הקלטה נטענה בהצלחה: {file_path} ({len(self.actions)} פעולות)")
            return True
        except Exception as e:
            logger.error(f"שגיאה בטעינת ההקלטה: {str(e)}")
            return False
    
    def playback(self, speed_factor=1.0):
        """הפעלת ההקלטה - ביצוע הפעולות המוקלטות"""
        if not PYAUTOGUI_AVAILABLE:
            logger.error("pyautogui לא מותקן - לא ניתן לבצע הקלטה")
            return False
        
        if not self.actions:
            logger.warning("אין פעולות להפעלה")
            return False
        
        logger.info(f"מתחיל הפעלת מאקרו התחברות ({len(self.actions)} פעולות)")
        pyautogui.FAILSAFE = True
        
        current_screen_size = pyautogui.size()
        logger.info(f"גודל מסך נוכחי: {current_screen_size}, גודל מסך מקורי: {self.screen_size}")
        
        try:
            for i, action in enumerate(self.actions):
                action_type = action["type"]
                params = action["params"]
                
                logger.debug(f"פעולה {i+1}/{len(self.actions)}: {action_type} - {params}")
                
                if action_type == "delay":
                    # חישוב השהייה עם מהירות משתנה
                    delay = params["seconds"] / speed_factor
                    logger.debug(f"משהה לפני הפעולה הבאה: {delay:.2f} שניות")
                    time.sleep(delay)
                
                elif action_type == "click":
                    # המרה מאחוזים לפיקסלים במסך הנוכחי
                    x = int(params["x_percent"] * current_screen_size[0])
                    y = int(params["y_percent"] * current_screen_size[1])
                    button = params.get("button", "left")
                    
                    logger.debug(f"לוחץ ב: ({x}, {y}) עם כפתור {button}")
                    pyautogui.click(x, y, button=button)
                
                elif action_type == "key":
                    logger.debug(f"לוחץ על מקש: {params['key']}")
                    pyautogui.press(params["key"])
                
                elif action_type == "write":
                    logger.debug(f"כותב טקסט: {params['text']}")
                    pyautogui.write(params["text"], interval=0.05)
                
                elif action_type == "hotkey":
                    logger.debug(f"מבצע קיצור מקשים: {'+'.join(params['keys'])}")
                    pyautogui.hotkey(*params["keys"])
            
            logger.info("הפעלת המאקרו הסתיימה בהצלחה")
            return True
        
        except Exception as e:
            logger.error(f"שגיאה בהפעלת המאקרו: {str(e)}")
            return False


# גישה ישירה לפונקציות
recorder = LoginMacroRecorder()

def start_login_recording():
    """התחלת הקלטת תהליך התחברות"""
    return recorder.start_recording()

def stop_login_recording():
    """סיום הקלטת תהליך התחברות"""
    return recorder.stop_recording()

def save_login_recording(file_path=DEFAULT_RECORDING_PATH):
    """שמירת הקלטת תהליך התחברות"""
    return recorder.save_recording(file_path)

def run_login_macro(file_path=DEFAULT_RECORDING_PATH, speed_factor=1.0):
    """הפעלת מאקרו התחברות"""
    if recorder.load_recording(file_path):
        logger.info(f"מריץ מאקרו התחברות עם {len(recorder.actions)} פעולות")
        logger.info(f"כתובת קובץ המאקרו: {file_path}")
        
        try:
            return recorder.playback(speed_factor)
        except Exception as e:
            logger.error(f"שגיאה בהרצת המאקרו: {str(e)}")
            # הוסף מידע נוסף לאבחון
            import traceback
            logger.error(f"פרטי שגיאה: {traceback.format_exc()}")
            return False
    
    logger.warning(f"לא ניתן לטעון את קובץ המאקרו: {file_path}")
    return False
