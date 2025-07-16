import logging
import os
from datetime import datetime

# --- Logging configuration ---
os.makedirs('logs', exist_ok=True)
log_file = os.path.join('logs', 'data_collector.log')
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
from ib_insync import IB, Stock, Index, util
import pandas as pd
import os
from datetime import datetime
import json
from dotenv import load_dotenv
import sys

# הוספת הנתיב הראשי של הפרויקט כדי לאפשר ייבוא מ-src
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.utils import load_system_config

# --- טען קונפיגורציה מ-system_config.json ---
system_config = load_system_config()
ibkr_settings = system_config.get('ibkr_settings', {})
IB_HOST = ibkr_settings.get('host', '127.0.0.1')
IB_PORT = int(ibkr_settings.get('port', 4001))
IB_CLIENTID = int(ibkr_settings.get('clientId', 123))


def fetch_all_historical_data(symbol='SPY', exchange='SMART', currency='USD', duration='15 Y', barSize='1 day', whatToShow='TRADES'):
    """
    Collects historical data for SPY and VIX from Interactive Brokers TWS/Gateway only.
    Saves the data as CSV in data/raw/{symbol}_ibkr.csv and data/raw/VIX_ibkr.csv
    """
    logging.info(f"Connecting to Interactive Brokers for symbols: {symbol}, VIX")
    ib = IB()
    try:
        logging.info("Attempting IBKR connection...")
        ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENTID)
        logging.info("Connected to IBKR!")
        # SPY
        contract = Stock(symbol, exchange, currency)
        ib.qualifyContracts(contract)
        logging.info(f"Requesting historical data for {symbol}...")
        bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=barSize,
            whatToShow=whatToShow,
            useRTH=True,
            formatDate=1
        )
        if not bars:
            logging.error(f"No data received for {symbol} from IBKR.")
        else:
            df = util.df(bars)
            os.makedirs('data/raw', exist_ok=True)
            out_path = f'data/raw/{symbol}_ibkr.csv'
            df.to_csv(out_path, index=False)
            logging.info(f"Saved {len(df)} rows to {out_path}")
        # VIX כ-Index
        vix_contract = Index('VIX', 'CBOE', 'USD')
        ib.qualifyContracts(vix_contract)
        logging.info("Requesting historical data for VIX...")
        vix_bars = ib.reqHistoricalData(
            vix_contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=barSize,
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1
        )
        if not vix_bars:
            logging.error("No data received for VIX from IBKR.")
        else:
            vix_df = util.df(vix_bars)
            vix_out_path = 'data/raw/VIX_ibkr.csv'
            vix_df.to_csv(vix_out_path, index=False)
            logging.info(f"Saved {len(vix_df)} rows to {vix_out_path}")
    except Exception as e:
        logging.error(f"IBKR data collection failed: {e}")
        raise
    finally:
        logging.info("Disconnecting from IBKR...")
        ib.disconnect()
        logging.info("Disconnected from IBKR.")

def fetch_option_greeks(symbol='SPY', exchange='SMART', currency='USD', expiry=None, strike=None, right='C'):
    """משיכת Greeks של אופציה בודדת לדוגמה"""
    from ib_insync import Option
    ib = IB()
    try:
        ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENTID)
        option = Option(symbol, expiry or '', strike or 0, right, exchange, currency)
        ib.qualifyContracts(option)
        ticker = ib.reqMktData(option, '', False, False)
        ib.sleep(2)
        greeks = ticker.modelGreeks
        if greeks:
            df = pd.DataFrame([{k: getattr(greeks, k) for k in dir(greeks) if not k.startswith('_')}])
            out_path = f'data/raw/{symbol}_option_greeks.csv'
            df.to_csv(out_path, index=False)
            print(f"[INFO] Saved option greeks to {out_path}")
        else:
            print("[WARN] No greeks data received.")
    except Exception as e:
        print(f"[ERROR] Option Greeks fetch failed: {e}")
    finally:
        ib.disconnect()

def fetch_book_data(symbol='SPY', exchange='SMART', currency='USD'):
    """משיכת עומק שוק (Level 2 Book) לדוגמה"""
    from ib_insync import Stock
    ib = IB()
    try:
        ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENTID)
        contract = Stock(symbol, exchange, currency)
        ib.qualifyContracts(contract)
        ticker = ib.reqMktDepth(contract, numRows=5)
        ib.sleep(2)
        if ticker:
            df = util.df(ticker)
            out_path = f'data/raw/{symbol}_book.csv'
            df.to_csv(out_path, index=False)
            print(f"[INFO] Saved book data to {out_path}")
        else:
            print("[WARN] No book data received.")
    except Exception as e:
        print(f"[ERROR] Book data fetch failed: {e}")
    finally:
        ib.disconnect()

def fetch_fundamentals(symbol='SPY', exchange='SMART', currency='USD'):
    """משיכת נתונים פנדומנטליים לדוגמה (snapshot)"""
    from ib_insync import Stock
    ib = IB()
    try:
        ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENTID)
        contract = Stock(symbol, exchange, currency)
        ib.qualifyContracts(contract)
        snapshot = ib.reqFundamentalData(contract, reportType='ReportSnapshot')
        if snapshot:
            out_path = f'data/raw/{symbol}_fundamentals.xml'
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(snapshot)
            print(f"[INFO] Saved fundamentals to {out_path}")
        else:
            print("[WARN] No fundamentals data received.")
    except Exception as e:
        print(f"[ERROR] Fundamentals fetch failed: {e}")
    finally:
        ib.disconnect()

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        fetch_all_historical_data()
    elif sys.argv[1] == "greeks":
        fetch_option_greeks()
    elif sys.argv[1] == "book":
        fetch_book_data()
    elif sys.argv[1] == "fundamentals":
        fetch_fundamentals()
    else:
        print("Unknown argument. Use: greeks | book | fundamentals | (none for historical data)")
