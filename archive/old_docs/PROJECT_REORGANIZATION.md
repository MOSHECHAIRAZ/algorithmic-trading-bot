# פרויקט מסחר אלגוריתמי - סיכום ארגון מחדש

## מבנה הפרויקט

פרויקט המסחר האלגוריתמי אורגן מחדש למבנה הבא:

### תיקיות מרכזיות
- `src/` - קבצי קוד המקור של המערכת
- `tests/` - קבצי בדיקה
- `scripts/` - סקריפטים ואוטומציה
- `data/` - קבצי נתונים (גולמיים ומעובדים)
- `models/` - מודלים מאומנים
- `logs/` - קבצי לוג
- `reports/` - דוחות והוצאות של הבקטסטים
- `agent/` - קוד סוכן המסחר
- `public/` - קבצים סטטיים של ממשק המשתמש

### קבצי הפעלה מרכזיים
- `run_all.py` - מריץ את התהליך המלא (איסוף נתונים, עיבוד, אימון)
- `run_server.bat` - מריץ את שרת ה-API
- `start_gateway_manager.bat` - מפעיל את מנהל ה-Gateway של IBKR

## קבצים שהועברו
1. `main_trainer.py` -> `src/main_trainer.py`
2. `run_preprocessing.py` -> `src/run_preprocessing.py`
3. `api_server.py` -> `src/api_server.py`
4. `backtester.py` -> `src/backtester.py`
5. בדיקות IB -> `tests/test_ibkr_connection.py`, `tests/test_ibkr_connection_extended.py`, `tests/test_ib_connection.py`
6. בדיקות מאקרו -> `tests/test_macro_recorder.py`
7. `auto_macro_recorder.py` -> `scripts/auto_macro_recorder.py`

## שינויים בקבצי הפעלה
1. `run_all.py` - עודכן להשתמש בקבצים מתיקיית `src`
2. `run_server.bat` - עודכן להפעיל את `src/api_server.py`
3. `start_gateway_manager.bat` - עודכן להפעיל את `src/gateway_manager.py`

## כיצד להשתמש במערכת

### הפעלת המערכת המלאה
```
python run_all.py
```

### הפעלת ה-API בלבד
```
run_server.bat
```

### הפעלת מנהל ה-Gateway
```
start_gateway_manager.bat
```

### הרצת בדיקות
```
cd tests
python test_ibkr_connection.py
```

## מה נשאר לבצע
1. לבדוק את המערכת המלאה אחרי הארגון מחדש
2. לעדכן את שאר הקבצים שעדיין בתיקייה הראשית (אם קיימים)
3. ליצור תיעוד מפורט יותר על כל חלק במערכת

הערה: אם יש בעיות בייבוא מודולים, ודאו שהתיקיות `src` ו-`scripts` מוכרות כחבילות Python באמצעות הוספת קבצי `__init__.py` ריקים בכל תיקייה.
