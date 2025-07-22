"""
api_server_refactored.py

גרסה משופרת של שרת ה-API המרכזי, עם מבנה מודולרי יותר.
שימוש ב-Blueprints של Flask להפרדה של אזורי אחריות שונים.
"""

import sys

# Force UTF-8 encoding for stdout/stderr to avoid UnicodeEncodeError on Windows consoles
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

import os
import logging
import json
import hashlib
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, abort, make_response, render_template
from flask_cors import CORS
from flask_socketio import SocketIO

# טעינת משתני סביבה מקובץ .env
load_dotenv()

# הגדרת לוגר
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/api_server_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# יצירת תיקיית לוגים אם לא קיימת
os.makedirs("logs", exist_ok=True)

# --- טעינת תצורת מערכת ---
try:
    # טעינת קובץ תצורה (אופציונלי)
    with open('system_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    API_HOST = config.get('api_settings', {}).get('host', '0.0.0.0')
    API_PORT = int(os.getenv("API_PORT", config.get('api_settings', {}).get('port', 5000)))
    logger.info(f"Loaded system configuration. API will run on {API_HOST}:{API_PORT}")
except Exception as e:
    logger.error(f"Failed to load system configuration: {e}")
    # ערכי ברירת מחדל אם הטעינה נכשלה
    API_HOST = '0.0.0.0'
    API_PORT = int(os.getenv("API_PORT", 5000))
    config = {"api_settings": {"host": API_HOST, "port": API_PORT}}

# --- אתחול שרת Flask ---
app = Flask(__name__, 
    static_folder='public',
    template_folder='templates'
)
CORS(app)  # הפעלת תמיכה ב-CORS

# יצירת Socket.IO לתקשורת בזמן אמת
socketio = SocketIO(app, cors_allowed_origins="*")

# --- אימות ---
# סיסמה מוגדרת מראש (יעודכן מקובץ אם קיים)
PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"  # SHA-256 of 'admin'

# בדיקה אם הסיסמה מוגדרת במשתני סביבה
dashboard_password = os.getenv("DASHBOARD_PASSWORD")
if dashboard_password:
    PASSWORD_HASH = hashlib.sha256(dashboard_password.encode()).hexdigest()
    logger.info("Using dashboard password from environment variable")
else:
    # בדיקה אם קיים קובץ סיסמה
    password_file = "dashboard_password.txt"
    if os.path.exists(password_file):
        try:
            with open(password_file, 'r', encoding='utf-8') as f:
                password = f.read().strip()
                if password:
                    PASSWORD_HASH = hashlib.sha256(password.encode()).hexdigest()
                    logger.info(f"Loaded password from {password_file}")
        except Exception as e:
            logger.error(f"Error reading password file: {e}")

def check_auth(password):
    """בודק אם הסיסמה תואמת להאש המאוחסן"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == PASSWORD_HASH

def requires_auth(f):
    """דקורטור שדורש אימות לנתיב"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"status": "error", "message": "Authentication required"}), 401
            
        token = auth_header.split(' ')[1]
        if not check_auth(token):
            return jsonify({"status": "error", "message": "Invalid authentication"}), 403
            
        return f(*args, **kwargs)
    return decorated

# --- יבוא ה-Blueprints ---
from src.routes.system import system_bp
from src.routes.processes import processes_bp
from src.routes.gateway import gateway_bp
from src.routes.agent import agent_bp
from src.routes.health import health_bp
from src.routes.analysis import analysis_bp
from src.routes.logs import logs_bp
from src.routes.ibkr import ibkr_bp

# --- רישום ה-Blueprints ---
app.register_blueprint(system_bp)
app.register_blueprint(processes_bp)
app.register_blueprint(gateway_bp)
app.register_blueprint(agent_bp)
app.register_blueprint(health_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(ibkr_bp)

# --- נתיבי מערכת בסיסיים ---

@app.route('/')
def index():
    """דף הבית - ינותב לדשבורד"""
    return send_from_directory('public/static', 'dashboard.html')

@app.route('/dashboard')
def dashboard():
    """דף הדשבורד"""
    return send_from_directory('public/static', 'dashboard.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """הגשת קבצים סטטיים"""
    return send_from_directory('public/static', filename)

@app.route('/api/login', methods=['POST'])
def login():
    """אימות משתמש"""
    try:
        data = request.json
        if not data or 'password' not in data:
            return jsonify({"status": "error", "message": "Password required"}), 400
            
        password = data.get('password', '')
        
        if check_auth(password):
            return jsonify({
                "status": "success",
                "message": "Authentication successful",
                "token": password  # בסביבת ייצור יש להשתמש בטוקן מאובטח
            })
        else:
            return jsonify({"status": "error", "message": "Invalid password"}), 403
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/public/<path:filename>')
def serve_public(filename):
    """שליחת קבצים מתיקיית public"""
    return send_from_directory('public', filename)

@app.route('/api/status/all', methods=['GET'])
def root_status_all():
    """נתיב עוקף לסטטוס תהליכים - הפניה אל המסלול של system"""
    from src.routes.system import get_all_statuses
    return get_all_statuses()

@app.route('/api/version')
def api_version():
    """מידע על גרסת ה-API"""
    return jsonify({
        "name": "Algorithmic Trading Bot API",
        "version": "2.0.0",
        "status": "active"
    })

# --- Socket.IO Events ---
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

# הפונקציה להפצת עדכוני סטטוס לכל הלקוחות
def broadcast_status(status_data):
    """שולח עדכון סטטוס לכל הלקוחות המחוברים"""
    socketio.emit('status_update', status_data)

# --- הפעלת השרת ---
if __name__ == '__main__':
    # יצירת תיקיות נדרשות
    os.makedirs('public', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # פרטי התחברות בסיסיים עבור השרת
    logger.info(f"Starting API server on {API_HOST}:{API_PORT}")
    socketio.run(app, host=API_HOST, port=API_PORT, debug=True, allow_unsafe_werkzeug=True)
