"""
מקליט מאקרו אוטומטי שמקליט את כל הפעולות בזמן אמת
"""

import json
import time
import threading
import logging
from datetime import datetime
import os

try:
    import pyautogui
    import pynput
    from pynput import mouse, keyboard
    RECORDING_AVAILABLE = True
    
    # הגדרות pyautogui
    pyautogui.FAILSAFE = True  # לביטחון - ESC יעצור את הפעולות
    pyautogui.PAUSE = 0.1      # השהייה קצרה בין פעולות
    
except ImportError as e:
    RECORDING_AVAILABLE = False
    print(f"שגיאה בייבוא חבילות: {e}")
    print("נדרש להתקין: pip install pyautogui pynput")

logger = logging.getLogger(__name__)

class AutoMacroRecorder:
    """מקליט אוטומטי שמקליט את כל הפעולות בזמן אמת"""
    
    def __init__(self):
        self.actions = []
        self.is_recording = False
        self.start_time = None
        self.mouse_listener = None
        self.keyboard_listener = None
        self.last_action_time = None
        
    def start_recording(self):
        """התחלת הקלטה אוטומטית"""
        if not RECORDING_AVAILABLE:
            logger.error("pynput או pyautogui לא מותקנים - לא ניתן להקליט")
            return False
            
        self.actions = []
        self.is_recording = True
        self.start_time = time.time()
        self.last_action_time = self.start_time
        
        # התחלת האזנה לעכבר
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self.mouse_listener.start()
        
        # התחלת האזנה למקלדת
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
        logger.info("הקלטה התחילה")
        return True
    
    def stop_recording(self):
        """הפסקת הקלטה אוטומטית"""
        if not self.is_recording:
            return False
            
        # הפסקת האזנה לעכבר ומקלדת
        if self.mouse_listener:
            self.mouse_listener.stop()
            
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
        self.is_recording = False
        logger.info(f"הקלטה הופסקה. {len(self.actions)} פעולות הוקלטו.")
        return True
    
    def _add_action(self, action_type, params=None):
        """הוספת פעולה להקלטה עם מדידת זמן"""
        if not self.is_recording:
            return
            
        now = time.time()
        delay = now - self.last_action_time
        
        # נוסיף השהייה רק אם עברה יותר מ-0.01 שניות מהפעולה הקודמת
        if delay > 0.01:
            action = {
                "type": action_type,
                "params": params if params is not None else {},
                "delay": round(delay, 3)  # עיגול ל-3 ספרות אחרי הנקודה
            }
            
            self.actions.append(action)
            self.last_action_time = now
    
    def _on_mouse_move(self, x, y):
        """טיפול בתזוזת עכבר"""
        # הקלטת תזוזת עכבר רק כל 100ms ואם זז יותר מ-5 פיקסלים
        # כדי למנוע הרבה פעולות מיותרות
        if len(self.actions) > 0 and self.actions[-1]["type"] == "mouse_move":
            last_x = self.actions[-1]["params"]["x"]
            last_y = self.actions[-1]["params"]["y"]
            
            # נקליט רק אם העכבר זז מספיק
            distance = ((x - last_x) ** 2 + (y - last_y) ** 2) ** 0.5
            if distance < 5:
                return
                
            # אם לא עברו לפחות 100ms מהתזוזה האחרונה, נעדכן את התזוזה האחרונה
            if time.time() - self.last_action_time < 0.1:
                self.actions[-1]["params"]["x"] = x
                self.actions[-1]["params"]["y"] = y
                return
                
        self._add_action("mouse_move", {"x": x, "y": y})
    
    def _on_mouse_click(self, x, y, button, pressed):
        """טיפול בלחיצת עכבר"""
        button_name = str(button).split(".")[-1]
        self._add_action(
            "mouse_click" if pressed else "mouse_release",
            {"x": x, "y": y, "button": button_name}
        )
        
        # ESC דרך העכבר - מעט מוזר אבל נתמוך בזה
        if button == mouse.Button.middle and pressed:
            logger.info("לחיצה על כפתור אמצעי - מפסיק הקלטה")
            self.stop_recording()
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """טיפול בגלילת עכבר"""
        self._add_action("mouse_scroll", {"x": x, "y": y, "dx": dx, "dy": dy})
    
    def _on_key_press(self, key):
        """טיפול בלחיצת מקש"""
        try:
            # ניסיון לקבל את הערך של המקש
            key_char = key.char
        except AttributeError:
            # אם אין ערך (למשל מקשים מיוחדים), נשתמש בשם
            key_char = str(key).split(".")[-1]
            
            # לבדוק אם זה מקש ESC
            if key == keyboard.Key.esc:
                logger.info("מקש ESC נלחץ - מפסיק הקלטה")
                self.stop_recording()
                return
        
        self._add_action("key_press", {"key": key_char})
    
    def _on_key_release(self, key):
        """טיפול בשחרור מקש"""
        try:
            key_char = key.char
        except AttributeError:
            key_char = str(key).split(".")[-1]
            
        self._add_action("key_release", {"key": key_char})
    
    def save_recording(self, filename):
        """שמירת ההקלטה לקובץ JSON"""
        try:
            # וידוא שתיקיית היעד קיימת
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # יצירת אובייקט JSON עם מידע נוסף
            recording_data = {
                "metadata": {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "duration": round(time.time() - self.start_time, 2),
                    "actions_count": len(self.actions)
                },
                "actions": self.actions
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(recording_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"הקלטה נשמרה בהצלחה: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"שגיאה בשמירת הקלטה: {e}")
            return False
    
    def play_recording(self, filename=None, speed=1.0):
        """הפעלת הקלטה מקובץ או מההקלטה הנוכחית"""
        actions = self.actions
        
        # אם יש שם קובץ, נטען את ההקלטה ממנו
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "actions" in data:
                        actions = data["actions"]
                    else:
                        actions = data  # למקרה שיש רק מערך של פעולות
                        
                logger.info(f"טעינת הקלטה מקובץ: {filename} ({len(actions)} פעולות)")
            except Exception as e:
                logger.error(f"שגיאה בטעינת הקלטה: {e}")
                return False
        
        if not actions:
            logger.warning("אין פעולות להפעלה")
            return False
            
        # וידוא שיש לנו את הספריות הנדרשות
        if not RECORDING_AVAILABLE:
            logger.error("pyautogui לא מותקן - לא ניתן להפעיל")
            return False
            
        # הפעלת כל הפעולות
        try:
            for action in actions:
                # המתנה לפי ההשהיה שנרשמה
                delay = action.get("delay", 0) / speed
                if delay > 0:
                    time.sleep(delay)
                
                action_type = action["type"]
                params = action.get("params", {})
                
                if action_type == "mouse_move":
                    pyautogui.moveTo(params["x"], params["y"])
                    
                elif action_type == "mouse_click":
                    button = params.get("button", "left")
                    pyautogui.mouseDown(params["x"], params["y"], button=button)
                    
                elif action_type == "mouse_release":
                    button = params.get("button", "left")
                    pyautogui.mouseUp(params["x"], params["y"], button=button)
                    
                elif action_type == "mouse_scroll":
                    pyautogui.scroll(params.get("dy", 0) * 10)  # הכפלה כי pyautogui דורש ערכים גדולים יותר
                    
                elif action_type == "key_press":
                    key = params["key"]
                    if len(key) == 1:  # תו בודד
                        pyautogui.keyDown(key)
                    else:  # מקש מיוחד
                        pyautogui.keyDown(key)
                        
                elif action_type == "key_release":
                    key = params["key"]
                    if len(key) == 1:  # תו בודד
                        pyautogui.keyUp(key)
                    else:  # מקש מיוחד
                        pyautogui.keyUp(key)
            
            logger.info(f"הפעלת הקלטה הסתיימה בהצלחה ({len(actions)} פעולות)")
            return True
            
        except Exception as e:
            logger.error(f"שגיאה בהפעלת הקלטה: {e}")
            return False

# יצירת מופע גלובלי של המקליט
auto_recorder = AutoMacroRecorder()

# פונקציות עזר חיצוניות
def start_auto_recording():
    """התחלת הקלטה אוטומטית"""
    return auto_recorder.start_recording()

def stop_auto_recording():
    """הפסקת הקלטה אוטומטית"""
    return auto_recorder.stop_recording()

def save_auto_recording(filename):
    """שמירת ההקלטה האוטומטית לקובץ"""
    return auto_recorder.save_recording(filename)

def play_auto_recording(filename=None, speed=1.0):
    """הפעלת הקלטה אוטומטית מקובץ או מההקלטה הנוכחית"""
    return auto_recorder.play_recording(filename, speed)
