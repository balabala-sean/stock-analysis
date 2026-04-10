# -*- coding: utf-8 -*-
"""
VBA 风格函数库
"""

import numpy as np
import pandas as pd


def sma_without_zero_reset(series, N, M):
    """
    SMA 平滑移动平均，不重置零值

    Args:
        series: 输入序列
        N: 周期
        M: 权重因子

    Returns:
        SMA 结果序列
    """
    result = [series.iloc[0]]
    for i in range(1, len(series)):
        prev = result[-1]
        curr = series.iloc[i]
        val = (M * curr + (N - M) * prev) / N
        result.append(np.around(val, 4))
    return series.__class__(result, index=series.index)


def ema(series, N):
    """
    指数移动平均

    Args:
        series: 输入序列
        N: 周期

    Returns:
        EMA 结果序列
    """
    return series.ewm(span=N, adjust=False).mean()