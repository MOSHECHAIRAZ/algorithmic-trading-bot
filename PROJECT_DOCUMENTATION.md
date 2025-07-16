# Algorithmic Trading Bot Project Documentation

## Overview
This project is a modular algorithmic trading bot, combining Python and Node.js components for robust, automated trading. The architecture ensures separation of concerns, maintainability, and scalability.

## Project Structure
- `agent/` – Trading agent logic, state management, trade commands, logs.
- `archive/` – Backups, historical logs, analysis files.
- `data/` – Raw and processed market data.
- `db/` – Databases (e.g., SQLite).
- `logs/` – Execution, error, and process logs.
- `models/` – Trained models and artifacts.
- `reports/` – Analysis reports, graphs, optimization results.
- `scripts/` – Utility scripts.
- `src/` – Main source code.
- `tests/` – Unit and integration tests.

## Main Components
### 1. Data Collection
- Uses `yfinance`, `requests` to fetch market data.
- Stores data in `data/raw/`.
- Loads settings from `system_config.json` via `load_system_config()`.

### 2. Preprocessing & Feature Engineering
- Uses `pandas`, `numpy`, `pandas_ta` for data cleaning and indicator calculation.
- Stores processed data in `data/processed/`.
- Includes error handling and logging.

### 3. Model Training
- Uses `scikit-learn`, `lightgbm`, `optuna` for training and optimization.
- Saves models in `models/` using `joblib`.
- Documents results in `reports/`.

### 4. API
- Flask-based API (`dashboard.py`) with password protection.
- Exposes statistics, results, and agent status.

### 5. Trading Agent
- Node.js logic (`trading_agent.js`), integrates with IB via `@stoqey/ib`.
- State management in `state_manager.js`, stored in `state.db`/`state.json`.
- Scheduled actions with `node-cron`.
- Logs in `trading_log.txt`.

## Libraries Used
- Python: `pandas`, `numpy`, `scikit-learn`, `lightgbm`, `flask`, `requests`, `joblib`, `yfinance`, `pandas_ta`, `optuna`, `matplotlib`, `seaborn`.
- Node.js: `axios`, `node-cron`, `@stoqey/ib`.

## Configuration
All settings and paths are managed in `system_config.json` and loaded via `load_system_config()`.

## Error Handling & Logging
All modules include error handling and detailed logging for monitoring and debugging.

## Coding Principles
- Clean, modular, and well-documented code.
- Clear separation between data collection, preprocessing, feature engineering, model training, API, and trading logic.
- Use of popular, well-supported libraries.
- Error handling and logging in all components.

---
For detailed documentation of a specific module or file, see its respective docstring or README section.
