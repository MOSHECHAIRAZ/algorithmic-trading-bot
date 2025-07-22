# backtester.py (גרסה סופית ומתוקנת)
import pandas as pd
import numpy as np
import joblib
import json
import sys
import logging
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
from src.feature_calculator import FeatureCalculator
from src.utils import load_system_config
from sklearn.preprocessing import StandardScaler
from src.simulation_engine import run_trading_simulation
import argparse

# --- טעינת קונפיגורציה מרכזית ---
config = load_system_config()

# --- הגדרות לוגינג ---
log_file = Path('logs/backtester_output.log')
log_file.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8', mode='a'), # Append mode
        logging.StreamHandler(sys.stdout)
    ]
)

def run_backtest(data_path, config_path, model_path, scaler_path, output_suffix):
    logging.info(f"--- Starting Walk-Forward Backtest for suffix: '{output_suffix}' ---")
    backtest_params = config['backtest_params']
    
    try:
        df_full = pd.read_csv(data_path, parse_dates=['date'], index_col='date')
        training_config = config['training_params']
        test_size_split = training_config.get('test_size_split', 20) / 100
        split_idx = int(len(df_full) * (1 - test_size_split))
        df_raw = df_full.iloc[split_idx:]
        logging.info(f"Backtesting on OUT-OF-SAMPLE data. Start: {df_raw.index.min().date()}, End: {df_raw.index.max().date()}")

        with open(config_path, 'r', encoding='utf-8') as f:
            model_config = json.load(f)
        selected_features = model_config['selected_features']
        risk_params = model_config.get('risk_params', config['risk_params'])
        
        model = joblib.load(model_path)
        # scaler_template loading removed (unused)
        
        # Get prediction thresholds from model config
        threshold = model_config.get('sim_params', {}).get('threshold', 0.01)
        stop_loss_pct = model_config.get('sim_params', {}).get('stop_loss_pct', 1.0)
        take_profit_pct = model_config.get('sim_params', {}).get('take_profit_pct', 2.0)
        risk_per_trade = model_config.get('sim_params', {}).get('risk_per_trade', 0.01)
        
        # Log configuration
        logging.info(f"Model: {model_path}")
        logging.info(f"Selected features: {len(selected_features)}")
        logging.info(f"Threshold: {threshold}, Stop Loss: {stop_loss_pct}%, Take Profit: {take_profit_pct}%")
        logging.info(f"Risk per trade: {risk_per_trade*100}%")
        
        # Generate predictions from model 
        X = df_raw[selected_features]
        logging.info(f"Generating predictions for {len(X)} samples")
        
        # Predict
        pred_proba = model.predict_proba(X)[:, 1]
        df_raw['prediction_proba'] = pred_proba
        
        # Run simulation
        results = run_trading_simulation(
            df_raw,
            threshold=threshold,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            risk_per_trade=risk_per_trade,
            initial_balance=backtest_params.get('initial_balance', 100000),
            commission=backtest_params.get('commission', 0.001),
            slippage=backtest_params.get('slippage', 0.0005)
        )
        
        # Create output paths
        outdir = Path(config['system_paths'].get('backtest_results', 'reports/backtest_results'))
        outdir.mkdir(exist_ok=True, parents=True)
        
        # Save detailed trades to CSV
        trades_df = pd.DataFrame(results.get('trades', []))
        if not trades_df.empty:
            trades_file = outdir / f"trades_{output_suffix}.csv"
            trades_df.to_csv(trades_file)
            logging.info(f"Saved {len(trades_df)} trades to {trades_file}")
        
        # Save equity curve
        equity_df = pd.DataFrame(results.get('equity_curve', []))
        if not equity_df.empty:
            equity_file = outdir / f"equity_{output_suffix}.csv"
            equity_df.to_csv(equity_file)
            logging.info(f"Saved equity curve to {equity_file}")
        
        # Save summary to database
        save_to_database(results, output_suffix)
        
        # Log results
        logging.info("Backtest Results:")
        logging.info(f"Total Return: {results.get('total_return', 0):.2f}%")
        logging.info(f"Annualized Return: {results.get('annualized_return', 0):.2f}%")
        logging.info(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
        logging.info(f"Max Drawdown: {results.get('max_drawdown', 0):.2f}%")
        logging.info(f"Win Rate: {results.get('win_rate', 0)*100:.1f}%")
        logging.info(f"Profit Factor: {results.get('profit_factor', 0):.2f}")
        logging.info(f"Total Trades: {results.get('total_trades', 0)}")
        
        return results
        
    except Exception as e:
        logging.error(f"Error in backtest: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": str(e), "total_return": 0, "sharpe_ratio": 0}

def save_to_database(results, suffix):
    """Save backtest results to SQLite database."""
    import sqlite3
    from datetime import datetime
    
    db_path = "spy_strategy_optimization.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategy_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_timestamp TEXT,
            strategy_name TEXT,
            total_return REAL,
            annualized_return REAL,
            sharpe_ratio REAL,
            max_drawdown REAL,
            win_rate REAL,
            profit_factor REAL,
            total_trades INTEGER,
            avg_trade_return REAL,
            avg_win REAL,
            avg_loss REAL,
            max_win REAL,
            max_loss REAL,
            threshold REAL,
            stop_loss_pct REAL,
            take_profit_pct REAL,
            risk_per_trade REAL,
            initial_balance REAL,
            commission REAL,
            slippage REAL
        )
        """)
        
        # Insert data
        cursor.execute("""
        INSERT INTO strategy_results (
            run_timestamp, strategy_name, total_return, annualized_return, 
            sharpe_ratio, max_drawdown, win_rate, profit_factor, total_trades,
            avg_trade_return, avg_win, avg_loss, max_win, max_loss,
            threshold, stop_loss_pct, take_profit_pct, risk_per_trade,
            initial_balance, commission, slippage
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            suffix,
            results.get('total_return', 0),
            results.get('annualized_return', 0),
            results.get('sharpe_ratio', 0),
            results.get('max_drawdown', 0),
            results.get('win_rate', 0),
            results.get('profit_factor', 0),
            results.get('total_trades', 0),
            results.get('avg_trade_return', 0),
            results.get('avg_win', 0),
            results.get('avg_loss', 0),
            results.get('max_win', 0),
            results.get('max_loss', 0),
            results.get('threshold', 0),
            results.get('stop_loss_pct', 0),
            results.get('take_profit_pct', 0),
            results.get('risk_per_trade', 0),
            results.get('initial_balance', 100000),
            results.get('commission', 0.001),
            results.get('slippage', 0.0005)
        ))
        
        conn.commit()
        logging.info(f"Results saved to database: {db_path}")
        
    except Exception as e:
        logging.error(f"Error saving to database: {e}")
    finally:
        if conn:
            conn.close()

def run_backtest_from_api():
    """Run a backtest using the latest model - for API use."""
    system_paths = config.get('system_paths', {})
    feature_data_path = system_paths.get('feature_data', 'data/processed/SPY_features.csv')
    model_path = system_paths.get('champion_model', 'models/champion_model.pkl')
    config_path = system_paths.get('champion_config', 'models/champion_model_config.json')
    scaler_path = system_paths.get('champion_scaler', 'models/champion_scaler.pkl')
    
    # Check if files exist
    for path in [feature_data_path, model_path, config_path]:
        if not Path(path).exists():
            return {"error": f"Required file not found: {path}"}
    
    # Generate timestamp suffix
    suffix = f"api_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Run backtest
    results = run_backtest(
        feature_data_path,
        config_path,
        model_path,
        scaler_path,
        suffix
    )
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a backtest with the champion model')
    parser.add_argument('--suffix', type=str, default=datetime.now().strftime('%Y%m%d_%H%M%S'),
                        help='Suffix for output files')
    args = parser.parse_args()
    
    # הפעלת בקטסט עם מודל האלוף הנוכחי
    system_paths = config.get('system_paths', {})
    feature_data_path = system_paths.get('feature_data', 'data/processed/SPY_features.csv')
    model_path = system_paths.get('champion_model', 'models/champion_model.pkl')
    config_path = system_paths.get('champion_config', 'models/champion_model_config.json')
    scaler_path = system_paths.get('champion_scaler', 'models/champion_scaler.pkl')
    
    run_backtest(
        feature_data_path,
        config_path,
        model_path,
        scaler_path,
        args.suffix
    )
