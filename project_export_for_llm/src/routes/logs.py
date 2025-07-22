"""
routes/logs.py - נתיבי קבצי לוג

נתיבים הקשורים לניהול וצפייה בקבצי לוג
"""

from flask import Blueprint, jsonify, send_from_directory, request
import logging
import os
from datetime import datetime, timedelta
import random

logs_bp = Blueprint('logs', __name__, url_prefix='/api/logs')

@logs_bp.route('/list', methods=['GET'])
def get_logs_list():
    """מחזיר רשימת קבצי לוג זמינים"""
    
    # מידע לדוגמה על קבצי לוג
    log_files = []
    
    # יצירת 15 קבצי לוג לדוגמה
    for i in range(15):
        hours_ago = i * 3
        log_date = datetime.now() - timedelta(hours=hours_ago)
        
        log_type = random.choice([
            "api_server", "backtester", "model_trainer", 
            "feature_engineering", "agent", "gateway"
        ])
        
        log_entry = {
            "id": f"{log_type}_{log_date.strftime('%Y%m%d_%H%M')}",
            "filename": f"{log_type}.log.{log_date.strftime('%Y%m%d_%H%M')}",
            "type": log_type,
            "size_kb": random.randint(5, 1500),
            "created": log_date.isoformat(),
            "path": f"logs/{log_type}.log.{log_date.strftime('%Y%m%d_%H%M')}"
        }
        
        log_files.append(log_entry)
    
    return jsonify(log_files)

@logs_bp.route('/content', methods=['GET'])
def get_log_content():
    """מחזיר תוכן של קובץ לוג"""
    
    filename = request.args.get('filename')
    
    if not filename:
        return jsonify({"error": "No filename specified"}), 400
    
    # לדוגמה, יצירת תוכן לוג מדומה
    log_type = "api_server"
    if "backtester" in filename:
        log_type = "backtester"
    elif "model_trainer" in filename:
        log_type = "model_trainer"
    elif "feature_engineering" in filename:
        log_type = "feature_engineering"
    elif "agent" in filename:
        log_type = "agent"
    elif "gateway" in filename:
        log_type = "gateway"
    
    # יצירת רשומות לוג לדוגמה
    log_lines = []
    log_date = datetime.now()
    
    # סוגי הודעות לפי סוג הלוג
    messages = {
        "api_server": [
            "API server started on port 5000",
            "Received request for /api/status/all",
            "Served request in 25ms",
            "Authentication successful for admin user",
            "Socket.IO connection established",
            "Broadcast status update to 2 clients",
            "Error handling request: Invalid parameter",
            "CPU usage: 15%, Memory: 120MB"
        ],
        "backtester": [
            "Backtester initialized with data from 2023-01-01 to 2023-06-30",
            "Loading model from models/champion_v3.2.pkl",
            "Running backtest with SPY 1D data",
            "Trade executed: LONG @ $420.50",
            "Trade closed: LONG @ $435.75, profit: 3.63%",
            "Processing day 45/180...",
            "Completed backtest with 68 trades",
            "Final equity: $12,350.25, profit: 23.5%"
        ],
        "model_trainer": [
            "Starting training for LightGBM model",
            "Loading training data: 235,000 samples",
            "Feature importance calculation complete",
            "Cross-validation fold 3/5: accuracy 0.763",
            "Early stopping at epoch 156",
            "Model saved to models/lightgbm_v3.2.pkl",
            "Training completed in 25 minutes",
            "Final validation metrics: Accuracy=0.782, F1=0.753"
        ],
        "feature_engineering": [
            "Computing features for SPY data",
            "Calculating RSI features",
            "Computing MACD indicators",
            "Feature correlation analysis complete",
            "Removing features with high correlation",
            "Saving feature set to disk",
            "Total features generated: 46",
            "Feature engineering completed in 8 minutes"
        ],
        "agent": [
            "Trading agent initialized",
            "Connecting to broker API",
            "Evaluating market conditions",
            "Signal detected: LONG with confidence 0.82",
            "Executing order: BUY 100 SPY @ MARKET",
            "Order filled: 100 SPY @ $432.50",
            "Setting stop loss at $425.85",
            "Daily trading session complete, P&L: +$350.25"
        ],
        "gateway": [
            "Gateway manager started",
            "IBKR Gateway launch sequence initiated",
            "Waiting for TWS to initialize",
            "Login sequence started",
            "Executing login macro",
            "Login successful",
            "API connection established",
            "Gateway ready for trading operations"
        ]
    }
    
    # יצירת 50 שורות לוג אקראיות
    for i in range(50):
        minutes_ago = i * random.randint(1, 5)
        entry_time = log_date - timedelta(minutes=minutes_ago)
        level = random.choice(["INFO", "INFO", "INFO", "INFO", "WARNING", "ERROR", "DEBUG"])
        
        # צבע הרמה בהתאם לחומרה
        if level == "ERROR":
            level_colored = f"<span class='text-red-500'>{level}</span>"
        elif level == "WARNING":
            level_colored = f"<span class='text-yellow-500'>{level}</span>"
        elif level == "DEBUG":
            level_colored = f"<span class='text-blue-400'>{level}</span>"
        else:
            level_colored = f"<span class='text-gray-400'>{level}</span>"
        
        # בחירת הודעה אקראית לפי סוג הלוג
        message = random.choice(messages[log_type])
        
        # הוספת שגיאות אקראיות
        if level == "ERROR":
            message = random.choice([
                "Exception occurred: ConnectionError",
                "Failed to connect to database",
                "Invalid configuration parameter",
                "API request timeout",
                "Out of memory error"
            ])
        
        log_line = f"[{entry_time.strftime('%Y-%m-%d %H:%M:%S')}] {level_colored} - {message}"
        log_lines.append(log_line)
    
    return jsonify({
        "filename": filename,
        "content": log_lines,
        "type": log_type
    })
