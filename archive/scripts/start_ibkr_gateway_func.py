"""
IBKR Gateway Starter Module

This module provides the functionality to start the Interactive Brokers Gateway
from the API server. It contains the implementation of the /api/ibkr/start endpoint.
"""

import os
import sys
import time
import json
import socket
import subprocess
from flask import jsonify

# Load system configuration from JSON file
def load_system_config():
    """Load system configuration from JSON file."""
    try:
        with open('system_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading system_config.json: {e}")
        return {}

def is_ibkr_available():
    """Check if IBKR Gateway/TWS is available.
    
    Returns:
        tuple: (is_available, host, port, error_message)
            - is_available (bool): True if IBKR is accessible
            - host (str): The IBKR host
            - port (int): The IBKR port
            - error_message (str): Error message if not available, empty string otherwise
    """
    try:
        config = load_system_config()
        ibkr_settings = config.get('ibkr_settings', {})
        host = ibkr_settings.get('host', '127.0.0.1')
        port = int(ibkr_settings.get('port', 4001))
        
        # Try to connect to IBKR port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return True, host, port, ""
        else:
            error_msg = f"IBKR Gateway/TWS is not accessible on {host}:{port}. Make sure it's running and API is enabled."
            return False, host, port, error_msg
    except Exception as e:
        return False, "unknown", 0, f"Failed to check IBKR status: {e}"

def get_ibkr_gateway_path():
    """Get the path to IBKR Gateway executable from system config."""
    config = load_system_config()
    return config.get('ibkr_gateway_path', "C:\\Jts\\ibgateway\\1037\\ibgateway.exe")

# Define a Flask app to make this module testable standalone
from flask import Flask
app = Flask(__name__)

@app.route('/api/ibkr/start', methods=['POST'])
def start_ibkr_gateway():
    """Start IBKR Gateway application using the simplified start_ibkr.py script."""
    is_available, _, _, _ = is_ibkr_available()
    if is_available:
        return jsonify({
            "status": "already_running",
            "message": "IBKR Gateway is already running"
        })
    
    gateway_path = get_ibkr_gateway_path()
    if not gateway_path or not os.path.exists(gateway_path):
        return jsonify({
            "status": "error",
            "message": "IBKR Gateway path not configured or invalid. Please set the gateway_path in system_config.json."
        }), 400
    
    # Use the simplified start_ibkr.py script to launch the gateway
    start_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'start_ibkr.py')
    
    if not os.path.exists(start_script_path):
        return jsonify({
            "status": "error",
            "message": "start_ibkr.py script not found. Please ensure it exists in the project root directory."
        }), 500
    
    try:
        # Run the script in a separate process
        proc = subprocess.Popen(
            [sys.executable, start_script_path],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        # Check if process started successfully
        time.sleep(1)
        if proc.poll() is not None:
            out, err = proc.communicate()
            error_message = err.decode('utf-8', errors='replace')
            return jsonify({
                "status": "error",
                "message": f"Failed to start IBKR Gateway script: {error_message}",
                "error": error_message
            }), 500
        
        return jsonify({
            "status": "starting",
            "message": "IBKR Gateway is starting with the simplified automation script. Please wait...",
            "pid": proc.pid,
            "method": "Simplified Python script"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to start IBKR Gateway: {str(e)}",
            "error": str(e)
        }), 500

# Add this section to make the file runnable standalone
if __name__ == "__main__":
    print("IBKR Gateway API Starter")
    print("Starting Flask server on port 5000...")
    print("Use http://localhost:5000/api/ibkr/start to start the IBKR Gateway")
    app.run(debug=True, port=5000)
