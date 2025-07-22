"""
__init__.py - מודול אתחול עבור חבילת src

מאפשר ייבוא של מודולים מהחבילה, לדוגמה:
from src.utils import load_system_config
"""

# ייבוא מודולים חשובים לנוחות
try:
    from .utils import load_system_config, archive_existing_file, save_system_config
except ImportError:
    # אם utils הוא תיקייה, נבה את הפונקציות מutils.py
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from utils import load_system_config, archive_existing_file, save_system_config

from .process_manager import process_manager
from .gateway_manager import gateway_manager

# מידע על גרסת החבילה
__version__ = "2.0.0"
