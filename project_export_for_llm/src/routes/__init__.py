"""
__init__.py - מודול אתחול עבור חבילת routes

מאפשר ייבוא של blueprints מהחבילה, לדוגמה:
from src.routes.system import system_bp
"""

# ייבוא ה-blueprints לנוחות
from .system import system_bp
from .processes import processes_bp
from .gateway import gateway_bp
