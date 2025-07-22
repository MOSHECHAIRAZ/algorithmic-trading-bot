"""
routes/ibkr.py - נתיבי ממשק IBKR

נתיבים הקשורים לממשק עם Interactive Brokers
"""

from flask import Blueprint, jsonify, request
import logging
import os
import json
from datetime import datetime, timedelta
import random

ibkr_bp = Blueprint('ibkr', __name__, url_prefix='/api/ibkr')

@ibkr_bp.route('/status', methods=['GET'])
def get_ibkr_status():
    """מחזיר מידע על סטטוס החיבור ל-IBKR"""
    
    # מידע לדוגמה על סטטוס IBKR
    connected = random.choice([True, True, True, False])  # יותר סיכוי שיהיה מחובר
    
    status = {
        "connected": connected,
        "gateway_running": connected,
        "tws_running": False,  # לדוגמה, רק Gateway פעיל ולא TWS
        "connection_time": (datetime.now() - timedelta(hours=4)).isoformat() if connected else None,
        "account_id": "DU12345" if connected else None,
        "last_heartbeat": datetime.now().isoformat() if connected else None,
        "api_version": "9.81.1",
        "api_port": 4002,
        "environment": "Paper",  # Paper או Live
        "market_data_type": "DELAYED",  # REALTIME או DELAYED או FROZEN
        "client_id": 1,
        "errors": [] if connected else ["Connection timeout", "Gateway not responding"],
        "max_reqid": 5342 if connected else 0
    }
    
    return jsonify(status)

@ibkr_bp.route('/config', methods=['GET'])
def get_ibkr_config():
    """מחזיר את הגדרות ה-IBKR (ללא פרטים רגישים)"""
    
    config = {
        "api_settings": {
            "host": "127.0.0.1",
            "port": 4002,
            "client_id": 1,
            "timeout": 30,
            "readonly": False
        },
        "gateway_settings": {
            "path": "C:\\IBC",
            "version": "981",
            "mode": "gateway",  # gateway או tws
            "ibc_path": "C:\\IBController",
            "ibc_ini": "IBController.ini",
            "auto_restart": True,
            "auto_login": True
        },
        "account_settings": {
            "account_id": "DU12345",
            "paper_trading": True,
            "username": "***REDACTED***",
            "password": "***REDACTED***"
        },
        "connection_settings": {
            "auto_connect": True,
            "reconnect_interval": 60,
            "max_retries": 5
        }
    }
    
    return jsonify(config)

@ibkr_bp.route('/connect', methods=['POST'])
def connect_ibkr():
    """התחבר ל-IBKR Gateway"""
    
    try:
        # סימולציה של חיבור מוצלח
        success = random.random() > 0.2  # 80% סיכוי להצלחה
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Successfully connected to IBKR Gateway",
                "connection_time": datetime.now().isoformat(),
                "account_id": "DU12345"
            })
        else:
            error_message = random.choice([
                "Connection timeout",
                "Invalid credentials",
                "Gateway not running",
                "TWS is already running on the specified port"
            ])
            return jsonify({
                "status": "error",
                "message": f"Failed to connect: {error_message}"
            }), 500
    except Exception as e:
        logging.error(f"Error connecting to IBKR: {e}")
        return jsonify({
            "status": "error",
            "message": f"Exception occurred: {str(e)}"
        }), 500

@ibkr_bp.route('/disconnect', methods=['POST'])
def disconnect_ibkr():
    """ניתוק מ-IBKR Gateway"""
    
    try:
        # סימולציה של ניתוק מוצלח
        return jsonify({
            "status": "success",
            "message": "Successfully disconnected from IBKR Gateway",
            "disconnection_time": datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error disconnecting from IBKR: {e}")
        return jsonify({
            "status": "error",
            "message": f"Exception occurred: {str(e)}"
        }), 500
