#!/usr/bin/env python3
"""
organize_project.py - סקריפט לארגון ידני של הפרויקט

הפעל את הסקריפט הזה בכל עת כדי לארגן את הפרויקט ולנקות כפילויות.
"""

import sys
import os
from pathlib import Path

# הוספת הנתיב הראשי לPATH
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

# ייבוא ישיר
import importlib.util
spec = importlib.util.spec_from_file_location(
    "project_organizer", 
    BASE_DIR / "src" / "utils" / "project_organizer.py"
)
project_organizer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(project_organizer_module)
ProjectOrganizer = project_organizer_module.ProjectOrganizer
import logging

def main():
    """הפעלת ארגון מלא של הפרויקט"""
    
    # הגדרת לוגינג
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/project_organization.log', encoding='utf-8')
        ]
    )
    
    print("🔧 מתחיל ארגון הפרויקט...")
    
    try:
        organizer = ProjectOrganizer()
        
        # הצג דוח מצב לפני
        print("\n📊 מצב הפרויקט לפני הארגון:")
        report_before = organizer.get_status_report()
        for dir_name, info in report_before["directories"].items():
            if info.get("exists"):
                print(f"  {dir_name}: {info['file_count']} קבצים ({info['size_mb']} MB)")
        
        # בצע ארגון מלא
        organizer.organize_all()
        
        # הצג דוח מצב אחרי
        print("\n📊 מצב הפרויקט אחרי הארגון:")
        report_after = organizer.get_status_report()
        for dir_name, info in report_after["directories"].items():
            if info.get("exists"):
                print(f"  {dir_name}: {info['file_count']} קבצים ({info['size_mb']} MB)")
        
        print(f"\n✅ ארגון הפרויקט הושלם בהצלחה!")
        print(f"📦 גודל כולל: {report_after['total_size_mb']:.2f} MB")
        
    except Exception as e:
        print(f"❌ שגיאה בארגון הפרויקט: {e}")
        logging.error(f"Error in project organization: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    input("\nלחץ Enter לסגירה...")
    sys.exit(exit_code)
