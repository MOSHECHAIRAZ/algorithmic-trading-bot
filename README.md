# Algorithmic Trading Bot (Trend Following + ML + VIX)

## Overview
This project is a modular algorithmic trading bot that uses machine learning (trend following strategy) and VIX data. It is built in Python (data, ML, API) and Node.js (trading agent).

### Main Components
- **Data Collection (Python):** Collects historical and real-time stock/VIX data.
- **Data Preprocessing & Feature Engineering (Python):** Cleans, processes, and creates features.
- **Model Training (Python):** Trains and optimizes a machine learning model (LightGBM).
- **Model API (Flask):** Exposes the trained model as an API.
- **Trading Agent (Node.js):** Executes trades based on model predictions and interacts with broker APIs.
- **Risk Management & Logging:** Ensures robust, safe trading and full traceability.

### Folder Structure
- `src/` — Python source code (data, ML, API, config)
- `agent/` — Node.js trading agent
- `data/` — Raw, processed, and feature data
- `models/` — Saved models and configs
- `reports/plots/` — Visualizations and reports
- `.github/` — Copilot instructions

### Setup

#### Node.js CI Install
For CI/CD environments, use:
```sh
npm run ci-install
```
This runs `npm ci` for clean, reproducible installs. For local development, use the standard `npm install`.

1. **Install Python 3.x** ([python.org](https://www.python.org/downloads/))
2. **Install Node.js** ([nodejs.org](https://nodejs.org/))
3. **Install TA-Lib (required for pandas_ta and technical indicators):**

   TA-Lib requires native binaries. Install them **before** running `pip install -r requirements.txt`:

   **Windows:**
   - Download the appropriate TA-Lib .whl file for your Python version from [https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)
   - Install it with pip (replace the filename as needed):
     ```sh
     pip install ta_lib‑0.4.0‑cp39‑cp39‑win_amd64.whl
     ```

   **Linux:**
   - Install the TA-Lib C library:
     ```sh
     sudo apt-get update && sudo apt-get install -y build-essential
     sudo apt-get install -y libta-lib0 libta-lib0-dev
     ```
   - Or, if not available:
     ```sh
     wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
     tar -xzf ta-lib-0.4.0-src.tar.gz
     cd ta-lib-0.4.0
     ./configure --prefix=/usr
     make
     sudo make install
     ```

   **macOS:**
   - Install with Homebrew:
     ```sh
     brew install ta-lib
     ```

4. **Install Python dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
5. **Install Node.js dependencies:**
   ```sh
   npm install
   ```

## Configuration Management (2025 Update)

**All configuration is now managed in a single file: `system_config.json` (root directory).**
- All risk, contract, training, backtest, API, IBKR, and path settings are centralized here.
- Edit configuration via the dashboard (recommended) or directly in `system_config.json`.
- Old config files (e.g., `src/config.py`, `models/SPY_model_config.json`) are deprecated and ignored.

**Example `system_config.json`:**
```json
{
  "risk_params": {
    "sl_atr_multiplier": 2.0,
    "tp_atr_multiplier": 4.0,
    "risk_per_trade": 0.024,
    "position_size_pct": 0.1
  },
  "contract": {
    "symbol": "SPY",
    "secType": "STK",
    "exchange": "SMART",
    "currency": "USD",
    "primaryExch": "ARCA"
  },
  "training_params": {"n_trials": 200, "test_size_split": 0.2, "cv_splits": 5, "years_of_data": 15},
  "backtest_params": {"initial_balance": 100000, "commission": 0.001, "slippage": 0.0005, "min_history_days": 100},
  "api_settings": {"host": "0.0.0.0", "port": 5000},
  "ibkr_settings": {"host": "127.0.0.1", "port": 4001, "clientId": 101, "history_window": "90 D"},
  "system_paths": {
    "champion_model": "models/champion_model.pkl",
    "champion_scaler": "models/champion_scaler.pkl",
    "champion_config": "models/champion_model_config.json",
    "system_config": "system_config.json"
  }
}
```

**How to edit configuration:**
- Use the dashboard (tab: "ניהול המערכת" > "תצורת המערכת") for a safe UI.
- Or, edit `system_config.json` manually and restart the relevant processes.

## Environment Variables

To run the project, create a `.env` file in the root directory with the following content:

```
POLYGON_API_KEY=your_polygon_api_key_here
# Add any other required environment variables here
```

This ensures your API keys and secrets are not exposed in the codebase.

## Architecture Details
- **run_all.py**: Orchestrates the main pipeline: data collection, preprocessing, and model training.
- **data_collector.py**: Collects historical stock and VIX data (yfinance) to `data/raw/`.
- **run_preprocessing.py**: Cleans, validates, and preprocesses raw data to `data/processed/`.
- **main_trainer.py**: Handles both feature engineering (using pandas_ta, VIX, triple barrier labeling, etc.) and model training (Optuna, LightGBM, evaluation, saving model/config to `models/`).
- **model_api.py**: Flask API for model inference.
- **trading_agent.js**: Node.js trading agent, interacts with model API and broker (IB).
- **risk_management.py**: Risk management logic (stop loss, take profit, position sizing).
- **backtester.py**: Backtesting and simulation.

## 2025: Data Flow & File Map (Updated)


### Current Data Flow

1. `run_all.py` — Orchestrates the main pipeline: runs data collection, preprocessing, and model training in sequence.
2. `data_collector.py` — Collects all raw data (SPY, VIX, etc.) to `data/raw/`.
3. `run_preprocessing.py` — Cleans and preprocesses raw data, outputs to `data/processed/`.
4. `main_trainer.py` — Performs both feature engineering (technical indicators, VIX, labeling, etc.) and model training (feature selection, Optuna optimization, LightGBM training). Outputs to `models/` and `models/champion_model_config.json`.
5. `backtester.py` — Walk-forward backtesting, simulates live trading by entering/exiting at the next day's open.
6. `dashboard.py` — Streamlit dashboard for config, process management, and monitoring.
7. `agent/trading_agent.js` — Node.js trading agent, runs daily at 21:30 UTC and only closes positions on 'Sell' signal.

**Note:** Deprecated files such as `feature_engineer.py`, `vix_data_collector.py`, and old config files have been removed. All logic is now unified in the new pipeline. The market regime detection step is now integrated into the main training pipeline and does not require a separate script.

### Data Flow

The main workflow is orchestrated by `run_all.py` and consists of the following steps:
1.  **Data Collection:** Fetches the latest SPY and VIX data and saves to `data/raw/`.
2.  **Preprocessing:** Cleans and processes raw data, outputs to `data/processed/`.
3.  **Feature Engineering & Model Training:** `main_trainer.py` loads processed data, generates technical indicators (including market regime features), selects features, performs hyperparameter optimization (Optuna), trains the LightGBM model, and saves all outputs to `models/`.
4.  **API Serving:** Starts the Flask API server, which loads the latest champion model and serves predictions.
5.  **Trading Agent:** Node.js trading agent consumes predictions from the API and executes trades via Interactive Brokers.

## Logging
- All modules use Python/Node logging for error and event tracking.

---

## Workflow & Best Practices
- Always use the dashboard for configuration and process management.
- All modules (Python & Node.js) read their settings from `system_config.json`.
- For reproducibility, each trained model's config is snapshot to `models/champion_model_config.json`.
- Old config files are ignored and can be deleted.

---

## Next Steps
- Implement each module step by step as described in the project plan.
- See `copilot-instructions.md` for workspace-specific coding guidelines.

---
