# api_server.py
# This file replaces the old dashboard.py and acts as the central backend server.

import subprocess
import sys
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

from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
try:
    from flask_socketio import SocketIO, emit, disconnect
    SOCKETIO_AVAILABLE = True
except ImportError:
    print("⚠️  Flask-SocketIO not available, running without WebSocket support")
    SOCKETIO_AVAILABLE = False
    SocketIO = None

# Import existing logic from your project
from src.utils import load_system_config, save_system_config

# Global variables
START_TIME = time.time()

# --- Helper Functions ---
def load_training_summaries():
    """Load training summaries from various sources (moved from dashboard.py)"""
    try:
        models_dir = Path('models')
        results_dir = Path('reports/backtest_results')
        
        # Load all training summaries from models directory
        summaries = []
        
        # Check for training_summary.json files
        for summary_file in models_dir.glob('**/training_summary.json'):
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                    # Add file timestamp from filename
                    summary['file_ts'] = summary_file.parent.name if summary_file.parent.name != 'models' else 'latest'
                    summaries.append(summary)
            except Exception as e:
                print(f"Error loading {summary_file}: {e}")
                continue
        
        # Also check for individual model config files
        for config_file in models_dir.glob('**/candidate_model_config_*.json'):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Extract timestamp from filename
                    ts = config_file.name.replace('candidate_model_config_', '').replace('.json', '')
                    config['file_ts'] = ts
                    summaries.append(config)
            except Exception as e:
                print(f"Error loading {config_file}: {e}")
                continue
        
        # Convert to DataFrame
        if summaries:
            df = pd.DataFrame(summaries)
            # Sort by timestamp if available
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df = df.sort_values('timestamp', ascending=False)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error loading training summaries: {e}")
        return pd.DataFrame()

# --- Professional Caching System ---
class SmartCache:
    """Advanced caching system with TTL and change detection"""
    
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
        self.hashes = {}
        self.ttl = {}
        self.default_ttl = 60  # 60 seconds default
        
    def get(self, key, ttl=None):
        """Get cached value if still valid"""
        if key not in self.cache:
            return None
            
        current_time = time.time()
        cache_ttl = ttl or self.ttl.get(key, self.default_ttl)
        
        # Check if cache is still valid
        if current_time - self.timestamps.get(key, 0) < cache_ttl:
            return self.cache[key]
            
        # Cache expired, remove it
        self.invalidate(key)
        return None
        
    def set(self, key, value, ttl=None):
        """Set cached value with optional TTL"""
        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.ttl[key] = ttl or self.default_ttl
        
        # Store hash for change detection
        self.hashes[key] = hashlib.md5(str(value).encode()).hexdigest()
        
    def invalidate(self, key):
        """Remove cached value"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
        self.hashes.pop(key, None)
        self.ttl.pop(key, None)
        
    def has_changed(self, key, new_value):
        """Check if value has changed since last cache"""
        if key not in self.hashes:
            return True
        new_hash = hashlib.md5(str(new_value).encode()).hexdigest()
        return new_hash != self.hashes[key]
        
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()
        self.hashes.clear()
        self.ttl.clear()

# Global cache instance
cache = SmartCache()

# --- WebSocket Event Manager ---
class WebSocketManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.clients = set()
        self.last_broadcast = {}
        
    def add_client(self, sid):
        """Add a WebSocket client"""
        self.clients.add(sid)
        print(f"WebSocket client connected: {sid}")
        
    def remove_client(self, sid):
        """Remove a WebSocket client"""
        self.clients.discard(sid)
        print(f"WebSocket client disconnected: {sid}")
        
    def broadcast(self, event, data):
        """Broadcast data to all connected clients, only if changed"""
        data_key = f"{event}_data"
        
        # Check if data has changed
        if not cache.has_changed(data_key, data):
            # print(f"No change in {event}, skipping broadcast")  # Debug
            return  # No change, don't broadcast
            
        # Store new data in cache
        cache.set(data_key, data, ttl=30)
        
        # Broadcast to all clients (only if SocketIO is available)
        if self.clients and SOCKETIO_AVAILABLE and socketio:
            socketio.emit(event, data)
            print(f"Broadcasted {event} to {len(self.clients)} clients (data changed)")
        else:
            print(f"No clients connected or SocketIO not available for {event}")
            
    def get_client_count(self):
        """Get number of connected clients"""
        return len(self.clients)

# Global WebSocket manager
ws_manager = WebSocketManager()

# --- Global State ---
# A dictionary to keep track of running subprocesses
processes = {
    "model_api": None,
    "trading_agent": None,
    "main_trainer": None,
    "backtester": None,
    "data_collector": None,
    "preprocessor": None,
    "feature_engineering": None,
    "run_all": None,
}

# --- Flask App Initialization ---
app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app, cors_allowed_origins="*")  # Enable Cross-Origin Resource Sharing

# Initialize SocketIO if available
if SOCKETIO_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
else:
    socketio = None

# --- Decorators ---
def cached_endpoint(ttl=60):
    """Decorator for caching API endpoints"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key, ttl)
            if cached_result is not None:
                return cached_result
                
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

def get_process_status(name):
    """Checks the status of a managed subprocess."""
    proc = processes.get(name)
    if not proc:
        return {"status": "not_started", "pid": None}
    
    poll_result = proc.poll()
    if poll_result is None:
        return {"status": "running", "pid": proc.pid}
    else:
        # Process finished, clear it from our state
        processes[name] = None
        return {"status": "finished", "pid": proc.pid, "return_code": poll_result}

# --- WebSocket Events ---
if SOCKETIO_AVAILABLE:
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        ws_manager.add_client(request.sid)
        
        # Send initial data to new client
        emit('status_update', get_all_statuses_data())
        emit('system_info', get_system_info_data())
        
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        ws_manager.remove_client(request.sid)

    @socketio.on('request_update')
    def handle_request_update(data):
        """Handle manual update request from client"""
        update_type = data.get('type', 'all')
        
        if update_type == 'status' or update_type == 'all':
            emit('status_update', get_all_statuses_data())
        if update_type == 'system_info' or update_type == 'all':
            emit('system_info', get_system_info_data())
        if update_type == 'position' or update_type == 'all':
            emit('position_update', get_agent_position_data())

# --- Background Tasks ---
def background_monitor():
    """Background task to monitor system changes and broadcast updates"""
    if not SOCKETIO_AVAILABLE:
        print("⚠️  Background monitoring disabled - WebSocket not available")
        return
        
    while True:
        try:
            # Check for status changes
            status_data = get_all_statuses_data()
            ws_manager.broadcast('status_update', status_data)
            
            # Check for system info changes
            system_info = get_system_info_data()
            ws_manager.broadcast('system_info', system_info)
            
            # Check for position changes
            position_data = get_agent_position_data()
            ws_manager.broadcast('position_update', position_data)
            
            # Sleep for monitoring interval
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"Background monitor error: {e}")
            time.sleep(30)  # Wait longer on error

# --- Helper Functions for Data Retrieval ---
def get_all_statuses_data():
    """Get all process statuses (cached)"""
    return {name: get_process_status(name) for name in processes.keys()}

def get_system_info_data():
    """Get system information (cached) - same format as HTTP API"""
    try:
        import psutil
        import os
        import platform
        
        # Get system information
        memory = psutil.virtual_memory()
        
        # Get disk information
        try:
            # Try Windows C: drive first, then fallback to root
            disk = psutil.disk_usage('C:' if os.name == 'nt' else '/')
        except:
            disk = psutil.disk_usage('/')
        
        # Get system uptime
        uptime_seconds = int(time.time() - psutil.boot_time())
        
        info = {
            'config_loaded': True,
            'timestamp': datetime.now().isoformat(),
            'processes_count': len([p for p in processes.values() if p is not None]),
            'cache_size': len(cache.cache),
            'connected_clients': ws_manager.get_client_count(),
            'os': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            },
            'cpu': {
                'physical_cores': psutil.cpu_count(logical=False),
                'total_cores': psutil.cpu_count(logical=True),
                'usage_percent': psutil.cpu_percent(interval=0.5),
                'frequency': {
                    'current': psutil.cpu_freq().current if psutil.cpu_freq() else None,
                    'min': psutil.cpu_freq().min if psutil.cpu_freq() else None,
                    'max': psutil.cpu_freq().max if psutil.cpu_freq() else None
                }
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total,
                'free': disk.free,
                'used': disk.used,
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'percent': disk.percent
            },
            'uptime': {
                'seconds': uptime_seconds,
                'formatted': f"{uptime_seconds // 86400}d {(uptime_seconds % 86400) // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"
            }
        }
        return info
    except Exception as e:
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}

def get_agent_position_data():
    """Get agent position data (cached)"""
    try:
        # Try to read from agent state
        state_file = Path('agent/state.json')
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                return {
                    'position': state.get('position', 'none'),
                    'symbol': state.get('symbol', '-'),
                    'size': state.get('size', '-'),
                    'entry_time': state.get('entry_time', '-'),
                    'timestamp': datetime.now().isoformat()
                }
        return {'position': 'none', 'timestamp': datetime.now().isoformat()}
    except Exception as e:
        return {'error': str(e), 'position': 'none', 'timestamp': datetime.now().isoformat()}

# --- API Endpoints ---

@app.route('/')
def serve_dashboard():
    """Serves the main dashboard.html file."""
    # This ensures that visiting the root URL serves your new frontend
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - START_TIME
    })

@app.route('/api/status/all', methods=['GET'])
@cached_endpoint(ttl=30)
def get_all_statuses():
    """Returns the status of all managed processes."""
    all_statuses = get_all_statuses_data()
    return jsonify(all_statuses)

@app.route('/api/processes/start/<name>', methods=['POST'])
def start_process(name):
    """Starts a new process by name."""
    if name not in processes:
        return jsonify({"error": "Unknown process name"}), 404
    
    if get_process_status(name)["status"] == "running":
        return jsonify({"error": f"Process '{name}' is already running"}), 400

    command = []
    # Map process names to their respective script paths
    script_map = {
        "model_api": ["src/model_api.py"],
        "main_trainer": ["main_trainer.py"],
        "backtester": ["backtester.py"],
        "data_collector": ["src/data_collector.py"],
        "preprocessor": ["run_preprocessing.py"],
        "feature_engineering": ["src/feature_engineering.py"],
        "feature_engineering_technical": ["src/feature_engineering.py", "--category", "technical"],
        "feature_engineering_candlestick": ["src/feature_engineering.py", "--category", "candlestick"],
        "feature_engineering_volume": ["src/feature_engineering.py", "--category", "volume"],
        "feature_engineering_statistical": ["src/feature_engineering.py", "--category", "statistical"],
        "run_all": ["run_all.py"],
    }

    if name in script_map:
        command = [sys.executable] + script_map[name]
    elif name == "trading_agent":
        command = ["node", "agent/trading_agent.js"]
    else:
        return jsonify({"error": "פקודת תהליך לא מוגדרת"}), 500

    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        processes[name] = proc
        return jsonify({"message": f"תהליך '{name}' הופעל בהצלחה", "pid": proc.pid})
    except Exception as e:
        return jsonify({"error": f"נכשל בהפעלת תהליך '{name}': {e}", "trace": traceback.format_exc()}), 500


@app.route('/api/processes/stop/<name>', methods=['POST'])
def stop_process(name):
    """Stops a running process by name."""
    if name not in processes:
        return jsonify({"error": "Unknown process name"}), 404

    proc = processes.get(name)
    if not proc or proc.poll() is not None:
        return jsonify({"error": f"Process '{name}' is not running"}), 400
        
    try:
        proc.terminate()
        proc.wait(timeout=5)
        processes[name] = None
        return jsonify({"message": f"תהליך '{name}' הופסק."})
    except subprocess.TimeoutExpired:
        proc.kill()
        processes[name] = None
        return jsonify({"message": f"תהליך '{name}' הופסק בכוח."})
    except Exception as e:
        return jsonify({"error": f"נכשל בהפסקת תהליך '{name}': {e}"}), 500

# --- Agent Control ---
@app.route('/api/agent/command', methods=['POST'])
def agent_command():
    """Receives a command and writes it to the agent's command file."""
    command_data = request.json
    if not command_data or 'command' not in command_data:
        return jsonify({"error": "Invalid command data"}), 400
    
    command_path = Path('agent/command.json')
    try:
        command_data['timestamp'] = datetime.now().isoformat()
        with open(command_path, 'w', encoding='utf-8') as f:
            json.dump(command_data, f)
        return jsonify({"message": f"פקודה '{command_data['command']}' נשלחה לסוכן."})
    except Exception as e:
        return jsonify({"error": f"נכשל בכתיבת קובץ הפקודה: {e}"}), 500

@app.route('/api/agent/position', methods=['GET'])
def get_agent_position():
    """Reads the current trade state from the agent's database."""
    db_path = Path('agent/state.db')
    if not db_path.exists():
        return jsonify({"error": "Agent state database not found."}), 404
    
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        row = cur.execute("SELECT value FROM state WHERE key = ?", ('trade_state',)).fetchone()
        conn.close()
        
        trade_state = json.loads(row[0]) if row and row[0] else {}
        return jsonify(trade_state)
    except Exception as e:
        return jsonify({"error": f"Error accessing agent state DB: {e}"}), 500

# --- Config and Data Health ---
@app.route('/api/config', methods=['GET', 'POST', 'PUT'])
def handle_config():
    """Handles loading and saving of the system_config.json file."""
    if request.method == 'GET':
        try:
            config_data = load_system_config()
            return jsonify(config_data)
        except Exception as e:
            return jsonify({"error": f"Failed to load system_config.json: {e}"}), 500
    
    elif request.method in ['POST', 'PUT']:
        try:
            new_config_data = request.json
            if not new_config_data:
                return jsonify({"error": "לא סופקו נתוני JSON"}), 400
            save_system_config(new_config_data)
            return jsonify({"message": "התצורה נשמרה בהצלחה."})
        except Exception as e:
            return jsonify({"error": f"נכשל בשמירת system_config.json: {e}"}), 500

@app.route('/api/data_health', methods=['GET'])
def get_data_health():
    """Checks the status of key data files."""
    data_files = [
        ("SPY_ibkr.csv", "data/raw/SPY_ibkr.csv"),
        ("VIX_ibkr.csv", "data/raw/VIX_ibkr.csv"),
        ("SPY_processed.csv", "data/processed/SPY_processed.csv"),
        ("SPY_features.csv", "data/processed/SPY_features.csv")
    ]
    health_info = []
    for label, path_str in data_files:
        path = Path(path_str)
        info = {"file": label, "exists": False}
        if path.exists():
            try:
                stat = path.stat()
                info["exists"] = True
                info["modified_date"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                
                # Read file to get row count and date range
                if path.suffix.lower() == '.csv':
                    try:
                        df = pd.read_csv(path, parse_dates=True, index_col=0)
                        info["rows"] = len(df)
                        
                        # Try to get date range if there's a date column/index
                        if hasattr(df.index, 'min') and hasattr(df.index, 'max'):
                            try:
                                # Convert index to datetime if it's not already
                                if not pd.api.types.is_datetime64_any_dtype(df.index):
                                    date_index = pd.to_datetime(df.index, errors='coerce')
                                else:
                                    date_index = df.index
                                
                                # Get valid dates (not NaT)
                                valid_dates = date_index.dropna()
                                if len(valid_dates) > 0:
                                    info["start_date"] = valid_dates.min().strftime("%Y-%m-%d")
                                    info["end_date"] = valid_dates.max().strftime("%Y-%m-%d")
                                else:
                                    info["start_date"] = "לא זוהו תאריכים"
                                    info["end_date"] = "לא זוהו תאריכים"
                            except Exception:
                                info["start_date"] = "שגיאה בקריאת תאריכים"
                                info["end_date"] = "שגיאה בקריאת תאריכים"
                        else:
                            info["start_date"] = "לא זוהו תאריכים"
                            info["end_date"] = "לא זוהו תאריכים"
                    except Exception as e:
                        info["rows"] = f"שגיאה בקריאת הקובץ: {str(e)[:50]}"
                        info["start_date"] = "לא זמין"
                        info["end_date"] = "לא זמין"
                elif path.suffix.lower() == '.json':
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        info["rows"] = len(data) if isinstance(data, (list, dict)) else 1
                        info["start_date"] = "לא רלוונטי"
                        info["end_date"] = "לא רלוונטי"
                    except Exception as e:
                        info["rows"] = f"שגיאה: {str(e)[:50]}"
                        info["start_date"] = "לא זמין"
                        info["end_date"] = "לא זמין"
                elif path.suffix.lower() == '.pkl':
                    try:
                        # For pickle files, we just show that they exist
                        info["rows"] = "קובץ מודל"
                        info["start_date"] = "לא רלוונטי"
                        info["end_date"] = "לא רלוונטי"
                    except Exception:
                        info["rows"] = "לא ניתן לקרוא"
                        info["start_date"] = "לא זמין"
                        info["end_date"] = "לא זמין"
                else:
                    # For other files, just count lines
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            info["rows"] = sum(1 for _ in f)
                        info["start_date"] = "לא רלוונטי"
                        info["end_date"] = "לא רלוונטי"
                    except Exception:
                        info["rows"] = "לא ניתן לקרוא"
                        info["start_date"] = "לא זמין"
                        info["end_date"] = "לא זמין"
            except Exception as e:
                info["rows"] = f"שגיאה: {e}"
                info["start_date"] = "לא זמין"
                info["end_date"] = "לא זמין"
        else:
            info["rows"] = "קובץ לא קיים"
            info["start_date"] = "לא זמין"
            info["end_date"] = "לא זמין"
        health_info.append(info)
    return jsonify(health_info)

@app.route('/api/model_health', methods=['GET'])
def get_model_health():
    """Checks the status of model files."""
    model_files = [
        ("champion_model.pkl", "models/champion_model.pkl"),
        ("champion_scaler.pkl", "models/champion_scaler.pkl"),
        ("champion_config.json", "models/champion_model_config.json")
    ]
    health_info = []
    for label, path_str in model_files:
        path = Path(path_str)
        info = {"file": label, "exists": False}
        if path.exists():
            try:
                stat = path.stat()
                info["exists"] = True
                info["modified_date"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                
                # Handle different file types
                if path.suffix.lower() == '.json':
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        info["rows"] = len(data) if isinstance(data, (list, dict)) else 1
                        info["start_date"] = "לא רלוונטי"
                        info["end_date"] = "לא רלוונטי"
                    except Exception as e:
                        info["rows"] = f"שגיאה: {str(e)[:50]}"
                        info["start_date"] = "לא זמין"
                        info["end_date"] = "לא זמין"
                elif path.suffix.lower() == '.pkl':
                    try:
                        # For pickle files, we just show that they exist
                        info["rows"] = "קובץ מודל"
                        info["start_date"] = "לא רלוונטי"
                        info["end_date"] = "לא רלוונטי"
                    except Exception:
                        info["rows"] = "לא ניתן לקרוא"
                        info["start_date"] = "לא זמין"
                        info["end_date"] = "לא זמין"
                else:
                    info["rows"] = "לא זמין"
                    info["start_date"] = "לא זמין"
                    info["end_date"] = "לא זמין"
            except Exception as e:
                info["rows"] = f"שגיאה: {str(e)[:50]}"
                info["start_date"] = "לא זמין"
                info["end_date"] = "לא זמין"
        else:
            info["rows"] = "קובץ לא קיים"
            info["start_date"] = "לא זמין"
            info["end_date"] = "לא זמין"
        health_info.append(info)
    return jsonify(health_info)

# --- Analysis Endpoints ---
@app.route('/api/analysis/training_summaries', methods=['GET'])
def get_training_summaries():
    """Gets all training summaries."""
    try:
        df = load_training_summaries()
        if df.empty:
            return jsonify([])
        result = df.to_json(orient="records", date_format="iso")
        return jsonify(json.loads(result))
    except Exception as e:
        return jsonify({"error": f"Could not load training summaries: {e}", "trace": traceback.format_exc()}), 500

@app.route('/api/analysis/backtests', methods=['GET'])
def list_backtests():
    """Lists available backtest summary files."""
    results_dir = Path("reports/backtest_results")
    if not results_dir.exists():
        return jsonify([])
    
    summary_files = sorted(results_dir.glob("summary_*.json"), key=os.path.getmtime, reverse=True)
    return jsonify([f.name for f in summary_files])

@app.route('/api/analysis/backtests/<filename>', methods=['GET'])
def get_backtest_summary(filename):
    """Gets a specific backtest summary."""
    results_dir = Path("reports/backtest_results")
    summary_file = results_dir / filename
    
    if not summary_file.exists() or not filename.startswith("summary_"):
        # Return empty structure instead of 404
        return jsonify({
            "error": "קובץ לא נמצא",
            "message": f"סיכום בקטסט '{filename}' לא נמצא ב-reports/backtest_results",
            "filename": filename,
            "data": {}
        })
    
    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({
            "error": f"לא ניתן לקרוא קובץ סיכום: {e}",
            "message": "שגיאה בקריאת קובץ סיכום בקטסט",
            "filename": filename,
            "data": {}
        })

@app.route('/api/analysis/promote/<timestamp>', methods=['POST'])
def promote_model(timestamp):
    """Promotes a candidate model to champion."""
    model_dir = Path('models')
    candidate_model_path = model_dir / f'candidate_model_{timestamp}.pkl'
    candidate_scaler_path = model_dir / f'candidate_scaler_{timestamp}.pkl'
    candidate_config_path = model_dir / f'candidate_model_config_{timestamp}.json'

    if not all([p.exists() for p in [candidate_model_path, candidate_scaler_path, candidate_config_path]]):
        return jsonify({"error": f"Candidate model files for timestamp {timestamp} not found."}), 404

    champion_model = model_dir / 'champion_model.pkl'
    champion_scaler = model_dir / 'champion_scaler.pkl'
    champion_config = model_dir / 'champion_model_config.json'
    
    try:
        # 1. Archive existing champion
        if champion_model.exists():
            archive_dir = model_dir / 'archive'
            archive_dir.mkdir(exist_ok=True)
            ts_archive = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            shutil.move(champion_model, archive_dir / f"{champion_model.name}.promoted_away.{ts_archive}")
            if champion_scaler.exists():
                shutil.move(champion_scaler, archive_dir / f"{champion_scaler.name}.promoted_away.{ts_archive}")
            if champion_config.exists():
                shutil.move(champion_config, archive_dir / f"{champion_config.name}.promoted_away.{ts_archive}")

        # 2. Promote candidate to champion
        shutil.copy(candidate_model_path, champion_model)
        shutil.copy(candidate_scaler_path, champion_scaler)
        shutil.copy(candidate_config_path, champion_config)
        
        return jsonify({"message": f"מודל {timestamp} קודם לאלוף בהצלחה."})
    except Exception as e:
        return jsonify({"error": f"נכשל בקידום המודל: {e}", "trace": traceback.format_exc()}), 500

# --- Log Management ---
@app.route('/api/logs/list', methods=['GET'])
def list_logs():
    """Lists available log files."""
    log_files = [
        'main_trainer_output.log',
        'backtester_output.log', 
        'all_features_computed.log',
        'agent/trading_log.txt'
    ]
    
    available_logs = []
    for log_file in log_files:
        log_path = Path(log_file)
        if log_path.exists():
            stat = log_path.stat()
            available_logs.append({
                'name': log_file,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return jsonify(available_logs)

@app.route('/api/logs/<path:filename>', methods=['GET'])
def get_log_content(filename):
    """Gets log file content with optional line range."""
    log_path = Path(filename)
    if not log_path.exists():
        return jsonify({"error": "Log file not found"}), 404
    
    lines = int(request.args.get('lines', 100))
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
            # Return last N lines
            content = content[-lines:] if len(content) > lines else content
            return jsonify({"content": "".join(content), "total_lines": len(content)})
    except Exception as e:
        return jsonify({"error": f"Failed to read log file: {e}"}), 500

# --- Optuna Analysis ---
@app.route('/api/analysis/optuna', methods=['GET'])
def get_optuna_analysis():
    """Gets Optuna study analysis."""
    db_path = Path('spy_strategy_optimization.db')
    if not db_path.exists():
        return jsonify({
            "error": "מסד נתוני Optuna לא נמצא",
            "message": "אין מחקרי Optuna זמינים. הרץ אימון תחילה כדי ליצור נתונים.",
            "study_name": None,
            "trials": [],
            "params": [],
            "values": []
        })
    
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        
        # Get studies
        studies_df = pd.read_sql_query(
            "SELECT study_name, storage_id FROM studies ORDER BY study_id DESC",
            conn
        )
        
        if studies_df.empty:
            conn.close()
            return jsonify({
                "error": "לא נמצאו מחקרים",
                "message": "מסד הנתונים קיים אך לא מכיל מחקרים. הרץ אימון תחילה.",
                "study_name": None,
                "trials": [],
                "params": [],
                "values": []
            })
        
        study_name = studies_df['study_name'].iloc[0]
        
        # Get trials
        trials_df = pd.read_sql_query(
            f"SELECT * FROM trials WHERE study_id = (SELECT study_id FROM studies WHERE study_name = '{study_name}') ORDER BY trial_id",
            conn
        )
        
        # Get trial params
        params_df = pd.read_sql_query(
            f"SELECT * FROM trial_params WHERE trial_id IN (SELECT trial_id FROM trials WHERE study_id = (SELECT study_id FROM studies WHERE study_name = '{study_name}'))",
            conn
        )
        
        # Get trial values
        values_df = pd.read_sql_query(
            f"SELECT * FROM trial_values WHERE trial_id IN (SELECT trial_id FROM trials WHERE study_id = (SELECT study_id FROM studies WHERE study_name = '{study_name}'))",
            conn
        )
        
        conn.close()
        
        return jsonify({
            "study_name": study_name,
            "trials": trials_df.to_dict('records'),
            "params": params_df.to_dict('records'),
            "values": values_df.to_dict('records')
        })
        
    except Exception as e:
        return jsonify({
            "error": f"נכשל בטעינת נתוני Optuna: {e}",
            "message": "אירעה שגיאת מסד נתונים",
            "study_name": None,
            "trials": [],
            "params": [],
            "values": []
        })

# --- System Status ---
@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Gets detailed system status including process monitoring."""
    try:
        import psutil
        
        # Get current processes
        system_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                info = proc.info
                if info['cmdline']:
                    cmdline = ' '.join(info['cmdline'])
                    # Check if it's one of our processes
                    if any(script in cmdline for script in ['dashboard.py', 'api_server.py', 'main_trainer.py', 'trading_agent.js']):
                        system_processes.append({
                            'pid': info['pid'],
                            'name': info['name'],
                            'cmdline': cmdline
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return jsonify({
            "managed_processes": {name: get_process_status(name) for name in processes.keys()},
            "system_processes": system_processes
        })
        
    except ImportError:
        return jsonify({
            "managed_processes": {name: get_process_status(name) for name in processes.keys()},
            "system_processes": []
        })

@app.route('/api/system/info', methods=['GET'])
def get_system_info():
    """Gets detailed system information including CPU, memory and disk usage."""
    try:
        import psutil
        from platform import system, release, version, machine, processor
        
        # Get system information
        os_info = {
            "system": system(),
            "release": release(),
            "version": version(),
            "machine": machine(),
            "processor": processor()
        }
        
        # Get CPU information
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "usage_percent": psutil.cpu_percent(interval=0.5),
            "frequency": {
                "current": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "min": psutil.cpu_freq().min if psutil.cpu_freq() else None,
                "max": psutil.cpu_freq().max if psutil.cpu_freq() else None
            }
        }
        
        # Get memory information
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent,
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2)
        }
        
        # Get disk information
        try:
            # Try Windows C: drive first, then fallback to root
            disk = psutil.disk_usage('C:' if os.name == 'nt' else '/')
        except:
            disk = psutil.disk_usage('/')
            
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2)
        }
        
        # Get system uptime
        uptime_seconds = int(time.time() - psutil.boot_time())
        uptime = {
            "seconds": uptime_seconds,
            "formatted": f"{uptime_seconds // 86400}d {(uptime_seconds % 86400) // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"
        }
        
        return jsonify({
            "os": os_info,
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "uptime": uptime,
            "timestamp": datetime.now().isoformat()
        })
        
    except ImportError:
        return jsonify({
            "error": "psutil not installed",
            "message": "מודול psutil לא מותקן. התקן אותו באמצעות 'pip install psutil'"
        })


# --- Command History ---
@app.route('/api/agent/command/history', methods=['GET'])
def get_command_history():
    """Gets the command history of the agent from the log file."""
    try:
        command_path = Path('agent/command.json')
        command_log_path = Path('agent/trading_log.txt')
        
        # Parse commands from the trading log
        commands = []
        if command_log_path.exists():
            with open(command_log_path, encoding='utf-8', errors='ignore') as f:
                log_content = f.readlines()
                
                for line in log_content:
                    if "Received command:" in line:
                        try:
                            parts = line.split("Received command:", 1)
                            if len(parts) > 1:
                                timestamp = parts[0].strip()
                                cmd_json = parts[1].strip()
                                command_data = json.loads(cmd_json)
                                command_data["timestamp"] = timestamp
                                commands.append(command_data)
                        except Exception as e:
                            print(f"Error parsing command line: {e}")
        
        # Get current command
        current_command = {}
        if command_path.exists():
            try:
                with open(command_path, encoding='utf-8') as f:
                    content = f.read()
                    current_command = json.loads(content) if content else {}
            except Exception as e:
                print(f"Error reading command.json: {e}")
        
        # Get command history from trading_log.txt
        commands_history = []
        if command_log_path.exists():
            try:
                with open(command_log_path, encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if "COMMAND:" in line:
                            commands_history.append({
                                "timestamp": line.split("[")[1].split("]")[0] if "[" in line else "N/A",
                                "command": line.strip()
                            })
                            if len(commands_history) >= 10:  # Limit to last 10 commands
                                break
            except Exception as e:
                print(f"Error reading trading_log.txt: {e}")
        
        return jsonify({
            "current": current_command,
            "history": commands_history,
            "commands": commands
        })
    except Exception as e:
        return jsonify({"error": f"Failed to get command history: {e}"}), 500

# --- Data Reset ---
@app.route('/api/data/reset', methods=['POST'])
def reset_data():
    """Resets all data files and starts collection process from scratch."""
    try:
        data_files = [
            Path("data/raw/SPY_ibkr.csv"),
            Path("data/raw/VIX_ibkr.csv"),
            Path("data/processed/SPY_processed.csv")
        ]
        
        # Delete data files
        for file_path in data_files:
            if file_path.exists():
                file_path.unlink()
        
        # Start data collection process
        command = [sys.executable, "run_all.py"]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        processes["run_all"] = proc
        
        return jsonify({
            "message": "הנתונים אופסו והתהליך המלא הופעל מחדש",
            "deleted_files": [str(p) for p in data_files if not p.exists()]
        })
    except Exception as e:
        return jsonify({"error": f"Failed to reset data: {e}", "trace": traceback.format_exc()}), 500

# --- Feature Engineering Endpoints ---
@app.route('/api/features/info', methods=['GET'])
def get_feature_info():
    """Get feature engineering information."""
    try:
        config = load_system_config()
        processed_file = Path(config.get('processed_data_path', 'data/processed/SPY_processed.csv'))
        
        info = {
            'total_features': '-',
            'new_features': '-',
            'last_processing_time': '-'
        }
        
        if processed_file.exists():
            df = pd.read_csv(processed_file)
            info['total_features'] = len(df.columns)
            
            # Get last modification time
            mod_time = processed_file.stat().st_mtime
            info['last_processing_time'] = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
            
            # Count new features (this is a simple example)
            basic_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            new_features = len(df.columns) - len(basic_columns)
            info['new_features'] = max(0, new_features)
        
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": f"Failed to get feature info: {e}"}), 500

@app.route('/api/features/importance', methods=['GET'])
def get_feature_importance():
    """Get feature importance data."""
    try:
        # Look for feature importance files
        models_dir = Path('models')
        importance_files = list(models_dir.glob('**/feature_importance.json'))
        
        if not importance_files:
            return jsonify({"error": "No feature importance data found"}), 404
            
        # Load the most recent one
        latest_file = max(importance_files, key=lambda p: p.stat().st_mtime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            importance_data = json.load(f)
            
        return jsonify(importance_data)
    except Exception as e:
        return jsonify({"error": f"Failed to get feature importance: {e}"}), 500

# --- Training Endpoints ---
@app.route('/api/training/results', methods=['GET'])
def get_training_results():
    """Get training results and metrics."""
    try:
        results = {
            'accuracy': '-',
            'f1_score': '-',
            'auc': '-',
            'last_training_time': '-'
        }
        
        # Look for training results
        models_dir = Path('models')
        result_files = list(models_dir.glob('**/training_summary.json'))
        
        if result_files:
            # Load the most recent one
            latest_file = max(result_files, key=lambda p: p.stat().st_mtime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
                
            # Extract metrics
            if 'metrics' in training_data:
                metrics = training_data['metrics']
                results['accuracy'] = f"{metrics.get('accuracy', 0):.3f}"
                results['f1_score'] = f"{metrics.get('f1_score', 0):.3f}"
                results['auc'] = f"{metrics.get('roc_auc', 0):.3f}"
                
            # Get timestamp
            if 'timestamp' in training_data:
                results['last_training_time'] = training_data['timestamp']
            else:
                mod_time = latest_file.stat().st_mtime
                results['last_training_time'] = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
        
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"Failed to get training results: {e}"}), 500

@app.route('/api/training/history', methods=['GET'])
def get_training_history():
    """Get training history."""
    try:
        models_dir = Path('models')
        history = []
        
        # Look for all training summary files
        for summary_file in models_dir.glob('**/training_summary.json'):
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Add file info
                data['file_path'] = str(summary_file)
                data['file_timestamp'] = summary_file.stat().st_mtime
                history.append(data)
            except Exception as e:
                continue
                
        # Sort by timestamp
        history.sort(key=lambda x: x.get('file_timestamp', 0), reverse=True)
        
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": f"Failed to get training history: {e}"}), 500

# --- Backtest Endpoints ---
@app.route('/api/backtest/results', methods=['GET'])
def get_backtest_results():
    """Get latest backtest results."""
    try:
        results = {
            'total_return': '-',
            'sharpe_ratio': '-',
            'max_drawdown': '-',
            'win_rate': '-',
            'last_backtest_time': '-'
        }
        
        # Look for backtest results
        results_dir = Path('reports/backtest_results')
        if results_dir.exists():
            summary_files = list(results_dir.glob('summary_*.json'))
            if summary_files:
                # Get the most recent summary file
                latest_file = max(summary_files, key=lambda p: p.stat().st_mtime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    backtest_data = json.load(f)
                    
                # Extract metrics
                results['total_return'] = f"{backtest_data.get('total_return', 0)*100:.2f}%"
                results['sharpe_ratio'] = f"{backtest_data.get('sharpe_ratio', 0):.2f}"
                results['max_drawdown'] = f"{backtest_data.get('max_drawdown', 0)*100:.2f}%"
                results['win_rate'] = f"{backtest_data.get('win_rate', 0)*100:.2f}%"
                
                # Get timestamp
                mod_time = latest_file.stat().st_mtime
                results['last_backtest_time'] = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
        
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"Failed to get backtest results: {e}"}), 500

@app.route('/api/backtest/equity', methods=['GET'])
def get_backtest_equity():
    """Get backtest equity curve data."""
    try:
        results_dir = Path('reports/backtest_results')
        equity_files = list(results_dir.glob('equity_curve_*.csv'))
        
        if not equity_files:
            return jsonify({"error": "No equity curve data found"}), 404
            
        # Get the most recent equity file
        latest_file = max(equity_files, key=lambda p: p.stat().st_mtime)
        df = pd.read_csv(latest_file, index_col=0, parse_dates=True)
        
        # Convert to JSON format for charts
        equity_data = {
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'equity': df['equity'].tolist(),
            'benchmark': df.get('benchmark_equity', df['equity']).tolist()
        }
        
        return jsonify(equity_data)
    except Exception as e:
        return jsonify({"error": f"Failed to get equity curve: {e}"}), 500

# --- Trading Agent Endpoints ---
@app.route('/api/agent/status', methods=['GET'])
def get_agent_status():
    """Get trading agent status."""
    try:
        status = {
            'status': 'כבוי',
            'test_mode': True,
            'ibkr_connected': False,
            'active_model': None,
            'last_action': '-',
            'uptime': '-',
            'open_positions': 0,
            'daily_pnl': '$0.00',
            'total_pnl': '$0.00'
        }
        
        # Check if agent is running
        if processes.get('trading_agent') and processes['trading_agent'].poll() is None:
            status['status'] = 'פעיל'
            
            # Try to get more details from agent files
            agent_dir = Path('agent')
            if agent_dir.exists():
                # Check state file
                state_file = agent_dir / 'state.json'
                if state_file.exists():
                    with open(state_file, 'r', encoding='utf-8') as f:
                        agent_state = json.load(f)
                        status['ibkr_connected'] = agent_state.get('connected', False)
                        status['last_action'] = agent_state.get('last_action', '-')
                        
                # Check configuration
                config = load_system_config()
                status['test_mode'] = config.get('agent_settings', {}).get('TEST_MODE_ENABLED', True)
                
                # Check if model exists
                model_path = Path('models/champion_model.pkl')
                status['active_model'] = 'טעון' if model_path.exists() else 'לא טעון'
        
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": f"Failed to get agent status: {e}"}), 500

@app.route('/api/agent/positions', methods=['GET'])
def get_agent_positions():
    """Get trading agent positions."""
    try:
        positions = []
        
        # Try to read positions from agent state or database
        agent_dir = Path('agent')
        if agent_dir.exists():
            state_file = agent_dir / 'state.json'
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    agent_state = json.load(f)
                    positions = agent_state.get('positions', [])
        
        return jsonify({'positions': positions})
    except Exception as e:
        return jsonify({"error": f"Failed to get agent positions: {e}"}), 500

@app.route('/api/agent/orders', methods=['GET'])
def get_agent_orders():
    """Get trading agent orders."""
    try:
        orders = []
        
        # Try to read orders from agent logs or database
        agent_dir = Path('agent')
        if agent_dir.exists():
            log_file = agent_dir / 'trading_log.txt'
            if log_file.exists():
                # Parse recent orders from log file
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-50:]  # Last 50 lines
                    for line in lines:
                        if 'ORDER' in line.upper():
                            # Parse order information from log
                            # This is a simplified example
                            parts = line.strip().split()
                            if len(parts) >= 6:
                                order = {
                                    'time': parts[0] + ' ' + parts[1],
                                    'symbol': 'SPY',
                                    'type': 'BUY' if 'BUY' in line.upper() else 'SELL',
                                    'quantity': '1',
                                    'price': '0.00',
                                    'status': 'Filled'
                                }
                                orders.append(order)
        
        return jsonify({'orders': orders})
    except Exception as e:
        return jsonify({"error": f"Failed to get agent orders: {e}"}), 500

@app.route('/api/agent/logs', methods=['GET'])
def get_agent_logs():
    """Get trading agent logs."""
    try:
        logs = []
        
        agent_dir = Path('agent')
        if agent_dir.exists():
            log_file = agent_dir / 'trading_log.txt'
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-100:]  # Last 100 lines
                    for line in lines:
                        if line.strip():
                            # Parse timestamp and message
                            parts = line.strip().split(' ', 2)
                            if len(parts) >= 3:
                                log = {
                                    'timestamp': parts[0] + ' ' + parts[1],
                                    'message': ' '.join(parts[2:])
                                }
                                logs.append(log)
        
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({"error": f"Failed to get agent logs: {e}"}), 500

@app.route('/api/models/<ts>', methods=['DELETE'])
def delete_model(ts):
    """Delete a specific model by timestamp."""
    try:
        models_dir = Path('models')
        model_path = models_dir / ts
        
        if not model_path.exists():
            return jsonify({"error": f"Model {ts} not found"}), 404
        
        # Check if it's a directory or file
        if model_path.is_dir():
            # Remove the entire directory
            shutil.rmtree(model_path)
        else:
            # Remove the file
            model_path.unlink()
        
        return jsonify({"message": f"Model {ts} deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to delete model {ts}: {e}"}), 500

if __name__ == '__main__':
    # Start background monitoring thread
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    
    print("🚀 Starting advanced API server...")
    if SOCKETIO_AVAILABLE:
        print(f"📡 WebSocket endpoint: ws://localhost:5001/socket.io/")
        print(f"💾 Caching: Enabled with smart change detection")
    else:
        print("⚠️  Running without WebSocket support")
    print(f"🌐 Dashboard: http://localhost:5001/")
    
    # Run with SocketIO if available, otherwise regular Flask
    if SOCKETIO_AVAILABLE and socketio:
        socketio.run(app, host='0.0.0.0', port=5001, debug=True)
    else:
        app.run(host='0.0.0.0', port=5001, debug=True)
