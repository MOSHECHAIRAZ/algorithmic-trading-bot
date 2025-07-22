# מערכת ארגון הפרויקט

## מטרה
המערכת מבטיחה שהפרויקט יישאר מסודר ונקי מכפילויות. כל קובץ יונח במקום הנכון וקבצים ישנים יועברו לארכיון.

## מאפיינים

### ארגון אוטומטי
- **אחרי אימון מודל**: המערכת מארגנת אוטומטיט את כל הקבצים
- **אחרי בדיקה אחורית**: המערכת מנקה ומסדרת את הפלטים
- **קבצי פלט**: כל קובץ שנוצר מועבר לתיקייה המתאימה

### ניהול כפילויות
- **מודלים**: רק המודל החדש ביותר נשמר, הישנים עוברים לארכיון
- **נתונים**: רק הנתונים העדכניים נשמרים
- **לוגים**: לוגים ישנים מועברים לארכיון אוטומטית

### מבנה תיקיות
```
📁 הפרויקט/
├── 📁 data/
│   ├── 📁 raw/          # נתוני גלם
│   └── 📁 processed/    # נתונים מעובדים
├── 📁 models/           # מודלים מאומנים
├── 📁 reports/          # דוחות ותוצאות
├── 📁 logs/             # קבצי לוג נוכחיים
├── 📁 archive/          # ארכיון
│   ├── 📁 old_models/   # מודלים ישנים
│   ├── 📁 old_logs/     # לוגים ישנים
│   └── 📁 backups/      # גיבויים כלליים
└── 📁 src/              # קוד המקור
```

## איך להשתמש

### ארגון ידני
```bash
# הפעל את קובץ ה-BAT
organize_project.bat

# או הפעל ישירות עם Python
python scripts/organize_project.py
```

### ארגון אוטומטי
המערכת מתפעלת אוטומטית כאשר:
- מריצים `main_trainer.py`
- מריצים `backtester.py`

### הגדרות
ב-`system_config.json` תחת `"project_organization"`:

```json
{
  "project_organization": {
    "auto_organize_after_training": true,
    "auto_organize_after_backtest": true,
    "keep_latest_files": 3,
    "archive_old_files": true,
    "cleanup_temp_files": true
  }
}
```

## פעולות המערכת

### 1. ארגון קבצי פלט
- קבצי `.pkl`, `.joblib` → `models/`
- קבצי `.csv` עם נתוני raw → `data/raw/`
- קבצי `.csv` עם נתונים מעובדים → `data/processed/`
- קבצי `.csv` אחרים → `reports/`
- קבצי `.log` → `logs/`

### 2. ניקוי קבצים ישנים
- שמירת 3 הקבצים החדשים ביותר מכל סוג
- העברת הישנים לארכיון
- גיבוי לפני מחיקה

### 3. הסרת כפילויות
- זיהוי קבצים דומים
- שמירת הגרסה החדשה ביותר
- ארכוב הישנות

### 4. ניקוי קבצים זמניים
- מחיקת `*.tmp`, `*.temp`
- מחיקת `__pycache__`
- מחיקת קבצי מערכת (.DS_Store, Thumbs.db)

## לוגים
כל פעולת ארגון נרשמת ב:
- `logs/project_organization.log`
- פלט למסוף

## דוגמאות שימוש

### בדיקת מצב הפרויקט
```python
from src.utils.project_organizer import ProjectOrganizer

organizer = ProjectOrganizer()
report = organizer.get_status_report()
print(f"גודל כולל: {report['total_size_mb']:.2f} MB")
```

### ארגון חלקי
```python
organizer = ProjectOrganizer()
organizer.organize_output_files()  # רק ארגון קבצי פלט
organizer.cleanup_temp_files()     # רק ניקוי קבצים זמניים
```

## התאמה אישית
ניתן להתאים את ההגדרות ב-`system_config.json`:
- `keep_latest_files`: כמה קבצים לשמור
- `file_patterns`: סוגי קבצים שונים לזיהוי
- `auto_organize_*`: הפעלה/כיבוי ארגון אוטומטי

המערכת מבטיחה פרויקט נקי ומסודר! 🎯
