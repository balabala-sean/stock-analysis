# -*- coding: utf-8 -*-
"""
可视化包单元测试
"""

import pytest
import sys
import os
import pandas as pd
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.visualization import Plotter


def create_sample_dataframe(rows=50):
    """创建样本 DataFrame 用于测试"""
    dates = pd.date_range('2024-01-01', periods=rows, freq='D')

    np.random.seed(42)
    base_price = 100

    # 生成随机价格数据
    close = base_price + np.cumsum(np.random.randn(rows))
    high = close + np.abs(np.random.randn(rows)) * 0.5
    low = close - np.abs(np.random.randn(rows)) * 0.5
    open_price = close - np.random.randn(rows) * 0.3

    df = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'vol': np.random.randint(1000, 10000, rows),
        'amount': np.random.randint(10000, 100000, rows),
    }, index=dates)

    return df


class TestPlotter:
    """Plotter 测试类"""

    def test_init(self):
        """测试初始化"""
        plotter = Plotter()
        assert plotter is not None
        assert plotter.style is not None

    def test_init_with_style(self):
        """测试自定义样式初始化"""
        plotter = Plotter(style='china')
        assert plotter.style is not None

        plotter_default = Plotter(style='default')
        assert plotter_default.style is not None

    def test_print_signal_summary(self, capsys):
        """测试打印信号汇总"""
        df = create_sample_dataframe()
        df['BUY_POINT'] = False
        df['FILTER_BUY'] = False
        df['MONEY_COND'] = True
        df['UP_LINE'] = 20.0
        df['DOWN_LINE'] = 18.0

        plotter = Plotter()
        plotter.print_signal_summary(df, '600036', '招商银行')

        captured = capsys.readouterr()
        assert '600036' in captured.out
        assert '招商银行' in captured.out
        assert 'MONEY_COND' in captured.out


class TestSignalSummary:
    """信号汇总测试"""

    def test_empty_signals(self, capsys):
        """测试无信号情况"""
        df = create_sample_dataframe()
        df['BUY_POINT'] = False
        df['FILTER_BUY'] = False
        df['MONEY_COND'] = False
        df['UP_LINE'] = 50.0
        df['DOWN_LINE'] = 50.0

        plotter = Plotter()
        plotter.print_signal_summary(df, '600036', '招商银行')

        captured = capsys.readouterr()
        assert '信号统计' in captured.out
        assert '0' in captured.out

    def test_with_buy_signals(self, capsys):
        """测试有买入信号情况"""
        df = create_sample_dataframe()
        df['BUY_POINT'] = False
        df['FILTER_BUY'] = False
        df['MONEY_COND'] = True
        df['UP_LINE'] = 20.0
        df['DOWN_LINE'] = 18.0

        # 设置一些买入信号
        df.loc[df.index[10], 'BUY_POINT'] = True
        df.loc[df.index[10], 'FILTER_BUY'] = True

        plotter = Plotter()
        plotter.print_signal_summary(df, '600036', '招商银行')

        captured = capsys.readouterr()
        assert '买入点位' in captured.out or '过滤后买入' in captured.out
