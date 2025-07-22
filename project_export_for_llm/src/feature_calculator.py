"""
Unified Feature Calculator (Robust Version)
מחשב אינדיקטורים באופן אינדיבידואלי כדי למנוע קריסה כללית.
"""
import warnings
import pandas as pd
import pandas_ta as ta
import numpy as np
import logging

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class FeatureCalculator:
    """
    מחשב את כל האינדיקטורים הטכניים הזמינים מספריית pandas_ta
    באופן אינדיבידואלי כדי לעקוף שגיאות באינדיקטורים ספציפיים.
    """

    def add_all_possible_indicators(self, df: pd.DataFrame, verbose: bool = False, features_to_calculate: list = None) -> tuple[pd.DataFrame, dict]:
        """
        הפונקציה המרכזית לחישוב פיצ'רים. מקבלת DataFrame עם עמודות
        'open', 'high', 'low', 'close', 'volume' ומחזירה tuple:
        (DataFrame עם כל האינדיקטורים שחושבו בהצלחה, dict סטטיסטיקות חישוב)
        """
        if df.empty:
            stats = {"total_attempted": 0, "succeeded": 0, "failed": 0, "failed_list": []}
            if verbose:
                logging.warning("Input DataFrame is empty. Returning as is.")
            return df, stats
        df_with_features = df.copy()
        df_with_features.columns = [col.lower() for col in df_with_features.columns]
        required_cols = {'open', 'high', 'low', 'close', 'volume'}
        if not required_cols.issubset(df_with_features.columns):
            missing = required_cols - set(df_with_features.columns)
            raise ValueError(f"Missing required OHLCV columns in DataFrame: {missing}")

        if features_to_calculate:
            base_indicator_names = sorted(list(set([ind.split('_')[0].upper() for ind in features_to_calculate])))
            available_indicators = [name for name in base_indicator_names if hasattr(ta, name.lower())]
            if verbose:
                logging.info(f"Calculating a specific list of {len(available_indicators)} base indicators.")
        else:
            available_indicators = []
            for category in ta.Category:
                available_indicators.extend(ta.Category[category])
            if verbose:
                logging.info(f"Attempting to calculate all {len(available_indicators)} available indicators...")

        successful_indicators_count = 0
        failed_indicators_details = []
        total_attempted = len(available_indicators)

        for indicator_name in available_indicators:
            try:
                cols_before = len(df_with_features.columns)
                
                # תיקון לבעיית append המיושנת - יצירת DataFrame זמני ואיחוד במקום שימוש ב-append
                indicator_func = getattr(ta, indicator_name.lower(), None)
                if indicator_func:
                    # חישוב האינדיקטור
                    temp_result = indicator_func(
                        high=df_with_features['high'] if 'high' in df_with_features.columns else None,
                        low=df_with_features['low'] if 'low' in df_with_features.columns else None,
                        close=df_with_features['close'] if 'close' in df_with_features.columns else None,
                        open_=df_with_features['open'] if 'open' in df_with_features.columns else None,
                        volume=df_with_features['volume'] if 'volume' in df_with_features.columns else None,
                    )
                    
                    # אם התוצאה היא סדרה בודדת
                    if isinstance(temp_result, pd.Series):
                        df_with_features[temp_result.name] = temp_result
                    # אם התוצאה היא DataFrame
                    elif isinstance(temp_result, pd.DataFrame):
                        # מיזוג של הDataFrame עם התוצאות לDF המקורי
                        for col in temp_result.columns:
                            df_with_features[col] = temp_result[col]
                else:
                    # ניסיון להפעיל את הפונקציה ב-DataFrame ישירות
                    df_with_features.ta(kind=indicator_name, append=True)
                
                cols_after = len(df_with_features.columns)
                if cols_after > cols_before:
                    successful_indicators_count += 1
                else:
                    failed_indicators_details.append({
                        "indicator": indicator_name,
                        "error": "Execution finished but no columns were added."
                    })
            except Exception as e:
                failed_indicators_details.append({
                    "indicator": indicator_name,
                    "error": f"{type(e).__name__}: {str(e)}"
                })

        initial_cols = len(df_with_features.columns)
        df_with_features.dropna(axis=1, how='all', inplace=True)
        cols_to_drop = [col for col in df_with_features.columns if df_with_features[col].nunique(dropna=False) <= 1]
        df_with_features.drop(columns=cols_to_drop, inplace=True, errors='ignore')
        final_cols = len(df_with_features.columns)
        if verbose:
            logging.info(f"Cleanup: Removed {initial_cols - final_cols} constant or all-NaN columns.")
        if 'vix_close' not in df_with_features.columns and 'vix_close' in df.columns:
            df_with_features['vix_close'] = df['vix_close']
        if 'close' in df_with_features.columns:
            df_with_features['logret_1'] = ta.log_return(df_with_features['close'], length=1)
        df_with_features.replace([np.inf, -np.inf], np.nan, inplace=True)
        final_columns = list(df.columns) + [col for col in df_with_features.columns if col not in df.columns]
        df_with_features = df_with_features.reindex(columns=final_columns, fill_value=np.nan)

        stats = {
            "total_attempted": total_attempted,
            "succeeded": successful_indicators_count,
            "failed": len(failed_indicators_details),
            "failed_list": failed_indicators_details
        }
        if verbose:
            logging.info(f"Calculation summary: {stats['succeeded']} succeeded, {stats['failed']} failed out of {stats['total_attempted']} attempted.")
        return df_with_features, stats

    def add_critical_indicators(self, df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
        """
        מוסיף אינדיקטורים קריטיים לאסטרטגיות מסחר באופן ישיר.
        מטרת הפונקציה לוודא שהאינדיקטורים החשובים ביותר תמיד מחושבים, 
        גם אם הם נכשלים בגישה הכללית.
        
        Args:
            df: DataFrame עם נתוני OHLCV
            verbose: האם להדפיס לוגים מפורטים
            
        Returns:
            DataFrame עם אינדיקטורים קריטיים
        """
        if verbose:
            logging.info("Adding critical indicators directly...")
            
        result_df = df.copy()
        result_df.columns = [col.lower() for col in result_df.columns]
        
        # וידוא שיש את כל העמודות הנדרשות
        required_cols = {'open', 'high', 'low', 'close', 'volume'}
        if not required_cols.issubset(result_df.columns):
            missing = required_cols - set(result_df.columns)
            if verbose:
                logging.warning(f"Missing columns for critical indicators: {missing}")
            return result_df
            
        # רשימת האינדיקטורים הקריטיים והפונקציות שלהם
        critical_indicators = {
            "stoch": self._add_stochastic,
            "bbands": self._add_bollinger_bands,
            "atr": self._add_average_true_range,
            "rsi": self._add_rsi,
            "macd": self._add_macd,
            "adx": self._add_adx,
            "obv": self._add_obv
        }
        
        # הוספת כל אינדיקטור בנפרד עם טיפול בשגיאות
        for name, func in critical_indicators.items():
            try:
                result_df = func(result_df)
                if verbose:
                    logging.info(f"✓ Added {name} indicator successfully")
            except Exception as e:
                if verbose:
                    logging.warning(f"✗ Failed to add {name} indicator: {str(e)}")
                    
        return result_df
    
    def _add_stochastic(self, df):
        """מוסיף אינדיקטור סטוכסטי (Stochastic Oscillator)"""
        high_14 = df['high'].rolling(window=14).max()
        low_14 = df['low'].rolling(window=14).min()
        
        # חישוב %K (קו מהיר)
        df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
        
        # חישוב %D (קו איטי) - ממוצע נע פשוט של 3 תקופות של %K
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
        return df
    
    def _add_bollinger_bands(self, df):
        """מוסיף את רצועות בולינגר (Bollinger Bands)"""
        # פרמטרים סטנדרטיים: תקופה של 20 וסטיית תקן של 2
        period = 20
        std_dev = 2
        
        # חישוב הממוצע הנע
        df['bbands_middle'] = df['close'].rolling(window=period).mean()
        
        # חישוב סטיית התקן
        rolling_std = df['close'].rolling(window=period).std()
        
        # חישוב הרצועות העליונה והתחתונה
        df['bbands_upper'] = df['bbands_middle'] + (rolling_std * std_dev)
        df['bbands_lower'] = df['bbands_middle'] - (rolling_std * std_dev)
        
        # חישוב אחוז B (מיקום המחיר בין הרצועות)
        df['bbands_pct_b'] = (df['close'] - df['bbands_lower']) / (df['bbands_upper'] - df['bbands_lower'])
        
        return df
    
    def _add_average_true_range(self, df):
        """מוסיף אינדיקטור ATR (Average True Range)"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # חישוב True Range
        df['tr1'] = abs(high - low)
        df['tr2'] = abs(high - close.shift())
        df['tr3'] = abs(low - close.shift())
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # חישוב ATR - ממוצע נע של 14 ימים
        df['atr'] = df['tr'].rolling(window=14).mean()
        
        # ניקוי עמודות ביניים
        df.drop(['tr1', 'tr2', 'tr3', 'tr'], axis=1, inplace=True)
        
        return df
    
    def _add_rsi(self, df):
        """מוסיף אינדיקטור RSI (Relative Strength Index)"""
        delta = df['close'].diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def _add_macd(self, df):
        """מוסיף אינדיקטור MACD (Moving Average Convergence Divergence)"""
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def _add_adx(self, df):
        """מוסיף אינדיקטור ADX (Average Directional Index)"""
        # חישוב +DM ו-DM
        df['dm_plus'] = 0.0
        df['dm_minus'] = 0.0
        
        for i in range(1, len(df)):
            high_diff = df['high'].iloc[i] - df['high'].iloc[i-1]
            low_diff = df['low'].iloc[i-1] - df['low'].iloc[i]
            
            if high_diff > low_diff and high_diff > 0:
                df['dm_plus'].iloc[i] = high_diff
            else:
                df['dm_plus'].iloc[i] = 0
                
            if low_diff > high_diff and low_diff > 0:
                df['dm_minus'].iloc[i] = low_diff
            else:
                df['dm_minus'].iloc[i] = 0
        
        # חישוב ATR
        self._add_average_true_range(df)
        
        # חישוב +DI ו-DI
        period = 14
        df['di_plus'] = 100 * (df['dm_plus'].rolling(window=period).mean() / df['atr'])
        df['di_minus'] = 100 * (df['dm_minus'].rolling(window=period).mean() / df['atr'])
        
        # חישוב DX ו-ADX
        df['dx'] = 100 * (abs(df['di_plus'] - df['di_minus']) / (df['di_plus'] + df['di_minus']))
        df['adx'] = df['dx'].rolling(window=period).mean()
        
        # ניקוי עמודות ביניים
        df.drop(['dm_plus', 'dm_minus', 'dx'], axis=1, inplace=True)
        
        return df
    
    def _add_obv(self, df):
        """מוסיף אינדיקטור OBV (On-Balance Volume)"""
        df['obv'] = 0
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                df['obv'].iloc[i] = df['obv'].iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                df['obv'].iloc[i] = df['obv'].iloc[i-1] - df['volume'].iloc[i]
            else:
                df['obv'].iloc[i] = df['obv'].iloc[i-1]
                
        return df

# ...existing code...
