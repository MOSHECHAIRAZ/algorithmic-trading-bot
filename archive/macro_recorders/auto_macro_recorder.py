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
        
        # הקלטת גודל מסך
        screen_size = pyautogui.size()
        self.screen_width = screen_size.width
        self.screen_height = screen_size.height
        
        logger.info(f"מתחיל הקלטה אוטומטית. גודל מסך: {self.screen_width}x{self.screen_height}")
        
        # הפעלת מאזינים
        self._start_listeners()
        
        return True
    
    def _start_listeners(self):
        """הפעלת מאזינים לעכבר ומקלדת"""
        # מאזין לעכבר
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        
        # מאזין למקלדת
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        logger.info("מאזינים הופעלו - מקליט את כל הפעולות")
    
    def _on_mouse_click(self, x, y, button, pressed):
        """טיפול בקליקים של עכבר"""
        if not self.is_recording or not pressed:
            return
            
        current_time = time.time()
        delay = current_time - self.last_action_time
        
        # המרה לאחוזים
        x_percent = x / self.screen_width
        y_percent = y / self.screen_height
        
        action = {
            "type": "click",
            "delay": delay,
            "params": {
                "x_percent": x_percent,
                "y_percent": y_percent,
                "button": str(button).split('.')[-1].lower(),
                "absolute_x": x,
                "absolute_y": y
            },
            "timestamp": current_time - self.start_time
        }
        
        self.actions.append(action)
        self.last_action_time = current_time
        
        logger.debug(f"קליק הוקלט: ({x}, {y}) כפתור {button}")
    
    def _on_mouse_scroll(self, x, y, dx, dy):
        """טיפול בגלילה של עכבר"""
        if not self.is_recording:
            return
            
        current_time = time.time()
        delay = current_time - self.last_action_time
        
        action = {
            "type": "scroll",
            "delay": delay,
            "params": {
                "x": x,
                "y": y,
                "dx": dx,
                "dy": dy
            },
            "timestamp": current_time - self.start_time
        }
        
        self.actions.append(action)
        self.last_action_time = current_time
    
    def _on_key_press(self, key):
        """טיפול בלחיצות מקשים"""
        if not self.is_recording:
            return
            
        current_time = time.time()
        delay = current_time - self.last_action_time
        
        # המרת המקש לפורמט מתאים
        try:
            if hasattr(key, 'char') and key.char is not None:
                key_name = key.char
            else:
                # מקשים מיוחדים
                key_name = str(key).replace('Key.', '')
        except AttributeError:
            key_name = str(key).replace('Key.', '')
        
        # דילוג על מקשים מסוימים שלא רוצים להקליט
        skip_keys = ['ctrl_l', 'ctrl_r', 'alt_l', 'alt_r', 'shift', 'shift_r', 'cmd']
        if key_name.lower() in skip_keys:
            return
        
        action = {
            "type": "key_press",
            "delay": delay,
            "params": {
                "key": key_name
            },
            "timestamp": current_time - self.start_time
        }
        
        self.actions.append(action)
        self.last_action_time = current_time
        
        logger.debug(f"מקש הוקלט: {key_name}")
    
    def _on_key_release(self, key):
        """טיפול בשחרור מקשים"""
        # בדיקה אם זה מקש עצירה (Escape)
        if key == keyboard.Key.esc:
            logger.info("נלחץ מקש Escape - עוצר הקלטה")
            self.stop_recording()
            return False  # עוצר את המאזין
    
    def stop_recording(self):
        """עצירת ההקלטה"""
        if not self.is_recording:
            return False
            
        self.is_recording = False
        
        # עצירת מאזינים
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        duration = time.time() - self.start_time
        logger.info(f"הקלטה הופסקה. משך: {duration:.1f} שניות, {len(self.actions)} פעולות")
        
        return True
    
    def save_recording(self, file_path):
        """שמירת ההקלטה"""
        try:
            recording_data = {
                "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "screen_size": [self.screen_width, self.screen_height],
                "duration": time.time() - self.start_time if self.start_time else 0,
                "actions_count": len(self.actions),
                "actions": self.actions
            }
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(recording_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"הקלטה נשמרה: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"שגיאה בשמירת הקלטה: {str(e)}")
            return False
    
    def load_and_playback(self, file_path, speed_factor=1.0):
        """טעינה והפעלה של הקלטה"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            actions = data.get('actions', [])
            original_screen_size = data.get('screen_size', [1920, 1080])
            
            logger.info(f"מפעיל הקלטה: {len(actions)} פעולות")
            
            # קבלת גודל מסך נוכחי
            current_screen = pyautogui.size()
            scale_x = current_screen.width / original_screen_size[0]
            scale_y = current_screen.height / original_screen_size[1]
            
            logger.info(f"גודל מסך מקורי: {original_screen_size}, נוכחי: {current_screen.width}x{current_screen.height}")
            logger.info(f"קנה מידה: X={scale_x:.2f}, Y={scale_y:.2f}")
            
            for i, action in enumerate(actions):
                # המתנה לפי השהייה המוקלטת
                delay = action.get('delay', 0) / speed_factor
                if delay > 0.05:  # השהייה מינימלית
                    time.sleep(delay)
                
                action_type = action.get('type')
                params = action.get('params', {})
                
                try:
                    if action_type == 'click':
                        # חישוב מיקום מתאים לגודל מסך נוכחי
                        if 'x_percent' in params:
                            x = int(params['x_percent'] * current_screen.width)
                            y = int(params['y_percent'] * current_screen.height)
                        else:
                            x = int(params.get('absolute_x', 0) * scale_x)
                            y = int(params.get('absolute_y', 0) * scale_y)
                        
                        button = params.get('button', 'left')
                        
                        logger.debug(f"קליק {i+1}/{len(actions)}: ({x}, {y}) כפתור {button}")
                        pyautogui.click(x, y, button=button)
                    
                    elif action_type == 'key_press':
                        key = params.get('key', '')
                        if key and len(key) > 0:
                            try:
                                # טיפול במקשים מיוחדים
                                if len(key) == 1:
                                    # תו רגיל
                                    pyautogui.write(key, interval=0.05)
                                else:
                                    # מקש מיוחד
                                    if key == 'space':
                                        pyautogui.press('space')
                                    elif key == 'enter':
                                        pyautogui.press('enter')
                                    elif key == 'tab':
                                        pyautogui.press('tab')
                                    elif key == 'backspace':
                                        pyautogui.press('backspace')
                                    elif key == 'delete':
                                        pyautogui.press('delete')
                                    else:
                                        # ניסיון להפעיל מקש כפי שהוא
                                        pyautogui.press(key)
                                
                                logger.debug(f"מקש {i+1}/{len(actions)}: {key}")
                            except Exception as key_error:
                                logger.warning(f"שגיאה במקש {key}: {str(key_error)}")
                                continue
                    
                    elif action_type == 'scroll':
                        x = int(params.get('x', 0) * scale_x)
                        y = int(params.get('y', 0) * scale_y)
                        dy = params.get('dy', 0)
                        pyautogui.scroll(dy, x=x, y=y)
                
                except Exception as e:
                    logger.warning(f"שגיאה בפעולה {i+1}: {str(e)}")
                    continue
            
            logger.info("הפעלת המאקרו הושלמה")
            return True
            
        except Exception as e:
            logger.error(f"שגיאה בהפעלת מאקרו: {str(e)}")
            return False


# יצירת instance גלובלי
auto_recorder = AutoMacroRecorder()

def start_auto_recording():
    """התחלת הקלטה אוטומטית"""
    return auto_recorder.start_recording()

def stop_auto_recording():
    """עצירת הקלטה אוטומטית"""
    return auto_recorder.stop_recording()

def save_auto_recording(file_path):
    """שמירת הקלטה אוטומטית"""
    return auto_recorder.save_recording(file_path)

def playback_auto_recording(file_path, speed_factor=1.0):
    """הפעלת הקלטה אוטומטית"""
    return auto_recorder.load_and_playback(file_path, speed_factor)
