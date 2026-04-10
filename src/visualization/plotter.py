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
                    label='Buy'
                )
                addplots.append(ap_buy)

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
            'xrotation': 45
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
        show: bool = True
    ):
        """
        绘制策略信号图

        Args:
            df: 已计算策略指标的 DataFrame
            stock_code: 股票代码
            stock_name: 股票名称
            save_dir: 保存目录，如 None 则不保存
            show: 是否显示图表
        """
        # 创建买入信号标记
        buy_markers = df[df['FILTER_BUY'] == True] if 'FILTER_BUY' in df.columns else None

        title = f'{stock_code} - {stock_name} DFB 信号分析' if stock_code else 'DFB 信号分析'

        save_path = None
        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = os.path.join(save_dir, f"{stock_code}_{timestamp}_signal.png")

        self.plot_with_signals(
            df=df,
            title=title,
            save_path=save_path,
            buy_markers=buy_markers
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
