# main_trainer.py (גרסה סופית, שלמה ומתוקנת עם תמיכה בפרמטרים קבועים)
import pandas as pd
import numpy as np
import joblib
import optuna
from sklearn.model_selection import TimeSeriesSplit
from datetime import datetime
import json
import logging
import os
import sys
import warnings
from pathlib import Path
from dotenv import load_dotenv
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMClassifier
from src.feature_calculator import FeatureCalculator
from src.utils import archive_existing_file, load_system_config
from src.simulation_engine import run_trading_simulation

# --- הגדרות לוגינג ---
log_file = 'logs/main_trainer_output.log'
os.makedirs(os.path.dirname(log_file), exist_ok=True)
archive_existing_file(log_file)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler(sys.stdout)]
)
warnings.filterwarnings("ignore")
load_dotenv()

# --- טעינת קונפיגורציה מרכזית ---
config = load_system_config()

def save_training_summary(metrics: dict):
    model_dir = os.path.dirname(config['system_paths']['champion_model'])
    summary_path = os.path.join(model_dir, 'training_summary.json')
    archive_existing_file(summary_path)
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False)
    logging.info(f"Training summary saved to {summary_path}")

def load_data():
    try:
        # בדיקה אם קובץ פיצ'רים קיים
        feature_data_path = config['system_paths'].get('feature_data', 'data/processed/SPY_features.csv')
        if os.path.exists(feature_data_path):
            logging.info(f"Loading pre-computed features from {feature_data_path}")
            df = pd.read_csv(feature_data_path, parse_dates=['date'], index_col='date')
        else:
            # אחרת טען את הנתונים המעובדים הבסיסיים
            logging.info("Feature file not found. Loading base processed data.")
            df = pd.read_csv('data/processed/SPY_processed.csv', parse_dates=['date'], index_col='date')
        
        # סינון לפי שנים
        years_of_data = config.get('training_params', {}).get('years_of_data', 15)
        start_date = df.index.max() - pd.DateOffset(years=years_of_data)
        df = df[df.index >= start_date]
        logging.info(f"Loaded data from {df.index.min().date()} to {df.index.max().date()}. Shape: {df.shape}")
        return df
    except Exception as e:
        logging.error(f"Error loading data: {e}", exc_info=True)
        return None

def get_dynamic_target(df_close: pd.Series, horizon: int, threshold: float):
    future_return = df_close.shift(-horizon) / df_close - 1
    return (future_return > threshold).astype(int)

def rank_features(X: pd.DataFrame, y: pd.Series, top_n: int):
    model = LGBMClassifier(n_estimators=100, random_state=42, verbosity=-1, n_jobs=-1)
    model.fit(X, y)
    importances = pd.Series(model.feature_importances_, index=X.columns)
    return importances.nlargest(top_n).index.tolist()

def objective(trial, df_raw, X_features_full, split_idx):
    param_limits = config.get('optuna_param_limits', {})
    
    # --- Suggest Hyperparameters (Dynamic or Fixed) ---
    def get_param(param_name, param_type='float', log=False):
        p_config = param_limits.get(param_name, {})
        # בודק אם הפרמטר קיים במפתחות ואם הדגל 'optimize' דלוק
        if param_name in param_limits and p_config.get('optimize', True):
            min_val, max_val = p_config.get('min'), p_config.get('max')
            if param_type == 'int':
                return trial.suggest_int(param_name, int(min_val), int(max_val))
            return trial.suggest_float(param_name, min_val, max_val, log=log)
        else:
            # מחזיר את הערך הקבוע מהשדה 'fixed_value' עם המרה לסוג הנתונים הנכון
            fixed_value = p_config.get('fixed_value', p_config.get('min', 0))
            if param_type == 'int':
                return int(fixed_value)
            else:
                return float(fixed_value)

    horizon = get_param('horizon', 'int')
    threshold = get_param('threshold', 'float')
    top_n = get_param('top_n_features', 'int')
    stop_loss_pct = get_param('stop_loss_pct', 'float')
    take_profit_pct = get_param('take_profit_pct', 'float')
    risk_per_trade = get_param('risk_per_trade', 'float')
    learning_rate = get_param('learning_rate', 'float', log=True)
    n_estimators = get_param('n_estimators', 'int')
    max_depth = get_param('max_depth', 'int')
    
    # --- Run Cross-Validation Simulation ---
    y_target = get_dynamic_target(df_raw['close'], horizon, threshold)
    X_train, y_train = X_features_full.iloc[:split_idx].align(y_target, join='inner', axis=0)

    cv_splits = config['training_params'].get('cv_splits', 5)
    if len(X_train) < cv_splits * 2: return -999.0

    all_metrics = []
    tscv = TimeSeriesSplit(n_splits=cv_splits)
    for train_idx, val_idx in tscv.split(X_train):
        X_model_train, X_strategy_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_model_train, y_strategy_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
        if y_model_train.nunique() < 2 or (y_model_train == 1).sum() < 5:
            continue
        selected_features = rank_features(X_model_train, y_model_train, top_n=top_n)
        model_params = {'n_estimators': n_estimators, 'max_depth': max_depth, 'learning_rate': learning_rate, 'random_state': 42, 'verbosity': -1, 'n_jobs': -1}
        scale_pos_weight = (y_model_train == 0).sum() / max(1, (y_model_train == 1).sum())
        model = LGBMClassifier(**model_params, scale_pos_weight=scale_pos_weight)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_model_train[selected_features])
        X_val_scaled = scaler.transform(X_strategy_val[selected_features])
        model.fit(X_train_scaled, y_model_train)
        predictions = pd.Series(model.predict(X_val_scaled), index=X_strategy_val.index)
        backtest_config = config['backtest_params']
        _, _, metrics = run_trading_simulation(
            prices_df=df_raw.loc[X_strategy_val.index].copy(),
            predictions=predictions,
            commission=backtest_config.get('commission', 0.001),
            slippage=backtest_config.get('slippage', 0.0005),
            initial_balance=backtest_config.get('initial_balance', 100000),
            sl_pct=stop_loss_pct / 100.0,
            tp_pct=take_profit_pct / 100.0,
            risk_per_trade=risk_per_trade
        )
        all_metrics.append(metrics)

    selected_objective = config.get('training_params', {}).get('optuna_target_metric', 'multi_objective')

    if not all_metrics:
        return -5.0 if selected_objective != 'multi_objective' else (-5.0, -5.0)

    if selected_objective == 'multi_objective':
        avg_return = float(np.mean([m.get('total_return', -2.0) for m in all_metrics]))
        avg_sharpe = float(np.mean([m.get('sharpe_ratio', -2.0) for m in all_metrics]))
        return avg_return, avg_sharpe
    else:
        scores = [m.get(selected_objective, -2.0) for m in all_metrics]
        return float(np.mean(scores))

def main():
    logging.info("--- Starting New Training Pipeline ---")
    run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    df_raw = load_data()
    if df_raw is None: return

    # הגדרת param_limits גם בפונקציה main
    param_limits = config.get('optuna_param_limits', {})

    logging.info("Step 1: Preparing features...")
    # כבר טענו את הנתונים עם הפיצ'רים ב-load_data()
    # נבצע רק ניקוי וסינון נתונים
    X_features_full = df_raw.copy()
    X_features_full = X_features_full.select_dtypes(include=np.number).replace([np.inf, -np.inf], 0).fillna(0)
    logging.info(f"Feature dataset ready with {X_features_full.shape[1]} columns.")
    
    test_size_split = config['training_params']['test_size_split'] / 100
    split_idx = int(len(X_features_full) * (1 - test_size_split))

    n_startup_trials = config.get('training_params', {}).get('n_startup_trials', 10)
    sampler = optuna.samplers.TPESampler(n_startup_trials=n_startup_trials)
    logging.info(f"Using TPESampler with {n_startup_trials} startup trials.")

    logging.info("Step 2: Setting up and running Optuna study...")
    selected_objective = config.get('training_params', {}).get('optuna_target_metric', 'multi_objective')
    study_name = f"spy_strategy_{selected_objective}_{run_timestamp}"
    logging.info(f"Using Optuna study name: {study_name}")

    study_directions = ['maximize', 'maximize'] if selected_objective == 'multi_objective' else ['maximize']
    logging.info(f"Setting up Optuna study with objective: '{selected_objective}' and directions: {study_directions}")

    study = optuna.create_study(
        study_name=study_name,
        storage=f"sqlite:///db/spy_strategy_optimization.db",
        directions=study_directions,
        sampler=sampler,
        load_if_exists=False # מתחילים תמיד study חדש כדי להתאים ל-timestamp בשם
    )
    study.optimize(lambda trial: objective(trial, df_raw, X_features_full, split_idx), n_trials=config['training_params']['n_trials'], show_progress_bar=True)

    if selected_objective == 'multi_objective':
        best_trials = study.best_trials
        logging.info(f"Optuna finished. Found {len(best_trials)} best trials in the Pareto front.")
        if not best_trials:
             logging.error("No best trials found for multi-objective! Aborting.")
             return
        best_trial = max(best_trials, key=lambda t: t.values[1])
        logging.info(f'--- Selected Best Trial (by Sharpe) ---\nReturn: {best_trial.values[0]:.4f}, Sharpe: {best_trial.values[1]:.4f}')
    else:
        best_trial = study.best_trial
        logging.info(f'--- Optuna Finished ---\nBest Score for {selected_objective}: {best_trial.value:.4f}')

    best_params = best_trial.params
    
    # הוספת הפרמטרים הקבועים לתוצאות
    all_params = {}
    for param_name, param_config in param_limits.items():
        if param_name in best_params:
            # פרמטר שעבר אופטימיזציה
            all_params[param_name] = {
                "value": best_params[param_name],
                "optimized": True
            }
        else:
            # פרמטר קבוע
            all_params[param_name] = {
                "value": param_config.get('fixed_value', param_config.get('min', 0)),
                "optimized": False
            }
    
    logging.info(f'Best Parameters (optimized + fixed): {json.dumps(all_params, indent=2)}')
    logging.info(f'Original Best Parameters (optimized only): {json.dumps(best_params, indent=2)}')

    # --- Final model training on all training data with best params ---
    final_horizon, final_threshold = best_params['horizon'], best_params['threshold']
    y_final = get_dynamic_target(df_raw['close'], final_horizon, final_threshold)
    X_train, X_test = X_features_full.iloc[:split_idx], X_features_full.iloc[split_idx:]
    y_train, y_test = y_final.iloc[:split_idx], y_final.iloc[split_idx:]
    X_train, y_train = X_train.align(y_train, join='inner', axis=0)
    X_test, y_test = X_test.align(y_test, join='inner', axis=0)

    # קח את top_n_features מהקונפיגורציה או מ-best_params
    top_n_features = best_params.get('top_n_features', 
                                     int(param_limits['top_n_features'].get('fixed_value', 30)))
    
    final_selected_features = rank_features(X_train, y_train, top_n=top_n_features)
    X_train_final, X_test_final = X_train[final_selected_features], X_test[final_selected_features]
    
    final_model_params = {}
    # קח את הפרמטרים מ-best_params או מהקונפיגורציה
    for param in ['n_estimators', 'max_depth', 'learning_rate']:
        if param in best_params:
            final_model_params[param] = best_params[param]
        elif param in param_limits:
            if param == 'n_estimators' or param == 'max_depth':
                final_model_params[param] = int(param_limits[param].get('fixed_value', 300 if param == 'n_estimators' else 6))
            else:
                final_model_params[param] = float(param_limits[param].get('fixed_value', 0.1))
    
    final_scale_pos_weight = (y_train == 0).sum() / max(1, (y_train == 1).sum())
    final_model = LGBMClassifier(**final_model_params, scale_pos_weight=final_scale_pos_weight, random_state=42, verbosity=-1)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_final)
    final_model.fit(X_train_scaled, y_train)

    X_test_scaled = scaler.transform(X_test_final)
    preds_test = final_model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, preds_test)
    report = classification_report(y_test, preds_test, output_dict=True, zero_division=0)
    logging.info(f'--- Final Performance on Test Set ---\nTest Accuracy: {accuracy:.4f}\n{classification_report(y_test, preds_test, zero_division=0)}')

    # --- Save candidate artifacts ---
    try:
        model_dir = Path('models')
        model_dir.mkdir(parents=True, exist_ok=True)
        candidate_model_path = model_dir / f'candidate_model_{run_timestamp}.pkl'
        candidate_scaler_path = model_dir / f'candidate_scaler_{run_timestamp}.pkl'
        candidate_config_path = model_dir / f'candidate_model_config_{run_timestamp}.json'

        joblib.dump(final_model, candidate_model_path)
        joblib.dump(scaler, candidate_scaler_path)
        logging.info(f"New candidate model saved: {candidate_model_path.name}")

        risk_params = {
            'stop_loss_pct': best_params.get('stop_loss_pct'),
            'take_profit_pct': best_params.get('take_profit_pct'),
            'risk_per_trade': best_params.get('risk_per_trade')
        }
        final_config_data = {
            "training_run_timestamp": run_timestamp,
            "optuna_study_name": study_name,
            "selected_features": final_selected_features,
            "params": best_params,
            "scaler": True,
            "risk_params": risk_params,
            "contract": config.get('contract', {})
        }
        with open(candidate_config_path, 'w', encoding='utf-8') as f:
            json.dump(final_config_data, f, indent=2)
        logging.info(f"Candidate artifacts for run {run_timestamp} saved successfully.")

    except Exception as e:
        logging.error(f"Failed to save model artifacts: {e}", exc_info=True)
        sys.exit(1)

    training_summary = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "training_run_timestamp": run_timestamp,
        "optuna_study_name": study_name,
        "objective_function": selected_objective,
        "optuna_scores": best_trial.values,
        "test_accuracy": accuracy,
        "classification_report": report,
        "best_params": best_params,  # רק הפרמטרים המאופטמיזציה
        "all_params": all_params,    # כל הפרמטרים עם סימון אופטימיזציה
        "selected_features_list": final_selected_features
    }
    save_training_summary(training_summary)
    logging.info("--- Training pipeline finished successfully! ---")

if __name__ == "__main__":
    main()