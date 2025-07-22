"""
מקליט מאקרו ידני - המשתמש מגדיר את הפעולות ידנית
"""

import json
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ManualMacroRecorder:
    """מקליט מאקרו ידני שמאפשר למשתמש להגדיר פעולות"""
    
    def __init__(self):
        self.actions = []
        self.screen_width = 1920
        self.screen_height = 1080
    
    def create_login_macro(self, username_field_pos, password_field_pos, login_button_pos):
        """יצירת מאקרו התחברות בסיסי"""
        try:
            import pyautogui
            current_screen = pyautogui.size()
            self.screen_width = current_screen.width
            self.screen_height = current_screen.height
        except:
            pass
        
        self.actions = []
        
        # פעולה 1: קליק על שדה שם משתמש
        self.actions.append({
            "type": "click",
            "delay": 1.0,
            "params": {
                "x_percent": username_field_pos[0] / self.screen_width,
                "y_percent": username_field_pos[1] / self.screen_height,
                "button": "left",
                "absolute_x": username_field_pos[0],
                "absolute_y": username_field_pos[1]
            },
            "timestamp": 1.0
        })
        
        # פעולה 2: ניקוי השדה
        self.actions.append({
            "type": "key_press",
            "delay": 0.5,
            "params": {"key": "ctrl+a"},
            "timestamp": 1.5
        })
        
        # פעולה 3: כתיבת שם משתמש (placeholder)
        self.actions.append({
            "type": "write_username",
            "delay": 0.3,
            "params": {"text": "{{USERNAME}}"},
            "timestamp": 1.8
        })
        
        # פעולה 4: מעבר לשדה סיסמה
        self.actions.append({
            "type": "click",
            "delay": 0.5,
            "params": {
                "x_percent": password_field_pos[0] / self.screen_width,
                "y_percent": password_field_pos[1] / self.screen_height,
                "button": "left",
                "absolute_x": password_field_pos[0],
                "absolute_y": password_field_pos[1]
            },
            "timestamp": 2.3
        })
        
        # פעולה 5: ניקוי שדה סיסמה
        self.actions.append({
            "type": "key_press",
            "delay": 0.3,
            "params": {"key": "ctrl+a"},
            "timestamp": 2.6
        })
        
        # פעולה 6: כתיבת סיסמה (placeholder)
        self.actions.append({
            "type": "write_password",
            "delay": 0.3,
            "params": {"text": "{{PASSWORD}}"},
            "timestamp": 2.9
        })
        
        # פעולה 7: קליק על כפתור התחברות
        self.actions.append({
            "type": "click",
            "delay": 1.0,
            "params": {
                "x_percent": login_button_pos[0] / self.screen_width,
                "y_percent": login_button_pos[1] / self.screen_height,
                "button": "left",
                "absolute_x": login_button_pos[0],
                "absolute_y": login_button_pos[1]
            },
            "timestamp": 3.9
        })
        
        logger.info(f"נוצר מאקרו עם {len(self.actions)} פעולות")
        return True
    
    def save_recording(self, file_path):
        """שמירת המאקרו"""
        try:
            recording_data = {
                "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "screen_size": [self.screen_width, self.screen_height],
                "duration": 5.0,
                "actions_count": len(self.actions),
                "recording_type": "manual",
                "actions": self.actions
            }
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(recording_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"מאקרו נשמר: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"שגיאה בשמירת מאקרו: {str(e)}")
            return False
    
    def load_and_playback(self, file_path, username, password, speed_factor=1.0):
        """הפעלת המאקרו עם נתונים אמיתיים"""
        try:
            import pyautogui
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            actions = data.get('actions', [])
            original_screen_size = data.get('screen_size', [1920, 1080])
            
            logger.info(f"מפעיל מאקרו: {len(actions)} פעולות")
            
            # קבלת גודל מסך נוכחי
            current_screen = pyautogui.size()
            scale_x = current_screen.width / original_screen_size[0]
            scale_y = current_screen.height / original_screen_size[1]
            
            logger.info(f"גודל מסך מקורי: {original_screen_size}, נוכחי: {current_screen.width}x{current_screen.height}")
            
            import time
            
            for i, action in enumerate(actions):
                # המתנה לפי השהייה
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
                        
                        logger.debug(f"קליק {i+1}/{len(actions)}: ({x}, {y})")
                        pyautogui.click(x, y, button=button)
                    
                    elif action_type == 'key_press':
                        key = params.get('key', '')
                        if key:
                            logger.debug(f"מקש {i+1}/{len(actions)}: {key}")
                            if '+' in key:
                                # קיצור מקשים
                                keys = key.split('+')
                                pyautogui.hotkey(*keys)
                            else:
                                pyautogui.press(key)
                    
                    elif action_type == 'write_username':
                        logger.debug(f"כתיבת שם משתמש {i+1}/{len(actions)}")
                        pyautogui.write(username, interval=0.05)
                    
                    elif action_type == 'write_password':
                        logger.debug(f"כתיבת סיסמה {i+1}/{len(actions)}")
                        pyautogui.write(password, interval=0.05)
                
                except Exception as e:
                    logger.warning(f"שגיאה בפעולה {i+1}: {str(e)}")
                    continue
            
            logger.info("הפעלת המאקרו הושלמה")
            return True
            
        except Exception as e:
            logger.error(f"שגיאה בהפעלת מאקרו: {str(e)}")
            return False


# יצירת instance גלובלי
manual_recorder = ManualMacroRecorder()

def create_manual_login_macro(username_pos, password_pos, login_pos):
    """יצירת מאקרו התחברות ידני"""
    return manual_recorder.create_login_macro(username_pos, password_pos, login_pos)

def save_manual_recording(file_path):
    """שמירת מאקרו ידני"""
    return manual_recorder.save_recording(file_path)

def playback_manual_recording(file_path, username, password, speed_factor=1.0):
    """הפעלת מאקרו ידני"""
    return manual_recorder.load_and_playback(file_path, username, password, speed_factor)
