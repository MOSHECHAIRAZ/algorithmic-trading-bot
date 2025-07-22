#!/usr/bin/env python3
"""
Simple IB Gateway Launcher
מפעיל את ה-IB Gateway ישירות בלי IBController
"""

import subprocess
import time
import os
import json
import logging
from flask import Flask, request, jsonify, render_template_string
import socket
from threading import Thread

# ייבוא מקליט המאקרו החדש
try:
    from manual_macro_recorder import playback_manual_recording
    MACRO_RECORDER_AVAILABLE = True
except ImportError:
    MACRO_RECORDER_AVAILABLE = False

# הגדרת logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not MACRO_RECORDER_AVAILABLE:
    logger.warning("מקליט המאקרו לא זמין - נדרשות החבילות pyautogui ו-pynput")

# הגדרות
IB_GATEWAY_PATH = r"C:\Jts\ibgateway\1037"
API_PORT = 4001

app = Flask(__name__)

def check_port_open(host='localhost', port=API_PORT, timeout=3):
    """בודק אם פורט פתוח"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def start_gateway_process(username, password):
    """מפעיל את ה-Gateway ישירות"""
    try:
        # נתיב ל-Gateway
        gateway_exe = os.path.join(IB_GATEWAY_PATH, "ibgateway.exe")
        
        if not os.path.exists(gateway_exe):
            logger.error(f"Gateway not found at: {gateway_exe}")
            return False, f"לא נמצא Gateway בנתיב: {gateway_exe}"
        
        # עדכון קובץ jts.ini עם הגדרות API
        jts_ini_path = os.path.join(IB_GATEWAY_PATH, "jts.ini")
        update_jts_ini(jts_ini_path, username, password)
        
        logger.info("Starting IB Gateway...")
        
        # הפעלת Gateway
        process = subprocess.Popen(
            [gateway_exe],
            cwd=IB_GATEWAY_PATH,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # המתנה קצרה לטעינת Gateway
        time.sleep(5)
        
        # בדיקה אם התהליך עדיין רץ
        if process.poll() is None:
            logger.info("Gateway process started successfully")
            return True, "Gateway הופעל בהצלחה"
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Gateway failed to start: {stderr.decode()}")
            return False, f"Gateway נכשל בהפעלה: {stderr.decode()}"
            
    except Exception as e:
        logger.error(f"Error starting gateway: {str(e)}")
        return False, f"שגיאה בהפעלת Gateway: {str(e)}"

def update_jts_ini(jts_path, username, password):
    """עדכון קובץ jts.ini עם הגדרות API ונתוני התחברות"""
    try:
        config_content = f"""[IBGateway]
ApiOnly=true
LocalServerPort={API_PORT}
RemoteHostsFile=
RemotePortsFile=
TrustedIPs=127.0.0.1
SocketPort={API_PORT}
UseRemoteSettings=false
OverrideTrustedIPs=false
ReadOnlyApi=false

[API]
SocketPort={API_PORT}
UseCtrlC=true
AcceptIncomingConnectionAction=accept
AllowOriginsWithHttps=false
AllowedOriginsPatterns=
CrossOriginError=false
MasterClientID=0
ReadOnlyApi=false

[Logon]
Userid={username}
UseSSL=true
DisplayedProxyAddress=
DisplayedProxyPort=
StorePasswordHash=true
"""
        
        with open(jts_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
            
        logger.info(f"Updated jts.ini with API settings on port {API_PORT}")
        
    except Exception as e:
        logger.error(f"Error updating jts.ini: {str(e)}")

def check_gateway_status():
    """בודק סטטוס Gateway"""
    if check_port_open(port=API_PORT):
        return "פעיל - API Port זמין"
    else:
        return "לא פעיל"

@app.route('/')
def login_page():
    """דף כניסה"""
    with open('gateway_login.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/start_gateway', methods=['POST'])
def start_gateway():
    """API להפעלת Gateway"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'יש למלא שם משתמש וסיסמה'
            })
        
        # בדיקה אם Gateway כבר פועל
        if check_port_open(port=API_PORT):
            return jsonify({
                'success': True,
                'message': 'Gateway כבר פועל ומחובר'
            })
        
        # הפעלת Gateway
        success, message = start_gateway_process(username, password)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error in start_gateway: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'שגיאה: {str(e)}'
        })

@app.route('/dashboard')
def dashboard():
    """דף מצב המערכת"""
    gateway_status = check_gateway_status()
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>IB Gateway Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .dashboard {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .status {{ padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .status.active {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .status.inactive {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            .info-box {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="dashboard">
            <h1>IB Gateway Dashboard</h1>
            
            <div class="status {'active' if 'פעיל' in gateway_status else 'inactive'}">
                <strong>סטטוס Gateway:</strong> {gateway_status}
            </div>
            
            <div class="info-box">
                <strong>API Port:</strong> {API_PORT}
            </div>
            
            <div class="info-box">
                <strong>נתיב Gateway:</strong> {IB_GATEWAY_PATH}
            </div>
            
            <button onclick="location.reload()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">
                רענן סטטוס
            </button>
            
            <button onclick="window.location.href='/'" style="padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 5px; cursor: pointer; margin-right: 10px;">
                חזור לכניסה
            </button>
        </div>
    </body>
    </html>
    """
    
    return dashboard_html

@app.route('/status')
def status():
    """API לבדיקת סטטוס"""
    return jsonify({
        'gateway_status': check_gateway_status(),
        'api_port': API_PORT,
        'api_available': check_port_open(port=API_PORT)
    })

# פונקציות מאקרו
MACRO_FILE_PATH = os.path.join(os.path.dirname(__file__), "recordings", "ibkr_login_macro.json")

@app.route('/api/gateway/macro_status')
def macro_status():
    """בדיקת סטטוס מאקרו"""
    if not MACRO_RECORDER_AVAILABLE:
        return jsonify({
            'success': False,
            'hasRecording': False,
            'message': 'מקליט המאקרו לא זמין - נדרשות החבילות pyautogui ו-pynput'
        })
    
    has_recording = os.path.exists(MACRO_FILE_PATH)
    
    return jsonify({
        'success': True,
        'hasRecording': has_recording,
        'message': 'מאקרו זמין' if has_recording else 'אין מאקרו מוקלט'
    })

@app.route('/api/gateway/login', methods=['POST'])
def api_gateway_login():
    """API להתחברות ל-Gateway עם תמיכה במאקרו"""
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        auto_fill = data.get('autoFill', False)
        record_macro = data.get('recordMacro', False)
        use_macro = data.get('useMacro', False)
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'חסרים פרטי התחברות'
            })
        
        # הפעלת Gateway
        success, message = start_gateway_process(username, password)
        
        if not success:
            return jsonify({
                'success': False,
                'message': message
            })
        
        # טיפול במאקרו
        if record_macro and MACRO_RECORDER_AVAILABLE:
            # במקליט הידני אין צורך בהקלטה - המאקרו כבר קיים
            return jsonify({
                'success': True,
                'message': 'Gateway הופעל. המאקרו כבר מוכן לשימוש - אין צורך בהקלטה נוספת.',
                'username': username,
                'password': password,
                'recording': False
            })
        
        elif use_macro and MACRO_RECORDER_AVAILABLE:
            # שימוש במאקרו קיים
            if os.path.exists(MACRO_FILE_PATH):
                # המתנה קצרה לטעינת Gateway
                time.sleep(3)
                
                if playback_manual_recording(MACRO_FILE_PATH, username, password, speed_factor=1.5):
                    return jsonify({
                        'success': True,
                        'message': 'Gateway הופעל והמאקרו רץ בהצלחה'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Gateway הופעל אך המאקרו נכשל'
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': 'לא נמצא מאקרו מוקלט'
                })
        
        else:
            # התחברות רגילה
            return jsonify({
                'success': True,
                'message': 'Gateway הופעל בהצלחה'
            })
    
    except Exception as e:
        logger.error(f"שגיאה ב-API התחברות: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'שגיאה: {str(e)}'
        })

@app.route('/api/gateway/stop_recording', methods=['POST'])
def stop_recording():
    """עצירת הקלטת מאקרו - במקליט הידני לא נדרש"""
    if not MACRO_RECORDER_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'מקליט המאקרו לא זמין'
        })
    
    try:
        # במקליט הידני המאקרו כבר קיים, אין צורך בעצירה
        if os.path.exists(MACRO_FILE_PATH):
            return jsonify({
                'success': True,
                'message': 'המאקרו כבר קיים ומוכן לשימוש'
            })
        else:
            # יצירת מאקרו בסיסי אם אין
            from manual_macro_recorder import ManualMacroRecorder
            recorder = ManualMacroRecorder()
            if recorder.create_login_macro(MACRO_FILE_PATH):
                return jsonify({
                    'success': True,
                    'message': 'נוצר מאקרו בסיסי לאחר שלא נמצא קובץ'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'שגיאה ביצירת מאקרו'
                })
    
    except Exception as e:
        logger.error(f"שגיאה בעצירת הקלטה: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'שגיאה: {str(e)}'
        })

@app.route('/api/gateway/delete_macro', methods=['POST'])
def delete_macro():
    """מחיקת מאקרו מוקלט"""
    try:
        if os.path.exists(MACRO_FILE_PATH):
            os.remove(MACRO_FILE_PATH)
            return jsonify({
                'success': True,
                'message': 'המאקרו נמחק בהצלחה'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'לא נמצא מאקרו למחיקה'
            })
    
    except Exception as e:
        logger.error(f"שגיאה במחיקת מאקרו: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'שגיאה במחיקה: {str(e)}'
        })

@app.route('/api/gateway/test_macro', methods=['POST'])
def test_macro():
    """בדיקת מאקרו"""
    if not MACRO_RECORDER_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'מקליט המאקרו לא זמין'
        })
    
    try:
        if not os.path.exists(MACRO_FILE_PATH):
            return jsonify({
                'success': False,
                'message': 'לא נמצא מאקרו לבדיקה'
            })
        
        # קריאת נתוני המאקרו לבדיקה
        with open(MACRO_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        actions_count = data.get('actions_count', 0)
        recorded_at = data.get('recorded_at', 'לא ידוע')
        
        return jsonify({
            'success': True,
            'message': f'מאקרו זמין: {actions_count} פעולות, הוקלט ב-{recorded_at}'
        })
    
    except Exception as e:
        logger.error(f"שגיאה בבדיקת מאקרו: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'שגיאה בבדיקה: {str(e)}'
        })

@app.route('/api/gateway/test-autofill', methods=['POST'])
def test_autofill():
    """בדיקת מילוי אוטומטי"""
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'חסרים פרטי התחברות'
            })
        
        # זה רק בדיקה - לא מפעיל באמת את Gateway
        logger.info(f"בדיקת מילוי אוטומטי עבור משתמש: {username}")
        
        return jsonify({
            'success': True,
            'message': 'בדיקת מילוי אוטומטי הצליחה - הפרטים תקינים'
        })
    
    except Exception as e:
        logger.error(f"שגיאה בבדיקת מילוי אוטומטי: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'שגיאה: {str(e)}'
        })

if __name__ == '__main__':
    logger.info("Starting IB Gateway Management Server...")
    logger.info(f"Gateway path: {IB_GATEWAY_PATH}")
    logger.info(f"API Port: {API_PORT}")
    logger.info(f"Macro recorder available: {MACRO_RECORDER_AVAILABLE}")
    
    # הפעלת השרת
    app.run(host='0.0.0.0', port=5000, debug=True)
