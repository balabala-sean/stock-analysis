# -*- coding: utf-8 -*-
"""
买入信号计算器
均值回归策略核心逻辑
"""

import pandas as pd
from typing import Tuple, Dict, Any
from pandas import DataFrame
from ..base import BaseSignalCalculator
from ..indicator import SlowTrendLineIndicator, PriceMeanIndicator


class BuySignalCalculator(BaseSignalCalculator):
    """买入信号计算器"""

    def __init__(self):
        """初始化计算器，创建指标实例"""
        self.trend_line_indicator = SlowTrendLineIndicator()
        self.price_mean_indicator = PriceMeanIndicator()

    def calculate_signals(self, df: DataFrame) -> DataFrame:
        """
        计算策略信号

        Args:
            df: 包含 OHLCV 数据的 DataFrame

        Returns:
            添加了信号列的 DataFrame
        """
        df_calc = df.copy()
        df_calc = self.trend_line_indicator.calculate(df_calc)
        df_calc = self.price_mean_indicator.calculate(df_calc)

        # 资金条件：过去 10 天内 MONEY_COMING 或 MONEY_LIVING 至少触发 5 次
        money_coming_cnt = (df_calc['MONEY_COMING'] > 0).rolling(window=10, min_periods=1).sum()
        money_living_cnt = (df_calc['MONEY_LIVING'] > 0).rolling(window=10, min_periods=1).sum()
        df_calc['MONEY_COND'] = (money_coming_cnt + money_living_cnt) >= 5

        # UP_LINE 条件：上穿 DOWN_LINE 且两者都 <= 25
        df_calc['UP_LINE_COND'] = (
            (df_calc['UP_LINE'] > df_calc['DOWN_LINE']) &
            (df_calc['UP_LINE'].shift(1) <= df_calc['DOWN_LINE'].shift(1)) &
            (df_calc['UP_LINE'] <= 25) &
            (df_calc['DOWN_LINE'] <= 25)
        )

        # 买入点：同时满足资金条件和 UP_LINE 条件
        df_calc['BUY_POINT'] = df_calc['MONEY_COND'] & df_calc['UP_LINE_COND']

        # 过滤信号：相邻信号至少间隔 5 个周期
        df_calc['FILTER_BUY'] = self._filter_signal(df_calc['BUY_POINT'], 5)

        return df_calc

    def _filter_signal(self, signal_series: pd.Series, n: int) -> pd.Series:
        """
        过滤信号，确保相邻信号至少间隔 n 个周期

        Args:
            signal_series: 原始信号序列
            n: 最小间隔周期数

        Returns:
            过滤后的信号序列
        """
        result = pd.Series(False, index=signal_series.index)
        last_signal_idx = -float('inf')

        for i in range(len(signal_series)):
            if signal_series.iloc[i]:
                if i - last_signal_idx > n:
                    result.iloc[i] = True
                    last_signal_idx = i

        return result

    def get_signals(self, df: DataFrame) -> Dict[str, Any]:
        """
        获取最新信号状态

        Args:
            df: 包含 OHLCV 数据的 DataFrame

        Returns:
            字典包含最新信号状态和指标值
        """
        df_calc = self.calculate_signals(df)

        last_row = df_calc.iloc[-1]

        return {
            'UP_LINE': float(last_row['UP_LINE']),
            'DOWN_LINE': float(last_row['DOWN_LINE']),
            'MONEY_COND': bool(last_row['MONEY_COND']),
            'BUY_POINT': bool(last_row['BUY_POINT']),
            'FILTER_BUY': bool(last_row['FILTER_BUY']),
        }

    def is_signal_triggered(self, df: DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        判断买入信号是否触发

        Args:
            df: 包含 OHLCV 数据的 DataFrame

        Returns:
            (是否有买入信号，信号详情字典)
        """
        df_calc = self.calculate_signals(df)

        if df_calc['FILTER_BUY'].iloc[-1]:
            return True, {
                'UP_LINE': float(df_calc['UP_LINE'].iloc[-1]),
                'DOWN_LINE': float(df_calc['DOWN_LINE'].iloc[-1]),
                'MONEY_COND': bool(df_calc['MONEY_COND'].iloc[-1]),
            }
        return False, {}

    