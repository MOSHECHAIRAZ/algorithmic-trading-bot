# 🤖 Algorithmic Trading Bot - מערכת מסחר אלגוריתמית מתקדמת

> **מערכת מסחר אלגוריתמית מלאה המשלבת בינה מלאכותית, ניתוח טכני, ואינטגרציה עם Interactive Brokers**

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Node.js](https://img.shields.io/badge/node.js-16+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

## � תוכן עניינים

- [🎯 סקירה כללית](#-סקירה-כללית)
- [⚡ תכונות עיקריות](#-תכונות-עיקריות)
- [🏗️ ארכיטקטורת המערכת](#️-ארכיטקטורת-המערכת)
- [📊 רכיבי המערכת](#-רכיבי-המערכת)
- [🚀 התקנה מהירה](#-התקנה-מהירה)
- [📁 מבנה הפרויקט](#-מבנה-הפרויקט)
- [⚙️ הגדרת הקונפיגורציה](#️-הגדרת-הקונפיגורציה)
- [🔧 השימוש במערכת](#-השימוש-במערכת)
- [📈 אסטרטגיות המסחר](#-אסטרטגיות-המסחר)
- [🛡️ ניהול סיכונים](#️-ניהול-סיכונים)
- [📊 ניתוח ודוחות](#-ניתוח-ודוחות)
- [🔌 API ואינטגרציות](#-api-ואינטגרציות)
- [🧪 בדיקות ואימותים](#-בדיקות-ואימותים)
- [📚 תיעוד מפורט](#-תיעוד-מפורט)

---

## 🎯 סקירה כללית

מערכת מסחר אלגוריתמית מתקדמת הכוללת:

- **🧠 בינה מלאכותית**: מודלי Machine Learning מבוססי LightGBM
- **📊 ניתוח טכני**: מעל 100 אינדיקטורים טכניים מתקדמים
- **⚡ מסחר בזמן אמת**: אינטגרציה ישירה עם Interactive Brokers
- **🎯 אופטימיזציה**: אלגוריתמי Optuna לאופטימיזציה אוטומטית
- **🛡️ ניהול סיכונים**: מערכת Stop Loss ו-Take Profit חכמה
- **📈 בקטסטינג**: סימולציות מדויקות על נתונים היסטוריים

### � יכולות מיוחדות:
- **רכיבי VIX**: שימוש באינדקס הפחד לזיהוי מצבי שוק
- **Market Regime Detection**: זיהוי מצבי שוק שונים (טרנד/רווח/תנודתיות)
- **Multi-Timeframe Analysis**: ניתוח על מספר מסגרות זמן
- **Sentiment Analysis**: שילוב אינדיקטורי סנטימנט

---

## ⚡ תכונות עיקריות

### 🔮 בינה מלאכותית מתקדמת
- **מודלי LightGBM**: אופטימיזציה עם Optuna
- **Feature Engineering**: מעל 100 פיצ'רים מתקדמים
- **Cross-Validation**: אימות זמני מדויק
- **Hyperparameter Optimization**: אופטימיזציה אוטומטית של פרמטרים

### 📊 ניתוח טכני מקיף
- **Technical Indicators**: RSI, MACD, Bollinger Bands ועוד
- **Custom Indicators**: אינדיקטורים מותאמים אישית
- **Multi-Asset Analysis**: ניתוח SPY + VIX
- **Market Microstructure**: ניתוח מיקרו-מבנה השוק

### ⚡ מסחר אוטומטי
- **Real-Time Trading**: מסחר בזמן אמת עם IB
- **Order Management**: ניהול פקודות מתקדם
- **Position Sizing**: חישוב גודל פוזיציה אוטומטי
- **Risk Management**: Stop Loss ו-Take Profit דינמיים

### 🛡️ בטיחות וניהול סיכונים
- **Portfolio Risk**: ניהול סיכון תיק
- **Position Limits**: מגבלות פוזיציה
- **Drawdown Control**: בקרת ירידות
- **Emergency Stop**: עצירת חירום אוטומטית

---

## 🏗️ ארכיטקטורת המערכת

```
Data Layer:
[yfinance/IBKR] → [Raw Data] → [Data Processing] → [Feature Engineering]

ML Layer:
[Data Processing] → [Model Training] → [Optuna Optimization] → [Champion Model]

Trading Layer:
[Champion Model] → [Signal Generation] → [Risk Management] → [Order Execution]

Infrastructure:
[Flask API] → [Web Dashboard]
[Node.js Agent] → [IB Gateway]
[SQLite DB] → [State Management]
```

### 🔧 טכנולוגיות ליבה:
- **Python 3.8+**: ליבת המערכת, ML, ניתוח נתונים
- **Node.js 16+**: אגנט מסחר, אינטגרציה עם IB
- **Flask**: API ו-Dashboard
- **SQLite**: מסד נתונים מקומי
- **LightGBM**: מודלי Machine Learning
- **Optuna**: אופטימיזציה
- **pandas/numpy**: עיבוד נתונים

---

## 📊 רכיבי המערכת

### 1. 📈 מודול איסוף הנתונים (`src/data_collector.py`)
```python
# איסוף נתונים מ-yfinance ו-IBKR
- נתוני SPY (S&P 500 ETF)
- נתוני VIX (מדד הפחד)
- נתונים היסטוריים עד 15 שנים
- עדכונים בזמן אמת
```

### 2. 🧮 מודול עיבוד הנתונים (`src/preprocessing.py`)
```python
# ניקוי ועיבוד נתונים גולמיים
- טיפול בנתונים חסרים
- נרמול נתונים
- סנכרון מסגרות זמן
- בדיקת איכות נתונים
```

### 3. 🔬 מודול הנדסת פיצ'רים (`src/feature_engineering.py`)
```python
# יצירת פיצ'רים מתקדמים
- אינדיקטורים טכניים (100+)
- פיצ'רי VIX מתקדמים
- מדדי סנטימנט
- Market Regime Features
```

### 4. 🧠 מודול אימון המודל (`src/main_trainer.py`)
```python
# אימון מודלי ML מתקדמים
- LightGBM עם אופטימיזציה
- Cross-validation זמני
- Feature selection אוטומטי
- שמירת מודל אלוף
```

### 5. 🏃 אגנט המסחר (`agent/trading_agent.js`)
```javascript
// אגנט מסחר בזמן אמת
- חיבור ל-Interactive Brokers
- קבלת אותות מהמודל
- ביצוע פקודות
- ניהול פוזיציות
```

### 6. 🌐 שרת API (`api_server.py`)
```python
# API ו-Dashboard מרכזיים
- ממשק ניהול מרכזי
- מעקב אחר ביצועים
- ניהול הגדרות
- דוחות בזמן אמת
```

### 7. 🔄 מנהל הפרויקט (`src/utils/project_organizer.py`)
```python
# ניהול וארגון המערכת
- ניקוי קבצים זמניים
- ארגון תוצאות
- גיבוי אוטומטי
- ניהול גרסאות
```

---

## 🚀 התקנה מהירה

### דרישות מערכת:
- **Windows 10/11**
- **Python 3.8+**
- **Node.js 16+**
- **Interactive Brokers TWS/Gateway**
- **8GB RAM (מינימום)**
- **50GB אחסון פנוי**

### 1. 📥 שיבוט הפרויקט
```bash
git clone https://github.com/MOSHECHAIRAZ/algorithmic-trading-bot.git
cd algorithmic-trading-bot
```

### 2. 🐍 התקנת תלויות Python
```bash
# יצירת סביבה וירטואלית
python -m venv trading_env
trading_env\Scripts\activate

# התקנת תלויות
pip install -r requirements.txt
```

### 3. 📦 התקנת תלויות Node.js
```bash
npm install
```

### 4. ⚙️ הגדרת משתני סביבה
```bash
# יצירת קובץ .env
copy .env.example .env
# ערוך את משתני הסביבה לפי הצרכים
```

### 5. 🏁 הפעלה ראשונית
```bash
# הפעלת המערכת
python run_all.py
```


