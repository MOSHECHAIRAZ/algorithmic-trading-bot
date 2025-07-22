"""
routes/analysis.py - נתיבי ניתוח וסיכום

נתיבים הקשורים לסיכומי אימון, בדיקות אחוריות ואופטימיזציה
"""

from flask import Blueprint, jsonify, send_from_directory
import logging
import os
import json
from datetime import datetime, timedelta
import random

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

@analysis_bp.route('/training_summaries', methods=['GET'])
def get_training_summaries():
    """מחזיר סיכומי אימון של מודלים"""
    
    # מידע לדוגמה על סיכומי אימון
    summaries = []
    
    # יצירת 5 סיכומי אימון לדוגמה
    for i in range(5):
        days_ago = i * 2
        train_date = datetime.now() - timedelta(days=days_ago)
        accuracy = random.uniform(0.65, 0.85)
        f1 = random.uniform(0.60, 0.80)
        
        summary = {
            "id": f"train_{train_date.strftime('%Y%m%d')}_{i}",
            "model_type": "lightgbm",
            "version": f"v{3+i//2}.{i%3}",
            "train_date": train_date.isoformat(),
            "train_duration_seconds": random.randint(600, 3600),
            "accuracy": accuracy,
            "f1_score": f1,
            "precision": random.uniform(0.65, 0.85),
            "recall": random.uniform(0.60, 0.85),
            "feature_count": random.randint(30, 50),
            "hyperparameters": {
                "learning_rate": 0.05,
                "max_depth": 5,
                "n_estimators": 200,
                "colsample_bytree": 0.8
            },
            "training_dataset": {
                "start_date": (train_date - timedelta(days=365)).strftime("%Y-%m-%d"),
                "end_date": train_date.strftime("%Y-%m-%d"),
                "symbol": "SPY",
                "samples": random.randint(100000, 500000)
            },
            "validation_stats": {
                "confusion_matrix": [
                    [random.randint(300, 500), random.randint(50, 150)],
                    [random.randint(50, 150), random.randint(300, 500)]
                ],
                "roc_auc": random.uniform(0.65, 0.90)
            },
            "is_champion": i == 0
        }
        
        summaries.append(summary)
    
    return jsonify(summaries)

@analysis_bp.route('/backtests', methods=['GET'])
def get_backtest_list():
    """מחזיר רשימת בדיקות אחוריות"""
    
    # מידע לדוגמה על בדיקות אחוריות
    backtests = []
    
    # יצירת 10 בדיקות אחוריות לדוגמה
    for i in range(10):
        days_ago = i 
        test_date = datetime.now() - timedelta(days=days_ago)
        profit = random.uniform(-15, 25)
        
        backtest = {
            "id": f"backtest_{test_date.strftime('%Y%m%d')}_{i}",
            "file_name": f"backtest_{test_date.strftime('%Y%m%d')}_{i}.json",
            "model_version": f"v{3+i//3}.{i%3}",
            "test_date": test_date.isoformat(),
            "symbol": "SPY",
            "period": "1d",
            "start_date": (test_date - timedelta(days=180)).strftime("%Y-%m-%d"),
            "end_date": test_date.strftime("%Y-%m-%d"),
            "total_trades": random.randint(20, 100),
            "win_rate": random.uniform(0.4, 0.7),
            "profit_percent": profit,
            "max_drawdown": random.uniform(-15, -5),
            "sharpe_ratio": random.uniform(0.5, 2.5),
            "is_champion": i == 0
        }
        
        backtests.append(backtest)
    
    return jsonify(backtests)

@analysis_bp.route('/backtests/summary_champion.json', methods=['GET'])
def get_champion_backtest():
    """מחזיר מידע על בדיקה אחורית של המודל האלוף"""
    
    # מידע לדוגמה על בדיקה אחורית של המודל האלוף
    test_date = datetime.now() - timedelta(days=1)
    
    champion = {
        "id": f"backtest_champion_{test_date.strftime('%Y%m%d')}",
        "model_version": "v3.2",
        "test_date": test_date.isoformat(),
        "symbol": "SPY",
        "period": "1d",
        "start_date": (test_date - timedelta(days=180)).strftime("%Y-%m-%d"),
        "end_date": test_date.strftime("%Y-%m-%d"),
        "total_trades": 68,
        "win_rate": 0.65,
        "profit_percent": 18.7,
        "max_drawdown": -8.3,
        "sharpe_ratio": 1.8,
        "trades": [
            # לדוגמה, 10 עסקאות
            *[{
                "entry_date": (test_date - timedelta(days=180-i*5)).isoformat(),
                "exit_date": (test_date - timedelta(days=180-i*5-2)).isoformat(),
                "position": "LONG" if random.random() > 0.4 else "SHORT",
                "entry_price": random.uniform(350, 450),
                "exit_price": random.uniform(350, 450),
                "profit_percent": random.uniform(-5, 8),
                "duration_days": 2
            } for i in range(10)]
        ],
        "equity_curve": [
            # לדוגמה, נקודות בעקומת הון
            *[{
                "date": (test_date - timedelta(days=180-i*10)).isoformat(),
                "equity": 10000 * (1 + random.uniform(-0.15, 0.3))
            } for i in range(19)]
        ],
        "monthly_returns": {
            f"{(test_date - timedelta(days=30*i)).strftime('%Y-%m')}": random.uniform(-8, 12)
            for i in range(1, 7)
        }
    }
    
    return jsonify(champion)

@analysis_bp.route('/optuna', methods=['GET'])
def get_optuna_data():
    """מחזיר מידע על אופטימיזציה באמצעות Optuna"""
    
    # מידע לדוגמה על אופטימיזציה
    study_date = datetime.now() - timedelta(days=5)
    
    optuna_data = {
        "study_name": "lightgbm_optimization",
        "study_date": study_date.isoformat(),
        "n_trials": 100,
        "best_trial": 78,
        "best_value": 0.83,
        "metric": "f1_score",
        "duration_hours": 5.3,
        "parameters_importance": {
            "learning_rate": 0.35,
            "max_depth": 0.25,
            "n_estimators": 0.15,
            "min_child_samples": 0.1,
            "subsample": 0.08,
            "colsample_bytree": 0.07
        },
        "trials": [
            # לדוגמה, 10 ניסיונות
            *[{
                "trial_id": i,
                "value": random.uniform(0.5, 0.83),
                "params": {
                    "learning_rate": random.uniform(0.01, 0.1),
                    "max_depth": random.randint(3, 10),
                    "n_estimators": random.randint(100, 500),
                    "min_child_samples": random.randint(5, 30),
                    "subsample": random.uniform(0.6, 1.0),
                    "colsample_bytree": random.uniform(0.6, 1.0)
                }
            } for i in range(10)]
        ],
        "param_slice": {
            "learning_rate": [
                *[(round(0.01 + i*0.01, 2), random.uniform(0.5, 0.83)) for i in range(10)]
            ],
            "max_depth": [
                *[(i, random.uniform(0.5, 0.83)) for i in range(3, 13)]
            ]
        }
    }
    
    return jsonify(optuna_data)
