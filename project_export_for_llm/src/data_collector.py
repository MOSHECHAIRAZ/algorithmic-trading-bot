import logging
import os
import sys
import time  # הוסף ייבוא של time לצורך מדידת זמני ביצוע
# ייבואים לא בשימוש הוסרו
import pandas as pd
from ib_insync import IB, Stock, Index, util

# הוספת הנתיב הראשי של הפרויקט כדי לאפשר ייבוא מ-src
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
    
# אנחנו מעבירים את הייבואים למעלה כנדרש לפי flake8
from src.utils import load_system_config

# --- Logging configuration ---
os.makedirs('logs', exist_ok=True)
log_file = os.path.join('logs', 'data_collector.log')
logging.basicConfig(
    level=logging.DEBUG,  # שינוי רמת הלוג ל-DEBUG לקבלת מידע מפורט יותר
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# --- טען קונפיגורציה מ-system_config.json ---
system_config = load_system_config()
ibkr_settings = system_config.get('ibkr_settings', {})
IB_HOST = ibkr_settings.get('host', '127.0.0.1')
IB_PORT = int(ibkr_settings.get('port', 4001))
# משתמשים במזהה לקוח אקראי כדי למנוע התנגשויות
import random
IB_CLIENTID = random.randint(10000, 99999)


def fetch_all_historical_data(symbol='SPY', exchange='SMART', currency='USD', duration='15 Y', barSize='1 day', whatToShow='TRADES'):
    """
    Collects historical data for SPY and VIX from Interactive Brokers TWS/Gateway only.
    Saves the data as CSV in data/raw/{symbol}_ibkr.csv and data/raw/VIX_ibkr.csv
    """
    start_time = time.time()
    logging.info(f"Starting historical data collection process")
    logging.info(f"Target symbols: {symbol}, VIX")
    logging.info(f"Parameters: duration={duration}, barSize={barSize}, whatToShow={whatToShow}")
    logging.debug(f"IBKR connection parameters: Host={IB_HOST}, Port={IB_PORT}, ClientId={IB_CLIENTID}")
    
    # יצירת אובייקט IB
    ib = IB()
    
    try:
        logging.info("Attempting IBKR connection...")
        
        # בדיקה האם ה-port פתוח לפני ניסיון החיבור
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((IB_HOST, IB_PORT))
        if result == 0:
            logging.debug(f"Port {IB_PORT} is open and accepting connections")
        else:
            logging.error(f"Port {IB_PORT} is not open. Connection might fail. Error code: {result}")
        sock.close()
        
        # הגדלת זמן ה-timeout ל-60 שניות
        logging.debug("Starting IB.connect() with 60s timeout")
        ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENTID, timeout=60)
        logging.debug("IB.connect() call returned successfully")
        
        # מחכה רגע לוודא שהחיבור יציב
        logging.debug("Waiting 2 seconds for connection to stabilize")
        time.sleep(2)
        
        # מוודא שהחיבור פעיל
        connected = ib.isConnected()
        logging.debug(f"Connection check after 2s: isConnected={connected}")
        if not connected:
            logging.error("Failed to establish stable connection to IBKR")
            return
            
        logging.info("Connected to IBKR!")
        
        # יצירת רשימה ריקה למקרה של כישלון
        account_values = []
        accounts = []
        
        try:
            server_version = ib.client.serverVersion()
            connection_time = ib.client.twsConnectionTime()
            logging.info(f"API connection version: {server_version}")
            logging.info(f"Connection time: {connection_time}")
        except Exception as e:
            logging.error(f"Error getting server info: {e}", exc_info=True)
        
        # נדלג על בדיקת account values ונמשיך ישירות להורדת נתונים היסטוריים
        
        # רשימת מניות זמינות לבדיקה - מתחילים עם הראשון ברשימה
        symbols_to_try = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'AMZN']
        
        # נדלג על בדיקות המניות ונמשיך ישירות להורדת נתונים היסטוריים
        logging.debug("Skipping symbol testing, moving directly to historical data")
        
        # המשך הקוד המקורי...
        # SPY
        try:
            logging.debug(f"Creating contract for historical data: {symbol}")
            contract = Stock(symbol, exchange, currency)
            
            logging.debug("Qualifying contract")
            ib.qualifyContracts(contract)
            
            logging.info(f"Requesting historical data for {symbol}...")
            
            # מנסה לקבל נתונים עם פסקי זמן קטנים יותר
            try:
                # קבלת יום אחד בלבד לבדיקה
                logging.debug(f"Requesting only 1 day of data for initial test")
                test_bars = ib.reqHistoricalData(
                    contract,
                    endDateTime='',
                    durationStr='1 D',  # רק יום אחד במקום 15 שנה
                    barSizeSetting=barSize,
                    whatToShow=whatToShow,
                    useRTH=True,
                    formatDate=1,
                    timeout=15  # זמן קצר יותר לבדיקה
                )
                
                if test_bars:
                    logging.info(f"Test successful! Received {len(test_bars)} bars for 1 day")
                    
                    # עכשיו ננסה לקבל את כל הנתונים
                    logging.debug(f"Now requesting full data: duration={duration}, barSize={barSize}")
                    bars = ib.reqHistoricalData(
                        contract,
                        endDateTime='',
                        durationStr=duration,
                        barSizeSetting=barSize,
                        whatToShow=whatToShow,
                        useRTH=True,
                        formatDate=1,
                        timeout=30
                    )
                    logging.debug(f"Historical data request returned {len(bars) if bars else 0} bars")
                else:
                    logging.error("Test request failed, not attempting full data request")
                    bars = None
            except Exception as e:
                logging.error(f"Error requesting {symbol} data: {e}", exc_info=True)
                bars = None
                
            if not bars:
                logging.error(f"No data received for {symbol} from IBKR.")
            else:
                try:
                    logging.debug(f"Converting {len(bars)} bars to DataFrame")
                    df = util.df(bars)
                    
                    logging.debug("Ensuring data/raw directory exists")
                    os.makedirs('data/raw', exist_ok=True)
                    
                    out_path = f'data/raw/{symbol}_ibkr.csv'
                    logging.debug(f"Saving data to {out_path}")
                    df.to_csv(out_path, index=False)
                    
                    logging.info(f"Saved {len(df)} rows to {out_path}")
                except Exception as e:
                    logging.error(f"Error saving {symbol} data: {e}", exc_info=True)
        except Exception as e:
            logging.error(f"Error processing {symbol}: {e}", exc_info=True)
        # VIX כ-Index
        try:
            logging.debug("Creating VIX contract")
            vix_contract = Index('VIX', 'CBOE', 'USD')
            
            logging.debug("Qualifying VIX contract")
            ib.qualifyContracts(vix_contract)
            
            logging.info("Requesting historical data for VIX...")
            
            # מנסה לקבל נתונים עם פסקי זמן קטנים יותר
            try:
                # קבלת יום אחד בלבד לבדיקה
                logging.debug(f"Requesting only 1 day of VIX data for initial test")
                test_vix_bars = ib.reqHistoricalData(
                    vix_contract,
                    endDateTime='',
                    durationStr='1 D',  # רק יום אחד במקום 15 שנה
                    barSizeSetting=barSize,
                    whatToShow='TRADES',
                    useRTH=True,
                    formatDate=1,
                    timeout=15  # זמן קצר יותר לבדיקה
                )
                
                if test_vix_bars:
                    logging.info(f"VIX test successful! Received {len(test_vix_bars)} bars for 1 day")
                    
                    # עכשיו ננסה לקבל את כל הנתונים
                    logging.debug(f"Now requesting full VIX data: duration={duration}")
                    vix_bars = ib.reqHistoricalData(
                        vix_contract,
                        endDateTime='',
                        durationStr=duration,
                        barSizeSetting=barSize,
                        whatToShow='TRADES',
                        useRTH=True,
                        formatDate=1,
                        timeout=30
                    )
                    logging.debug(f"VIX historical data request returned {len(vix_bars) if vix_bars else 0} bars")
                else:
                    logging.error("VIX test request failed, not attempting full data request")
                    vix_bars = None
            except Exception as e:
                logging.error(f"Error requesting VIX data: {e}", exc_info=True)
                vix_bars = None
                
            if not vix_bars:
                logging.error("No data received for VIX from IBKR.")
            else:
                try:
                    logging.debug(f"Converting {len(vix_bars)} VIX bars to DataFrame")
                    vix_df = util.df(vix_bars)
                    
                    vix_out_path = 'data/raw/VIX_ibkr.csv'
                    logging.debug(f"Saving VIX data to {vix_out_path}")
                    vix_df.to_csv(vix_out_path, index=False)
                    
                    logging.info(f"Saved {len(vix_df)} rows to {vix_out_path}")
                except Exception as e:
                    logging.error(f"Error saving VIX data: {e}", exc_info=True)
        except Exception as e:
            logging.error(f"Error processing VIX: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"IBKR data collection failed: {e}", exc_info=True)
        raise
    finally:
        logging.info("Disconnecting from IBKR...")
        try:
            ib.disconnect()
            logging.info("Disconnected from IBKR.")
        except Exception as e:
            logging.error(f"Error during disconnect: {e}", exc_info=True)
        
        # סיכום הפעילות וזמן ביצוע
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info("-" * 40)
        logging.info(f"Historical data collection summary:")
        logging.info(f"Total execution time: {elapsed_time:.2f} seconds")
        logging.info(f"SPY data: {'Success' if 'bars' in locals() and bars is not None else 'Failed'}")
        logging.info(f"VIX data: {'Success' if 'vix_bars' in locals() and vix_bars is not None else 'Failed'}")
        logging.info("-" * 40)
        
        return {'SPY': 'bars' in locals() and bars is not None, 
                'VIX': 'vix_bars' in locals() and vix_bars is not None,
                'elapsed_time': elapsed_time}


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


def main():
    """
    Main entry point for data collection.
    """
    logging.info("-" * 50)
    logging.info("Data Collector Starting")
    logging.info("-" * 50)
    
    try:
        # מנסה להתחבר ל-IB
        logging.info("Connecting to Interactive Brokers...")
        config = load_system_config()
        
        host = config.get('ibkr_gateway', {}).get('host', '127.0.0.1')
        port = config.get('ibkr_gateway', {}).get('port', 4001)
        client_id = config.get('ibkr_gateway', {}).get('client_id', 1)
        
        logging.info(f"Connecting to IB at {host}:{port} with client ID {client_id}")
        
        # מוסיף פרטי חיבור נוספים ללוג
        logging.info(f"TWS/Gateway connection parameters:")
        logging.info(f"  - Host: {host}")
        logging.info(f"  - Port: {port}")
        logging.info(f"  - Client ID: {client_id}")
        logging.info(f"  - Connection timeout: 30 seconds")
        
        # יצירת מופע IB ללא חיבור עדיין
        ib = IB()
        
        # ניסיון התחברות עם טיימאאוט
        connection_start = time.time()
        logging.info("Attempting connection...")
        ib.connect(host, port, clientId=client_id, timeout=30, readonly=True)
        connection_time = time.time() - connection_start
        logging.info(f"Connection established in {connection_time:.2f} seconds")
        
        # בודק אם החיבור הצליח
        if not ib.isConnected():
            logging.error("Failed to connect to IB Gateway/TWS")
            return False
            
        logging.info("Successfully connected to IB Gateway/TWS")
        
        # מידע על חיבור
        server_time = ib.reqCurrentTime()
        logging.info(f"Server time: {server_time}")
        
        # איסוף נתונים
        all_data = fetch_all_historical_data()
        
        # בדיקת תוצאות
        if all_data:
            logging.info("Data collection results:")
            for symbol, success in all_data.items():
                if symbol != 'elapsed_time':
                    logging.info(f"  - {symbol}: {'Success' if success else 'Failed'}")
            
            # בדיקה אם לפחות סימול אחד הצליח
            success_count = sum(1 for k, v in all_data.items() if k != 'elapsed_time' and v)
            if success_count > 0:
                logging.info(f"Successfully collected data for {success_count} symbols")
            else:
                logging.error("Failed to collect data for any symbols")
                return False
        else:
            logging.error("Data collection failed completely")
            return False
        
        # ניתוק מ-IB
        logging.info("Disconnecting from IB Gateway/TWS")
        ib.disconnect()
        
        return True
        
    except Exception as e:
        logging.error(f"Error in data collection: {e}", exc_info=True)
        return False
        
    finally:
        logging.info("-" * 50)
        logging.info("Data Collector Finished")
        logging.info("-" * 50)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        main()  # Call main() instead of fetch_all_historical_data() directly
    elif sys.argv[1] == "greeks":
        fetch_option_greeks()
    elif sys.argv[1] == "book":
        fetch_book_data()
    elif sys.argv[1] == "fundamentals":
        fetch_fundamentals()
    else:
        print("Unknown argument. Use: greeks | book | fundamentals | (none for historical data)")
