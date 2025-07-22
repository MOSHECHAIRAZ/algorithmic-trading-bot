# סיכום ארכוב קבצים

כחלק מארגון מחדש של הפרויקט, קבצים שאינם נדרשים עוד לפעילות השוטפת של המערכת הועברו לספריית `archive/`.

## קבצים שאורכבו

הקבצים אורגנו לפי הקטגוריות הבאות:

### 1. רכיבי הקלטת מאקרו (`archive/macro_recorders/`)
- `auto_macro_recorder.py`
- `manual_macro_recorder.py`
- `windows_macro_recorder.py`
- `test_macro_recorder.py`
- `test_windows_recorder.py`
- `create_basic_macro.py`
- `login_recorder.py`
- ספריית `recordings/`

### 2. גרסאות ישנות (`archive/old_versions/`)
- `api_server_refactored.py`
- `module_refactor.py`
- `README_NEW.md`
- `gateway_login.html.new`
- `gateway_login_fixed.html`
- `requirements.txt.bak`
- `requirements.txt.updated`

### 3. קבצי בדיקה (`archive/test_files/`)
- `test_ibkr_connection_extended.py`
- `test_ib_connection.py`
- `tests/test_ibkr_connection_comprehensive.py`
- `tests/test_ibkr_connection_extended.py`
- `tests/test_ibkr_detailed.py`
- `tests/test_ib_connection.py`

### 4. תיעוד ישן (`archive/old_docs/`)
- `PROJECT_REORGANIZATION.md`
- `REFACTORING_PLAN.md`
- `scripts/ci_npm_install.md`
- `scripts/CLEANUP_TODO.md`
- `scripts/REMOVE_OLD_CONFIG.md`

## קבצים שנשמרו

הקבצים הבאים זוהו כבעלי חשיבות קריטית למערכת ולכן לא אורכבו:

### רכיבי ליבה
- `api_server.py` - שרת ה-API המרכזי
- `run_all.py` - סקריפט הרצה ראשי
- `backtester.py` - מנגנון בדיקה היסטורית
- `system_config.json` - הגדרות המערכת

### ספריות מרכזיות
- `agent/` - הסוכן המסחרי
- `src/` - קוד מקור מרכזי
- `models/` - מודלים מאומנים
- `data/` - נתוני מסחר
- `db/` - מסדי נתונים

### רכיבי IBKR
- `IBController/` - ממשק ל-IB Gateway
- `IBC/` - תשתיות נוספות ל-IBKR

## מטרת הארכוב

1. **ניקיון הפרויקט**: הקטנת כמות הקבצים בספריות הראשיות לשיפור קריאות וניהול הקוד
2. **פשטות תחזוקה**: התמקדות ברכיבים הנדרשים בלבד
3. **שמירת היסטוריה**: שמירת קבצים ישנים לצורך תיעוד ומחקר עתידי

## שיחזור במקרה הצורך

במידה ויש צורך בקבצים שאורכבו, ניתן למצוא אותם בקלות בספריית `archive/` תחת הקטגוריה המתאימה.
דו"ח מפורט על כל פעולות הארכוב זמין בקובץ `archive/archive_report.md`.
