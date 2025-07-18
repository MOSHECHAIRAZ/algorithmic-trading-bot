"""
Data Collection Module for Algorithmic Trading Bot

This module is responsible for fetching market data from various sources,
primarily using yfinance and requests. It stores the raw data in the data/raw directory
and handles connection errors, retries, and data validation.

Author: GitHub Copilot
Date: Created based on project instructions
"""

import os
import json
import logging
import time
from datetime import datetime
import pandas as pd
import yfinance as yf
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_collection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('data_collection')

def load_system_config(config_path='system_config.json'):
    """
    Load system configuration from JSON file
    
    Args:
        config_path (str): Path to the system config file
        
    Returns:
        dict: Configuration settings
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Successfully loaded system configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading system configuration: {str(e)}")
        raise

def ensure_directories(config):
    """
    Ensure required directories exist
    
    Args:
        config (dict): System configuration
    """
    paths = [
        config['system_paths'].get('preprocessed_data', 'data/processed'),
        config['system_paths'].get('feature_data', 'data/processed'),
        'data/raw',
        'logs',
        'models'
    ]
    
    for path in paths:
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")

def fetch_yfinance_data(symbol, period="5y", interval="1d", retries=3, retry_delay=5):
    """
    Fetch historical market data from Yahoo Finance
    
    Args:
        symbol (str): Stock symbol
        period (str): Time period to fetch (e.g., '5y' for 5 years)
        interval (str): Data interval (e.g., '1d' for daily)
        retries (int): Number of retry attempts
        retry_delay (int): Delay between retries in seconds
        
    Returns:
        pd.DataFrame: Historical market data
    """
    attempt = 0
    while attempt < retries:
        try:
            logger.info(f"Fetching data for {symbol}, attempt {attempt+1}/{retries}")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                attempt += 1
                time.sleep(retry_delay)
                continue
                
            logger.info(f"Successfully fetched {len(df)} records for {symbol}")
            return df
        
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            attempt += 1
            if attempt < retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to fetch data for {symbol} after {retries} attempts")
                raise
    
    return pd.DataFrame()  # Return empty DataFrame if all attempts fail

def save_raw_data(df, symbol, data_dir="data/raw"):
    """
    Save raw market data to CSV file
    
    Args:
        df (pd.DataFrame): Market data
        symbol (str): Stock symbol
        data_dir (str): Directory to save data
        
    Returns:
        str: Path to saved file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Format current date for filename
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{symbol}_raw_{timestamp}.csv"
        filepath = os.path.join(data_dir, filename)
        
        # Save data to CSV
        df.to_csv(filepath)
        logger.info(f"Saved raw data to {filepath}")
        
        return filepath
    except Exception as e:
        logger.error(f"Error saving raw data for {symbol}: {str(e)}")
        raise

def collect_data(config=None):
    """
    Main function to collect data for all symbols in configuration
    
    Args:
        config (dict, optional): System configuration. If None, loads from file.
        
    Returns:
        dict: Paths to saved data files by symbol
    """
    # Load configuration if not provided
    if config is None:
        config = load_system_config()
    
    # Ensure directories exist
    ensure_directories(config)
    
    # Get list of symbols
    symbols = [config['contract']['symbol']]
    
    # Extract API parameters
    retries = config.get('training_params', {}).get('api_retry_attempts', 3)
    retry_delay = config.get('training_params', {}).get('api_retry_delay', 5)
    
    # Determine data path
    data_dir = os.path.dirname(config['system_paths'].get('preprocessed_data', 'data/processed'))
    raw_dir = os.path.join(data_dir, '../raw')
    
    saved_files = {}
    
    # Fetch data for each symbol
    for symbol in symbols:
        try:
            # Get data from Yahoo Finance
            df = fetch_yfinance_data(
                symbol=symbol,
                period=f"{config['training_params'].get('years_of_data', 5)}y",
                interval="1d",
                retries=retries,
                retry_delay=retry_delay
            )
            
            if df.empty:
                logger.warning(f"Skipping {symbol} due to empty data")
                continue
            
            # Save raw data
            filepath = save_raw_data(df, symbol, raw_dir)
            saved_files[symbol] = filepath
            
        except Exception as e:
            logger.error(f"Failed to collect data for {symbol}: {str(e)}")
    
    return saved_files

if __name__ == "__main__":
    try:
        logger.info("Starting data collection process")
        config = load_system_config()
        saved_files = collect_data(config)
        logger.info(f"Data collection completed. Files saved: {saved_files}")
    except Exception as e:
        logger.error(f"Data collection process failed: {str(e)}")
