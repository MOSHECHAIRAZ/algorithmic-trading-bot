"""
מקליט מאקרו מתקדם ל-Windows עם תמיכה ב-win32
"""

import json
import time
import threading
import logging
from datetime import datetime
import os

try:
    import pyautogui
    import win32api
    import win32con
    import win32gui
    import ctypes
    from ctypes import wintypes
    RECORDING_AVAILABLE = True
    
    # הגדרות pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1
    
except ImportError as e:
    RECORDING_AVAILABLE = False
    print(f"שגיאה בייבוא חבילות: {e}")
    print("נדרש להתקין: pip install pyautogui pywin32")

logger = logging.getLogger(__name__)

class WindowsMacroRecorder:
    """מקליט מאקרו מבוסס Windows API"""
    
    def __init__(self):
        self.actions = []
        self.is_recording = False
        self.start_time = None
        self.last_action_time = None
        self.hook_manager = None
        self.recording_thread = None
        
    def start_recording(self):
        """התחלת הקלטה"""
        if not RECORDING_AVAILABLE:
            logger.error("החבילות הנדרשות לא מותקנות")
            return False
            
        self.actions = []
        self.is_recording = True
        self.start_time = time.time()
        self.last_action_time = self.start_time
        
        # קבלת גודל מסך
        self.screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        self.screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        
        logger.info(f"מתחיל הקלטה. גודל מסך: {self.screen_width}x{self.screen_height}")
        
        # התחלת הקלטה בחוט נפרד
        self.recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.recording_thread.start()
        
        return True
    
    def _record_loop(self):
        """לולאת הקלטה ראשית"""
        logger.info("הקלטה החלה - בצע פעולות עכשיו")
        
        prev_mouse_pos = None
        prev_keys_state = {}
        
        while self.is_recording:
            try:
                current_time = time.time()
                
                # בדיקת מיקום עכבר
                cursor_pos = win32gui.GetCursorPos()
                
                # בדיקת קליקי עכבר
                left_button = win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000
                right_button = win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000
                
                if left_button and not prev_keys_state.get('left_mouse', False):
                    self._record_mouse_click(cursor_pos[0], cursor_pos[1], 'left', current_time)
                    prev_keys_state['left_mouse'] = True
                elif not left_button:
                    prev_keys_state['left_mouse'] = False
                    
                if right_button and not prev_keys_state.get('right_mouse', False):
                    self._record_mouse_click(cursor_pos[0], cursor_pos[1], 'right', current_time)
                    prev_keys_state['right_mouse'] = True
                elif not right_button:
                    prev_keys_state['right_mouse'] = False
                
                # בדיקת מקשים נפוצים
                keys_to_check = {
                    win32con.VK_RETURN: 'enter',
                    win32con.VK_TAB: 'tab',
                    win32con.VK_SPACE: 'space',
                    win32con.VK_BACK: 'backspace',
                    win32con.VK_DELETE: 'delete',
                    win32con.VK_ESCAPE: 'escape'
                }
                
                # בדיקת מקשי אותיות ומספרים
                for i in range(48, 58):  # 0-9
                    keys_to_check[i] = chr(i)
                for i in range(65, 91):  # A-Z
                    keys_to_check[i] = chr(i).lower()
                
                for vk_code, key_name in keys_to_check.items():
                    is_pressed = win32api.GetAsyncKeyState(vk_code) & 0x8000
                    prev_state = prev_keys_state.get(f'key_{vk_code}', False)
                    
                    if is_pressed and not prev_state:
                        self._record_key_press(key_name, current_time)
                        prev_keys_state[f'key_{vk_code}'] = True
                        
                        # אם נלחץ Escape, עוצר הקלטה
                        if key_name == 'escape':
                            logger.info("נלחץ Escape - עוצר הקלטה")
                            self.stop_recording()
                            break
                            
                    elif not is_pressed:
                        prev_keys_state[f'key_{vk_code}'] = False
                
                # השהייה קצרה
                time.sleep(0.05)
                
            except Exception as e:
                logger.error(f"שגיאה בלולאת הקלטה: {str(e)}")
                break
    
    def _record_mouse_click(self, x, y, button, current_time):
        """הקלטת קליק עכבר"""
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
                "button": button,
                "absolute_x": x,
                "absolute_y": y
            },
            "timestamp": current_time - self.start_time
        }
        
        self.actions.append(action)
        self.last_action_time = current_time
        
        logger.debug(f"קליק הוקלט: ({x}, {y}) כפתור {button}")
    
    def _record_key_press(self, key, current_time):
        """הקלטת לחיצת מקש"""
        delay = current_time - self.last_action_time
        
        action = {
            "type": "key_press",
            "delay": delay,
            "params": {
                "key": key
            },
            "timestamp": current_time - self.start_time
        }
        
        self.actions.append(action)
        self.last_action_time = current_time
        
        logger.debug(f"מקש הוקלט: {key}")
    
    def stop_recording(self):
        """עצירת הקלטה"""
        if not self.is_recording:
            return False
            
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join(timeout=2)
        
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
                if delay > 0.05:
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
                        if key:
                            logger.debug(f"מקש {i+1}/{len(actions)}: {key}")
                            pyautogui.press(key)
                
                except Exception as e:
                    logger.warning(f"שגיאה בפעולה {i+1}: {str(e)}")
                    continue
            
            logger.info("הפעלת המאקרו הושלמה")
            return True
            
        except Exception as e:
            logger.error(f"שגיאה בהפעלת מאקרו: {str(e)}")
            return False


# יצירת instance גלובלי
windows_recorder = WindowsMacroRecorder()

def start_windows_recording():
    """התחלת הקלטה עם Windows API"""
    return windows_recorder.start_recording()

def stop_windows_recording():
    """עצירת הקלטה עם Windows API"""
    return windows_recorder.stop_recording()

def save_windows_recording(file_path):
    """שמירת הקלטה עם Windows API"""
    return windows_recorder.save_recording(file_path)

def playback_windows_recording(file_path, speed_factor=1.0):
    """הפעלת הקלטה עם Windows API"""
    return windows_recorder.load_and_playback(file_path, speed_factor)
