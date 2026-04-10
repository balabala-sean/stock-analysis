# -*- coding: utf-8 -*-
"""
数据拉取包单元测试
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_kline import DataFetcher


class TestDataFetcher:
    """DataFetcher 测试类"""

    def test_init(self):
        """测试初始化"""
        fetcher = DataFetcher()
        assert fetcher.market == 'std'
        assert fetcher.client is not None

    def test_init_with_market(self):
        """测试自定义市场参数初始化"""
        fetcher = DataFetcher(market='ext')
        assert fetcher.market == 'ext'

    def test_get_bars_basic(self):
        """测试获取 K 线数据"""
        fetcher = DataFetcher()
        df = fetcher.get_bars('600036', frequency=5, offset=10)

        assert df is not None
        assert not df.empty
        assert len(df) == 10
        assert 'open' in df.columns
        assert 'close' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'vol' in df.columns
        fetcher.close()

    def test_get_bars_different_frequency(self):
        """测试不同周期的 K 线数据"""
        fetcher = DataFetcher()

        # 测试日线
        df_daily = fetcher.get_bars('600036', frequency=5, offset=5)
        assert len(df_daily) == 5

        # 测试周线
        df_weekly = fetcher.get_bars('600036', frequency=6, offset=5)
        assert len(df_weekly) == 5

        fetcher.close()

    def test_get_bars_different_stocks(self):
        """测试不同股票的数据获取"""
        fetcher = DataFetcher()

        # 测试上交所股票
        df_sh = fetcher.get_bars('600519', frequency=5, offset=5)
        assert len(df_sh) == 5

        # 测试深交所股票
        df_sz = fetcher.get_bars('000001', frequency=5, offset=5)
        assert len(df_sz) == 5

        fetcher.close()

    def test_get_index_bars(self):
        """测试获取指数 K 线数据"""
        fetcher = DataFetcher()

        # 测试科创 50 指数
        df = fetcher.get_index_bars('000688', frequency=5, offset=5)
        assert len(df) == 5

        fetcher.close()

    def test_context_manager(self):
        """测试上下文管理器"""
        with DataFetcher() as fetcher:
            assert fetcher is not None
            df = fetcher.get_bars('600036', frequency=5, offset=5)
            assert len(df) == 5
        # 退出上下文后连接应该关闭

    def test_sleep_between_requests(self):
        """测试请求间延迟（确保不被限流）"""
        import time

        fetcher = DataFetcher()

        # 记录第一次请求时间
        start = time.time()
        fetcher.get_bars('600036', frequency=5, offset=5)
        elapsed = time.time() - start

        # 确保有 0.5 秒的延迟
        assert elapsed >= 0.5

        fetcher.close()


class TestAddMarketPrefix:
    """测试市场前缀添加功能"""

    def test_sh_prefix_for_6(self):
        """测试 6 开头的股票添加 sh 前缀"""
        fetcher = DataFetcher()
        result = fetcher._add_market_prefix('600036')
        assert result == 'sh600036'
        fetcher.close()

    def test_sz_prefix_for_0(self):
        """测试 0 开头的股票添加 sz 前缀"""
        fetcher = DataFetcher()
        result = fetcher._add_market_prefix('000001')
        assert result == 'sz000001'
        fetcher.close()

    def test_sz_prefix_for_3(self):
        """测试 3 开头的股票添加 sz 前缀"""
        fetcher = DataFetcher()
        result = fetcher._add_market_prefix('300750')
        assert result == 'sz300750'
        fetcher.close()

    def test_sh_prefix_for_9(self):
        """测试 9 开头的股票添加 sh 前缀"""
        fetcher = DataFetcher()
        result = fetcher._add_market_prefix('900000')
        assert result == 'sh900000'
        fetcher.close()

    def test_default_sz_prefix(self):
        """测试其他情况默认添加 sz 前缀"""
        fetcher = DataFetcher()
        result = fetcher._add_market_prefix('123456')
        assert result == 'sz123456'
        fetcher.close()
