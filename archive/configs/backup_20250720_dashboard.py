# dashboard.py
"""
דשבורד ניהול - בוט מסחר אלגוריתמי
ממשק משתמש באמצעות Streamlit - גרסה מלאה ומתוקנת
"""
import streamlit as st
import json
import os
import sys
import subprocess
import time
import hashlib
import glob
import atexit
import traceback
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import optuna
from streamlit_cookies_manager import EncryptedCookieManager

from src.utils import load_system_config, save_system_config

# --- הגדרות כלליות ---
# --- Cookie Manager ---
cookie_password = os.environ.get("COOKIE_ENCRYPTION_PASSWORD", "default_cookie_password")
cookies = EncryptedCookieManager(
    password=cookie_password,
)
if not cookies.ready():
    st.stop()

# --- פונקציות עזר ---

@st.cache_data
def load_training_summaries():
    """
    Load and parse the main and archived training summary JSON files, returning a pandas DataFrame.
    """
    try:
        config = load_system_config()
        model_dir = Path(config['system_paths']['champion_model']).parent
        archive_dir = model_dir / 'archive'
        main_summary_file = model_dir / 'training_summary.json'
        archived_summaries = sorted(glob.glob(str(archive_dir / 'training_summary.json.*')), reverse=True)

        summary_files = []
        if main_summary_file.exists():
            summary_files.append(str(main_summary_file))
        summary_files.extend(archived_summaries)

        rows = []
        for fpath_str in summary_files:
            fpath = Path(fpath_str)
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)

                file_ts = data.get('training_run_timestamp')
                if not file_ts:
                    continue  # Skip if the essential timestamp is missing

                best_params = data.get('best_params', {})
                all_params = data.get('all_params', {})
                class_report = data.get('classification_report', {})
                
                row = {
                    'timestamp': pd.to_datetime(data.get('timestamp')).strftime('%Y-%m-%d %H:%M') if data.get('timestamp') else 'N/A',
                    'objective_function': data.get('objective_function'),
                    'optuna_scores': str(data.get('optuna_scores', 'N/A')),
                    'test_accuracy': data.get('test_accuracy'),
                    'file_ts': file_ts,
                    'recall_0': class_report.get('0', {}).get('recall'),
                    'precision_0': class_report.get('0', {}).get('precision'),
                    'f1_0': class_report.get('0', {}).get('f1-score'),
                    'support_0': class_report.get('0', {}).get('support'),
                    'recall_1': class_report.get('1', {}).get('recall'),
                    'precision_1': class_report.get('1', {}).get('precision'),
                    'f1_1': class_report.get('1', {}).get('f1-score'),
                    'support_1': class_report.get('1', {}).get('support'),
                }
                
                # הוספת הפרמטרים עם סימון אופטימיזציה
                if all_params:
                    # אם יש all_params, השתמש בהם
                    for param_name, param_info in all_params.items():
                        value = param_info.get('value', 'N/A')
                        optimized = param_info.get('optimized', False)
                        
                        # עיצוב הערך בהתאם לסוג
                        if param_name in ['threshold', 'risk_per_trade'] and isinstance(value, float):
                            formatted_value = f"{value*100:.2f}%"
                        else:
                            formatted_value = value
                        
                        # הוספת סימון אופטימיזציה
                        if optimized:
                            row[param_name] = f"🔄 {formatted_value}"
                        else:
                            row[param_name] = f"⚪ {formatted_value}"
                else:
                    # אם אין all_params, השתמש ב-best_params הישן
                    for k, v in best_params.items():
                        if k in ['threshold', 'risk_per_trade'] and isinstance(v, float):
                            row[k] = f"{v*100:.2f}%"
                        else:
                            row[k] = v
                rows.append(row)
            except (json.JSONDecodeError, KeyError, TypeError):
                # Silently skip corrupted or malformed summary files
                continue
                
        if rows:
            return pd.DataFrame(rows).fillna('N/A')
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error loading training summaries: {e}")
        return pd.DataFrame()

def set_rtl_layout():
    """Injects custom CSS to force RTL layout and fix pinned columns."""
    st.markdown(
        """
        <style>
        /* ========= General RTL Layout ========= */
        html, body, [class*="st-"] {
            direction: rtl !important;
            text-align: right !important;
        }
        .st-emotion-cache-16txtl3 { /* Expander header */
            text-align: right !important;
        }
        th, td { /* Table headers and cells */
            text-align: right !important;
            direction: rtl !important;
        }

        /* ========= Advanced Pinned Column Fix ========= */
        /* Find the container for the table cells */
        .st-emotion-cache-tcwslb {
            direction: ltr !important; /* Force LTR on the direct container */
        }
        /* Find the row container and reverse its element order */
        .st-emotion-cache-10trblm {
            display: flex !important;
            flex-direction: row-reverse !important;
        }
        /* Style the pinned (sticky) columns */
        div[data-testid="stDataFrameTable"] [data-sticky-td] {
            left: unset !important;
            right: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def show_alert(msg, type_='info'):
    """פונקציה להצגת התראה בולטת."""
    if type_ == 'success':
        st.success(msg)
    elif type_ == 'error':
        st.error(msg)
    elif type_ == 'warning':
        st.warning(msg)
    else:
        st.info(msg)

def run_and_stream_process(command, spinner_text):
    """מריץ תהליך ומזרים את הפלט שלו בזמן אמת לדשבורד."""
    progress_bar = st.progress(0, text="מתחיל...")
    log_content = ""
    
    with st.expander(f"צפה בפלט החי של: {spinner_text}", expanded=True):
        output_placeholder = st.code("", language='log')
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            st.session_state['last_process'] = process

            for i, line in enumerate(iter(process.stdout.readline, '')):
                log_content += line
                output_placeholder.code(log_content, language='log')
                # Improved progress bar logic for better UX
                progress = min(0.95, 0.05 + i * 0.0005) 
                progress_bar.progress(progress, text=f"{spinner_text} (מעבד שורה {i+1})...")

            process.wait()
            progress_bar.progress(1.0, text="הסתיים!")
            
            if process.returncode == 0:
                show_alert(f"התהליך '{' '.join(command)}' הסתיים בהצלחה!", type_='success')
            else:
                show_alert(f"התהליך '{' '.join(command)}' נכשל עם קוד שגיאה {process.returncode}.", type_='error')

        except FileNotFoundError:
            show_alert(f"שגיאה: הפקודה '{command[0]}' לא נמצאה. ודא שהנתיב נכון.", type_='error')
            log_content += f"ERROR: Command not found: {command[0]}"
            output_placeholder.code(log_content, language='log')
            progress_bar.progress(1.0, text="נכשל!")
        except Exception as e:
            show_alert(f"שגיאה בהרצת התהליך: {e}", type_='error')
            log_content += f"\n--- TRACEBACK ---\n{traceback.format_exc()}"
            output_placeholder.code(log_content, language='log')
            progress_bar.progress(1.0, text="נכשל!")

def cleanup_processes():
    """מנקה תהליכים פתוחים בסגירת הדשבורד."""
    for key in ['api_process', 'agent_process', 'optuna_dashboard_proc']:
        proc = st.session_state.get(key)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                pass
atexit.register(cleanup_processes)

def get_process_status(proc):
    """בודק סטטוס של תהליך."""
    if not proc: return 'לא הופעל'
    return 'רץ' if proc.poll() is None else f'הסתיים (קוד {proc.returncode})'

def stop_process(key):
    """עוצר תהליך לפי מפתח ב-session_state."""
    proc = st.session_state.get(key)
    if proc and proc.poll() is None:
        proc.terminate()
        st.session_state[key] = None
        st.toast(f"התהליך '{key}' נעצר.")
        time.sleep(1)
        st.rerun()

st.set_page_config(
    page_title="דשבורד ניהול - בוט מסחר אלגוריתמי",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📊"
)
set_rtl_layout()

# --- ניהול סיסמה ---
PASSWORD_FILE = Path("dashboard_password.txt")

def get_password_hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_dashboard_password(pw):
    if not PASSWORD_FILE.exists():
        default_pw = os.environ.get('DASHBOARD_PASSWORD', 'admin')
        with open(PASSWORD_FILE, 'w') as f:
            f.write(get_password_hash(default_pw))
    with open(PASSWORD_FILE, 'r') as f:
        saved_hash = f.read().strip()
    return get_password_hash(pw) == saved_hash

# --- תפריט צד ואימות ---
st.sidebar.title("ניווט")

if st.session_state.get('authenticated', False):  
    pass
elif cookies.get('authenticated_user'):
    st.session_state['authenticated'] = True
else:
    st.session_state['authenticated'] = False

if not st.session_state.authenticated:
    st.title("כניסה למערכת")
    pwd = st.text_input("סיסמה:", type="password")
    if st.button("התחבר"):
        if check_dashboard_password(pwd):
            st.session_state.authenticated = True
            cookies['authenticated_user'] = pwd
            cookies.save()
            st.rerun()
        else:
            st.error("סיסמה שגויה.")
    st.stop()

# --- תוכן הדשבורד (מוצג רק לאחר אימות) ---
page = st.sidebar.radio(
    "בחר עמוד:",
    ("סקירה כללית", "ניהול המערכת", "לוגים", "תצורת מערכת", "ניתוח תוצאות"),
    key="nav_radio"
)
st.sidebar.markdown("---")
if st.sidebar.button("התנתק"):
    st.session_state.authenticated = False
    del cookies['authenticated_user']
    cookies.save()
    st.rerun()

# --- עמוד סקירה כללית ---
if page == "סקירה כללית":
    st.markdown("---")
    st.subheader(":rotating_light: פיקוד ידני")
    command_path = Path('agent/command.json')
    current_command = {}
    if command_path.exists():
        try:
            with open(command_path, encoding='utf-8') as f:
                content = f.read()
                current_command = json.loads(content) if content else {}
        except Exception:
            current_command = {}

    colmo1, colmo2, colmo3 = st.columns([2, 2, 2])
    with colmo1:
        if st.button("🚨 סגור את כל הפוזיציות מיד (שוק)!", type="primary"):
            cmd = {"command": "CLOSE_ALL", "timestamp": datetime.now().isoformat()}
            with open(command_path, 'w', encoding='utf-8') as f:
                json.dump(cmd, f)
            st.warning("פקודת סגירת כל הפוזיציות נשלחה לסוכן!", icon="⚠️")
    with colmo2:
        pause_state = current_command.get('pause_new_entries', False)
        pause_toggle = st.toggle("השהה כניסה לפוזיציות חדשות", value=pause_state)
        if pause_toggle != pause_state:
            cmd = {"command": "PAUSE_NEW_ENTRIES", "pause_new_entries": pause_toggle, "timestamp": datetime.now().isoformat()}
            with open(command_path, 'w', encoding='utf-8') as f:
                json.dump(cmd, f)
            st.info(f"מצב השהיית כניסות עודכן ל-{pause_toggle}")
    with colmo3:
        if st.button("🔄 הפעל מחדש את לוגיקת המסחר"):
            cmd = {"command": "RESTART_LOGIC", "timestamp": datetime.now().isoformat()}
            with open(command_path, 'w', encoding='utf-8') as f:
                json.dump(cmd, f)
            st.success("פקודת הפעלה מחדש נשלחה לסוכן.")

    st.title("📊 סקירה כללית ומצב המערכת")
    
    # סטטוס מערכת בזמן אמת
    st.subheader("🔄 סטטוס מערכת בזמן אמת")
    
    # בדיקת סטטוס אימון
    def check_training_status():
        try:
            # בדיקה אם קיים תהליך אימון פעיל
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'main_trainer.py' in ' '.join(proc.info['cmdline'] or []):
                    return "🟢 פעיל", f"PID: {proc.info['pid']}"
            return "🔴 לא פעיל", "לא רץ כרגע"
        except:
            return "⚪ לא ידוע", "לא ניתן לבדוק"
    
    # בדיקת סטטוס backtester
    def check_backtester_status():
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'backtester.py' in ' '.join(proc.info['cmdline'] or []):
                    return "🟢 פעיל", f"PID: {proc.info['pid']}"
            return "🔴 לא פעיל", "לא רץ כרגע"
        except:
            return "⚪ לא ידוע", "לא ניתן לבדוק"
    
    # הצגת סטטוס במטריקות
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        api_proc = st.session_state.get('api_process')
        api_status = get_process_status(api_proc)
        st.metric("🌐 שרת API", api_status)
    
    with col2:
        agent_proc = st.session_state.get('agent_process')
        agent_status = get_process_status(agent_proc)
        st.metric("🤖 סוכן מסחר", agent_status)
    
    with col3:
        training_status, training_detail = check_training_status()
        st.metric("🧠 אימון מודל", training_status, training_detail)
    
    with col4:
        backtester_status, backtester_detail = check_backtester_status()
        st.metric("📊 Backtester", backtester_status, backtester_detail)
    
    st.subheader("🎛️ בקרת תהליכים")
    api_proc = st.session_state.get('api_process')
    agent_proc = st.session_state.get('agent_process')

    col1, col2 = st.columns(2)
    with col1:
        if api_proc and api_proc.poll() is None:
            if st.button("⏹️ עצור שרת ה-API"):
                stop_process('api_process')
        else:
            if st.button("▶️ הפעל שרת ה-API"):
                proc = subprocess.Popen([sys.executable, "model_api.py"])
                st.session_state['api_process'] = proc
                st.rerun()
    with col2:
        if agent_proc and agent_proc.poll() is None:
            if st.button("⏹️ עצור סוכן מסחר"):
                stop_process('agent_process')
        else:
            if st.button("▶️ הפעל סוכן מסחר"):
                proc = subprocess.Popen(["node", "agent/trading_agent.js"])
                st.session_state['agent_process'] = proc
                st.rerun()

    st.markdown("---")
    st.subheader(":chart_with_upwards_trend: מצב פוזיציה חי")
    db_path = 'agent/state.db'
    trade_state = {}
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        row = cur.execute("SELECT value FROM state WHERE key = ?", ('trade_state',)).fetchone()
        trade_state = json.loads(row[0]) if row and row[0] else {}
        conn.close()
    except Exception as e:
        st.error(f"שגיאה בגישה ל-agent/state.db: {e}")

    position = trade_state.get('position')
    size = trade_state.get('size')
    entry = trade_state.get('entryPrice')
    stop_loss = trade_state.get('stopLoss')
    take_profit = trade_state.get('takeProfit')
    
    try:
        config = load_system_config()
        symbol = config.get('contract', {}).get('symbol', 'SPY')
    except Exception:
        symbol = 'SPY'

    st.info(f"נכס: {symbol}")
    if not position:
        st.write(":blue_circle: אין פוזיציה פעילה.")
    else:
        st.write(f"**פוזיציה נוכחית:** {'לונג' if position == 'long' else 'שורט' if position == 'short' else position}")
        st.write(f"**גודל:** {size if size is not None else '-'} מניות")
        st.write(f"**מחיר כניסה:** ${entry if entry is not None else '-'}")
        st.write(f"**עצירת הפסד (SL):** ${stop_loss if stop_loss is not None else '-'}")
        st.write(f"**לקיחת רווח (TP):** ${take_profit if take_profit is not None else '-'}")

    colr1, colr2 = st.columns([1, 1])
    with colr1:
        if st.button("רענן מצב פוזיציה"):
            st.rerun()
    with colr2:
        refresh = st.checkbox("רענון אוטומטי כל 5 שניות", value=False)
        if refresh:
            time.sleep(5)
            st.rerun()

    st.markdown("---")
    st.subheader("בדיקת זמינות ה-API")
    try:
        resp = requests.get("http://localhost:5000/status", timeout=3)
        if resp.status_code == 200 and resp.json().get('model_loaded'):
            st.success("שרת ה-API פעיל והמודל טעון בהצלחה.", icon="✅")
            st.json(resp.json())
        else:
            st.warning("שרת ה-API זמין אך המודל לא טעון או שישנה בעיה אחרת.", icon="⚠️")
    except requests.exceptions.ConnectionError:
        st.error("שרת ה-API לא זמין. ודא שהפעלת את שרת ה-API.", icon="❌")
    except Exception as e:
        st.error(f"שגיאה בבדיקת שרת ה-API: {e}")

# --- עמוד ניהול המערכת ---
elif page == "ניהול המערכת":
    st.markdown("---")
    st.subheader(":bar_chart: בריאות נתונים (Data Health)")
    data_files = [
        ("SPY_ibkr.csv", "data/raw/SPY_ibkr.csv"),
        ("VIX_ibkr.csv", "data/raw/VIX_ibkr.csv"),
        ("SPY_processed.csv", "data/processed/SPY_processed.csv")
    ]
    table = []
    for label, path in data_files:
        file_info = {"קובץ": label, "תאריך שינוי": "-", "גודל (MB)": "-", "שורות": "-"}
        if os.path.exists(path):
            stat = os.stat(path)
            file_info["תאריך שינוי"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            file_info["גודל (MB)"] = f"{stat.st_size/1024/1024:.2f}"
            try:
                nrows = sum(1 for _ in open(path, encoding='utf-8', errors='ignore')) - 1
                file_info["שורות"] = str(nrows)
            except Exception:
                file_info["שורות"] = "?"
        table.append(file_info)
    st.table(table)

    if st.button("🧹 אפס ואסוף הכל מחדש", type="primary"):
        for _, path in data_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        st.info("הקבצים נמחקו. מריץ pipeline מלא...")
        run_and_stream_process([sys.executable, "run_all.py"], "מריץ pipeline מלא לאיסוף נתונים ועיבוד...")
    
    st.title("⚙️ ניהול ותפעול המערכת")
    st.subheader("הרצת צינור הנתונים והאימון המלא")
    st.info("תהליך זה מריץ איסוף נתונים, עיבוד מקדים ואימון מודל חדש ברצף.")
    if st.button("🚀 הרץ את כל התהליך (Run All)"):
        run_and_stream_process([sys.executable, "run_all.py"], "מריץ את כל צינור הנתונים והאימון...")

    st.markdown("---")
    st.subheader("הרצת תהליכים בודדים")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("1. איסוף נתונים"):
            run_and_stream_process([sys.executable, "src/data_collector.py"], "אוסף נתונים...")
    with col2:
        if st.button("2. עיבוד נתונים"):
            run_and_stream_process([sys.executable, "run_preprocessing.py"], "מעבד נתונים...")
    with col3:
        if st.button("3. אימון מודל"):
            run_and_stream_process([sys.executable, "main_trainer.py"], "מריץ אימון ואופטימיזציה...")

# --- עמוד לוגים ---
elif page == "לוגים":
    st.title("📜 צפייה בלוגים ודוחות מערכת")
    log_dirs = [Path("logs"), Path("agent"), Path("db")]
    all_files = []
    for log_dir in log_dirs:
        if log_dir.exists():
            all_files.extend(log_dir.glob("**/*"))

    all_files = [f for f in all_files if f.is_file()]

    log_desc = {
        'main_trainer_output.log': 'לוג אימון מודל (main_trainer)',
        'backtester_output.log': 'לוג בדיקות Backtest',
        'trading_log.txt': 'יומן פקודות מסחר',
        'state.db': 'מסד נתונים של מצב הסוכן',
        'test_order.js': 'קוד בדיקות לסוכן',
        'state_manager.js': 'ניהול מצב סוכן',
        'trading_agent.js': 'קוד סוכן מסחר',
    }

    def get_log_label(p: Path):
        desc = log_desc.get(p.name, "")
        return f"{p.name} — {desc}" if desc else str(p)

    if all_files:
        all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        file_labels = [get_log_label(f) for f in all_files]
        selected_idx = st.selectbox(
            "בחר קובץ לוג או דוח להצגה (מסודר לפי עדכון אחרון):",
            range(len(all_files)),
            format_func=lambda i: file_labels[i]
        )
        selected_file_path = all_files[selected_idx]
        if selected_file_path:
            p = Path(selected_file_path)
            st.download_button(f"📥 הורד את {p.name}", data=p.read_bytes(), file_name=p.name)

            if p.suffix.lower() not in ['.db', '.pkl', '.json', '.zip', '.egg', '.pyc']:
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    last_lines = lines[-200:] if len(lines) > 200 else lines
                    st.text_area(f"תוכן {get_log_label(p)} ({len(last_lines)} שורות אחרונות)", "".join(last_lines), height=400)
                except Exception as e:
                    st.error(f"לא ניתן היה לקרוא את הקובץ: {e}")
            else:
                st.info(f"לא ניתן להציג תצוגה מקדימה לקבצים מסוג '{p.suffix}'.")
    else:
        st.warning("לא נמצאו קבצי לוג או דוחות.")

# --- עמוד תצורת מערכת ---
elif page == "תצורת מערכת":
    try:
        config_data = load_system_config()
    except Exception as e:
        st.error(f"שגיאה קריטית בטעינת system_config.json: {e}")
        st.stop()
    
    # הקטנת הדף בעמודות
    col1, col2, col3 = st.columns([1, 4, 1])
    
    with col2:  # השדות יופיעו בעמודה האמצעית
        st.title("📝 עריכת תצורת המערכת")
        
        with st.form(key='config_form'):
            edited_config = json.loads(json.dumps(config_data))

            with st.expander("פרמטרי אימון (Training)", expanded=False):
                # שימוש בעמודות פנימיות לקיצור
                c1, c2 = st.columns(2)
                with c1:
                    edited_config['training_params']['n_trials'] = st.number_input("מספר ניסיונות Optuna", min_value=1, value=edited_config['training_params'].get('n_trials', 100))
                    edited_config['training_params']['cv_splits'] = st.number_input("מספר קפלים (CV)", min_value=2, value=edited_config['training_params'].get('cv_splits', 5))
                    test_size_percent = st.number_input("אחוז בדיקה", min_value=10, max_value=50, value=int(edited_config['training_params'].get('test_size_split', 20)), step=1)
                    edited_config['training_params']['test_size_split'] = test_size_percent
                
                with c2:
                    edited_config['training_params']['n_startup_trials'] = st.number_input("ניסיונות אקראיים", min_value=0, value=edited_config['training_params'].get('n_startup_trials', 10))
                    edited_config['training_params']['years_of_data'] = st.number_input("שנות נתונים", min_value=1, max_value=30, value=edited_config['training_params'].get('years_of_data', 15))
                    
                    optuna_target_options = {
                        'multi_objective': 'רב-יעדי',
                        'total_return': 'תשואה',
                        'sharpe_ratio': 'שארפ'
                    }
                    optuna_target_default = edited_config['training_params'].get('optuna_target_metric', 'multi_objective')
                    if optuna_target_default not in optuna_target_options:
                        optuna_target_default = list(optuna_target_options.keys())[0]
                    optuna_target_index = list(optuna_target_options.keys()).index(optuna_target_default)
                    optuna_target = st.selectbox("יעד אופטימיזציה", options=list(optuna_target_options.keys()), format_func=lambda k: optuna_target_options[k], index=optuna_target_index)
                    edited_config['training_params']['optuna_target_metric'] = optuna_target

            with st.expander("הגדרת גבולות לפרמטרי אופטימיזציה (Optuna)", expanded=False):
                optuna_limits = edited_config.get('optuna_param_limits', {})
                
                param_labels = {
                    'horizon': 'אופק (ימים)', 'threshold': 'סף (%)',
                    'top_n_features': 'פיצ׳רים', 
                    'stop_loss_pct': 'הפסד (%)',
                    'take_profit_pct': 'רווח (%)',
                    'risk_per_trade': 'סיכון (%)',
                    'learning_rate': 'למידה', 'n_estimators': 'עצים', 'max_depth': 'עומק'
                }
                
                for param, lims in optuna_limits.items():
                    if param not in param_labels: continue

                    label = param_labels[param]
                    st.markdown(f"**{label}**")
                    col1, col2, col3 = st.columns(3)

                    is_dynamic = lims.get('optimize', True)
                    min_val = lims.get('min', 0)
                    max_val = lims.get('max', 1)
                    fixed_val = lims.get('fixed_value', min_val)
                    
                    with col1:
                        user_min = st.number_input(
                            "מינימום", 
                            key=f"min_{param}", 
                            value=float(min_val), 
                            format="%.4f"
                        )
                    with col2:
                        user_max = st.number_input(
                            "מקסימום", 
                            key=f"max_{param}", 
                            value=float(max_val), 
                            format="%.4f"
                        )
                    with col3:
                        user_fixed = st.number_input(
                            "ערך קבוע", 
                            key=f"fixed_{param}", 
                            value=float(fixed_val), 
                            format="%.4f"
                        )
                    
                    new_dynamic_state = st.checkbox(
                        "אופטימיזציה פעילה", 
                        value=is_dynamic, 
                        key=f"opt_{param}"
                    )

                    edited_config['optuna_param_limits'][param]['optimize'] = new_dynamic_state
                    edited_config['optuna_param_limits'][param]['min'] = user_min
                    edited_config['optuna_param_limits'][param]['max'] = user_max
                    edited_config['optuna_param_limits'][param]['fixed_value'] = user_fixed
                    st.divider()

            with st.expander("פרמטרי Backtest", expanded=False):
                edited_config['backtest_params']['initial_balance'] = st.number_input("יתרת התחלה ($)", min_value=1000, value=edited_config['backtest_params'].get('initial_balance', 100000))
                edited_config['backtest_params']['commission'] = st.number_input("עמלה (0.001 = 0.1%)", min_value=0.0, max_value=0.01, value=edited_config['backtest_params'].get('commission', 0.001), step=0.0001, format="%.4f")
                edited_config['backtest_params']['slippage'] = st.number_input("החלקה (0.0005 = 0.05%)", min_value=0.0, max_value=0.01, value=edited_config['backtest_params'].get('slippage', 0.0005), step=0.0001, format="%.4f")
                edited_config['backtest_params']['min_history_days'] = st.number_input("ימי היסטוריה מינימליים", min_value=30, max_value=365, value=edited_config['backtest_params'].get('min_history_days', 100), help="מספר ימי מסחר מינימלי לפני תחילת הבקטסט")
                
                # הוספת פרמטרי סיכון
                if 'risk_params' not in edited_config:
                    edited_config['risk_params'] = {}
                edited_config['risk_params']['position_size_pct'] = st.number_input("אחוז גודל פוזיציה (0.1 = 10%)", min_value=0.01, max_value=1.0, value=edited_config['risk_params'].get('position_size_pct', 0.1), step=0.01, format="%.2f", help="אחוז מקסימלי מהתיק לפוזיציה אחת")

            with st.expander("פרטי חוזה ונכס (Contract)", expanded=False):
                if 'contract' not in edited_config:
                    edited_config['contract'] = {}
                
                c1, c2 = st.columns(2)
                with c1:
                    edited_config['contract']['symbol'] = st.text_input("סימבול", value=edited_config['contract'].get('symbol', 'SPY'))
                    edited_config['contract']['secType'] = st.selectbox("סוג נייר ערך", options=['STK', 'OPT', 'FUT', 'CASH', 'CFD'], index=0 if edited_config['contract'].get('secType', 'STK') == 'STK' else 0, help="STK = מניות, OPT = אופציות, FUT = עתידיים")
                    edited_config['contract']['exchange'] = st.text_input("בורסה", value=edited_config['contract'].get('exchange', 'SMART'), help="SMART = ניתוב חכם, NASDAQ, NYSE, וכו'")
                with c2:
                    edited_config['contract']['currency'] = st.selectbox("מטבע", options=['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD'], index=0 if edited_config['contract'].get('currency', 'USD') == 'USD' else 0)
                    edited_config['contract']['primaryExch'] = st.text_input("בורסה ראשית", value=edited_config['contract'].get('primaryExch', 'ARCA'), help="ARCA, NASDAQ, NYSE, וכו'")
                    
                # הערה חשובה על פרמטרי סיכון
                st.info("💡 **פרמטרי סיכון** (עצירת הפסד, לקיחת רווח, סיכון לעסקה) נמצאים בטאב 'פרמטרי אופטימיזציה'. שם תוכל להגדיר אותם כקבועים או לאפטמיזציה.")

            with st.expander("הגדרות חיבורים (API & IBKR)", expanded=False):
                c1, c2 = st.columns(2)
                with c1:
                    edited_config['api_settings']['host'] = st.text_input("כתובת API", value=edited_config['api_settings'].get('host', '0.0.0.0'), help="כתובת השרת לAPI")
                    edited_config['api_settings']['port'] = st.number_input("פורט API", min_value=1024, max_value=65535, value=edited_config['api_settings'].get('port', 5000))
                    edited_config['ibkr_settings']['host'] = st.text_input("כתובת IBKR", value=edited_config['ibkr_settings'].get('host', '127.0.0.1'), help="כתובת שרת Interactive Brokers")
                    edited_config['ibkr_settings']['port'] = st.number_input("פורט IBKR", min_value=1024, max_value=65535, value=edited_config['ibkr_settings'].get('port', 4001))
                with c2:
                    edited_config['ibkr_settings']['clientId'] = st.number_input("IBKR Client ID", min_value=1, value=edited_config['ibkr_settings'].get('clientId', 101))
                    edited_config['ibkr_settings']['history_window'] = st.text_input("חלון זמן נתונים", value=edited_config['ibkr_settings'].get('history_window', '90 D'), help="כמה זמן אחורה לטעון נתונים (למשל: '90 D', '1 Y')")
                    
                    # הגדרות מצב בדיקה
                    if 'agent_settings' not in edited_config:
                        edited_config['agent_settings'] = {}
                    edited_config['agent_settings']['TEST_MODE_ENABLED'] = st.checkbox("מצב בדיקה", value=edited_config['agent_settings'].get('TEST_MODE_ENABLED', True), help="מצב בדיקה - לא מבצע עסקאות אמיתיות")
                    
                    if edited_config['agent_settings']['TEST_MODE_ENABLED']:
                        edited_config['agent_settings']['TEST_BUY_QUANTITY'] = st.number_input("כמות בדיקה", min_value=1, value=edited_config['agent_settings'].get('TEST_BUY_QUANTITY', 1), help="כמות מניות במצב בדיקה")
                        edited_config['agent_settings']['TEST_BUY_PRICE_FACTOR'] = st.number_input("פקטור מחיר בדיקה", min_value=0.5, max_value=1.5, value=edited_config['agent_settings'].get('TEST_BUY_PRICE_FACTOR', 0.95), step=0.01, format="%.2f", help="פקטור המחיר במצב בדיקה (0.95 = 95% מהמחיר)")

            submitted = st.form_submit_button("💾 שמור שינויים", use_container_width=True)
            if submitted:
                try:
                    save_system_config(edited_config)
                    show_alert("ההגדרות נשמרו בהצלחה!", type_='success')
                    st.rerun()
                except Exception as e:
                    show_alert(f"שגיאה בשמירת ההגדרות: {e}", type_='error')

# --- עמוד ניתוח תוצאות ---
elif page == "ניתוח תוצאות":
    st.title("📈 ניתוח תוצאות")
    
    tab1, tab2, tab3, tab4 = st.tabs(["תוצאות Backtest", "ניתוח אופטימיזציה (Optuna)", "סיכום אימונים קודמים", "קידום מודלים (Staging)"])

    with tab1:
        st.header("ניתוח Backtest")
        results_dir = Path("reports/backtest_results")
        
        summary_files = sorted(results_dir.glob("summary_*.json"), key=os.path.getmtime, reverse=True)
        summary_options = {f.name: f for f in summary_files}
        
        selected_summary_name = st.selectbox("בחר ריצת בקטסט להצגה:", list(summary_options.keys()))

        if selected_summary_name:
            selected_summary_path = summary_options[selected_summary_name]
            suffix = selected_summary_name.replace("summary_", "").replace(".json", "")
            
            equity_path = results_dir / f"equity_curve_{suffix}.csv"
            trades_path = results_dir / f"trades_{suffix}.csv"

            with open(selected_summary_path, encoding="utf-8") as f:
                summary = json.load(f)
            
            st.subheader(f"מדדים מרכזיים עבור: {suffix}")
            cols = st.columns(4)
            cols[0].metric("תשואה כוללת", f"{summary.get('total_return', 0)*100:.2f}%")
            cols[1].metric("יחס שארפ", f"{summary.get('sharpe_ratio', 0):.2f}")
            cols[2].metric("ירידת ערך מירבית", f"{summary.get('max_drawdown', 0)*100:.2f}%")
            cols[3].metric("אחוז הצלחות", f"{summary.get('win_rate', 0)*100:.2f}%")

            if equity_path.exists():
                try:
                    equity_df = pd.read_csv(equity_path, index_col=0, parse_dates=True)
                    fig_equity = px.line(equity_df, y=['equity', 'benchmark_equity'], title=f'Equity Curve vs. Benchmark ({suffix})', labels={'value': 'Equity ($)', 'date': 'Date', 'variable': 'Strategy'})
                    fig_equity.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_equity, use_container_width=True)
                except Exception as e:
                    st.error(f"שגיאה בגרף ה-Equity: {e}")
            else:
                st.warning(f"קובץ עקומת הון לא נמצא עבור {suffix}")
                
            if trades_path.exists():
                st.subheader(f"ניתוח עסקאות ({suffix})")
                try:
                    trades_df = pd.read_csv(trades_path)
                    st.dataframe(trades_df.tail())
                except Exception as e:
                    st.error(f"שגיאה בניתוח קובץ העסקאות: {e}")
            else:
                st.warning(f"קובץ עסקאות לא נמצא עבור {suffix}")
        else:
            st.info("לא נמצאו קבצי תוצאות בקטסט. יש להריץ בקטסט תחילה.")

    with tab2:
        st.header("ניתוח אופטימיזציה (Optuna)")
        st.info("מציג תוצאות מקובץ מסד הנתונים של Optuna, המיוצר אוטומטית בעת הרצת האימון.")
        db_path = Path("db/spy_strategy_optimization.db")
        if db_path.exists():
            optuna_proc = st.session_state.get('optuna_dashboard_proc')
            if optuna_proc and optuna_proc.poll() is None:
                if st.button("⏹️ עצור את דשבורד Optuna"):
                    stop_process('optuna_dashboard_proc')
            else:
                if st.button("▶️ הפעל את דשבורד Optuna החי"):
                    try:
                        cmd = ["optuna-dashboard", f"sqlite:///{db_path.resolve()}"]
                        proc = subprocess.Popen(cmd)
                        st.session_state['optuna_dashboard_proc'] = proc
                        st.success("דשבורד Optuna הופעל! פתח אותו בכתובת http://127.0.0.1:8080 בדפדפן.")
                    except Exception as e:
                        st.error(f"שגיאה בהפעלת דשבורד Optuna: {e}")

            st.markdown("---")
            st.subheader("הצגת גרפים סטטיים מהאימון האחרון")
            try:
                config = load_system_config()
                selected_objective = config['training_params'].get('optuna_target_metric', 'multi_objective')
                
                # מציאת ה-study העדכני ביותר
                conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
                studies_df = pd.read_sql_query("SELECT study_name FROM studies ORDER BY study_id DESC", conn)
                conn.close()
                
                if not studies_df.empty:
                    study_name = studies_df['study_name'].iloc[0]
                    st.info(f"טוען נתונים עבור ה-study העדכני ביותר: `{study_name}`")
                    study = optuna.load_study(study_name=study_name, storage=f"sqlite:///{db_path.resolve()}")
                    
                    try:
                        st.plotly_chart(optuna.visualization.plot_optimization_history(study), use_container_width=True)
                    except Exception as e:
                        st.error(f"שגיאה בהצגת גרף היסטוריית אופטימיזציה: {e}")
                    
                    try:
                        st.plotly_chart(optuna.visualization.plot_parallel_coordinate(study), use_container_width=True)
                    except Exception as e:
                        st.error(f"שגיאה בהצגת גרף קואורדינטות מקבילות: {e}")
                    
                    try:
                        st.plotly_chart(optuna.visualization.plot_param_importances(study), use_container_width=True)
                    except Exception as e:
                        st.error(f"שגיאה בהצגת גרף חשיבות פרמטרים: {e}")
                else:
                    st.warning("לא נמצאו מחקרי Optuna (studies) במסד הנתונים.")
            except ImportError:
                st.error("החבילות 'optuna' ו-'plotly' אינן מותקנות בסביבה זו.")
            except Exception as e:
                st.error(f"שגיאה בטעינת נתוני ה-Study של Optuna: {e}")
        else:
            st.warning("קובץ מסד הנתונים של Optuna לא נמצא. יש להריץ אימון תחילה.")

    with tab3:
        st.header("סיכום אימונים קודמים (training_summary.json)")
        models_dir = Path('models')
        results_dir = Path('reports/backtest_results')
        df_for_iteration = load_training_summaries()
        
        # כפתור למחיקת כל הריצות
        if not df_for_iteration.empty:
            st.markdown("---")
            delete_col1, delete_col2 = st.columns([3, 1])
            
            with delete_col2:
                if st.button("🗑️ מחק כל הריצות", help="מחק את כל קבצי האימונים והתוצאות", type="secondary"):
                    try:
                        deleted_files = 0
                        deleted_dirs = 0
                        
                        # מחיקת תיקיית המודלים
                        if models_dir.exists():
                            import shutil
                            shutil.rmtree(models_dir)
                            deleted_dirs += 1
                        
                        # מחיקת תיקיית תוצאות הבקטסט
                        if results_dir.exists():
                            import shutil
                            shutil.rmtree(results_dir)
                            deleted_dirs += 1
                        
                        # מחיקת קובץ מסד הנתונים של Optuna
                        db_path = Path('spy_strategy_optimization.db')
                        if db_path.exists():
                            db_path.unlink()
                            deleted_files += 1
                        
                        # מחיקת קבצי לוגים
                        log_files = ['main_trainer_output.log', 'backtester_output.log', 'all_features_computed.log']
                        for log_file in log_files:
                            log_path = Path(log_file)
                            if log_path.exists():
                                log_path.unlink()
                                deleted_files += 1
                        
                        st.success(f"✅ נמחקו {deleted_files} קבצים ו-{deleted_dirs} תיקיות")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"שגיאה במחיקת הקבצים: {e}")
                        st.code(traceback.format_exc())
            
            st.markdown("---")
        
        param_he_map = {
            'timestamp': 'תאריך', 'optuna_scores': 'ציוני Optuna',
            'test_accuracy': 'דיוק כללי', 
            'recall_0': 'ריכול (0-Hold)', 'precision_0': 'דיוק (0-Hold)', 'f1_0': 'F1 (0-Hold)', 'support_0': 'דגימות (0-Hold)',
            'recall_1': 'ריכול (1-Buy)', 'precision_1': 'דיוק (1-Buy)', 'f1_1': 'F1 (1-Buy)', 'support_1': 'דגימות (1-Buy)',
            'horizon': 'אופק (ימים)', 'threshold': 'סף החלטה (%)', 'top_n_features': 'מספר פיצ׳רים',
            'stop_loss_pct': 'עצירת הפסד (%)',       # חדש
            'take_profit_pct': 'לקיחת רווח (%)',     # חדש
            'risk_per_trade': 'סיכון לעסקה (%)', 'learning_rate': 'קצב למידה',
            'n_estimators': 'מספר עצים', 'max_depth': 'עומק מירבי',
        }
        if df_for_iteration.empty:
            st.info("לא נמצאו סיכומי אימון בארכיון או בתיקיה הראשית.")
        else:
            st.markdown("#### לחץ על ריצת אימון כדי לראות פרטים מלאים ולהריץ בקטסט:")
            for index, row in df_for_iteration.iterrows():
                try:
                    optuna_target_options = {
                        'multi_objective': 'רב-יעדי', 'total_return': 'תשואה כוללת', 'sharpe_ratio': 'יחס שארפ'
                    }
                    objective_key = row.get('objective_function', 'N/A')
                    objective_display = optuna_target_options.get(objective_key, objective_key)
                    
                    scores_str = "N/A"
                    try:
                        scores_list_str = row.get('optuna_scores', '[]')
                        scores_list = json.loads(scores_list_str.replace("'", '"')) if isinstance(scores_list_str, str) else scores_list_str
                        if isinstance(scores_list, list) and scores_list:
                            scores_str = ", ".join([f"{s:.2f}" for s in scores_list])
                    except (json.JSONDecodeError, TypeError):
                        scores_str = str(row.get('optuna_scores', "N/A"))

                    test_accuracy_val = row.get('test_accuracy', 0)
                    test_accuracy_str = f"{test_accuracy_val:.2%}" if isinstance(test_accuracy_val, float) else "N/A"
                    ts = row.get('file_ts');
                    expander_title = f"**ריצה: {row.get('timestamp', 'N/A')}** | מזהה: `{ts}` | יעד: {objective_display} | ציון: {scores_str} | דיוק: {test_accuracy_str}"

                    with st.expander(expander_title):
                        if not ts or ts == 'N/A':
                            st.warning("לא נמצא מזהה (timestamp) עבור ריצה זו.")
                            continue

                        candidate_model_path = models_dir / f'candidate_model_{ts}.pkl'
                        candidate_scaler_path = models_dir / f'candidate_scaler_{ts}.pkl'
                        candidate_config_path = models_dir / f'candidate_model_config_{ts}.json'
                        summary_path = results_dir / f'summary_candidate_{ts}.json'

                        exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 2])
                        with exp_col1:
                            if candidate_model_path.exists() and candidate_config_path.exists():
                                # כפתורים אחד ליד השני
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button(f"🔄 המשך", key=f"continue_{ts}", help="המשך אופטימיזציה על פי תצורת המערכת"):
                                        try:
                                            current_config = load_system_config()
                                            n_trials = current_config['training_params']['n_trials']
                                            
                                            st.success(f"מתחיל המשך אימון עם {n_trials} נסיונות...")
                                            
                                            # הרצת האימון
                                            run_and_stream_process([sys.executable, "main_trainer.py"], f"ממשיך אימון עם {n_trials} נסיונות...")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"שגיאה בהמשך האימון: {e}")
                                
                                with col2:
                                    if st.button(f"📊 בקטסט", key=f"bt_{ts}"):
                                        cmd = [sys.executable, "backtester.py", "--model", str(candidate_model_path), "--scaler", str(candidate_scaler_path), "--config", str(candidate_config_path), "--output_suffix", f"candidate_{ts}"]
                                        run_and_stream_process(cmd, f"מריץ בקטסט על מודל {ts}...")
                                        st.rerun()
                            else:
                                st.caption("קבצי מודל חסרים")
                        
                        # כפתור החלת תוצאות על תצורת המערכת
                        st.markdown("---")
                        apply_col1, apply_col2 = st.columns([2, 1])
                        
                        with apply_col1:
                            if st.button(f"⚙️ החל תוצאות על תצורת המערכת", key=f"apply_{ts}", help="מעדכן את system_config.json עם הפרמטרים המאופטמיזציה"):
                                try:
                                    # טעינת התצורה הנוכחית
                                    current_config = load_system_config()
                                    
                                    # בדיקה אם יש all_params בנתונים
                                    training_summary_path = models_dir / 'training_summary.json'
                                    if training_summary_path.exists():
                                        with open(training_summary_path, 'r', encoding='utf-8') as f:
                                            training_data = json.load(f)
                                        
                                        if 'all_params' in training_data:
                                            # שימוש ב-all_params החדש
                                            optimized_params = {k: v['value'] for k, v in training_data['all_params'].items() if v['optimized']}
                                        else:
                                            # נפילה לשיטה הישנה
                                            optimized_params = training_data.get('best_params', {})
                                        
                                        # עדכון התצורה
                                        updated_count = 0
                                        for param_name, param_value in optimized_params.items():
                                            if param_name in current_config['optuna_param_limits']:
                                                current_config['optuna_param_limits'][param_name]['fixed_value'] = param_value
                                                current_config['optuna_param_limits'][param_name]['optimize'] = False
                                                updated_count += 1
                                        
                                        # שמירת התצורה המעודכנת
                                        with open('system_config.json', 'w', encoding='utf-8') as f:
                                            json.dump(current_config, f, indent=2, ensure_ascii=False)
                                        
                                        st.success(f"✅ עודכנו {updated_count} פרמטרים בתצורת המערכת. הפרמטרים המאופטמיזציה הפכו לקבועים.")
                                        
                                        # הצגת הפרמטרים שעודכנו
                                        if optimized_params:
                                            st.info("**פרמטרים שעודכנו:**")
                                            for param, value in optimized_params.items():
                                                st.write(f"• {param}: {value}")
                                            
                                            st.info("💡 כעת תוכל לאפטמיזציה פרמטרים אחרים בעוד שאלו יישארו קבועים.")
                                        
                                    else:
                                        st.error("לא נמצא קובץ training_summary.json")
                                        
                                except Exception as e:
                                    st.error(f"שגיאה בהחלת התוצאות: {e}")
                                    st.code(traceback.format_exc())
                        
                        with apply_col2:
                            if st.button(f"🗑️ מחק ריצה", key=f"delete_{ts}", help="מחק את כל הקבצים הקשורים לריצה זו", type="secondary"):
                                try:
                                    # רשימת הקבצים למחיקה
                                    files_to_delete = []
                                    
                                    # קבצי מודל
                                    if candidate_model_path.exists():
                                        files_to_delete.append(candidate_model_path)
                                    if candidate_scaler_path.exists():
                                        files_to_delete.append(candidate_scaler_path)
                                    if candidate_config_path.exists():
                                        files_to_delete.append(candidate_config_path)
                                    
                                    # קבצי תוצאות
                                    training_summary_path = models_dir / 'training_summary.json'
                                    if training_summary_path.exists():
                                        files_to_delete.append(training_summary_path)
                                    
                                    backtest_summary_path = models_dir / 'backtest_summary.json'
                                    if backtest_summary_path.exists():
                                        files_to_delete.append(backtest_summary_path)
                                    
                                    # מחיקת הקבצים
                                    deleted_count = 0
                                    for file_path in files_to_delete:
                                        try:
                                            file_path.unlink()
                                            deleted_count += 1
                                        except Exception as file_error:
                                            st.warning(f"לא ניתן למחוק {file_path.name}: {file_error}")
                                    
                                    # מחיקת תיקיית המודלים אם היא ריקה
                                    try:
                                        if models_dir.exists() and not any(models_dir.iterdir()):
                                            models_dir.rmdir()
                                            st.info(f"נמחקה תיקיית המודלים הריקה: {models_dir.name}")
                                    except Exception:
                                        pass
                                    
                                    if deleted_count > 0:
                                        st.success(f"✅ נמחקו {deleted_count} קבצים")
                                        st.rerun()
                                    else:
                                        st.info("לא נמצאו קבצים למחיקה")
                                        
                                except Exception as e:
                                    st.error(f"שגיאה במחיקת הריצה: {e}")
                                    st.code(traceback.format_exc())

                        with exp_col2:
                            if summary_path.exists():
                                with open(summary_path, encoding='utf-8') as f: summary_data = json.load(f)
                                st.metric("תשואת בקטסט", f"{summary_data.get('total_return', 0):.2%}", help=f"יחס שארפ: {summary_data.get('sharpe_ratio', 0):.2f}")
                            else:
                                st.info("אין תוצאות בקטסט")

                        with exp_col3:
                            st.caption(f"קבצים: `{candidate_model_path.name}`")

                        st.markdown("---")

                        param_groups = {
                            "פרמטרי אסטרטגיה וסיכון": ['horizon', 'threshold', 'top_n_features', 'risk_per_trade', 'stop_loss_pct', 'take_profit_pct'],
                            "היפר-פרמטרים (מודל)": ['learning_rate', 'n_estimators', 'max_depth'],
                            "ביצועים (Buy - 1)": ['test_accuracy', 'precision_1', 'recall_1', 'f1_1', 'support_1'],
                            "ביצועים (Hold - 0)": ['precision_0', 'recall_0', 'f1_0', 'support_0']
                        }

                        group_cols = st.columns(len(param_groups))

                        for i, (group_title, group_keys) in enumerate(param_groups.items()):
                            with group_cols[i]:
                                st.subheader(group_title)
                                data_for_df = []
                                for key in group_keys:
                                    if key in row and pd.notna(row[key]) and row[key] != 'N/A':
                                        val = row[key]
                                        display_val = val
                                        if isinstance(val, float):
                                            if key in ['test_accuracy', 'precision_1', 'recall_1', 'f1_1', 'precision_0', 'recall_0', 'f1_0']:
                                                display_val = f"{val:.2%}"
                                            else:
                                                display_val = f"{val:.4f}"
                                        data_for_df.append({"מדד": param_he_map.get(key, key), "ערך": display_val})
                                if data_for_df:
                                    st.table(pd.DataFrame(data_for_df).set_index("מדד"))

                except Exception as e:
                    st.error(f"שגיאה בעיבוד ריצה {row.get('file_ts', 'לא ידוע')}: {e}")
                    st.code(traceback.format_exc())

    with tab4:
        st.header(":rocket: קידום מודלים (Staging)")
        model_dir = Path('models')
        results_dir = Path('reports/backtest_results')

        champion_model = model_dir / 'champion_model.pkl'
        champion_scaler = model_dir / 'champion_scaler.pkl'
        champion_config = model_dir / 'champion_model_config.json'
        
        candidate_models = sorted(model_dir.glob('candidate_model_*.pkl'), key=os.path.getmtime, reverse=True)
        
        if not candidate_models:
            st.info("לא נמצא מודל מועמד. יש לאמן מודל חדש תחילה.")
        else:
            candidate_model_path = candidate_models[0]
            ts = "_".join(candidate_model_path.stem.split('_')[-2:])
            candidate_scaler_path = model_dir / f'candidate_scaler_{ts}.pkl'
            candidate_config_path = model_dir / f'candidate_model_config_{ts}.json'

            st.success(f"נמצא מודל מועמד: `{candidate_model_path.name}`")

            def load_summary(path):
                try:
                    with open(path, encoding='utf-8') as f: return json.load(f)
                except (FileNotFoundError, json.JSONDecodeError): return None

            champ_summary = load_summary(results_dir / 'summary_champion.json')
            cand_summary = load_summary(results_dir / f'summary_candidate_{ts}.json')

            col1, col2 = st.columns(2)
            with col1:
                if not champ_summary and champion_model.exists():
                    if st.button("📊 הרץ בקטסט למודל האלוף", key="bt_champ"):
                        cmd = [sys.executable, "backtester.py", "--output_suffix", "champion", "--model", str(champion_model), "--scaler", str(champion_scaler), "--config", str(champion_config)]
                        run_and_stream_process(cmd, "מריץ בקטסט על מודל האלוף...")
                        st.rerun()
            with col2:
                if not cand_summary and candidate_model_path.exists():
                    if st.button("📊 הרץ בקטסט למודל המועמד", key="bt_cand"):
                         cmd = [sys.executable, "backtester.py", "--model", str(candidate_model_path), "--scaler", str(candidate_scaler_path), "--config", str(candidate_config_path), "--output_suffix", f"candidate_{ts}"]
                         run_and_stream_process(cmd, f"מריץ בקטסט על מועמד {ts}...")
                         st.rerun()

            st.subheader("השוואת ביצועים: Champion vs. Candidate")
            if champ_summary or cand_summary:
                metrics_to_show = ["total_return", "sharpe_ratio", "max_drawdown", "win_rate", "trades", "benchmark_return"]
                metric_names_he = {
                    "total_return": "תשואה כוללת",
                    "sharpe_ratio": "יחס שארפ",
                    "max_drawdown": "ירידת ערך מירבית",
                    "win_rate": "אחוז הצלחות",
                    "trades": "מספר עסקאות",
                    "benchmark_return": "תשואת ייחוס"
                }
                data = {'מדד': [metric_names_he.get(m, m) for m in metrics_to_show]}

                def format_metric(s_dict, metric):
                    if not s_dict: return "N/A"
                    val = s_dict.get(metric)
                    if val is None: return "N/A"
                    if metric in ["total_return", "max_drawdown", "win_rate", "benchmark_return"]: return f"{val:.2%}"
                    if isinstance(val, float): return f"{val:.2f}"
                    return val

                data['אלוף'] = [format_metric(champ_summary, m) for m in metrics_to_show]
                data['מועמד'] = [format_metric(cand_summary, m) for m in metrics_to_show]
                st.table(pd.DataFrame(data).set_index('מדד'))
            else:
                st.warning("לא נמצאו נתוני ביצועים להשוואה. יש להריץ בקטסטים תחילה.")

            if cand_summary:
                if st.button("🚀 קדם מודל זה לאלוף (Promote to Champion)", type="primary"):
                    try:
                        # Archive existing champion before overwriting
                        if champion_model.exists():
                            archive_dir = model_dir / 'archive'
                            archive_dir.mkdir(exist_ok=True)
                            ts_archive = datetime.now().strftime('%Y%m%d_%H%M%S')
                            shutil.move(champion_model, archive_dir / f"{champion_model.name}.promoted_away.{ts_archive}")
                            if champion_scaler.exists(): shutil.move(champion_scaler, archive_dir / f"{champion_scaler.name}.promoted_away.{ts_archive}")
                            if champion_config.exists(): shutil.move(champion_config, archive_dir / f"{champion_config.name}.promoted_away.{ts_archive}")

                        shutil.copy(candidate_model_path, champion_model)
                        shutil.copy(candidate_scaler_path, champion_scaler)
                        shutil.copy(candidate_config_path, champion_config)
                        
                        # Also copy the backtest results
                        cand_summary_path = results_dir / f'summary_candidate_{ts}.json'
                        champ_summary_path = results_dir / 'summary_champion.json'
                        if cand_summary_path.exists(): shutil.copy(cand_summary_path, champ_summary_path)

                        st.success("המודל קודם לאלוף בהצלחה! יש להפעיל מחדש את שרת ה-API ו/או הסוכן.")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"שגיאה בקידום המודל: {e}")