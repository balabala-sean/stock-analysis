# -*- coding: utf-8 -*-
"""
K 线图可视化模块
使用 mplfinance 绘制带信号标记的 K 线图
"""

import os
import platform
from datetime import datetime
from typing import List, Optional

import pandas as pd
import numpy as np
import mplfinance as mpf
from pandas import DataFrame


# K 线周期映射表
FREQUENCY_MAP = {
    0: '1分钟',
    1: '5分钟',
    2: '15分钟',
    3: '60分钟',
    4: '日线',
    5: '周线',
    6: '月线'
}


def get_frequency_name(frequency: int) -> str:
    """
    将 frequency 数值转换为周期名称

    Args:
        frequency: K线周期代码 (0-6)

    Returns:
        str: 周期名称，如 '日线'、'60分钟' 等
    """
    return FREQUENCY_MAP.get(frequency, f'周期{frequency}')


def _get_chinese_font() -> str:
    """根据操作系统返回合适的中文字体"""
    system = platform.system()
    if system == 'Darwin':  # macOS
        return 'Heiti TC'
    elif system == 'Windows':
        return 'SimHei'
    else:  # Linux 或其他
        return 'WenQuanYi Micro Hei'


class Plotter:
    """K 线图绘制器"""

    def __init__(self, style: str = 'china'):
        """
        初始化绘制器

        Args:
            style: 图表样式，'china'=中国红绿样式，'default'=默认样式
        """
        self.style = self._get_market_style(style)

    def plot_with_signals(
        self,
        df: DataFrame,
        title: str = '',
        save_path: Optional[str] = None,
        show: bool = True,
        figsize: tuple = (20, 12),
        buy_markers: Optional[DataFrame] = None,
        frequency: int = 4,
        offset: int = 300,
    ):
        """
        绘制带信号标记的 K 线图

        Args:
            df: 包含 OHLCV 数据的 DataFrame，索引为 datetime
            title: 图表标题
            save_path: 保存路径，如 None 则不保存
            show: 是否显示图表
            figsize: 图表大小
            buy_markers: 买入信号标记数据（需包含 'low' 列）
            frequency: K线周期代码，用于显示周期名称
            offset: K线数量
        """
        addplots = []

        # 添加买入信号标记（绿色五角星）
        if buy_markers is not None and len(buy_markers) > 0:
            buy_values = pd.Series(np.nan, index=df.index)
            for idx in buy_markers.index:
                if idx in buy_values.index:
                    buy_values.loc[idx] = buy_markers.loc[idx, 'low'] * 0.98

            if buy_values.notna().any():
                ap_buy = mpf.make_addplot(
                    buy_values,
                    type='scatter',
                    marker='*',
                    markersize=150,
                    color='darkgreen',
                    label='Buy',
                    panel=0  # 主K线图区域
                )
                addplots.append(ap_buy)

        # 添加指标到独立区域（panel=2），所有指标共享Y轴
        # 先添加 UP_LINE/DOWN_LINE（值范围0-100），确保Y轴范围正确
        if 'UP_LINE' in df.columns:
            # UP_LINE - 红色实线
            ap_up = mpf.make_addplot(
                df['UP_LINE'],
                type='line',
                color='darkred',
                width=1.5,
                label='UP_LINE',
                panel=2,
                ylabel='指标'
            )
            addplots.append(ap_up)

        if 'DOWN_LINE' in df.columns:
            # DOWN_LINE - 蓝色实线
            ap_down = mpf.make_addplot(
                df['DOWN_LINE'],
                type='line',
                color='darkblue',
                width=1.5,
                label='DOWN_LINE',
                panel=2
            )
            addplots.append(ap_down)

        # 处理 MONEY_COMING 和 MONEY_LIVING：大于5的值显示为10，值为0时不显示
        if 'MONEY_COMING' in df.columns:
            money_coming = df['MONEY_COMING'].copy()
            money_coming = money_coming.apply(lambda x: 10 if x > 5 else x if pd.notna(x) and x > 0 else np.nan)
            # MONEY_COMING - 红色柱状图
            ap_coming = mpf.make_addplot(
                money_coming,
                type='bar',
                color='red',
                width=0.8,
                label='MONEY_COMING',
                panel=2
            )
            addplots.append(ap_coming)

        if 'MONEY_LIVING' in df.columns:
            money_living = df['MONEY_LIVING'].copy()
            money_living = money_living.apply(lambda x: 10 if x > 5 else x if pd.notna(x) and x > 0 else np.nan)
            # MONEY_LIVING - 绿色柱状图
            ap_living = mpf.make_addplot(
                money_living,
                type='bar',
                color='green',
                width=0.8,
                label='MONEY_LIVING',
                panel=2
            )
            addplots.append(ap_living)

        # 绘制图表
        kwargs = {
            'type': 'candle',
            'style': self.style,
            'title': title,
            'ylabel': '价格',
            'volume': True,
            'ylabel_lower': '成交量',
            'figscale': 1.5,
            'figsize': figsize,
            'datetime_format': '%Y-%m-%d',
            'xrotation': 45,
            'panel_ratios': (4, 1, 1.5)  # K线:成交量:指标区 = 4:1:1.5
        }

        # 只有存在附加图表时才传递 addplot 参数
        if addplots:
            kwargs['addplot'] = addplots

        if save_path:
            kwargs['savefig'] = dict(fname=save_path, dpi=300)

        mpf.plot(df, **kwargs)

    def plot_buy_signals(
        self,
        df: DataFrame,
        stock_code: str = '',
        stock_name: str = '',
        save_dir: Optional[str] = None,
        frequency: int = 4,
        offset: int = 300,
    ):
        """
        绘制策略信号图

        Args:
            df: 已计算策略指标的 DataFrame
            stock_code: 股票代码
            stock_name: 股票名称
            save_dir: 保存目录，如 None 则不保存
            frequency: K线周期代码 (0-6)
            offset: K线数量
        """
        # 创建买入信号标记
        buy_markers = df[df['FILTER_BUY'] == True] if 'FILTER_BUY' in df.columns else None

        # 构建标题，包含周期和K线数量信息
        freq_name = get_frequency_name(frequency)
        kline_count = len(df)
        title = f'{stock_code} - {stock_name} [{freq_name} K线:{kline_count}条]' if stock_code else f'信号分析 [{freq_name} K线:{kline_count}条]'

        save_path = None
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = os.path.join(save_dir, f"{stock_code}_{timestamp}_signal.png")

        self.plot_with_signals(
            df=df,
            title=title,
            save_path=save_path,
            buy_markers=buy_markers,
            frequency=frequency,
            offset=offset
        )

        return save_path

    def print_signal_summary(self, df: DataFrame, stock_code: str = '', stock_name: str = ''):
        """
        打印信号汇总信息

        Args:
            df: 已计算信号的 DataFrame
            stock_code: 股票代码
            stock_name: 股票名称
        """
        print(f"\n{'='*60}")
        print(f"股票：{stock_code} - {stock_name}")
        print(f"数据范围：{df.index[0]} 至 {df.index[-1]}")
        print(f"总记录数：{len(df)}")
        print(f"{'='*60}")

        # 统计各类信号数量
        buy_point_cnt = (df['BUY_POINT'] == True).sum() if 'BUY_POINT' in df.columns else 0
        filter_buy_cnt = (df['FILTER_BUY'] == True).sum() if 'FILTER_BUY' in df.columns else 0
        money_cond_cnt = (df['MONEY_COND'] == True).sum() if 'MONEY_COND' in df.columns else 0

        print(f"\n信号统计:")
        print(f"  MONEY_COND 触发次数：{money_cond_cnt}")
        print(f"  BUY_POINT 触发次数：{buy_point_cnt}")
        print(f"  FILTER_BUY 触发次数：{filter_buy_cnt}")

        # 列出具体信号点
        print(f"\n详细信号点:")

        if buy_point_cnt > 0:
            buy_points = df[df['BUY_POINT'] == True]
            print(f"\n【买入点位】共 {len(buy_points)} 个:")
            for idx, row in buy_points.iterrows():
                print(f"  {idx}: close={row['close']}, UP_LINE={row['UP_LINE']:.2f}, DOWN_LINE={row['DOWN_LINE']:.2f}")

        if filter_buy_cnt > 0:
            filter_buy_points = df[df['FILTER_BUY'] == True]
            print(f"\n【过滤后买入】共 {len(filter_buy_points)} 个:")
            for idx, row in filter_buy_points.iterrows():
                print(f"  {idx}: close={row['close']}, UP_LINE={row['UP_LINE']:.2f}, DOWN_LINE={row['DOWN_LINE']:.2f}")

        print(f"\n{'='*60}\n")

    def _get_market_style(self, style: str):
        """获取市场样式"""
        if style == 'china':
            mc = mpf.make_marketcolors(
                up='red',
                down='green',
                edge='inherit',
                wick='inherit',
                volume='inherit'
            )
            return mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='--',
                gridcolor='lightgray',
                rc={'font.family': _get_chinese_font()}
            )
        else:
            return mpf.make_mpf_style()
