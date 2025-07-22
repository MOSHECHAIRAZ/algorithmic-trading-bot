"""
יצירת מאקרו התחברות בסיסי ל-IB Gateway
"""

from manual_macro_recorder import ManualMacroRecorder

# מיקומים טיפוסיים בחלון IB Gateway (אלה צריכים להיות מותאמים למסך שלך)
# נניח שחלון ה-Gateway נפתח במרכז המסך

# מיקומים משוערים (יצטרכו התאמה)
username_field = (960, 400)  # מרכז המסך, חלק עליון
password_field = (960, 450)  # קצת מתחת לשדה שם המשתמש
login_button = (960, 500)    # מתחת לשדה הסיסמה

print("יוצר מאקרו התחברות בסיסי...")
print(f"מיקומי שדות משוערים:")
print(f"  שדה שם משתמש: {username_field}")
print(f"  שדה סיסמה: {password_field}")
print(f"  כפתור התחברות: {login_button}")

# יצירת המקליט והמאקרו
recorder = ManualMacroRecorder()
macro_file = "recordings/ibkr_login_macro.json"

# יצירת המאקרו עם המיקומים
if recorder.create_login_macro(username_field, password_field, login_button):
    # שמירת המאקרו לקובץ
    if recorder.save_recording(macro_file):
        print(f"מאקרו נוצר ונשמר בהצלחה: {macro_file}")
        print("\nהמאקרו כולל את הפעולות הבאות:")
        print("1. קליק על שדה שם משתמש")
        print("2. ניקוי השדה (Ctrl+A)")
        print("3. הקלדת שם המשתמש")
        print("4. קליק על שדה סיסמה")
        print("5. ניקוי השדה (Ctrl+A)")
        print("6. הקלדת הסיסמה")
        print("7. קליק על כפתור התחברות")
        print("\nעכשיו תוכל להשתמש במאקרו דרך הממשק!")
    else:
        print("שגיאה בשמירת המאקרו")
else:
    print("שגיאה ביצירת המאקרו")
