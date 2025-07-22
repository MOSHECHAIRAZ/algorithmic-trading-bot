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
        
        logging.info(f"Loaded model '{Path(model_path).name}' with {len(selected_features)} features.")
    except Exception as e:
        logging.error(f"Failed to load initial files for backtest: {e}", exc_info=True)
        return

    # --- Pre-calculate all features for the backtest period ---
    logging.info("Pre-calculating all features for the backtest period...")
    fc = FeatureCalculator()
    features_df_full, _ = fc.add_all_possible_indicators(df_raw.copy(), verbose=False)
    logging.info("Feature pre-calculation complete.")

    # --- Walk-Forward Scaling and Prediction (Vectorized, No Lookahead Bias) ---
    logging.info("Preparing data for vectorized walk-forward prediction...")
    X_full = features_df_full[selected_features].fillna(0)

    # Use expanding window to calculate mean and std deviation to prevent lookahead bias
    # min_periods ensures we have enough data before starting calculations
    min_periods = backtest_params.get('min_history_days', 100)
    expanding_mean = X_full.expanding(min_periods=min_periods).mean()
    expanding_std = X_full.expanding(min_periods=min_periods).std()

    # Replace std=0 with 1 to avoid division by zero
    expanding_std.replace(0, 1, inplace=True)

    # Manually scale the data point-in-time
    X_full_scaled = (X_full - expanding_mean) / expanding_std

    # Drop initial period where we don't have enough data for scaling
    X_full_scaled.dropna(inplace=True)

    logging.info(f"Generating predictions on {len(X_full_scaled)} data points...")
    predictions = model.predict(X_full_scaled)
    walk_forward_predictions = pd.Series(predictions, index=X_full_scaled.index)
    
    # --- הרצת סימולציה ---
    equity, trades, metrics = run_trading_simulation(
        prices_df=df_raw.copy(),
        predictions=walk_forward_predictions,
        commission=backtest_params.get('commission', 0.001),
        slippage=backtest_params.get('slippage', 0.0005),
        initial_balance=backtest_params.get('initial_balance', 100000),
        # --- שורות מתוקנות ---
        sl_pct=risk_params.get('stop_loss_pct', 5.0) / 100.0,  # קריאה מהקונפיגורציה של המודל והמרה לשבר עשרוני
        tp_pct=risk_params.get('take_profit_pct', 10.0) / 100.0, # קריאה מהקונפיגורציה של המודל והמרה לשבר עשרוני
        # ----------------------
        risk_per_trade=risk_params.get('risk_per_trade', 0.01),
        log_trades=False  # אין יותר צורך ב-atr_col
    )
    
    # --- עיבוד ושמירת תוצאות ---
    if not equity:
        logging.error("Simulation produced no equity results. Aborting.")
        return

    aligned_prices, _ = df_raw.align(walk_forward_predictions, join='inner', axis=0)
    equity_df = pd.DataFrame({'equity': equity}, index=aligned_prices.index)
    
    initial_price = aligned_prices['close'].iloc[0]
    equity_df['benchmark_equity'] = backtest_params['initial_balance'] * (aligned_prices['close'] / initial_price)
    
    num_years = (equity_df.index[-1] - equity_df.index[0]).days / 365.25
    cagr = ((equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0]) ** (1 / num_years) - 1) if num_years > 0 and equity_df['equity'].iloc[0] > 0 else 0.0
    
    logging.info(f"\n--- Backtest Results for '{output_suffix}' ---")
    logging.info(f"Total Return: {metrics.get('total_return', 0):.2%}")
    logging.info(f"CAGR: {cagr:.2%}")
    # ... (שאר הלוגים)

    # שמירת התוצאות
    results_dir = Path('reports/backtest_results')
    results_dir.mkdir(parents=True, exist_ok=True)
    
    equity_df.to_csv(results_dir / f'equity_curve_{output_suffix}.csv')
    pd.DataFrame(trades).to_csv(results_dir / f'trades_{output_suffix}.csv', index=False)
    
    summary = {
        "run_timestamp": datetime.now().isoformat(),
        "model_path": str(model_path),
        "total_return": metrics.get('total_return', 0),
        "cagr": cagr,
        "sharpe_ratio": metrics.get('sharpe_ratio', 0),
        "max_drawdown": metrics.get('max_drawdown', 0),
        "trades": len(trades),
        "win_rate": metrics.get('win_rate', 0),
        "final_equity": equity_df['equity'].iloc[-1] if not equity_df.empty else 0,
        "benchmark_return": metrics.get('benchmark_return', 0)
    }
    summary_path = results_dir / f'summary_{output_suffix}.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4)

    logging.info(f"Backtest results for '{output_suffix}' saved to {results_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a backtest for a specific model.")
    parser.add_argument('--model', default=config['system_paths']['champion_model'], help="Path to the model .pkl file.")
    parser.add_argument('--scaler', default=config['system_paths']['champion_scaler'], help="Path to the scaler .pkl file.")
    parser.add_argument('--config', default=config['system_paths']['champion_config'], help="Path to the model config .json file.")
    parser.add_argument('--output_suffix', default='champion_manual_run', help="Suffix for output files (e.g., 'champion' or a timestamp).")
    args = parser.parse_args()
    
    data_file = Path('data/processed/SPY_processed.csv')
    if data_file.exists():
        run_backtest(
            data_path=str(data_file), config_path=args.config,
            model_path=args.model, scaler_path=args.scaler,
            output_suffix=args.output_suffix
        )
    else:
        logging.error(f"Missing required data file: {data_file}")