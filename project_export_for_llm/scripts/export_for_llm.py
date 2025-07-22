"""
סקריפט להכנת קבצי פרויקט אלגוריתם מסחר לשיתוף עם מודל שפה.
הסקריפט מעתיק את הקבצים הרלוונטיים לתיקייה אחת, מסדר אותם לפי חשיבות,
ומחריג קבצים שאינם נחוצים (קבצים בינאריים, לוגים, ספריות, גיבויים, וכו').
"""

import os
import shutil
import datetime
import argparse
import logging
import sys

# הגדרת לוגינג
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# תיקיות להחרגה
EXCLUDED_DIRS = [
    ".git",
    ".github",
    ".vscode",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "archive",
    "logs",
    "data/raw",
    "data/processed",
    "data/old_backups",
    # "models",  # כעת נכלול קבצי מודלים
    "IBC",
    "IBController",
    "IBController_Clean",
    "db",
    "reports",  # דוחות וגרפים
    "project_export_for_llm",  # תיקיית הייצוא הקבועה
    "project_export",  # תיקיות ייצוא אחרות
    "project_export_updated",  # תיקיות ייצוא קודמות
    "project_export_clean",  # תיקיות ייצוא קודמות
    "project_export_final",  # תיקיות ייצוא קודמות
    "project_export_20250722_030333"  # תיקיות ייצוא ספציפיות
]

# סיומות קבצים להחרגה
EXCLUDED_EXTENSIONS = [
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".dat",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".log",
    ".csv",  # קבצי נתונים גולמיים
    ".bak",  # קבצי גיבוי
    ".tmp",  # קבצים זמניים
    ".png",  # קבצי תמונה
    ".jpg",  # קבצי תמונה
    ".jpeg", # קבצי תמונה
    ".gif",  # קבצי תמונה
    ".svg",  # קבצי תמונה
    # קבצי מודלים - עכשיו נכללים:
    # ".pickle",
    # ".pkl", 
    # ".npy",
    # ".npz",
    # ".joblib",
    ".lock",
    ".part",
    ".gitkeep",  # קבצי Git לשמירת תיקיות ריקות
    ".main"  # קבצים זמניים
]

# קבצים ספציפיים להחרגה
EXCLUDED_FILES = [
    "package-lock.json",
    ".gitignore",
    ".env",
    "dashboard_password.txt",
    "spy_strategy_optimization.db",
    "trading_log.txt",  # קובץ לוג של הסוכן
    "largest_files.txt",  # קובץ זמני שנוצר על ידי בדיקות
    ".delete_state_manager_py"  # קבצים שמסומנים למחיקה
]

# קבצים חשובים שצריך לכלול בהתחלת הרשימה
PRIORITY_FILES = [
    "README.md",
    "PROJECT_DOCUMENTATION.md",
    "PROJECT_STRUCTURE.md",
    "system_config.json",
    "api_server.py",
    "run_preprocessing.py",
    "run_all.py",
    "main_trainer.py",
    "backtester.py",
    "src/feature_engineering.py",
    "src/feature_calculator.py",
    "src/model_training.py",
    "src/run_preprocessing.py",
    "agent/trading_agent.js",
    "agent/state_manager.js"
]

def should_include_file(file_path):
    """בודק אם יש לכלול את הקובץ בתיקיית היצוא"""
    filename = os.path.basename(file_path)
    
    # בדוק אם הוא נמצא ברשימת הקבצים המוחרגים
    if filename in EXCLUDED_FILES:
        return False
    
    # החרג קבצים שמתחילים בנקודה (חוץ מקבצי .env.example)
    if filename.startswith('.') and not filename.endswith('.example'):
        return False
    
    # בדוק את סיומת הקובץ
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext in EXCLUDED_EXTENSIONS:
        return False
    
    # לא מחריגים קבצים גדולים - כל הקבצים יכללו
    return True

def is_in_excluded_dir(file_path, project_root):
    """בודק אם הקובץ נמצא בתיקייה שצריך להחריג"""
    rel_path = os.path.relpath(file_path, project_root)
    path_parts = rel_path.split(os.sep)
    
    for i in range(len(path_parts)):
        current_dir = path_parts[i]
        
        # בדוק תיקיות מוחרגות מפורשות
        if current_dir in EXCLUDED_DIRS:
            return True
        
        # בדוק תיקיות ייצוא (כל תיקייה שמתחילה ב-project_export)
        if current_dir.startswith("project_export"):
            return True
        
        # בדוק גם נתיבים מורכבים
        current_path = os.sep.join(path_parts[:i+1])
        if current_path in EXCLUDED_DIRS:
            return True
    
    return False

def collect_project_files(project_root):
    """אוסף את כל הקבצים הרלוונטיים בפרויקט"""
    all_files = []
    
    for root, dirs, files in os.walk(project_root):
        # דילוג על תיקיות מוחרגות
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and 
                  os.path.join(root, d).replace(project_root, "").replace("\\", "/").lstrip("/") not in EXCLUDED_DIRS]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_root)
            
            # דילוג על קבצים בתיקיות מוחרגות
            if is_in_excluded_dir(file_path, project_root):
                continue
                
            # בדוק אם הקובץ צריך להיכלל
            if should_include_file(file_path):
                all_files.append(rel_path)
    
    return all_files

def sort_files_by_priority(files, project_root):
    """מיון הקבצים לפי סדר חשיבות"""
    priority_files = []
    regular_files = []
    
    # המר נתיבים יחסיים לנתיבי Windows/Linux אחידים
    normalized_files = [f.replace("\\", "/") for f in files]
    normalized_priority = [f.replace("\\", "/") for f in PRIORITY_FILES]
    
    # חלק את הקבצים לפי עדיפות
    for file in normalized_files:
        if file in normalized_priority:
            priority_files.append((file, normalized_priority.index(file)))
        else:
            regular_files.append(file)
    
    # מיון קבצי עדיפות לפי הסדר שהוגדר
    priority_files.sort(key=lambda x: x[1])
    priority_files = [f[0] for f in priority_files]
    
    # מיון קבצים רגילים לפי שם
    regular_files.sort()
    
    # החזרת כל הקבצים בסדר הנכון
    all_sorted_files = priority_files + regular_files
    
    # המר בחזרה לנתיבים תואמי מערכת ההפעלה
    return [f.replace("/", os.sep) for f in all_sorted_files]

def create_export_directory(project_root, export_name=None):
    """יוצר תיקיית יצוא עם שם דינמי, דורס קיימת אם נדרש"""
    if not export_name:
        # אם לא מציינים שם, נשתמש בשם קבוע
        export_name = "project_export_for_llm"
    
    export_dir = os.path.join(project_root, export_name)
    
    # אם התיקייה כבר קיימת, נמחק אותה ונוצר מחדש
    if os.path.exists(export_dir):
        logging.info(f"מוחק תיקיית יצוא קיימת: {export_dir}")
        shutil.rmtree(export_dir)
    
    os.makedirs(export_dir, exist_ok=True)
    return export_dir

def create_directory_structure(file_path, export_dir):
    """יוצר את מבנה התיקיות הנדרש לקובץ"""
    dir_path = os.path.dirname(os.path.join(export_dir, file_path))
    os.makedirs(dir_path, exist_ok=True)

def copy_files_to_export(files, project_root, export_dir):
    """מעתיק את הקבצים לתיקיית היצוא"""
    copied_files = []
    
    for file in files:
        source_path = os.path.join(project_root, file)
        dest_path = os.path.join(export_dir, file)
        
        try:
            # וודא שמבנה התיקיות קיים
            create_directory_structure(file, export_dir)
            
            # העתק את הקובץ
            shutil.copy2(source_path, dest_path)
            copied_files.append(file)
        except Exception as e:
            logging.error(f"Failed to copy {file}: {str(e)}")
    
    return copied_files

def create_file_listing(files, export_dir):
    """יוצר קובץ רשימת קבצים לנוחות"""
    listing_path = os.path.join(export_dir, "00_FILE_LISTING.md")
    with open(listing_path, "w", encoding="utf-8") as f:
        f.write("# רשימת קבצי פרויקט לייעוץ עם מודל שפה\n\n")
        f.write(f"*נוצר בתאריך: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("## קבצים חשובים (מומלץ להתחיל מהם)\n\n")
        
        # כתיבת קבצי עדיפות גבוהה
        for file in files:
            norm_file = file.replace("\\", "/")
            if norm_file in [p.replace("\\", "/") for p in PRIORITY_FILES]:
                f.write(f"- `{file}`\n")
        
        f.write("\n## כל הקבצים לפי סדר\n\n")
        
        # כתיבת כל הקבצים
        current_dir = ""
        for file in files:
            file_dir = os.path.dirname(file)
            
            # הוספת כותרת משנה לתיקייה חדשה
            if file_dir != current_dir:
                current_dir = file_dir
                if current_dir:
                    f.write(f"\n### {current_dir}/\n\n")
                else:
                    f.write("\n### תיקייה ראשית\n\n")
            
            f.write(f"- `{file}`\n")

def create_readme_file(export_dir, project_root):
    """יוצר קובץ README.md לתיקיית היצוא"""
    readme_path = os.path.join(export_dir, "README_EXPORT.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# פרויקט אלגוריתם מסחר - יצוא לייעוץ עם מודל שפה\n\n")
        f.write(f"*נוצר בתאריך: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("## מטרת היצוא\n\n")
        f.write("קבצים אלה הוכנו להצגה בפני מודל שפה לצורך קבלת ייעוץ וניתוח. ")
        f.write("הקבצים מכילים את הפרויקט ללא קבצים בינאריים, קבצי לוג, ")
        f.write("וספריות צד שלישי.\n\n")
        
        f.write("## סדר קריאה מומלץ\n\n")
        f.write("1. תחילה קרא את `PROJECT_STRUCTURE.md` או `PROJECT_DOCUMENTATION.md` להבנת מבנה הפרויקט\n")
        f.write("2. בדוק את קובץ `system_config.json` להבנת הגדרות המערכת\n")
        f.write("3. עיין ב-`api_server.py` שהוא השרת המרכזי של המערכת\n")
        f.write("4. עבור לתיקיית `src/` שמכילה את רוב הלוגיקה העסקית\n")
        f.write("5. בדוק את תיקיית `agent/` להבנת הלוגיקה של סוכן המסחר\n\n")
        
        f.write("## קבצים שהוחרגו\n\n")
        f.write("קבצים ותיקיות שלא נכללו ביצוא זה:\n\n")
        f.write("- קבצים בינאריים וקבצי מודל\n")
        f.write("- קבצי לוג ונתונים גולמיים\n")
        f.write("- תיקיות ספריות חיצוניות (`node_modules`, `.venv`, וכו')\n")
        f.write("- קבצי גיבוי ותיקיות ארכיון\n")
        f.write("- קבצי סביבה ותצורה אישיים\n\n")
        
        f.write("## הערה חשובה\n\n")
        f.write("בכל פעם שמריצים את הסקריפט `export_for_llm.py`, הוא אוסף את כל הקבצים העדכניים ")
        f.write("בפרויקט. כלומר, כל קובץ חדש שנוסף לפרויקט ייכלל בהרצה הבאה של הסקריפט (כל עוד ")
        f.write("הוא לא בתיקיות או מסוגי הקבצים שהוחרגו).\n\n")
        f.write("כדי לכלול קבצים חדשים שהוספת לפרויקט, פשוט הרץ שוב את הסקריפט ליצירת יצוא עדכני.")

def main():
    parser = argparse.ArgumentParser(description="יצירת תיקיית יצוא של פרויקט לייעוץ עם מודל שפה")
    parser.add_argument("--output", "-o", help="שם תיקיית היצוא")
    parser.add_argument("--root", "-r", help="נתיב לתיקיית השורש של הפרויקט", default=".")
    args = parser.parse_args()
    
    project_root = os.path.abspath(args.root)
    
    logging.info(f"החל יצוא פרויקט מתיקייה: {project_root}")
    
    # איסוף הקבצים
    logging.info("אוסף קבצי פרויקט...")
    all_files = collect_project_files(project_root)
    logging.info(f"נמצאו {len(all_files)} קבצים רלוונטיים")
    
    # מיון הקבצים
    sorted_files = sort_files_by_priority(all_files, project_root)
    
    # יצירת תיקיית יצוא
    export_dir = create_export_directory(project_root, args.output)
    logging.info(f"נוצרה תיקיית יצוא: {export_dir}")
    
    # העתקת הקבצים
    logging.info("מעתיק קבצים...")
    copied_files = copy_files_to_export(sorted_files, project_root, export_dir)
    logging.info(f"הועתקו {len(copied_files)} קבצים")
    
    # יצירת קבצי מידע
    create_file_listing(copied_files, export_dir)
    create_readme_file(export_dir, project_root)
    
    logging.info(f"היצוא הושלם בהצלחה: {export_dir}")
    logging.info(f"כדי להעתיק את הקבצים למודל השפה, עבור לתיקייה: {export_dir}")

if __name__ == "__main__":
    main()
