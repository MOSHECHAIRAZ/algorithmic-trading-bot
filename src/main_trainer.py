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
import traceback
from pathlib import Path
from dotenv import load_dotenv
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMClassifier
from src.feature_calculator import FeatureCalculator
from src.utils import archive_existing_file, load_system_config
from src.simulation_engine import run_trading_simulation
# ייבוא ישיר של ProjectOrganizer
try:
    from src.utils.project_organizer import ProjectOrganizer
except ImportError:
    import importlib.util
    import sys
    BASE_DIR = Path(__file__).parent.parent
    spec = importlib.util.spec_from_file_location(
        "project_organizer", 
        BASE_DIR / "src" / "utils" / "project_organizer.py"
    )
    project_organizer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project_organizer_module)
    ProjectOrganizer = project_organizer_module.ProjectOrganizer

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
            df = pd.read_csv(feature_data_path, parse_dates=['date'])
            df.set_index('date', inplace=True)
            return df
        else:
            # טעינת נתונים מעובדים ויצירת פיצ'רים בזמן אמת
            processed_data_path = config['system_paths'].get('processed_data', 'data/processed/SPY_processed.csv')
            logging.info(f"Feature file not found. Loading processed data from {processed_data_path}")
            if not os.path.exists(processed_data_path):
                raise FileNotFoundError(f"Processed data file not found: {processed_data_path}")
                
            df = pd.read_csv(processed_data_path, parse_dates=['date'])
            df.set_index('date', inplace=True)
            
            # שמירה של תאריך אחרון לבדיקה
            last_date = df.index.max()
            logging.info(f"Last date in data: {last_date}")
            
            # חישוב פיצ'רים באמצעות החישוב המפורט
            logging.info("Computing features using FeatureCalculator")
            calculator = FeatureCalculator(df)
            df = calculator.calculate_all_features()
            
            # חישוב ישיר של תווית המטרה
            logging.info("Creating target labels")
            horizon = config.get('optuna_param_limits', {}).get('horizon', {}).get('fixed_value', 5)
            threshold = config.get('optuna_param_limits', {}).get('threshold', {}).get('fixed_value', 0.01)
            logging.info(f"Using horizon={horizon}, threshold={threshold} for labels")
            
            df['return_forward'] = df['close'].pct_change(periods=horizon).shift(-horizon)
            df['target'] = (df['return_forward'] > threshold).astype(int)
            
            # שמירת הפיצ'רים למען עיבוד עתידי מהיר
            df.reset_index(inplace=True)  # החזרת עמודת תאריך
            feature_dir = os.path.dirname(feature_data_path)
            os.makedirs(feature_dir, exist_ok=True)
            logging.info(f"Saving computed features to {feature_data_path}")
            df.to_csv(feature_data_path, index=False)
            
            # הגדרת אינדקס מחדש
            df.set_index('date', inplace=True)
            return df
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        raise


class OptunaTrainer:
    """
    מחלקה לאימון ואופטימיזציה של מודלים באמצעות Optuna.
    """
    def __init__(self, df):
        """
        :param df: DataFrame with features and target
        """
        self.df = df.copy()
        # Ensure DataFrame is sorted by date (critical for time series split)
        if not self.df.index.is_monotonic_increasing:
            logging.warning("DataFrame index is not sorted. Sorting by date...")
            self.df.sort_index(inplace=True)
        
        # Drop rows with missing values
        self.df.dropna(inplace=True)
        
        # Get feature columns (exclude special columns)
        exclude_cols = ['target', 'return_forward', 'close', 'open', 'high', 'low', 'volume', 'vix_close']
        self.feature_cols = [col for col in self.df.columns if col not in exclude_cols]
        
        logging.info(f"Initialized trainer with {len(self.df)} rows and {len(self.feature_cols)} features")
        
        # Print data range
        logging.info(f"Data range: {self.df.index.min()} to {self.df.index.max()}")
        
        # Split configuration
        self.test_size = config['training_params']['test_size_split']
        # Use time-series split 
        self.cv_splits = config['training_params']['cv_splits']
        self.n_trials = config['training_params']['n_trials']
        self.n_startup_trials = config['training_params']['n_startup_trials']
        
        # Get the last X% of data for test set
        test_size_percent = self.test_size / 100
        test_idx = int(len(self.df) * (1 - test_size_percent))
        
        self.X_train = self.df.iloc[:test_idx][self.feature_cols]
        self.y_train = self.df.iloc[:test_idx]['target']
        self.X_test = self.df.iloc[test_idx:][self.feature_cols]
        self.y_test = self.df.iloc[test_idx:]['target']
        
        # Create TimeSeriesSplit for cross-validation
        self.tscv = TimeSeriesSplit(n_splits=self.cv_splits)
        
        logging.info(f"Training set: {len(self.X_train)} rows, Test set: {len(self.X_test)} rows")
        logging.info(f"Target distribution in training: {self.y_train.value_counts(normalize=True).to_dict()}")
        logging.info(f"Target distribution in test: {self.y_test.value_counts(normalize=True).to_dict()}")
        
        # Save feature importances
        self.features_info = {}
        
        # Initialize default parameters from config
        param_limits = config.get('optuna_param_limits', {})
        
        # Get fixed parameters that won't be optimized
        self.fixed_params = {}
        for param_name, param_dict in param_limits.items():
            if param_dict.get('optimize', True) == False:
                self.fixed_params[param_name] = param_dict.get('fixed_value')
        
        logging.info(f"Fixed parameters (not optimized): {self.fixed_params}")
    
    def _get_model_params(self, trial):
        """
        מחזיר פרמטרים למודל, מתוך הפרמטרים הקבועים וכן ה-trial של optuna.
        """
        param_limits = config.get('optuna_param_limits', {})
        
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'verbosity': -1,
            'boosting_type': 'gbdt',
        }
        
        # Add fixed params directly
        params.update(self.fixed_params)
        
        # Add params from trial - only those not fixed
        for param_name, param_dict in param_limits.items():
            if param_name not in self.fixed_params and param_dict.get('optimize', True) == True:
                if param_name == 'learning_rate':
                    params['learning_rate'] = trial.suggest_float(
                        'learning_rate', 
                        param_dict.get('min', 0.001), 
                        param_dict.get('max', 0.1),
                        log=True
                    )
                elif param_name == 'n_estimators':
                    params['n_estimators'] = trial.suggest_int(
                        'n_estimators', 
                        param_dict.get('min', 50), 
                        param_dict.get('max', 300)
                    )
                elif param_name == 'max_depth':
                    params['max_depth'] = trial.suggest_int(
                        'max_depth', 
                        param_dict.get('min', 3), 
                        param_dict.get('max', 10)
                    )
                elif param_name == 'top_n_features':
                    params['top_n_features'] = trial.suggest_int(
                        'top_n_features', 
                        param_dict.get('min', 20), 
                        param_dict.get('max', 100)
                    )
        
        return params
    
    def _objective(self, trial):
        """
        פונקציית אופטימיזציה עבור Optuna.
        """
        params = self._get_model_params(trial)
        top_n_features = params.pop('top_n_features', None)
        
        # Feature selection - use only top N features if specified
        if top_n_features is not None and len(self.feature_cols) > top_n_features:
            # Use a simple initial model to rank features
            # TODO: move this outside the objective function if it's slow
            init_model = LGBMClassifier(
                objective='binary',
                verbosity=-1,
                n_estimators=50,
                max_depth=3,
                learning_rate=0.1,
                random_state=42
            )
            
            # Fit the simple model
            init_model.fit(self.X_train, self.y_train)
            
            # Get top features
            feature_importances = dict(zip(self.feature_cols, init_model.feature_importances_))
            top_features = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)[:top_n_features]
            selected_features = [f[0] for f in top_features]
            
            X_train_selected = self.X_train[selected_features]
            trial.set_user_attr("selected_features", selected_features)
        else:
            X_train_selected = self.X_train
            selected_features = self.feature_cols
            trial.set_user_attr("selected_features", selected_features)
        
        # Create and fit model
        model = LGBMClassifier(**params, random_state=42)
        
        # Cross-validation scores
        cv_scores = []
        for train_idx, val_idx in self.tscv.split(X_train_selected):
            X_fold_train, X_fold_val = X_train_selected.iloc[train_idx], X_train_selected.iloc[val_idx]
            y_fold_train, y_fold_val = self.y_train.iloc[train_idx], self.y_train.iloc[val_idx]
            
            model.fit(X_fold_train, y_fold_train, eval_set=[(X_fold_val, y_fold_val)], 
                    early_stopping_rounds=50, verbose=False)
            
            y_pred = model.predict(X_fold_val)
            accuracy = accuracy_score(y_fold_val, y_pred)
            cv_scores.append(accuracy)
        
        # Calculate mean validation score
        mean_accuracy = np.mean(cv_scores)
        
        # Final model training on full training set
        model.fit(X_train_selected, self.y_train)
        
        # Backtest simulation on test set
        if len(self.X_test) > 0:
            X_test_selected = self.X_test[selected_features]
            test_pred_proba = model.predict_proba(X_test_selected)[:, 1]
            
            # Add model predictions to test data for simulation
            test_df = self.df.iloc[len(self.X_train):].copy()
            test_df['prediction_proba'] = test_pred_proba
            
            # Log some predictions
            test_pred = (test_pred_proba > 0.5).astype(int)
            accuracy = accuracy_score(self.y_test, test_pred)
            trial.set_user_attr("test_accuracy", float(accuracy))
            
            # Get other fixed parameters for simulation
            sim_params = {}
            for param, param_dict in config.get('optuna_param_limits', {}).items():
                if param in ['threshold', 'stop_loss_pct', 'take_profit_pct', 'risk_per_trade']:
                    if param in self.fixed_params:
                        sim_params[param] = self.fixed_params[param]
                    else:
                        sim_params[param] = trial.suggest_float(
                            param, 
                            param_dict.get('min'), 
                            param_dict.get('max')
                        )
            
            # Run trading simulation
            logging.info(f"Running backtest with parameters: {sim_params}")
            backtest_results = run_trading_simulation(
                test_df,
                threshold=sim_params.get('threshold', 0.01),
                stop_loss_pct=sim_params.get('stop_loss_pct', 1.0),
                take_profit_pct=sim_params.get('take_profit_pct', 2.0),
                risk_per_trade=sim_params.get('risk_per_trade', 0.01)
            )
            
            # Save metrics as trial attributes
            for metric, value in backtest_results.items():
                if isinstance(value, (int, float)):
                    trial.set_user_attr(f"backtest_{metric}", float(value))
            
            # Return multiple objectives
            target_metric = config['training_params'].get('optuna_target_metric', 'multi_objective')
            
            if target_metric == 'multi_objective':
                # We'll optimize for multiple objectives together
                return (
                    backtest_results.get('profit_factor', 0),  # Higher is better
                    backtest_results.get('sharpe_ratio', 0),   # Higher is better
                    mean_accuracy                             # Higher is better
                )
            elif target_metric == 'profit_factor':
                return backtest_results.get('profit_factor', 0)
            elif target_metric == 'sharpe_ratio':
                return backtest_results.get('sharpe_ratio', 0)
            elif target_metric == 'accuracy':
                return mean_accuracy
            else:
                return backtest_results.get('total_return', 0)
        
        # If no test data or can't run simulation, just return CV score
        return mean_accuracy
    
    def run_optimization(self):
        """
        הרצה של אופטימיזציה באמצעות Optuna.
        """
        logging.info(f"Starting Optuna optimization with {self.n_trials} trials")
        
        target_metric = config['training_params'].get('optuna_target_metric', 'multi_objective')
        
        if target_metric == 'multi_objective':
            study = optuna.create_study(
                directions=['maximize', 'maximize', 'maximize'],
                sampler=optuna.samplers.TPESampler(n_startup_trials=self.n_startup_trials)
            )
        else:
            study = optuna.create_study(
                direction='maximize',
                sampler=optuna.samplers.TPESampler(n_startup_trials=self.n_startup_trials)
            )
        
        study.optimize(self._objective, n_trials=self.n_trials)
        
        # Get best trial
        if target_metric == 'multi_objective':
            # For multi-objective, we'll pick the trial with best profit factor
            best_trials = study.best_trials
            if best_trials:
                # Sort by profit factor (first objective)
                best_trials_by_profit = sorted(best_trials, key=lambda t: t.values[0], reverse=True)
                best_trial = best_trials_by_profit[0]
            else:
                # Fallback to any completed trial
                completed_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
                if completed_trials:
                    best_trial = completed_trials[0]
                else:
                    raise ValueError("No completed trials found")
        else:
            best_trial = study.best_trial
        
        logging.info(f"Best trial: #{best_trial.number}")
        logging.info(f"Best parameters: {best_trial.params}")
        
        for key, value in best_trial.user_attrs.items():
            if key.startswith("backtest_"):
                logging.info(f"  {key.replace('backtest_', '')}: {value}")
        
        # Get selected features
        selected_features = best_trial.user_attrs.get("selected_features", self.feature_cols)
        
        # Train final model
        final_params = self._get_model_params(best_trial)
        # Remove non-model parameters
        if 'top_n_features' in final_params:
            final_params.pop('top_n_features')
        
        final_model = LGBMClassifier(**final_params, random_state=42)
        final_model.fit(self.X_train[selected_features], self.y_train)
        
        # Create a scaler for the selected features
        scaler = StandardScaler()
        scaler.fit(self.X_train[selected_features])
        
        # Calculate feature importances
        feature_importances = dict(zip(selected_features, final_model.feature_importances_))
        sorted_importances = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)
        
        logging.info("Feature importances:")
        for feature, importance in sorted_importances:
            logging.info(f"  {feature}: {importance}")
            self.features_info[feature] = importance
        
        # Test predictions
        X_test_selected = self.X_test[selected_features]
        y_pred = final_model.predict(X_test_selected)
        
        # Calculate accuracy
        accuracy = accuracy_score(self.y_test, y_pred)
        logging.info(f"Test accuracy: {accuracy:.4f}")
        
        # Full classification report
        report = classification_report(self.y_test, y_pred)
        logging.info(f"Classification report:\n{report}")
        
        # Create final best parameters dict with all values
        best_params = {
            'model_params': final_params,
            'selected_features': selected_features,
            'feature_importances': feature_importances,
            'accuracy': float(accuracy)
        }
        
        # Add simulation parameters
        sim_params = {}
        for param in ['threshold', 'stop_loss_pct', 'take_profit_pct', 'risk_per_trade']:
            if param in best_trial.params:
                sim_params[param] = best_trial.params[param]
            elif param in self.fixed_params:
                sim_params[param] = self.fixed_params[param]
        
        best_params['sim_params'] = sim_params
        
        # Save model metrics
        metrics = {
            'accuracy': float(accuracy),
            'feature_importances': {str(k): float(v) for k, v in feature_importances.items()},
            'params': best_params,
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_start': self.df.index.min().strftime('%Y-%m-%d'),
            'data_end': self.df.index.max().strftime('%Y-%m-%d'),
            'training_samples': len(self.X_train),
            'test_samples': len(self.X_test),
        }
        
        # Add backtest metrics
        for key, value in best_trial.user_attrs.items():
            if key.startswith("backtest_"):
                metrics[key.replace('backtest_', '')] = value
        
        return final_model, scaler, best_params, metrics


def main():
    try:
        logging.info("===== Model Training Started =====")
        
        # טעינת נתונים
        df = load_data()
        
        # בדיקה אם יש מספיק נתונים
        min_rows = 100  # מינימום שורות נדרש
        if len(df) < min_rows:
            logging.error(f"Not enough data for training. Found {len(df)} rows, minimum required: {min_rows}")
            return
        
        # אימון ואופטימיזציה
        trainer = OptunaTrainer(df)
        champion_model, scaler, best_params, metrics = trainer.run_optimization()
        
        # שמירת המודל ומידע נלווה
        model_path = config['system_paths']['champion_model']
        scaler_path = config['system_paths']['champion_scaler']
        config_path = config['system_paths']['champion_config']
        
        # יצירת תיקיות נדרשות
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # גיבוי קבצים קיימים
        archive_existing_file(model_path)
        archive_existing_file(scaler_path)
        archive_existing_file(config_path)
        
        # שמירת מודל חדש
        logging.info(f"Saving champion model to {model_path}")
        joblib.dump(champion_model, model_path)
        
        # שמירת הסקיילר
        logging.info(f"Saving feature scaler to {scaler_path}")
        joblib.dump(scaler, scaler_path)
        
        # שמירת קונפיגורציה של המודל
        logging.info(f"Saving model configuration to {config_path}")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(best_params, f, indent=4, ensure_ascii=False)
        
        # שמירת סיכום אימון
        save_training_summary(metrics)
        
        logging.info("===== Model Training Completed Successfully =====")
        
        # ארגון אוטומטי של הפרויקט לאחר סיום האימון
        try:
            organizer = ProjectOrganizer()
            organizer.organize_all()
            logging.info("Project organization completed")
        except Exception as org_error:
            logging.warning(f"Project organization failed: {org_error}")
        
    except Exception as e:
        logging.error(f"Error in training process: {e}")
        logging.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
