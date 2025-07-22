import sys

# Force UTF-8 encoding for stdout/stderr to avoid UnicodeEncodeError on Windows consoles
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass
# Temporarily disabled for debugging:
# import eventlet
# eventlet.monkey_patch()

# api_server.py
# This file replaces the old dashboard.py and acts as the central backend server.

import subprocess
import json
import os
import shutil
import time
import pandas as pd
from pathlib import Path
import sqlite3
import traceback
from datetime import datetime
import threading
import hashlib
from functools import wraps
import logging
import re
import glob
from dotenv import load_dotenv

# טעינת משתני סביבה מקובץ .env
load_dotenv()
import logging
import re
import glob

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    # Set a safety pause to give user time to take control if needed
    pyautogui.PAUSE = 0.5
except ImportError:
    PYAUTOGUI_AVAILABLE = False


from flask import Flask, jsonify, request, send_from_directory, abort, make_response, render_template
from flask_cors import CORS
try:
    from flask_socketio import SocketIO, emit, disconnect
    SOCKETIO_AVAILABLE = True
except ImportError:
    print("Running without WebSocket support (temporarily disabled for debugging)")
    SOCKETIO_AVAILABLE = False

# Import shared utilities
from src.utils import load_system_config, archive_existing_file

# --- Setup Logging ---
log_file = 'logs/api_server.log'
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Load system configuration
try:
    config = load_system_config()
    API_HOST = config.get('api_settings', {}).get('host', '0.0.0.0')
    API_PORT = int(config.get('api_settings', {}).get('port', 5000))
    logging.info(f"Loaded system configuration. API will run on {API_HOST}:{API_PORT}")
except Exception as e:
    logging.error(f"Failed to load system configuration: {e}")
    config = {"api_settings": {"host": "0.0.0.0", "port": 5000}}
    API_HOST = "0.0.0.0"
    API_PORT = 5000

# Create Flask app
app = Flask(__name__, static_folder='public', template_folder='./')
CORS(app)

# Socket.IO setup if available
if SOCKETIO_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    logging.info("WebSocket support enabled with SocketIO")
else:
    socketio = None
    logging.warning("Running without WebSocket support")

# --- Authentication ---
# Default password hash (will be updated if password file exists)
PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"  # SHA-256 of 'admin'

# Try to read password from environment variable first
dashboard_password = os.getenv("DASHBOARD_PASSWORD")
if dashboard_password:
    PASSWORD_HASH = hashlib.sha256(dashboard_password.encode()).hexdigest()
    logging.info("Using dashboard password from environment variable")
else:
    # Try to read password from file
    password_file = "dashboard_password.txt"
    if os.path.exists(password_file):
        try:
            with open(password_file, 'r', encoding='utf-8') as f:
                password = f.read().strip()
                if password:
                    PASSWORD_HASH = hashlib.sha256(password.encode()).hexdigest()
                    logging.info(f"Loaded password from {password_file}")
        except Exception as e:
            logging.error(f"Error reading password file: {e}")

def check_auth(password):
    """Check if the password matches the stored hash"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == PASSWORD_HASH

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        password = None
        
        if auth_header:
            # Check for Bearer token
            if auth_header.startswith('Bearer '):
                password = auth_header[7:]
            # Check for Basic auth
            elif auth_header.startswith('Basic '):
                import base64
                try:
                    # Basic auth format is "Basic base64(username:password)"
                    # We ignore username and just use password
                    decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
                    password = decoded.split(':')[1] if ':' in decoded else decoded
                except Exception:
                    pass
        
        # If no header, check for auth in query parameters or form data
        if not password:
            password = request.args.get('auth') or request.form.get('auth')
        
        if not password or not check_auth(password):
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

# --- Helper Functions ---

def get_sqlite_connection(db_path):
    """Get a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database {db_path}: {e}")
        return None

def safe_read_json(file_path, default=None):
    """Safely read a JSON file, returning a default value if the file doesn't exist or is invalid."""
    if default is None:
        default = {}
    
    if not os.path.exists(file_path):
        return default
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading JSON file {file_path}: {e}")
        return default

def safe_write_json(file_path, data):
    """Safely write a JSON file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error writing JSON file {file_path}: {e}")
        return False

def get_model_info():
    """Get information about the current champion model."""
    model_config_path = config.get('system_paths', {}).get('champion_config', 'models/champion_model_config.json')
    model_summary_path = os.path.join(os.path.dirname(model_config_path), 'training_summary.json')
    
    model_config = safe_read_json(model_config_path)
    model_summary = safe_read_json(model_summary_path)
    
    return {
        'config': model_config,
        'summary': model_summary,
        'exists': os.path.exists(model_config_path),
        'last_modified': datetime.fromtimestamp(os.path.getmtime(model_config_path)).strftime('%Y-%m-%d %H:%M:%S') if os.path.exists(model_config_path) else None
    }

def get_agent_state():
    """Get the current state of the trading agent."""
    state_path = 'agent/state.json'
    command_path = 'agent/command.json'
    log_path = 'agent/trading_log.txt'
    
    state = safe_read_json(state_path, {'status': 'unknown', 'last_update': None})
    command = safe_read_json(command_path, {'command': None, 'timestamp': None})
    
    # Get last few lines of log
    log_lines = []
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                # Get last 20 lines
                log_lines = f.readlines()[-20:]
        except Exception as e:
            logging.error(f"Error reading log file {log_path}: {e}")
    
    return {
        'state': state,
        'command': command,
        'log_lines': log_lines
    }

def send_command_to_agent(command_data):
    """Send a command to the trading agent."""
    command_path = 'agent/command.json'
    
    # Add timestamp to command
    command_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return safe_write_json(command_path, command_data)

def get_backtest_results():
    """Get backtest results from the database."""
    db_path = 'spy_strategy_optimization.db'
    results = []
    
    if not os.path.exists(db_path):
        return {'error': f'Database not found: {db_path}', 'results': []}
    
    conn = get_sqlite_connection(db_path)
    if not conn:
        return {'error': 'Failed to connect to database', 'results': []}
    
    try:
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategy_results'")
        if not cursor.fetchone():
            return {'error': 'Strategy results table not found in database', 'results': []}
        
        # Get recent results, ordered by descending date
        cursor.execute("""
            SELECT * FROM strategy_results
            ORDER BY run_timestamp DESC
            LIMIT 10
        """)
        
        columns = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            result = dict(zip(columns, row))
            results.append(result)
        
        return {'results': results}
    
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return {'error': f'Database error: {e}', 'results': []}
    
    finally:
        if conn:
            conn.close()

def get_data_status():
    """Get status of data files."""
    data_files = {
        'raw_spy': config.get('system_paths', {}).get('raw_data', 'data/raw/SPY_ibkr.csv'),
        'raw_vix': config.get('system_paths', {}).get('vix_data', 'data/raw/VIX_ibkr.csv'),
        'processed': config.get('system_paths', {}).get('processed_data', 'data/processed/SPY_processed.csv'),
        'features': config.get('system_paths', {}).get('feature_data', 'data/processed/SPY_features.csv')
    }
    
    status = {}
    
    for name, path in data_files.items():
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, parse_dates=['date'] if 'date' in pd.read_csv(path, nrows=1).columns else None)
                status[name] = {
                    'exists': True,
                    'size_mb': round(os.path.getsize(path) / (1024 * 1024), 2),
                    'rows': len(df),
                    'date_range': f"{df['date'].min()} to {df['date'].max()}" if 'date' in df.columns else 'N/A',
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
                }
            except Exception as e:
                status[name] = {
                    'exists': True,
                    'error': str(e),
                    'size_mb': round(os.path.getsize(path) / (1024 * 1024), 2),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
                }
        else:
            status[name] = {
                'exists': False
            }
    
    return status

def run_collection_process():
    """Run the data collection process."""
    try:
        from src.data_collector import fetch_all_historical_data
        fetch_all_historical_data()
        return {'status': 'success', 'message': 'Data collection process completed'}
    except Exception as e:
        logging.error(f"Error in data collection: {e}")
        logging.error(traceback.format_exc())
        return {'status': 'error', 'message': f'Data collection failed: {str(e)}'}

def run_preprocessing_process():
    """Run the preprocessing process."""
    try:
        from src.run_preprocessing import preprocess_data
        preprocess_data()
        return {'status': 'success', 'message': 'Preprocessing completed'}
    except Exception as e:
        logging.error(f"Error in preprocessing: {e}")
        logging.error(traceback.format_exc())
        return {'status': 'error', 'message': f'Preprocessing failed: {str(e)}'}

def get_system_config():
    """Get the current system configuration."""
    try:
        return load_system_config()
    except Exception as e:
        logging.error(f"Error loading system config: {e}")
        return {'error': str(e)}

def update_system_config(new_config):
    """Update the system configuration."""
    config_path = 'system_config.json'
    
    try:
        # Backup the existing config
        archive_existing_file(config_path)
        
        # Write new config
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)
        
        return {'status': 'success', 'message': 'Configuration updated successfully'}
    
    except Exception as e:
        logging.error(f"Error updating system config: {e}")
        logging.error(traceback.format_exc())
        return {'status': 'error', 'message': f'Failed to update configuration: {str(e)}'}

def run_backtest():
    """Run a backtest."""
    try:
        from src.backtester import run_backtest_from_api
        results = run_backtest_from_api()
        return {'status': 'success', 'results': results}
    except Exception as e:
        logging.error(f"Error running backtest: {e}")
        logging.error(traceback.format_exc())
        return {'status': 'error', 'message': f'Backtest failed: {str(e)}'}

def train_model():
    """Start the model training process."""
    try:
        # Run training in a separate process
        subprocess.Popen([sys.executable, 'src/main_trainer.py'])
        return {'status': 'success', 'message': 'Model training process started'}
    except Exception as e:
        logging.error(f"Error starting model training: {e}")
        logging.error(traceback.format_exc())
        return {'status': 'error', 'message': f'Failed to start model training: {str(e)}'}

def get_recent_logs(log_name, max_lines=100):
    """Get recent lines from a log file."""
    log_path = f"logs/{log_name}.log"
    
    if not os.path.exists(log_path):
        return {'status': 'error', 'message': f'Log file not found: {log_path}', 'lines': []}
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            # Get last max_lines
            lines = f.readlines()[-max_lines:]
        
        return {'status': 'success', 'lines': lines}
    
    except Exception as e:
        logging.error(f"Error reading log file {log_path}: {e}")
        return {'status': 'error', 'message': f'Failed to read log file: {str(e)}', 'lines': []}

def get_running_processes():
    """Get list of running Python processes related to the trading system."""
    processes = []
    
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                # Check if this is a Python process
                if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    
                    # Only include processes related to our trading system
                    if any(x in cmdline for x in ['main_trainer.py', 'api_server.py', 'backtester.py', 'data_collector.py']):
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline,
                            'running_time': round((time.time() - proc.info['create_time']) / 60, 1)  # minutes
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except ImportError:
        logging.warning("psutil not available, cannot list running processes")
        return {'status': 'error', 'message': 'psutil module not available', 'processes': []}
    
    return {'status': 'success', 'processes': processes}

def get_disk_usage():
    """Get disk usage for important folders."""
    folders = ['data', 'models', 'logs', 'reports', 'archive']
    usage = {}
    
    for folder in folders:
        if os.path.exists(folder):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(folder):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(file_path)
            
            usage[folder] = {
                'size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': len([f for f in glob.glob(f'{folder}/**/*', recursive=True) if os.path.isfile(f)])
            }
        else:
            usage[folder] = {
                'size_mb': 0,
                'file_count': 0,
                'exists': False
            }
    
    return usage

def start_ibkr_gateway():
    """Start the IBKR Gateway process."""
    try:
        subprocess.Popen([sys.executable, 'start_ibkr.py'])
        return {'status': 'success', 'message': 'IBKR Gateway startup process initiated'}
    except Exception as e:
        logging.error(f"Error starting IBKR Gateway: {e}")
        logging.error(traceback.format_exc())
        return {'status': 'error', 'message': f'Failed to start IBKR Gateway: {str(e)}'}

def start_trading_agent():
    """Start the trading agent."""
    try:
        # Change directory to agent directory (for relative imports)
        os.chdir('agent')
        
        # Run node.js process
        subprocess.Popen(['node', 'trading_agent.js'])
        
        # Change back to original directory
        os.chdir('..')
        
        return {'status': 'success', 'message': 'Trading agent process started'}
    except Exception as e:
        logging.error(f"Error starting trading agent: {e}")
        logging.error(traceback.format_exc())
        return {'status': 'error', 'message': f'Failed to start trading agent: {str(e)}'}

# --- Routes ---

@app.route('/')
def serve_dashboard():
    return render_template('dashboard.html')

@app.route('/public/<path:path>')
def serve_static(path):
    return send_from_directory('public', path)

@app.route('/api/status')
@requires_auth
def api_status():
    return jsonify({
        'status': 'ok',
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'config': {
            'api_host': API_HOST,
            'api_port': API_PORT
        }
    })

@app.route('/api/model')
@requires_auth
def api_model():
    return jsonify(get_model_info())

@app.route('/api/agent')
@requires_auth
def api_agent():
    return jsonify(get_agent_state())

@app.route('/api/agent/command', methods=['POST'])
@requires_auth
def api_agent_command():
    command_data = request.json
    if not command_data or 'command' not in command_data:
        return jsonify({'status': 'error', 'message': 'Missing command parameter'})
    
    result = send_command_to_agent(command_data)
    if result:
        return jsonify({'status': 'success', 'message': f'Command {command_data["command"]} sent successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to send command'})

@app.route('/api/backtest')
@requires_auth
def api_backtest():
    return jsonify(get_backtest_results())

@app.route('/api/data')
@requires_auth
def api_data():
    return jsonify(get_data_status())

@app.route('/api/run/collect', methods=['POST'])
@requires_auth
def api_run_collect():
    return jsonify(run_collection_process())

@app.route('/api/run/preprocess', methods=['POST'])
@requires_auth
def api_run_preprocess():
    return jsonify(run_preprocessing_process())

@app.route('/api/run/backtest', methods=['POST'])
@requires_auth
def api_run_backtest():
    return jsonify(run_backtest())

@app.route('/api/run/train', methods=['POST'])
@requires_auth
def api_run_train():
    return jsonify(train_model())

@app.route('/api/config')
@requires_auth
def api_config():
    return jsonify(get_system_config())

@app.route('/api/config', methods=['POST'])
@requires_auth
def api_update_config():
    new_config = request.json
    if not new_config:
        return jsonify({'status': 'error', 'message': 'Missing configuration data'})
    
    return jsonify(update_system_config(new_config))

@app.route('/api/logs/<log_name>')
@requires_auth
def api_logs(log_name):
    max_lines = request.args.get('max_lines', default=100, type=int)
    return jsonify(get_recent_logs(log_name, max_lines))

@app.route('/api/processes')
@requires_auth
def api_processes():
    return jsonify(get_running_processes())

@app.route('/api/disk')
@requires_auth
def api_disk():
    return jsonify(get_disk_usage())

@app.route('/api/run/ibkr', methods=['POST'])
@requires_auth
def api_run_ibkr():
    return jsonify(start_ibkr_gateway())

@app.route('/api/run/agent', methods=['POST'])
@requires_auth
def api_run_agent():
    return jsonify(start_trading_agent())

# --- WebSocket API (if available) ---

if socketio:
    @socketio.on('connect')
    def socket_connect():
        logging.info(f"Client connected: {request.sid}")
    
    @socketio.on('disconnect')
    def socket_disconnect():
        logging.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('auth')
    def socket_auth(data):
        if not data or 'password' not in data or not check_auth(data['password']):
            emit('auth_response', {'status': 'error', 'message': 'Authentication failed'})
            disconnect()
        else:
            emit('auth_response', {'status': 'success', 'message': 'Authentication successful'})
    
    @socketio.on('get_status')
    def socket_get_status():
        emit('status_update', {
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'agent': get_agent_state(),
            'data': get_data_status()
        })

# --- Main function ---

def main():
    logging.info(f"Starting API server on {API_HOST}:{API_PORT}")
    
    # Check if we have WebSocket support
    if socketio:
        socketio.run(app, host=API_HOST, port=API_PORT, debug=False, allow_unsafe_werkzeug=True)
    else:
        app.run(host=API_HOST, port=API_PORT, debug=False)

if __name__ == "__main__":
    main()
