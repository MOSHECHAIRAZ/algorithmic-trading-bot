"""
Simulation Engine - Core trading simulation logic for both Optuna and Backtester
"""
import numpy as np
import pandas as pd
import logging

def run_trading_simulation(
    prices_df: pd.DataFrame,
    predictions: pd.Series,
    commission: float,
    slippage: float,
    initial_balance: float,
    sl_pct: float,
    tp_pct: float,
    risk_per_trade: float,
    log_trades: bool = False
):
    """
    Core trading simulation logic for both Optuna and Backtester.
    Position sizing is based on risk_per_trade and ATR, matching live agent logic.
    Returns: equity_curve, trades, metrics dict
    """
    balance = initial_balance
    position_size_shares = 0
    entry_price = 0
    sl_price = None
    tp_price = None
    equity = []
    trades = []
    position_type = None  # 'long', 'short', or None

    aligned_prices, aligned_preds = prices_df.align(predictions, join='inner', axis=0)

    for i in range(len(aligned_prices) - 1):
        price = aligned_prices['close'].iloc[i]
        open_next = aligned_prices['open'].iloc[i+1]
        high = aligned_prices['high'].iloc[i]
        low = aligned_prices['low'].iloc[i]
        pred = aligned_preds.iloc[i]

        # Exit logic (רק SL/TP)
        if position_type == 'long':
            if sl_price is not None and low <= sl_price:
                exit_price = sl_price * (1 - slippage)
                balance += (exit_price - entry_price) * position_size_shares
                balance -= (position_size_shares * exit_price * (commission + slippage))
                trades.append({'type': 'long', 'entry': entry_price, 'exit': exit_price, 'reason': 'SL'})
                position_type = None
                position_size_shares = 0
                entry_price = 0
                sl_price = None
                tp_price = None
            elif tp_price is not None and high >= tp_price:
                exit_price = tp_price * (1 - slippage)
                balance += (exit_price - entry_price) * position_size_shares
                balance -= (position_size_shares * exit_price * (commission + slippage))
                trades.append({'type': 'long', 'entry': entry_price, 'exit': exit_price, 'reason': 'TP'})
                position_type = None
                position_size_shares = 0
                entry_price = 0
                sl_price = None
                tp_price = None

        # Entry logic (Long only, risk-based sizing)
        if position_type is None and pred == 1:
            entry_price = open_next * (1 + slippage)
            # חישוב גודל פוזיציה מבוסס אחוז הפסד
            if sl_pct > 0:
                position_size_shares = (balance * risk_per_trade) / (entry_price * sl_pct)
            else:
                position_size_shares = 0
            position_size_shares = np.floor(position_size_shares)
            if position_size_shares < 1:
                position_size_shares = 0
                position_type = None
            else:
                balance -= (position_size_shares * entry_price * commission)
                position_type = 'long'
                # חישוב SL ו-TP כאחוז ממחיר הכניסה
                sl_price = entry_price * (1 - sl_pct)
                tp_price = entry_price * (1 + tp_pct)

        # Equity update
        if position_type == 'long':
            current_equity = balance + (position_size_shares * (price - entry_price))
        else:
            current_equity = balance
        equity.append(current_equity)

    # Close open position at end
    if position_type == 'long' and position_size_shares > 0:
        exit_price = aligned_prices['close'].iloc[-1] * (1 - slippage)
        balance += (exit_price - entry_price) * position_size_shares
        balance -= (position_size_shares * exit_price * (commission + slippage))
        trades.append({'type': 'long', 'entry': entry_price, 'exit': exit_price, 'reason': 'End'})

    # Metrics
    if not equity or initial_balance == 0:
        return equity, trades, {'total_return': -2.0, 'sharpe_ratio': -2.0, 'max_drawdown': 0, 'win_rate': 0}
    final_equity = equity[-1]
    total_return = (final_equity / initial_balance) - 1.0
    returns = pd.Series(equity).pct_change().fillna(0)
    sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else -2.0
    running_max = pd.Series(equity).cummax()
    drawdown = (pd.Series(equity) - running_max) / running_max
    max_drawdown = drawdown.min() if not drawdown.empty else 0
    long_trades = [t for t in trades if t.get('type') == 'long']
    win_rate = (sum([t['exit'] > t['entry'] for t in long_trades]) / len(long_trades)) if long_trades else 0
    # Calculate benchmark (buy-and-hold) return
    try:
        start_price = aligned_prices['close'].iloc[0]
        end_price = aligned_prices['close'].iloc[-1]
        if start_price != 0:
            benchmark_return = (end_price / start_price) - 1
        else:
            benchmark_return = 0
    except Exception as e:
        logging.error(f"Error calculating benchmark return: {e}")
        benchmark_return = 0

    metrics = {
        'total_return': total_return if np.isfinite(total_return) else -2.0,
        'sharpe_ratio': sharpe_ratio if np.isfinite(sharpe_ratio) else -2.0,
        'max_drawdown': max_drawdown if np.isfinite(max_drawdown) else 0,
        'win_rate': win_rate if np.isfinite(win_rate) else 0,
        'num_trades': len(trades),
        'benchmark_return': benchmark_return
    }
    return equity, trades, metrics
