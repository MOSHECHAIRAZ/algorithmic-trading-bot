"""
routes/health.py - נתיבי בריאות המערכת

נתיבים הקשורים למצב בריאות רכיבי המערכת השונים
"""

from flask import Blueprint, jsonify
import logging
import os
import json
from datetime import datetime, timedelta
import random

health_bp = Blueprint('health', __name__, url_prefix='/api')

@health_bp.route('/health', methods=['GET'])
def get_health():
    """בדיקת בריאות בסיסית לשרת API"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "7:23:15",  # מידע סטטי לדוגמה
        "api_version": "1.0.0"
    })

@health_bp.route('/data_health', methods=['GET'])
def get_data_health():
    """מחזיר מידע על בריאות מערכת איסוף ועיבוד הנתונים"""
    
    # מידע לדוגמה על בריאות הנתונים
    last_update = datetime.now() - timedelta(minutes=random.randint(5, 120))
    
    return jsonify({
        "status": "healthy",
        "lastDataUpdate": last_update.isoformat(),
        "dataPoints": random.randint(1000, 10000),
        "latestSymbol": "SPY",
        "dataSourceStatus": "connected",
        "errors": [],
        "warnings": ["API rate limit at 80%"],
        "processingQueue": random.randint(0, 10),
        "dataConsistencyScore": random.uniform(95, 100),
        "details": {
            "lastFullRefresh": (datetime.now() - timedelta(hours=12)).isoformat(),
            "connectedSources": ["yfinance", "alpha_vantage"],
            "pendingJobs": random.randint(0, 5)
        }
    })

@health_bp.route('/model_health', methods=['GET'])
def get_model_health():
    """מחזיר מידע על בריאות מודל המכונה"""
    
    # מידע לדוגמה על בריאות המודל
    last_train = datetime.now() - timedelta(hours=random.randint(1, 48))
    
    return jsonify({
        "status": "healthy",
        "currentModel": "lightgbm_v3.2",
        "lastTrained": last_train.isoformat(),
        "accuracy": random.uniform(0.65, 0.85),
        "f1Score": random.uniform(0.60, 0.80),
        "precision": random.uniform(0.65, 0.85),
        "recall": random.uniform(0.60, 0.85),
        "featureCount": random.randint(30, 50),
        "errors": [],
        "warnings": [],
        "inferenceLatency": random.uniform(0.1, 2.5),
        "details": {
            "hyperparameters": {
                "learning_rate": 0.05,
                "max_depth": 5,
                "n_estimators": 200
            },
            "lastEvaluation": (datetime.now() - timedelta(hours=2)).isoformat(),
            "stabilityScore": random.uniform(90, 99),
            "driftDetected": False
        }
    })
