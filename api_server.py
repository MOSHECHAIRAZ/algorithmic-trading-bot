# api_server.py
# This file replaces the old dashboard.py and acts as the central backend server.

import subprocess
import sys
import json
import os
import shutil
import pandas as pd
from pathlib import Path
import sqlite3
import traceback
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS

# Import existing logic from your project
from src.utils import load_system_config, save_system_config

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

# --- Global State ---
# A dictionary to keep track of running subprocesses
processes = {
    "model_api": None,
    "trading_agent": None,
    "main_trainer": None,
    "backtester": None,
    "data_collector": None,
    "preprocessor": None,
    "run_all": None,
}

# --- Flask App Initialization ---
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app) # Enable Cross-Origin Resource Sharing

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

# --- API Endpoints ---

@app.route('/')
def serve_dashboard():
    """Serves the main dashboard.html file."""
    # This ensures that visiting the root URL serves your new frontend
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/status/all', methods=['GET'])
def get_all_statuses():
    """Returns the status of all managed processes."""
    all_statuses = {name: get_process_status(name) for name in processes.keys()}
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
        "run_all": ["run_all.py"],
    }

    if name in script_map:
        command = [sys.executable] + script_map[name]
    elif name == "trading_agent":
        command = ["node", "agent/trading_agent.js"]
    else:
        return jsonify({"error": "Process command not defined"}), 500

    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        processes[name] = proc
        return jsonify({"message": f"Process '{name}' started successfully", "pid": proc.pid})
    except Exception as e:
        return jsonify({"error": f"Failed to start process '{name}': {e}", "trace": traceback.format_exc()}), 500


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
        return jsonify({"message": f"Process '{name}' stopped."})
    except subprocess.TimeoutExpired:
        proc.kill()
        processes[name] = None
        return jsonify({"message": f"Process '{name}' forcefully killed."})
    except Exception as e:
        return jsonify({"error": f"Failed to stop process '{name}': {e}"}), 500

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
        return jsonify({"message": f"Command '{command_data['command']}' sent to agent."})
    except Exception as e:
        return jsonify({"error": f"Failed to write command file: {e}"}), 500

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
@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Handles loading and saving of the system_config.json file."""
    if request.method == 'GET':
        try:
            config_data = load_system_config()
            return jsonify(config_data)
        except Exception as e:
            return jsonify({"error": f"Failed to load system_config.json: {e}"}), 500
    
    elif request.method == 'POST':
        try:
            new_config_data = request.json
            if not new_config_data:
                return jsonify({"error": "No JSON data provided"}), 400
            save_system_config(new_config_data)
            return jsonify({"message": "Configuration saved successfully."})
        except Exception as e:
            return jsonify({"error": f"Failed to save system_config.json: {e}"}), 500

@app.route('/api/data_health', methods=['GET'])
def get_data_health():
    """Checks the status of key data files."""
    data_files = [
        ("SPY_ibkr.csv", "data/raw/SPY_ibkr.csv"),
        ("VIX_ibkr.csv", "data/raw/VIX_ibkr.csv"),
        ("SPY_processed.csv", "data/processed/SPY_processed.csv")
    ]
    health_info = []
    for label, path_str in data_files:
        path = Path(path_str)
        info = {"file": label, "exists": False}
        if path.exists():
            stat = path.stat()
            info["exists"] = True
            info["modified_date"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            info["size_mb"] = f"{stat.st_size / (1024*1024):.2f}"
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
        abort(404, "Backtest summary not found.")
    
    try:
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Could not read summary file: {e}"}), 500

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
        
        return jsonify({"message": f"Model {timestamp} promoted to champion successfully."})
    except Exception as e:
        return jsonify({"error": f"Failed to promote model: {e}", "trace": traceback.format_exc()}), 500

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
        return jsonify({"error": "Optuna database not found"}), 404
    
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        
        # Get studies
        studies_df = pd.read_sql_query(
            "SELECT study_name, storage_id FROM studies ORDER BY study_id DESC",
            conn
        )
        
        if studies_df.empty:
            conn.close()
            return jsonify({"error": "No studies found"}), 404
        
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
        return jsonify({"error": f"Failed to load Optuna data: {e}"}), 500

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
