# -*- coding: utf-8 -*-
"""
慢速趋势线指标计算
"""

from pandas import DataFrame
from ..base import BaseIndicator


class SlowTrendLineIndicator(BaseIndicator):
    """慢速趋势线指标计算器"""

    def calculate(self, df: DataFrame, **kwargs) -> DataFrame:
        """
        计算慢速趋势线

        Args:
            df: 包含 OHLC 数据的 DataFrame
            N: 周期参数，默认 34

        Returns:
            添加了 UP_LINE, DOWN_LINE, DUO, KONG 列的 DataFrame
        """
        n = kwargs.get('N', 34)

        df_result = df.copy()
        df_result['DY11'] = (2 * df_result['close'] + df_result['high'] + df_result['low']) / 4
        df_result['DY22'] = df_result['low'].rolling(window=n, min_periods=1).min()
        df_result['DY33'] = df_result['high'].rolling(window=n, min_periods=1).max()

        denominator = df_result['DY33'] - df_result['DY22']
        denominator = denominator.replace(0, 1e-9)
        intermediate = (df_result['DY11'] - df_result['DY22']) / denominator * 100

        df_result['UP_LINE'] = intermediate.ewm(span=9, adjust=False).mean()

        ref_up_line = df_result['UP_LINE'].shift(1)
        weighted_avg = 0.667 * ref_up_line + 0.333 * df_result['UP_LINE']
        df_result['DOWN_LINE'] = weighted_avg.ewm(span=2, adjust=False).mean()

        df_result['DUO'] = intermediate.ewm(span=30, adjust=False).mean()
        df_result['KONG'] = df_result['DUO'].ewm(span=5, adjust=False).mean()

        # 删除中间变量
        cols_to_drop = ['DY11', 'DY22', 'DY33']
        df_result.drop(columns=cols_to_drop, errors="ignore", inplace=True)

        return df_result