#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Archive Unused Files

This script archives files that are no longer needed in the main project directory,
organizing them into categorized subdirectories within the archive folder.
"""

import os
import shutil
import datetime
from pathlib import Path

# קבצים שיועברו לארכיון, מאורגנים לפי קטגוריות
FILES_TO_ARCHIVE = {
    "macro_recorders": [
        "auto_macro_recorder.py",
        "manual_macro_recorder.py",
        "windows_macro_recorder.py",
        "test_macro_recorder.py",
        "test_windows_recorder.py",
        "create_basic_macro.py",
        "login_recorder.py",
        "scripts/auto_macro_recorder.py"
    ],
    "old_versions": [
        "api_server_refactored.py",
        "module_refactor.py",
        "README_NEW.md",
        "gateway_login.html.new",
        "gateway_login_fixed.html",
        "requirements.txt.bak",
        "requirements.txt.updated"
    ],
    "test_files": [
        "test_ibkr_connection_extended.py",
        "test_ib_connection.py",
        "tests/test_ibkr_connection_comprehensive.py",
        "tests/test_ibkr_connection_extended.py",
        "tests/test_ibkr_detailed.py",
        "tests/test_ib_connection.py",
        "tests/test_macro_recorder.py"
    ],
    "old_docs": [
        "PROJECT_REORGANIZATION.md",
        "REFACTORING_PLAN.md",
        "scripts/ci_npm_install.md",
        "scripts/CLEANUP_TODO.md",
        "scripts/REMOVE_OLD_CONFIG.md"
    ]
}

# ספריות שיועברו לארכיון
DIRECTORIES_TO_ARCHIVE = [
    "recordings"
]

def create_archive_structure():
    """יוצר את מבנה ספריות הארכיון"""
    archive_dir = Path("archive")
    archive_dir.mkdir(exist_ok=True)
    
    # יוצר תת-ספריות לפי קטגוריה
    for category in FILES_TO_ARCHIVE.keys():
        (archive_dir / category).mkdir(exist_ok=True)
    
    # ספרייה ייעודית לספריות מאורכבות
    (archive_dir / "directories").mkdir(exist_ok=True)
    
    return archive_dir

def archive_files(archive_dir):
    """מעביר את הקבצים המיועדים לארכיון"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    archived_files = []
    
    # ארכוב קבצים לפי קטגוריה
    for category, files in FILES_TO_ARCHIVE.items():
        category_dir = archive_dir / category
        
        for filename in files:
            source_path = Path(filename)
            if source_path.exists():
                # בדיקה אם הקובץ כבר קיים בארכיון
                if (category_dir / source_path.name).exists():
                    dest_path = category_dir / f"{source_path.stem}_{timestamp}{source_path.suffix}"
                else:
                    dest_path = category_dir / source_path.name
                
                try:
                    shutil.move(source_path, dest_path)
                    archived_files.append((str(source_path), str(dest_path)))
                    print(f"✓ Archived: {source_path} → {dest_path}")
                except Exception as e:
                    print(f"✗ Failed to archive {source_path}: {str(e)}")
    
    # ארכוב ספריות
    for dirname in DIRECTORIES_TO_ARCHIVE:
        source_path = Path(dirname)
        if source_path.exists() and source_path.is_dir():
            dest_path = archive_dir / "directories" / f"{source_path.name}_{timestamp}"
            try:
                shutil.move(source_path, dest_path)
                archived_files.append((str(source_path), str(dest_path)))
                print(f"✓ Archived directory: {source_path} → {dest_path}")
            except Exception as e:
                print(f"✗ Failed to archive directory {source_path}: {str(e)}")
    
    return archived_files

def create_archive_report(archived_files):
    """יוצר קובץ דו״ח על הקבצים שאורכבו"""
    if not archived_files:
        print("No files were archived.")
        return
        
    report_path = Path("archive") / "archive_report.md"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(report_path, "a", encoding="utf-8") as f:
        f.write(f"\n## Archive Operation: {timestamp}\n\n")
        f.write("| Original Path | Archive Path |\n")
        f.write("|---------------|-------------|\n")
        
        for source, dest in archived_files:
            f.write(f"| {source} | {dest} |\n")
    
    print(f"Archive report created at {report_path}")

def main():
    """פונקציה ראשית לארכוב קבצים"""
    print("Starting archive operation...")
    archive_dir = create_archive_structure()
    archived_files = archive_files(archive_dir)
    create_archive_report(archived_files)
    print("Archive operation completed.")

if __name__ == "__main__":
    main()
