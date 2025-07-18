"""
Model Training Module for Algorithmic Trading Bot

This module is responsible for training machine learning models using scikit-learn,
lightgbm, and optuna for hyperparameter optimization. It handles data loading,
preprocessing, feature selection, model training, evaluation, and saving.

Author: GitHub Copilot
Date: Created based on project instructions
"""

import os
import json
import logging
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

# ML libraries
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
import lightgbm as lgb
import optuna
from optuna.samplers import TPESampler

# Add parent directory to path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_collection import load_system_config, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/model_training.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('model_training')

class ModelTrainer:
    """
    Class for training and optimizing trading models
    """
    
    def __init__(self, config=None):
        """
        Initialize the model trainer with configuration
        
        Args:
            config (dict, optional): System configuration. If None, loads from file.
        """
        self.config = config if config else load_system_config()
        ensure_directories(self.config)
        
        # Set paths for data and models
        self.feature_data_path = self.config['system_paths'].get('feature_data', 'data/processed/SPY_features.csv')
        self.model_path = self.config['system_paths'].get('champion_model', 'models/champion_model.pkl')
        self.scaler_path = self.config['system_paths'].get('champion_scaler', 'models/champion_scaler.pkl')
        self.model_config_path = self.config['system_paths'].get('champion_config', 'models/champion_model_config.json')
        
        # Initialize other attributes
        self.feature_data = None
        self.X_train = None
        self.X_val = None
        self.X_test = None
        self.y_train = None
        self.y_val = None
        self.y_test = None
        self.best_model = None
        self.best_params = None
        self.scaler = None
        self.feature_importance = None
        self.selected_features = None
        
        # Set training parameters
        self.n_trials = self.config['training_params'].get('n_trials', 100)
        self.test_size = self.config['training_params'].get('test_size_split', 20) / 100
        self.cv_splits = self.config['training_params'].get('cv_splits', 5)
        self.n_startup_trials = self.config['training_params'].get('n_startup_trials', 10)
        self.target_metric = self.config['training_params'].get('optuna_target_metric', 'f1')
        
        # Set model parameters
        self.top_n_features = self.config['optuna_param_limits'].get('top_n_features', {}).get('fixed_value', 20)
        self.horizon = int(self.config['optuna_param_limits'].get('horizon', {}).get('fixed_value', 5))
        self.threshold = self.config['optuna_param_limits'].get('threshold', {}).get('fixed_value', 0.1)
        
    def load_and_prepare_data(self):
        """
        Load feature data and prepare for model training
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        try:
            # Load feature data
            logger.info(f"Loading feature data from {self.feature_data_path}")
            self.feature_data = pd.read_csv(self.feature_data_path, index_col=0, parse_dates=True)
            
            if self.feature_data.empty:
                logger.error("Feature data is empty")
                return False
            
            logger.info(f"Loaded feature data with shape {self.feature_data.shape}")
            
            # Create target variable based on future returns
            logger.info(f"Creating target variable with horizon={self.horizon} and threshold={self.threshold}")
            
            # Calculate future return over the specified horizon
            self.feature_data['future_return'] = self.feature_data['Close'].pct_change(periods=self.horizon).shift(-self.horizon)
            
            # Create binary target: 1 if future return > threshold, 0 otherwise
            self.feature_data['target'] = (self.feature_data['future_return'] > self.threshold).astype(int)
            
            # Drop rows with NaN in target
            self.feature_data = self.feature_data.dropna(subset=['target'])
            
            # Log class distribution
            target_distribution = self.feature_data['target'].value_counts(normalize=True) * 100
            logger.info(f"Target class distribution: {target_distribution.to_dict()}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading and preparing data: {str(e)}")
            return False
            
    def select_features(self, method='mutual_info'):
        """
        Select top features based on feature importance
        
        Args:
            method (str): Method for feature selection ('mutual_info' or 'f_classif')
            
        Returns:
            list: Selected feature names
        """
        logger.info(f"Selecting top {self.top_n_features} features using {method}")
        
        # Identify numeric columns for feature selection, excluding target and date columns
        exclude_cols = ['target', 'future_return', 'next_day_return', 'daily_return', 'log_return']
        feature_cols = [col for col in self.feature_data.columns if col not in exclude_cols and 
                        pd.api.types.is_numeric_dtype(self.feature_data[col])]
        
        # Fill NaN values with median
        X = self.feature_data[feature_cols].fillna(self.feature_data[feature_cols].median())
        y = self.feature_data['target']
        
        # Apply feature selection
        try:
            if method == 'mutual_info':
                selector = SelectKBest(mutual_info_classif, k=min(self.top_n_features, len(feature_cols)))
            else:
                selector = SelectKBest(f_classif, k=min(self.top_n_features, len(feature_cols)))
                
            selector.fit(X, y)
            
            # Get selected feature names
            mask = selector.get_support()
            selected_features = [feature_cols[i] for i in range(len(feature_cols)) if mask[i]]
            
            logger.info(f"Selected {len(selected_features)} features: {selected_features[:5]}...")
            self.selected_features = selected_features
            
            return selected_features
        
        except Exception as e:
            logger.error(f"Error selecting features: {str(e)}")
            # Fallback to using all features
            logger.warning(f"Using all {len(feature_cols)} features due to feature selection error")
            self.selected_features = feature_cols
            return feature_cols
            
    def split_data(self, features):
        """
        Split data into training, validation, and test sets
        
        Args:
            features (list): Feature names to use
            
        Returns:
            bool: True if split successfully, False otherwise
        """
        try:
            # Ensure all columns exist
            features = [f for f in features if f in self.feature_data.columns]
            
            if not features:
                logger.error("No valid features for model training")
                return False
                
            # Prepare feature matrix and target vector
            X = self.feature_data[features].fillna(self.feature_data[features].median())
            y = self.feature_data['target']
            
            # First split: Train+Val vs Test (chronological split)
            split_idx = int(len(X) * (1 - self.test_size))
            
            X_train_val = X.iloc[:split_idx]
            y_train_val = y.iloc[:split_idx]
            
            self.X_test = X.iloc[split_idx:]
            self.y_test = y.iloc[split_idx:]
            
            # Second split: Train vs Val (random split for cross-validation)
            self.X_train, self.X_val, self.y_train, self.y_val = train_test_split(
                X_train_val, y_train_val, test_size=0.2, random_state=42
            )
            
            # Apply scaling
            self.scaler = StandardScaler()
            self.X_train = pd.DataFrame(
                self.scaler.fit_transform(self.X_train), 
                columns=features, 
                index=self.X_train.index
            )
            
            self.X_val = pd.DataFrame(
                self.scaler.transform(self.X_val), 
                columns=features, 
                index=self.X_val.index
            )
            
            self.X_test = pd.DataFrame(
                self.scaler.transform(self.X_test), 
                columns=features, 
                index=self.X_test.index
            )
            
            logger.info(f"Data split complete. Train: {self.X_train.shape}, Val: {self.X_val.shape}, Test: {self.X_test.shape}")
            return True
            
        except Exception as e:
            logger.error(f"Error splitting data: {str(e)}")
            return False
            
    def objective(self, trial):
        """
        Objective function for Optuna hyperparameter optimization
        
        Args:
            trial (optuna.trial.Trial): Trial object
            
        Returns:
            float: Score to maximize (f1, accuracy, etc.)
        """
        # Hyperparameter search space
        param_grid = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'verbosity': -1,
            'boosting_type': 'gbdt',
            'n_estimators': trial.suggest_int('n_estimators', 100, 500),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
            'num_leaves': trial.suggest_int('num_leaves', 20, 150),
            'max_depth': trial.suggest_int('max_depth', 3, 12),
            'min_data_in_leaf': trial.suggest_int('min_data_in_leaf', 10, 100),
            'lambda_l1': trial.suggest_float('lambda_l1', 0.0, 10.0),
            'lambda_l2': trial.suggest_float('lambda_l2', 0.0, 10.0),
            'feature_fraction': trial.suggest_float('feature_fraction', 0.6, 1.0),
            'bagging_fraction': trial.suggest_float('bagging_fraction', 0.6, 1.0),
            'bagging_freq': trial.suggest_int('bagging_freq', 0, 10)
        }
        
        # Create time series cross-validation
        cv = TimeSeriesSplit(n_splits=self.cv_splits)
        
        # Convert to LightGBM datasets
        lgb_train = lgb.Dataset(self.X_train, self.y_train)
        lgb_val = lgb.Dataset(self.X_val, self.y_val, reference=lgb_train)
        
        # Train model
        model = lgb.train(
            param_grid,
            lgb_train,
            valid_sets=[lgb_train, lgb_val],
            valid_names=['train', 'valid'],
            early_stopping_rounds=50,
            verbose_eval=False
        )
        
        # Make predictions on validation set
        y_pred_proba = model.predict(self.X_val)
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # Calculate metrics
        accuracy = accuracy_score(self.y_val, y_pred)
        precision = precision_score(self.y_val, y_pred)
        recall = recall_score(self.y_val, y_pred)
        f1 = f1_score(self.y_val, y_pred)
        
        # Log metrics for this trial
        logger.info(f"Trial #{trial.number}: Accuracy={accuracy:.4f}, Precision={precision:.4f}, "
                   f"Recall={recall:.4f}, F1={f1:.4f}")
        
        # Return the target metric to optimize
        if self.target_metric == 'accuracy':
            return accuracy
        elif self.target_metric == 'precision':
            return precision
        elif self.target_metric == 'recall':
            return recall
        else:  # default to f1
            return f1
            
    def optimize_model(self):
        """
        Optimize model hyperparameters using Optuna
        
        Returns:
            bool: True if optimization completed successfully, False otherwise
        """
        try:
            # Create study for hyperparameter optimization
            logger.info(f"Starting hyperparameter optimization with {self.n_trials} trials")
            
            study = optuna.create_study(
                direction='maximize',
                sampler=TPESampler(n_startup_trials=self.n_startup_trials)
            )
            
            study.optimize(self.objective, n_trials=self.n_trials)
            
            # Get best parameters
            self.best_params = study.best_params
            best_score = study.best_value
            
            logger.info(f"Best {self.target_metric}: {best_score:.4f}")
            logger.info(f"Best parameters: {self.best_params}")
            
            # Train final model with best parameters
            final_params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'verbosity': -1,
                'boosting_type': 'gbdt',
                **self.best_params
            }
            
            lgb_train = lgb.Dataset(self.X_train, self.y_train)
            lgb_val = lgb.Dataset(self.X_val, self.y_val, reference=lgb_train)
            
            self.best_model = lgb.train(
                final_params,
                lgb_train,
                valid_sets=[lgb_train, lgb_val],
                valid_names=['train', 'valid'],
                early_stopping_rounds=50,
                verbose_eval=False
            )
            
            # Save feature importance
            self.feature_importance = pd.DataFrame({
                'Feature': self.X_train.columns,
                'Importance': self.best_model.feature_importance()
            }).sort_values(by='Importance', ascending=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing model: {str(e)}")
            return False
            
    def evaluate_model(self):
        """
        Evaluate the optimized model on test set
        
        Returns:
            dict: Evaluation metrics
        """
        try:
            # Make predictions on test set
            y_pred_proba = self.best_model.predict(self.X_test)
            y_pred = (y_pred_proba > 0.5).astype(int)
            
            # Calculate metrics
            accuracy = accuracy_score(self.y_test, y_pred)
            precision = precision_score(self.y_test, y_pred)
            recall = recall_score(self.y_test, y_pred)
            f1 = f1_score(self.y_test, y_pred)
            
            # Generate confusion matrix
            cm = confusion_matrix(self.y_test, y_pred)
            
            # Log evaluation metrics
            logger.info(f"Test metrics - Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, "
                       f"Recall: {recall:.4f}, F1: {f1:.4f}")
            logger.info(f"Confusion Matrix:\n{cm}")
            
            # Calculate ROC curve
            fpr, tpr, _ = roc_curve(self.y_test, y_pred_proba)
            roc_auc = auc(fpr, tpr)
            
            # Calculate precision-recall curve
            precision_curve, recall_curve, _ = precision_recall_curve(self.y_test, y_pred_proba)
            pr_auc = auc(recall_curve, precision_curve)
            
            # Generate and save plots
            self.generate_evaluation_plots(fpr, tpr, roc_auc, precision_curve, recall_curve, pr_auc, cm)
            
            # Return metrics
            metrics = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'roc_auc': roc_auc,
                'pr_auc': pr_auc
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return {}
            
    def generate_evaluation_plots(self, fpr, tpr, roc_auc, precision_curve, recall_curve, pr_auc, cm):
        """
        Generate and save evaluation plots
        
        Args:
            fpr (array): False positive rates for ROC curve
            tpr (array): True positive rates for ROC curve
            roc_auc (float): Area under ROC curve
            precision_curve (array): Precision values for PR curve
            recall_curve (array): Recall values for PR curve
            pr_auc (float): Area under PR curve
            cm (array): Confusion matrix
        """
        try:
            # Create reports directory if it doesn't exist
            reports_dir = 'reports'
            os.makedirs(reports_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create figure for all plots
            plt.figure(figsize=(18, 12))
            
            # ROC curve
            plt.subplot(2, 2, 1)
            plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {roc_auc:.4f})')
            plt.plot([0, 1], [0, 1], 'k--')
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title('Receiver Operating Characteristic')
            plt.legend(loc='lower right')
            
            # Precision-Recall curve
            plt.subplot(2, 2, 2)
            plt.plot(recall_curve, precision_curve, label=f'PR Curve (AUC = {pr_auc:.4f})')
            plt.xlabel('Recall')
            plt.ylabel('Precision')
            plt.title('Precision-Recall Curve')
            plt.legend(loc='lower left')
            
            # Confusion matrix
            plt.subplot(2, 2, 3)
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
            plt.xlabel('Predicted Label')
            plt.ylabel('True Label')
            plt.title('Confusion Matrix')
            
            # Feature importance (top 15)
            plt.subplot(2, 2, 4)
            if self.feature_importance is not None:
                top_features = self.feature_importance.head(15)
                sns.barplot(x='Importance', y='Feature', data=top_features)
                plt.title('Top 15 Feature Importance')
            else:
                plt.text(0.5, 0.5, 'Feature importance not available', ha='center')
                plt.title('Feature Importance')
            
            plt.tight_layout()
            plt.savefig(os.path.join(reports_dir, f'model_evaluation_{timestamp}.png'))
            logger.info(f"Evaluation plots saved to reports/model_evaluation_{timestamp}.png")
            
        except Exception as e:
            logger.error(f"Error generating evaluation plots: {str(e)}")
            
    def save_model(self, metrics):
        """
        Save the trained model, scaler, and configuration
        
        Args:
            metrics (dict): Evaluation metrics
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Create model directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Save the model
            joblib.dump(self.best_model, self.model_path)
            logger.info(f"Model saved to {self.model_path}")
            
            # Save the scaler
            joblib.dump(self.scaler, self.scaler_path)
            logger.info(f"Scaler saved to {self.scaler_path}")
            
            # Create model config
            model_config = {
                'model_type': 'lightgbm',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'features': self.selected_features,
                'hyperparameters': self.best_params,
                'metrics': metrics,
                'horizon': self.horizon,
                'threshold': self.threshold,
                'target_metric': self.target_metric,
                'feature_importance': self.feature_importance.to_dict() if self.feature_importance is not None else None
            }
            
            # Save model config
            with open(self.model_config_path, 'w') as f:
                json.dump(model_config, f, indent=4)
            logger.info(f"Model configuration saved to {self.model_config_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False
            
    def train_model(self):
        """
        Main method to train the model: load data, select features, train, evaluate, save
        
        Returns:
            bool: True if training completed successfully, False otherwise
        """
        # Load and prepare data
        if not self.load_and_prepare_data():
            logger.error("Failed to load and prepare data")
            return False
        
        # Select features
        features = self.select_features()
        
        # Split data
        if not self.split_data(features):
            logger.error("Failed to split data")
            return False
        
        # Optimize model
        if not self.optimize_model():
            logger.error("Failed to optimize model")
            return False
        
        # Evaluate model
        metrics = self.evaluate_model()
        if not metrics:
            logger.error("Failed to evaluate model")
            return False
        
        # Save model
        if not self.save_model(metrics):
            logger.error("Failed to save model")
            return False
        
        logger.info("Model training completed successfully")
        return True
        
if __name__ == "__main__":
    try:
        logger.info("Starting model training")
        config = load_system_config()
        trainer = ModelTrainer(config)
        success = trainer.train_model()
        
        if success:
            logger.info("Model training process completed successfully")
        else:
            logger.error("Model training process failed")
    except Exception as e:
        logger.error(f"Model training process failed: {str(e)}")
