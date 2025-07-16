"""
Unified Feature Calculator (Robust Version)
מחשב אינדיקטורים באופן אינדיבידואלי כדי למנוע קריסה כללית.
"""
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import pandas as pd
import pandas_ta as ta
import numpy as np
import logging

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

# ...existing code...
