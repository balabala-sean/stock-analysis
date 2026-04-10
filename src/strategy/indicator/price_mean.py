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
            N1: 参数 1，默认 34（用于计算低价偏离的绝对值 SMA）
            N2: 参数 2，默认 21（用于计算低价偏离的最大值 SMA）
            N3: 参数 3，默认 10（用于平滑比例值的 EWM 周期）
            N4: 参数 4，默认 33（用于计算滚动最低价的窗口）
            N5: 参数 5，默认 3（用于最终信号值的 EWM 周期）

        Returns:
            添加了 MONEY_COMING, MONEY_LIVING, price_mean_signal 等列的 DataFrame
        """
        n1 = kwargs.get('N1', 34)
        n2 = kwargs.get('N2', 21)
        n3 = kwargs.get('N3', 10)
        n4 = kwargs.get('N4', 33)
        n5 = kwargs.get('N5', 3)

        df_result = df.copy()

        # 计算平均价格（低、开、收、高的平均值）
        df_result['avg_price'] = (df_result['low'] + df_result['open'] + df_result['close'] + df_result['high']) / 4

        # 前一日均价，用于计算价格偏离
        df_result['prev_avg_price'] = df_result['avg_price'].shift(1)

        # 计算低价与前日均价的偏离
        df_result['low_diff_abs'] = (df_result['low'] - df_result['prev_avg_price']).abs()
        df_result['low_diff_max'] = (df_result['low'] - df_result['prev_avg_price']).clip(lower=0)

        # 计算 SMA，需要 reindex 对齐索引
        low_diff_abs_series = df_result['low_diff_abs'].dropna()
        low_diff_max_series = df_result['low_diff_max'].dropna()

        sma_abs = sma_without_zero_reset(low_diff_abs_series, n1, 1).reindex(df_result.index, fill_value=np.nan)
        sma_max = sma_without_zero_reset(low_diff_max_series, n2, 1).reindex(df_result.index, fill_value=np.nan)

        df_result['sma_abs'] = sma_abs
        df_result['sma_max'] = sma_max

        # 计算低价偏离比例
        df_result['low_diff_ratio'] = df_result['sma_abs'] / df_result['sma_max'].replace(0, np.nan)

        # 平滑比例值
        df_result['smoothed_ratio'] = df_result['low_diff_ratio'].ewm(span=n3, adjust=False).mean()

        # 计算滚动最低价（N4 周期内最低价）
        df_result['rolling_low_min'] = df_result['low'].rolling(window=n4, min_periods=1).min()

        # 当 当前低价 <= 滚动最低价时，使用平滑比例值，否则为 0
        condition = df_result['low'] <= df_result['rolling_low_min']
        df_result['signal_base'] = df_result['smoothed_ratio'].where(condition, 0)

        # 最终信号值（经过 EWM 平滑）
        df_result['price_mean_signal'] = df_result['signal_base'].ewm(span=n5, adjust=False).mean()

        # 资金流入信号：信号值上升且大于阈值 5
        df_result['MONEY_COMING'] = df_result['price_mean_signal'].where(
            (df_result['price_mean_signal'] > df_result['price_mean_signal'].shift(1)) & (df_result['price_mean_signal'] > 5), 0
        )

        # 资金流出信号：信号值下降且大于阈值 5
        df_result['MONEY_LIVING'] = df_result['price_mean_signal'].where(
            (df_result['price_mean_signal'] < df_result['price_mean_signal'].shift(1)) & (df_result['price_mean_signal'] > 5), 0
        )

        # 填充 NaN 值
        df_result['MONEY_COMING'] = df_result['MONEY_COMING'].fillna(0)
        df_result['MONEY_LIVING'] = df_result['MONEY_LIVING'].fillna(0)
        df_result['low_diff_ratio'] = df_result['low_diff_ratio'].fillna(np.nan)
        df_result['smoothed_ratio'] = df_result['smoothed_ratio'].fillna(np.nan)
        df_result['rolling_low_min'] = df_result['rolling_low_min'].fillna(np.nan)
        df_result['price_mean_signal'] = df_result['price_mean_signal'].fillna(np.nan)
        df_result['low_diff_abs'] = df_result['low_diff_abs'].fillna(np.nan)
        df_result['low_diff_max'] = df_result['low_diff_max'].fillna(np.nan)
        df_result['sma_abs'] = df_result['sma_abs'].fillna(np.nan)
        df_result['sma_max'] = df_result['sma_max'].fillna(np.nan)
        df_result['signal_base'] = df_result['signal_base'].fillna(np.nan)

        # 删除中间变量（不需要输出的列）
        df_result.drop(columns=['avg_price', 'signal_base'], errors="ignore", inplace=True)

        return df_result