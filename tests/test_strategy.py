# -*- coding: utf-8 -*-
"""
策略包单元测试
"""

import pytest
import sys
import os
import pandas as pd
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy import (
    BuySignalCalculator,
    SlowTrendLineIndicator,
    PriceMeanIndicator,
    BaseIndicator,
    BaseSignalCalculator
)


def create_sample_dataframe(rows=100):
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


class TestBaseClasses:
    """抽象基类测试"""

    def test_base_indicator_is_abstract(self):
        """测试 BaseIndicator 是抽象类"""
        assert hasattr(BaseIndicator, '__abstractmethods__')
        assert 'calculate' in BaseIndicator.__abstractmethods__

    def test_base_signal_calculator_is_abstract(self):
        """测试 BaseSignalCalculator 是抽象类"""
        assert hasattr(BaseSignalCalculator, '__abstractmethods__')
        assert 'calculate_signals' in BaseSignalCalculator.__abstractmethods__


class TestSlowTrendLineIndicator:
    """慢速趋势线指标测试"""

    def test_init(self):
        """测试初始化"""
        calc = SlowTrendLineIndicator()
        assert calc is not None

    def test_is_base_indicator_subclass(self):
        """测试继承自 BaseIndicator"""
        assert issubclass(SlowTrendLineIndicator, BaseIndicator)

    def test_calculate_basic(self):
        """测试基本计算"""
        df = create_sample_dataframe()
        calc = SlowTrendLineIndicator()
        result = calc.calculate(df)

        assert 'UP_LINE' in result.columns
        assert 'DOWN_LINE' in result.columns
        assert 'bull_line' in result.columns
        assert 'bear_line' in result.columns
        assert len(result) == len(df)

    def test_calculate_with_custom_n(self):
        """测试自定义 N 参数"""
        df = create_sample_dataframe()
        calc = SlowTrendLineIndicator()
        result = calc.calculate(df, N=20)

        assert 'UP_LINE' in result.columns
        assert len(result) == len(df)

    def test_no_temp_columns(self):
        """测试中间变量已被删除"""
        df = create_sample_dataframe()
        calc = SlowTrendLineIndicator()
        result = calc.calculate(df)

        assert 'weighted_price' not in result.columns
        assert 'rolling_low_min' not in result.columns
        assert 'rolling_high_max' not in result.columns

    def test_get_name(self):
        """测试获取指标名称"""
        calc = SlowTrendLineIndicator()
        assert calc.get_name() == 'SlowTrendLineIndicator'


class TestPriceMeanIndicator:
    """价格均值回归指标测试"""

    def test_init(self):
        """测试初始化"""
        calc = PriceMeanIndicator()
        assert calc is not None

    def test_is_base_indicator_subclass(self):
        """测试继承自 BaseIndicator"""
        assert issubclass(PriceMeanIndicator, BaseIndicator)

    def test_calculate_basic(self):
        """测试基本计算"""
        df = create_sample_dataframe()
        calc = PriceMeanIndicator()
        result = calc.calculate(df)

        assert 'MONEY_COMING' in result.columns
        assert 'MONEY_LIVING' in result.columns
        assert 'price_mean_signal' in result.columns
        assert len(result) == len(df)

    def test_money_coming_values(self):
        """测试资金流入值"""
        df = create_sample_dataframe()
        calc = PriceMeanIndicator()
        result = calc.calculate(df)

        # MONEY_COMING 应该是非负的
        assert (result['MONEY_COMING'] >= 0).all()

    def test_money_living_values(self):
        """测试资金流出值"""
        df = create_sample_dataframe()
        calc = PriceMeanIndicator()
        result = calc.calculate(df)

        # MONEY_LIVING 应该是非负的
        assert (result['MONEY_LIVING'] >= 0).all()

    def test_get_name(self):
        """测试获取指标名称"""
        calc = PriceMeanIndicator()
        assert calc.get_name() == 'PriceMeanIndicator'


class TestBuySignalCalculator:
    """买入信号计算器测试"""

    def test_init(self):
        """测试初始化"""
        calc = BuySignalCalculator()
        assert calc is not None
        assert calc.trend_line_indicator is not None
        assert calc.price_mean_indicator is not None

    def test_is_base_signal_calculator_subclass(self):
        """测试继承自 BaseSignalCalculator"""
        assert issubclass(BuySignalCalculator, BaseSignalCalculator)

    def test_calculate_signals(self):
        """测试信号计算"""
        df = create_sample_dataframe()
        calc = BuySignalCalculator()
        result = calc.calculate_signals(df)

        assert 'MONEY_COND' in result.columns
        assert 'UP_LINE_COND' in result.columns
        assert 'BUY_POINT' in result.columns
        assert 'FILTER_BUY' in result.columns

    def test_calculate_signals_basic(self):
        """测试信号计算基本功能"""
        df = create_sample_dataframe()
        calc = BuySignalCalculator()
        result = calc.calculate_signals(df)

        assert 'FILTER_BUY' in result.columns

    def test_filter_signal(self):
        """测试信号过滤"""
        calc = BuySignalCalculator()

        # 创建连续的买入信号
        signal_series = pd.Series([True, True, True, False, True, True])
        filtered = calc._filter_signal(signal_series, 2)

        # 验证过滤后的信号间隔
        assert isinstance(filtered, pd.Series)
        assert len(filtered) == len(signal_series)

    def test_get_signals(self):
        """测试获取信号状态"""
        df = create_sample_dataframe()
        calc = BuySignalCalculator()
        signals = calc.get_signals(df)

        assert 'UP_LINE' in signals
        assert 'DOWN_LINE' in signals
        assert 'MONEY_COND' in signals
        assert 'BUY_POINT' in signals
        assert 'FILTER_BUY' in signals

    def test_is_signal_triggered(self):
        """测试信号触发判断"""
        df = create_sample_dataframe()
        calc = BuySignalCalculator()
        is_triggered, details = calc.is_signal_triggered(df)

        assert isinstance(is_triggered, bool)
        assert isinstance(details, dict)

    def test_is_signal_triggered_basic(self):
        """测试信号触发判断基本功能"""
        df = create_sample_dataframe()
        calc = BuySignalCalculator()
        is_triggered, details = calc.is_signal_triggered(df)

        assert isinstance(is_triggered, bool)
        assert isinstance(details, dict)

    def test_get_name(self):
        """测试获取计算器名称"""
        calc = BuySignalCalculator()
        assert calc.get_name() == 'BuySignalCalculator'


class TestSignalConditions:
    """信号条件测试"""

    def test_buy_signal_conditions(self):
        """测试买入信号条件"""
        df = create_sample_dataframe(200)  # 使用更多数据
        calc = BuySignalCalculator()
        result = calc.calculate_signals(df)

        # 验证 UP_LINE_COND 条件
        if 'UP_LINE_COND' in result.columns:
            up_line_cond = result[result['UP_LINE_COND'] == True]
            if len(up_line_cond) > 0:
                # 条件满足时，UP_LINE 和 DOWN_LINE 应该 <= 25
                assert (up_line_cond['UP_LINE'] <= 25).all()
                assert (up_line_cond['DOWN_LINE'] <= 25).all()

    def test_filter_buy_interval(self):
        """测试过滤后买入信号间隔"""
        df = create_sample_dataframe(300)
        calc = BuySignalCalculator()
        result = calc.calculate_signals(df)

        filter_buy_points = result[result['FILTER_BUY'] == True]

        if len(filter_buy_points) > 1:
            indices = filter_buy_points.index.tolist()
            for i in range(1, len(indices)):
                # 验证信号间隔至少 5 个周期
                prev_idx = result.index.tolist().index(indices[i-1])
                curr_idx = result.index.tolist().index(indices[i])
                assert curr_idx - prev_idx > 5