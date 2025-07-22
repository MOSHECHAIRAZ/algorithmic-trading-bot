"""
Preprocessing and Feature Engineering Module for Algorithmic Trading Bot

This module is responsible for cleaning raw market data and calculating technical indicators
using pandas, numpy, and pandas_ta. It handles data cleaning, feature calculation,
and stores processed data in the data/processed directory.

Author: GitHub Copilot
Date: Created based on project instructions
"""

import os
import json
import logging
import pandas as pd
import numpy as np
import pandas_ta as ta
from pathlib import Path
import sys

# Add parent directory to path to import data_collection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_collection import load_system_config, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/preprocessing.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('preprocessing')

class DataPreprocessor:
    """
    Class for preprocessing market data and calculating technical indicators
    """
    
    def __init__(self, config=None):
        """
        Initialize the preprocessor with configuration
        
        Args:
            config (dict, optional): System configuration. If None, loads from file.
        """
        self.config = config if config else load_system_config()
        ensure_directories(self.config)
        
        # Set paths for data
        self.processed_data_path = self.config['system_paths'].get('preprocessed_data', 'data/processed/SPY_processed.csv')
        self.feature_data_path = self.config['system_paths'].get('feature_data', 'data/processed/SPY_features.csv')
        
        # Track failed features for reporting
        self.failed_features = {}
        
    def load_raw_data(self, symbol=None):
        """
        Load the most recent raw data file for a symbol
        
        Args:
            symbol (str, optional): Stock symbol. If None, uses symbol from config.
            
        Returns:
            pd.DataFrame: Raw market data
        """
        if symbol is None:
            symbol = self.config['contract']['symbol']
        
        # Get raw data directory
        data_dir = os.path.join(os.path.dirname(self.processed_data_path), '../raw')
        
        # Find the most recent file for the symbol
        files = [f for f in os.listdir(data_dir) if f.startswith(f"{symbol}_raw_") and f.endswith('.csv')]
        
        if not files:
            logger.error(f"No raw data files found for {symbol}")
            return pd.DataFrame()
        
        # Sort files by name (which includes timestamp) and get the most recent
        latest_file = sorted(files)[-1]
        filepath = os.path.join(data_dir, latest_file)
        
        logger.info(f"Loading raw data from {filepath}")
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        return df
    
    def clean_data(self, df):
        """
        Clean the raw market data
        
        Args:
            df (pd.DataFrame): Raw market data
            
        Returns:
            pd.DataFrame: Cleaned market data
        """
        logger.info(f"Cleaning data with shape {df.shape}")
        
        # Handle missing values
        if df.isnull().sum().sum() > 0:
            logger.info(f"Found {df.isnull().sum().sum()} missing values. Filling with forward fill method.")
            df = df.ffill()
            
            # If there are still NaNs (at the beginning), fill with backward fill
            if df.isnull().sum().sum() > 0:
                df = df.bfill()
                logger.info("Filled remaining missing values with backward fill.")
        
        # Verify data integrity
        if df.empty:
            logger.error("DataFrame is empty after cleaning")
            return df
        
        if not all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
            logger.error(f"DataFrame is missing required columns. Columns: {df.columns.tolist()}")
            return pd.DataFrame()
        
        # Remove rows with zero volume (likely non-trading days)
        if 'Volume' in df.columns:
            zero_volume_count = (df['Volume'] == 0).sum()
            if zero_volume_count > 0:
                logger.info(f"Removing {zero_volume_count} rows with zero volume")
                df = df[df['Volume'] > 0]
        
        # Ensure the index is sorted
        df = df.sort_index()
        
        logger.info(f"Data cleaning complete. Final shape: {df.shape}")
        return df
    
    def calculate_base_features(self, df):
        """
        Calculate base features like returns, log returns, etc.
        
        Args:
            df (pd.DataFrame): Cleaned market data
            
        Returns:
            pd.DataFrame: Market data with base features
        """
        logger.info("Calculating base features")
        
        # Calculate daily returns
        df['daily_return'] = df['Close'].pct_change()
        
        # Calculate log returns
        df['log_return'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Calculate volatility (rolling standard deviation of returns)
        for window in [5, 10, 20]:
            try:
                df[f'volatility_{window}d'] = df['daily_return'].rolling(window=window).std()
                logger.info(f"Calculated volatility_{window}d")
            except Exception as e:
                logger.error(f"Failed to calculate volatility_{window}d: {str(e)}")
                self.failed_features[f'volatility_{window}d'] = str(e)
        
        # Calculate price ratios
        df['close_to_open'] = df['Close'] / df['Open']
        df['high_to_low'] = df['High'] / df['Low']
        
        # Calculate next day's return as target
        df['next_day_return'] = df['daily_return'].shift(-1)
        
        # Calculate moving averages
        for ma_period in [5, 10, 20, 50, 200]:
            try:
                df[f'sma_{ma_period}'] = df['Close'].rolling(window=ma_period).mean()
                logger.info(f"Calculated sma_{ma_period}")
            except Exception as e:
                logger.error(f"Failed to calculate sma_{ma_period}: {str(e)}")
                self.failed_features[f'sma_{ma_period}'] = str(e)
                
        return df
    
    def calculate_technical_indicators(self, df):
        """
        Calculate technical indicators using pandas_ta
        
        Args:
            df (pd.DataFrame): Market data with base features
            
        Returns:
            pd.DataFrame: Market data with technical indicators
        """
        logger.info("Calculating technical indicators")
        
        # Make a copy of the DataFrame to avoid SettingWithCopyWarning
        df_indicators = df.copy()
        
        # Define basic indicators to calculate
        indicators = {
            "RSI": [14],
            "MACD": [{"fast": 12, "slow": 26, "signal": 9}],
            "ATR": [14],
            "ADX": [14],
            "CCI": [20],
            "OBV": None,
            "BBANDS": [{"length": 20, "std": 2}],
            "MFI": [14],
            "STOCH": [{"k": 14, "d": 3}]
        }
        
        # Calculate indicators
        for indicator, params_list in indicators.items():
            try:
                if params_list is None:
                    # If no parameters, just call the indicator function
                    method = getattr(ta, indicator.lower(), None)
                    if method:
                        indicator_df = method(df_indicators['High'], df_indicators['Low'], df_indicators['Close'], df_indicators['Volume'])
                        if isinstance(indicator_df, pd.DataFrame):
                            for col in indicator_df.columns:
                                df_indicators[col] = indicator_df[col]
                        else:  # Series
                            df_indicators[indicator.lower()] = indicator_df
                        logger.info(f"Calculated {indicator}")
                else:
                    # For indicators with parameters
                    for params in params_list:
                        if isinstance(params, dict):
                            method = getattr(ta, indicator.lower(), None)
                            if method:
                                indicator_df = method(df_indicators['High'], df_indicators['Low'], df_indicators['Close'], **params)
                                if isinstance(indicator_df, pd.DataFrame):
                                    for col in indicator_df.columns:
                                        df_indicators[col] = indicator_df[col]
                                else:  # Series
                                    name_parts = [indicator.lower()]
                                    for k, v in params.items():
                                        name_parts.append(f"{k}{v}")
                                    name = "_".join(map(str, name_parts))
                                    df_indicators[name] = indicator_df
                                logger.info(f"Calculated {indicator} with params {params}")
                        else:  # Just a single value parameter
                            method = getattr(ta, indicator.lower(), None)
                            if method:
                                indicator_df = method(df_indicators['High'], df_indicators['Low'], df_indicators['Close'], length=params)
                                if isinstance(indicator_df, pd.DataFrame):
                                    for col in indicator_df.columns:
                                        df_indicators[col] = indicator_df[col]
                                else:  # Series
                                    df_indicators[f"{indicator.lower()}_{params}"] = indicator_df
                                logger.info(f"Calculated {indicator} with length {params}")
            except Exception as e:
                logger.error(f"Failed to calculate {indicator}: {str(e)}")
                self.failed_features[indicator] = str(e)
        
        # Create custom features and ratios
        try:
            # Price to moving average ratios
            for ma_period in [20, 50, 200]:
                ma_col = f'sma_{ma_period}'
                if ma_col in df_indicators.columns:
                    df_indicators[f'price_to_{ma_col}'] = df_indicators['Close'] / df_indicators[ma_col]
            
            # Combine RSI and volatility
            if 'rsi_14' in df_indicators.columns and 'volatility_10d' in df_indicators.columns:
                df_indicators['rsi_volatility'] = df_indicators['rsi_14'] * df_indicators['volatility_10d']
        except Exception as e:
            logger.error(f"Failed to calculate custom features: {str(e)}")
            self.failed_features['custom_features'] = str(e)
        
        return df_indicators
    
    def save_feature_fail_report(self):
        """
        Save a report of failed features to a JSON file
        """
        if self.failed_features:
            report_path = 'logs/feature_fail_report.json'
            try:
                with open(report_path, 'w') as f:
                    json.dump(self.failed_features, f, indent=2)
                logger.info(f"Feature failure report saved to {report_path}")
            except Exception as e:
                logger.error(f"Failed to save feature failure report: {str(e)}")
    
    def preprocess_data(self, symbol=None):
        """
        Main method to preprocess data: load, clean, calculate features
        
        Args:
            symbol (str, optional): Stock symbol. If None, uses symbol from config.
            
        Returns:
            tuple: (processed_data, feature_data) DataFrames
        """
        if symbol is None:
            symbol = self.config['contract']['symbol']
        
        # Load raw data
        df = self.load_raw_data(symbol)
        if df.empty:
            logger.error("No data to preprocess")
            return pd.DataFrame(), pd.DataFrame()
        
        # Clean data
        df_cleaned = self.clean_data(df)
        if df_cleaned.empty:
            logger.error("Data cleaning resulted in empty DataFrame")
            return pd.DataFrame(), pd.DataFrame()
        
        # Calculate base features
        df_base_features = self.calculate_base_features(df_cleaned)
        
        # Save processed data (basic cleaning and base features)
        try:
            os.makedirs(os.path.dirname(self.processed_data_path), exist_ok=True)
            df_base_features.to_csv(self.processed_data_path)
            logger.info(f"Processed data saved to {self.processed_data_path}")
        except Exception as e:
            logger.error(f"Error saving processed data: {str(e)}")
        
        # Calculate technical indicators
        df_with_indicators = self.calculate_technical_indicators(df_base_features)
        
        # Save feature data (processed data + all technical indicators)
        try:
            os.makedirs(os.path.dirname(self.feature_data_path), exist_ok=True)
            df_with_indicators.to_csv(self.feature_data_path)
            logger.info(f"Feature data saved to {self.feature_data_path}")
        except Exception as e:
            logger.error(f"Error saving feature data: {str(e)}")
        
        # Save report of any features that failed to calculate
        self.save_feature_fail_report()
        
        return df_base_features, df_with_indicators

if __name__ == "__main__":
    try:
        logger.info("Starting data preprocessing")
        config = load_system_config()
        preprocessor = DataPreprocessor(config)
        processed_data, feature_data = preprocessor.preprocess_data()
        
        if not feature_data.empty:
            logger.info(f"Data preprocessing completed. Features generated: {len(feature_data.columns)}")
            logger.info(f"Feature data shape: {feature_data.shape}")
        else:
            logger.error("Data preprocessing failed to generate features")
    except Exception as e:
        logger.error(f"Data preprocessing process failed: {str(e)}")
