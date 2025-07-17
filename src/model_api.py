"""
Flask API exposing the trained ML model for predictions.
Refactored for simplicity and consistency with the new training pipeline.
"""
import sys
import os
import logging
import json
import joblib
import pandas as pd
import numpy as np
import traceback
from flask import Flask, request, jsonify

# הוספת הנתיב הראשי של הפרויקט כדי לאפשר ייבוא מ-src
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.utils import load_system_config
from src.feature_calculator import FeatureCalculator

# --- טעינת קונפיגורציה מרכזית ---
config = load_system_config()
paths = config['system_paths']
api_settings = config['api_settings']

# --- הגדרות לוגינג ---
log_path = os.path.join(BASE_DIR, 'logs', 'model_api.log')
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler(log_path, encoding='utf-8'), logging.StreamHandler(sys.stdout)]
)

app = Flask(__name__)

# --- Globals for model, scaler, and config ---
model = None
scaler = None
model_config = None
selected_features = []


def load_artifacts():
    """Loads the champion model, scaler, and configuration."""
    global model, scaler, model_config, selected_features
    try:
        logging.info(f"Loading model from: {paths['champion_model']}")
        model = joblib.load(paths['champion_model'])
        
        logging.info(f"Loading scaler from: {paths['champion_scaler']}")
        scaler = joblib.load(paths['champion_scaler'])
        
        logging.info(f"Loading model config from: {paths['champion_config']}")
        with open(paths['champion_config'], 'r', encoding='utf-8') as f:
            model_config = json.load(f)
        
        selected_features = model_config['selected_features']
        logging.info(f'Successfully loaded model with {len(selected_features)} features.')
        return True
    except Exception as e:
        logging.error(f"FATAL: Error loading model artifacts: {e}", exc_info=True)
        return False

@app.route('/status', methods=['GET'])
def status():
    """Checks if the model is loaded and the API is responsive."""
    model_loaded = model is not None and model_config is not None
    return jsonify({
        "status": "ok",
        "model_loaded": model_loaded,
        "features_count": len(selected_features) if model_loaded else 0
    })

@app.route('/reload', methods=['POST'])
def reload():
    """Triggers a reload of the model, scaler, and config."""
    logging.info("Received request to reload artifacts...")
    if load_artifacts():
        return jsonify({"status": "ok", "message": "Artifacts reloaded successfully."})
    else:
        return jsonify({"status": "error", "message": "Failed to reload artifacts."}), 500

@app.route('/predict', methods=['POST'])
def predict():
    """Receives historical data, computes features, and returns a prediction."""
    if not all([model, scaler, model_config]):
        logging.warning("Model artifacts not loaded. Attempting automatic reload...")
        load_artifacts()
        if not all([model, scaler, model_config]):
            return jsonify({"error": "Model, scaler, or config not loaded. Please check logs or /reload."}), 503

    try:
        data = request.get_json()
        if 'historical' not in data or not isinstance(data['historical'], list) or not data['historical']:
            return jsonify({"error": "Missing or invalid 'historical' data. Expecting a non-empty list of objects."}), 400
        
        historical_df = pd.DataFrame(data['historical'])
        # ה-agent שולח תאריך בפורמט ISO, נמיר אותו
        historical_df['date'] = pd.to_datetime(historical_df['date'])
        historical_df.set_index('date', inplace=True)

        # 1. חישוב כל הפיצ'רים עם המחשבון המאוחד
        fc = FeatureCalculator()
        features_df = fc.add_all_possible_indicators(historical_df.copy(), verbose=False)
        features_df_numeric = features_df.select_dtypes(include=np.number).fillna(0)
        
        # 2. הכנת ה-DataFrame הסופי למודל
        # השורה האחרונה מכילה את הפיצ'רים העדכניים ביותר
        latest_features = features_df_numeric.iloc[[-1]]

        # יישור לעמודות שהמודל מכיר, ומילוי ערכים חסרים ב-0
        X_today = pd.DataFrame(columns=selected_features)
        X_today = pd.concat([X_today, latest_features], sort=False)
        X_today = X_today[selected_features].fillna(0)

        # 3. נירמול וחיזוי
        X_scaled = scaler.transform(X_today)
        prediction_proba = model.predict_proba(X_scaled)[0]
        
        # החזרת תוצאה
        prediction = int(np.argmax(prediction_proba))
        final_prediction_label = "Buy" if prediction == 1 else "Hold"
        
        # קח את ערך ה-ATR העדכני ביותר מהפיצ'רים שחושבו
        atr_col_name = next((col for col in latest_features.columns if 'ATR_' in col.upper()), None)
        atr_value = latest_features[atr_col_name].iloc[0] if atr_col_name else None

        # Unified response: prediction, ATR, risk_params, contract
        risk_params = model_config.get('risk_params', {})
        contract = model_config.get('contract', {})
        return jsonify({
            "prediction": final_prediction_label,
            "probability_hold": float(prediction_proba[0]),
            "probability_buy": float(prediction_proba[1]),
            "atr_value": float(atr_value) if pd.notna(atr_value) else None,
            "risk_params": risk_params,
            "contract": contract
        })

    except Exception as e:
        logging.error(f"Prediction error: {e}", exc_info=True)
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

# --- נקודת קצה חדשה: קבלת פרמטרי סיכון מהקונפיגורציה של המודל ---
@app.route('/risk_params', methods=['GET'])
def get_risk_params():
    try:
        global model_config
        if model_config is None:
            raise ValueError("Model config not loaded in memory.")
        risk_params = model_config.get('risk_params', {})
        contract = model_config.get('contract', {})
        return jsonify({"risk_params": risk_params, "contract": contract})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    load_artifacts()
    app.run(host=api_settings['host'], port=api_settings['port'])
