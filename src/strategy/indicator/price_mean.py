# -*- coding: utf-8 -*-
"""
价格均值回归指标计算
"""

import numpy as np
from pandas import DataFrame
from ..base import BaseIndicator
from ..vba import sma_without_zero_reset


class PriceMeanIndicator(BaseIndicator):
    """价格均值回归指标计算器"""

    def calculate(self, df: DataFrame, **kwargs) -> DataFrame:
        """
        计算价格的均值回归范围（0~100）

        Args:
            df: 包含 OHLCV 数据的 DataFrame
            N1: 参数 1，默认 34
            N2: 参数 2，默认 21
            N3: 参数 3，默认 10
            N4: 参数 4，默认 33
            N5: 参数 5，默认 3

        Returns:
            添加了 MONEY_COMING, MONEY_LIVING, XIAO5 等列的 DataFrame
        """
        n1 = kwargs.get('N1', 34)
        n2 = kwargs.get('N2', 21)
        n3 = kwargs.get('N3', 10)
        n4 = kwargs.get('N4', 33)
        n5 = kwargs.get('N5', 3)

        df_result = df.copy()

        df_result['AVG'] = (df_result['low'] + df_result['open'] + df_result['close'] + df_result['high']) / 4
        df_result['XIAO1'] = df_result['AVG'].shift(1)

        df_result['low_diff'] = (df_result['low'] - df_result['XIAO1']).abs()
        df_result['max_diff'] = (df_result['low'] - df_result['XIAO1']).clip(lower=0)

        # 计算 SMA，需要 reindex 对齐索引
        low_diff_series = df_result['low_diff'].dropna()
        max_diff_series = df_result['max_diff'].dropna()

        sma_abs = sma_without_zero_reset(low_diff_series, n1, 1).reindex(df_result.index, fill_value=np.nan)
        sma_max = sma_without_zero_reset(max_diff_series, n2, 1).reindex(df_result.index, fill_value=np.nan)

        df_result['SMA_abs'] = sma_abs
        df_result['SMA_max'] = sma_max

        df_result['XIAO2'] = df_result['SMA_abs'] / df_result['SMA_max'].replace(0, np.nan)
        df_result['XIAO3'] = df_result['XIAO2'].ewm(span=n3, adjust=False).mean()
        df_result['XIAO4'] = df_result['low'].rolling(window=n4, min_periods=1).min()

        condition = df_result['low'] <= df_result['XIAO4']
        df_result['XIAO5_temp'] = df_result['XIAO3'].where(condition, 0)
        df_result['XIAO5'] = df_result['XIAO5_temp'].ewm(span=n5, adjust=False).mean()

        df_result['MONEY_COMING'] = df_result['XIAO5'].where(
            (df_result['XIAO5'] > df_result['XIAO5'].shift(1)) & (df_result['XIAO5'] > 5), 0
        )
        df_result['MONEY_LIVING'] = df_result['XIAO5'].where(
            (df_result['XIAO5'] < df_result['XIAO5'].shift(1)) & (df_result['XIAO5'] > 5), 0
        )

        df_result['MONEY_COMING'] = df_result['MONEY_COMING'].fillna(0)
        df_result['MONEY_LIVING'] = df_result['MONEY_LIVING'].fillna(0)
        df_result['XIAO2'] = df_result['XIAO2'].fillna(np.nan)
        df_result['XIAO3'] = df_result['XIAO3'].fillna(np.nan)
        df_result['XIAO4'] = df_result['XIAO4'].fillna(np.nan)
        df_result['XIAO5'] = df_result['XIAO5'].fillna(np.nan)
        df_result['low_diff'] = df_result['low_diff'].fillna(np.nan)
        df_result['max_diff'] = df_result['max_diff'].fillna(np.nan)
        df_result['SMA_abs'] = df_result['SMA_abs'].fillna(np.nan)
        df_result['SMA_max'] = df_result['SMA_max'].fillna(np.nan)
        df_result['XIAO5_temp'] = df_result['XIAO5_temp'].fillna(np.nan)

        df_result.drop(columns=['AVG', 'XIAO5_temp'], errors="ignore", inplace=True)

        return df_result