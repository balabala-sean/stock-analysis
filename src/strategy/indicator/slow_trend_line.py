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
            N: 周期参数，默认 34（用于计算滚动高低价的窗口）

        Returns:
            添加了 UP_LINE, DOWN_LINE, bull_line, bear_line 列的 DataFrame
        """
        n = kwargs.get('N', 34)

        df_result = df.copy()

        # 加权价格：给予收盘价更高权重
        df_result['weighted_price'] = (2 * df_result['close'] + df_result['high'] + df_result['low']) / 4

        # 当前及之前 N 个周期内的滚动最低价
        df_result['rolling_low_min'] = df_result['low'].rolling(window=n, min_periods=1).min()

        # 当前及之前 N 个周期内的滚动最高价
        df_result['rolling_high_max'] = df_result['high'].rolling(window=n, min_periods=1).max()

        # 计算相对位置指标（类似 KD 指标的 RSV）
        denominator = df_result['rolling_high_max'] - df_result['rolling_low_min']
        denominator = denominator.replace(0, 1e-9)
        relative_position = (df_result['weighted_price'] - df_result['rolling_low_min']) / denominator * 100

        # UP_LINE：相对位置的短期 EWM 平滑
        df_result['UP_LINE'] = relative_position.ewm(span=9, adjust=False).mean()

        # DOWN_LINE：加权平均后的 EWM 平滑
        ref_up_line = df_result['UP_LINE'].shift(1)
        weighted_avg = 0.667 * ref_up_line + 0.333 * df_result['UP_LINE']
        df_result['DOWN_LINE'] = weighted_avg.ewm(span=2, adjust=False).mean()

        # 多头线：相对位置的长期 EWM 平滑
        df_result['bull_line'] = relative_position.ewm(span=30, adjust=False).mean()

        # 空头线：多头线的短期 EWM 平滑
        df_result['bear_line'] = df_result['bull_line'].ewm(span=5, adjust=False).mean()

        # 删除中间变量
        cols_to_drop = ['weighted_price', 'rolling_low_min', 'rolling_high_max']
        df_result.drop(columns=cols_to_drop, errors="ignore", inplace=True)

        return df_result