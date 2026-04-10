# -*- coding: utf-8 -*-
"""
通达信数据拉取模块
支持实时行情、K 线数据获取
"""

import time
from datetime import datetime, date
from typing import Optional, Union
from pandas import DataFrame

from mootdx.quotes import Quotes


class DataFetcher:
    """通达信数据获取器"""

    def __init__(self, market: str = 'std'):
        """
        初始化数据获取器

        Args:
            market: 市场类型，'std'=标准市场 (股票/指数), 'ext'=扩展市场 (期货等)
        """
        self.market = market
        self.client = Quotes.factory(market=market, multithread=True, heartbeat=True, ipbest=True)

    def get_bars(
        self,
        symbol: str,
        frequency: int = 4,
        offset: int = 100
    ) -> DataFrame:
        """
        获取 K 线数据

        Args:
            symbol: 股票代码 (如 '600036')，无需添加 sh/sz 前缀
            frequency: K 线周期
                      0=1 分钟，1=5 分钟，2=15 分钟，3=60 分钟
                      4=日线，5=周线，6=月线，7=季线，8=年线
            offset: 获取数据条数

        Returns:
            DataFrame 包含 OHLCV 数据
        """
        data = self.client.bars(symbol=symbol, frequency=frequency, offset=offset)
        time.sleep(0.5)  # 速率限制：避免请求过快被通达信服务器断开连接

        return data

    def get_bars_by_date_range(
        self,
        symbol: str,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        frequency: int = 4,
        adjust: Optional[str] = None
    ) -> DataFrame:
        """
        按日期范围获取 K 线数据

        由于 mootdx 不支持直接按日期范围查询，此方法通过以下方式实现：
        1. 获取足够数量的历史数据（最大 800 条）
        2. 用 pandas 按日期范围过滤

        Args:
            symbol: 股票代码 (如 '600036')，无需添加 sh/sz 前缀
            start_date: 开始日期，支持格式：'YYYY-MM-DD'、datetime、date 对象
            end_date: 结束日期，支持格式：'YYYY-MM-DD'、datetime、date 对象
            frequency: K 线周期 (默认日线=4)
            adjust: 复权方式，None=不复权，'qfq'=前复权，'hfq'=后复权

        Returns:
            DataFrame 包含指定日期范围内的 OHLCV 数据

        Raises:
            ValueError: 如果日期范围超过 800 条数据（mootdx API 限制）
        """
        # 统一转换为 date 对象
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()

        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        elif isinstance(end_date, datetime):
            end_date = end_date.date()

        # 估算需要的数据条数（考虑不同周期）
        days_diff = (end_date - start_date).days
        if days_diff < 0:
            raise ValueError(f"开始日期 {start_date} 不能晚于结束日期 {end_date}")

        # 根据周期估算需要的条数
        # 日线：1条/天，周线：1条/周，月线：1条/月
        estimated_offset = self._estimate_bars_count(days_diff, frequency)
        max_offset = 800  # mootdx API 最大限制

        if estimated_offset > max_offset:
            raise ValueError(
                f"日期范围过大：{start_date} 至 {end_date}，"
                f"预计需要 {estimated_offset} 条数据，"
                f"但 mootdx API 最多支持 {max_offset} 条。"
                f"建议缩小日期范围或使用周线/月线周期。"
            )

        # 获取数据
        data = self.client.bars(
            symbol=symbol,
            frequency=frequency,
            offset=max_offset,
            adjust=adjust
        )
        time.sleep(0.5)  # 速率限制

        if data is None or data.empty:
            return DataFrame()

        # 按日期范围过滤
        # mootdx 返回的 DataFrame 的索引是 datetime 类型
        data = data.sort_index()  # 升序排列
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())

        filtered = data[(data.index >= start_dt) & (data.index <= end_dt)]

        return filtered

    def _estimate_bars_count(self, days: int, frequency: int) -> int:
        """
        根据天数和 K 线周期估算需要的数据条数

        Args:
            days: 天数差
            frequency: K 线周期

        Returns:
            预估的数据条数
        """
        # 考虑周末和节假日，实际交易日约为天数的 70%
        trading_days = int(days * 0.7) + 10  # 加 10 条余量

        if frequency == 4:  # 日线
            return trading_days
        elif frequency == 5:  # 周线
            return trading_days // 5 + 5
        elif frequency == 6:  # 月线
            return trading_days // 20 + 3
        elif frequency <= 3:  # 分钟线
            # 分钟线数据量更大，更容易超出限制
            # 日内分钟数：1分钟=240条/天，5分钟=48条/天，15分钟=16条/天，60分钟=4条/天
            minute_factors = {0: 240, 1: 48, 2: 16, 3: 4}
            return trading_days * minute_factors.get(frequency, 240)
        else:
            return trading_days

    def get_index_bars(
        self,
        symbol: str,
        frequency: int = 4,
        offset: int = 100
    ) -> DataFrame:
        """
        获取指数 K 线数据

        Args:
            symbol: 指数代码 (如 '000688' 科创 50)
            frequency: K 线周期 (默认日线)
            offset: 获取数据条数

        Returns:
            DataFrame 包含指数 OHLCV 数据
        """
        return self.get_bars(symbol, frequency=frequency, offset=offset)

    def get_realtime_quote(self, symbol: str) -> Optional[dict]:
        """
        获取实时行情

        Args:
            symbol: 股票代码

        Returns:
            字典包含实时价格信息
        """
        if not symbol.startswith(('sh', 'sz')):
            symbol = self._add_market_prefix(symbol)

        data = self.client.quote(symbol=symbol)
        time.sleep(0.5)  # 速率限制：避免请求过快被通达信服务器断开连接

        if data is not None and not data.empty:
            row = data.iloc[0]
            return {
                'symbol': symbol,
                'price': float(row.get('price', 0)),
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'prev_close': float(row.get('lastclose', 0)),
                'volume': float(row.get('volume', 0)),
                'amount': float(row.get('amount', 0)),
            }
        return None

    def _add_market_prefix(self, symbol: str) -> str:
        """根据代码规则添加市场前缀"""
        if symbol.startswith('6'):
            return f'sh{symbol}'
        elif symbol.startswith('0'):
            return f'sz{symbol}'
        elif symbol.startswith('3'):
            return f'sz{symbol}'
        elif symbol.startswith('9'):
            return f'sh{symbol}'
        else:
            # 默认深交所
            return f'sz{symbol}'

    def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
