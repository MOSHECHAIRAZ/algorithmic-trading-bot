"""
project_organizer.py - מערכת ארגון ותחזוקה של הפרויקט

מודול זה דואג לכך שכל קובץ יונח במקום הנכון ושלא יהיו כפילויות.
"""

import os
import json
import shutil
import glob
from datetime import datetime
from pathlib import Path
import logging

# הגדרת לוגר
logger = logging.getLogger(__name__)

class ProjectOrganizer:
    """מחלקה לארגון וניקוי הפרויקט"""
    
    def __init__(self, config_path="system_config.json"):
        """
        אתחול עם קובץ הגדרות המערכת
        
        Args:
            config_path (str): נתיב לקובץ ההגדרות
        """
        self.base_dir = Path(__file__).parent.parent.parent
        self.config_path = self.base_dir / config_path
        self.config = self._load_config()
        self.paths = self.config.get("system_paths", {})
        self.org_settings = self.config.get("project_organization", {})
        
    def _load_config(self):
        """טוען קובץ הגדרות המערכת"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"שגיאה בטעינת קובץ הגדרות: {e}")
            return {}
    
    def ensure_directories(self):
        """
        וודא שכל התיקיות הנדרשות קיימות
        """
        required_dirs = [
            "data/raw",
            "data/processed", 
            "models",
            "reports",
            "logs",
            "archive/backups",
            "archive/old_models",
            "archive/old_logs",
            "scripts",
            "src/utils",
            "tests",
            "public/static"
        ]
        
        for dir_path in required_dirs:
            full_path = self.base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"וודא שתיקייה קיימת: {full_path}")
    
    def organize_output_files(self):
        """
        מארגן קבצי פלט שנוצרו בתיקייה הראשית
        """
        # קבצי מודלים שנוצרו בשורש
        model_files = glob.glob(str(self.base_dir / "*.pkl")) + \
                     glob.glob(str(self.base_dir / "*.joblib"))
        
        for model_file in model_files:
            dest = self.base_dir / "models" / Path(model_file).name
            shutil.move(model_file, dest)
            logger.info(f"הועבר מודל: {Path(model_file).name} -> models/")
        
        # קבצי CSV שנוצרו בשורש
        csv_files = glob.glob(str(self.base_dir / "*.csv"))
        
        for csv_file in csv_files:
            filename = Path(csv_file).name
            # אם זה נתוני raw - לdata/raw
            if any(keyword in filename.lower() for keyword in ['raw', 'ibkr', 'yahoo']):
                dest = self.base_dir / "data" / "raw" / filename
            # אם זה נתונים מעובדים - לdata/processed  
            elif any(keyword in filename.lower() for keyword in ['processed', 'features', 'engineered']):
                dest = self.base_dir / "data" / "processed" / filename
            # אחרת - לreports
            else:
                dest = self.base_dir / "reports" / filename
                
            shutil.move(csv_file, dest)
            logger.info(f"הועבר CSV: {filename} -> {dest.parent.name}/")
        
        # קבצי לוג שנוצרו בשורש
        log_files = glob.glob(str(self.base_dir / "*.log"))
        
        for log_file in log_files:
            dest = self.base_dir / "logs" / Path(log_file).name
            shutil.move(log_file, dest)
            logger.info(f"הועבר לוג: {Path(log_file).name} -> logs/")
    
    def clean_old_outputs(self, keep_latest=None):
        """
        מנקה קבצי פלט ישנים ושומר רק את החדשים
        
        Args:
            keep_latest (int): כמה קבצים אחרונים לשמור מכל סוג
        """
        if keep_latest is None:
            keep_latest = self.org_settings.get("keep_latest_files", 3)
        directories_to_clean = {
            "logs": "*.log",
            "reports": ["*.csv", "*.html", "*.json"],
            "models": ["*.pkl", "*.joblib"],
            "data/processed": "*.csv"
        }
        
        for dir_name, patterns in directories_to_clean.items():
            dir_path = self.base_dir / dir_name
            if not dir_path.exists():
                continue
                
            if isinstance(patterns, str):
                patterns = [patterns]
            
            for pattern in patterns:
                files = list(dir_path.glob(pattern))
                # מיין לפי זמן שינוי (חדש ראשון)
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # מחק קבצים ישנים
                for old_file in files[keep_latest:]:
                    # גבה לארכיון לפני מחיקה
                    self._archive_file(old_file)
                    old_file.unlink()
                    logger.info(f"נמחק קובץ ישן: {old_file.name}")
    
    def _archive_file(self, file_path):
        """
        מגבה קובץ לארכיון לפני מחיקה
        
        Args:
            file_path (Path): נתיב הקובץ לגיבוי
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        
        # קביעת תיקיית ארכיון לפי סוג הקובץ
        if file_path.suffix in ['.pkl', '.joblib']:
            archive_dir = self.base_dir / "archive" / "old_models"
        elif file_path.suffix == '.log':
            archive_dir = self.base_dir / "archive" / "old_logs"
        else:
            archive_dir = self.base_dir / "archive" / "backups"
        
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / archive_name
        
        shutil.copy2(file_path, archive_path)
        logger.info(f"גובה לארכיון: {file_path.name} -> {archive_path}")
    
    def remove_duplicates(self):
        """
        מסיר כפילויות שנוצרו במהלך העבודה
        """
        # בדיקת כפילויות מודלים
        models_dir = self.base_dir / "models"
        if models_dir.exists():
            self._remove_duplicate_models(models_dir)
        
        # בדיקת כפילויות נתונים מעובדים
        processed_dir = self.base_dir / "data" / "processed"
        if processed_dir.exists():
            self._remove_duplicate_data(processed_dir)
    
    def _remove_duplicate_models(self, models_dir):
        """מסיר כפילויות מודלים"""
        model_files = list(models_dir.glob("*.pkl")) + list(models_dir.glob("*.joblib"))
        
        # קבץ מודלים לפי שם בסיס
        model_groups = {}
        for model_file in model_files:
            base_name = model_file.stem.split('_')[0]  # ללא timestamp
            if base_name not in model_groups:
                model_groups[base_name] = []
            model_groups[base_name].append(model_file)
        
        # לכל קבוצה, שמור רק את החדש ביותר
        for base_name, files in model_groups.items():
            if len(files) > 1:
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for old_file in files[1:]:  # שמור רק את הראשון (החדש)
                    self._archive_file(old_file)
                    old_file.unlink()
                    logger.info(f"הוסר מודל כפול: {old_file.name}")
    
    def _remove_duplicate_data(self, data_dir):
        """מסיר כפילויות נתונים מעובדים"""
        csv_files = list(data_dir.glob("*.csv"))
        
        # קבץ נתונים לפי שם בסיס
        data_groups = {}
        for csv_file in csv_files:
            base_name = csv_file.stem.split('_')[0]
            if base_name not in data_groups:
                data_groups[base_name] = []
            data_groups[base_name].append(csv_file)
        
        # לכל קבוצה, שמור רק את החדש ביותר
        for base_name, files in data_groups.items():
            if len(files) > 1:
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for old_file in files[1:]:
                    self._archive_file(old_file)
                    old_file.unlink()
                    logger.info(f"הוסר נתון כפול: {old_file.name}")
    
    def cleanup_temp_files(self):
        """
        מנקה קבצים זמניים שנוצרו במהלך הפעילות
        """
        temp_patterns = [
            "*.tmp",
            "*.temp", 
            "*~",
            ".DS_Store",
            "Thumbs.db",
            "*.pyc",
            "__pycache__"
        ]
        
        for pattern in temp_patterns:
            for temp_file in self.base_dir.rglob(pattern):
                if temp_file.is_file():
                    temp_file.unlink()
                    logger.info(f"נמחק קובץ זמני: {temp_file}")
                elif temp_file.is_dir() and pattern == "__pycache__":
                    shutil.rmtree(temp_file)
                    logger.info(f"נמחקה תיקיית זמנית: {temp_file}")
    
    def organize_all(self):
        """
        מבצע ארגון מלא של הפרויקט
        """
        logger.info("מתחיל ארגון מלא של הפרויקט...")
        
        # 1. וודא שכל התיקיות קיימות
        self.ensure_directories()
        
        # 2. ארגן קבצי פלט
        self.organize_output_files()
        
        # 3. נקה קבצים ישנים
        self.clean_old_outputs()
        
        # 4. הסר כפילויות
        self.remove_duplicates()
        
        # 5. נקה קבצים זמניים
        self.cleanup_temp_files()
        
        logger.info("ארגון הפרויקט הושלם בהצלחה!")
    
    def get_status_report(self):
        """
        מחזיר דוח מצב על הפרויקט
        
        Returns:
            dict: דוח מצב
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "directories": {},
            "file_counts": {},
            "total_size_mb": 0
        }
        
        important_dirs = ["data", "models", "logs", "reports", "src", "tests"]
        
        for dir_name in important_dirs:
            dir_path = self.base_dir / dir_name
            if dir_path.exists():
                files = list(dir_path.rglob("*"))
                file_count = len([f for f in files if f.is_file()])
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                
                report["directories"][dir_name] = {
                    "exists": True,
                    "file_count": file_count,
                    "size_mb": round(total_size / (1024*1024), 2)
                }
                report["total_size_mb"] += total_size / (1024*1024)
            else:
                report["directories"][dir_name] = {"exists": False}
        
        return report


def main():
    """פונקציה ראשית להרצת הארגון"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    organizer = ProjectOrganizer()
    organizer.organize_all()
    
    # הדפס דוח מצב
    report = organizer.get_status_report()
    print("\n=== דוח מצב הפרויקט ===")
    for dir_name, info in report["directories"].items():
        if info["exists"]:
            print(f"{dir_name}: {info['file_count']} קבצים ({info['size_mb']} MB)")
        else:
            print(f"{dir_name}: לא קיים")
    print(f"\nגודל כולל: {report['total_size_mb']:.2f} MB")


if __name__ == "__main__":
    main()
