"""
示例：单只股票均值回归策略分析（含可视化）

在项目根目录运行：
    python -m examples.single_stock_analysis                    # 从 config.json 读取股票池第一个元素
    python -m examples.single_stock_analysis --symbol 600621    # 自定义股票代码
    python -m examples.single_stock_analysis --symbol 600621 --name 华鑫股份 --frequency 4 --offset 300 --notify
"""

import sys
import os
import argparse
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")

from src.data_kline import DataFetcher
from src.strategy import BuySignalCalculator
from src.visualization import Plotter
from src.notify import EmailNotifier


def analyze_single_stock(symbol: str, name: str, frequency: int = 4, offset: int = 300, notify: bool = False, show_chart: bool = True):
    """
    单只股票完整分析

    Args:
        symbol: 股票代码
        name: 股票名称
        frequency: K 线周期 (默认日线)
        offset: 数据条数 (默认 300 条)
        notify: 是否启用邮件通知
        show_chart: 是否生成图表

    Returns:
        dict: 分析结果
    """
    print(f"\n{'='*60}")
    print(f"策略分析：{symbol} - {name} (周期={frequency}, 数据量={offset})")
    print(f"{'='*60}\n")

    result = {
        'symbol': symbol,
        'name': name,
        'buy_signal': False,
        'filter_buy_count': 0,
        'error': None
    }

    # 1. 获取数据
    print("正在获取数据...")
    with DataFetcher() as fetcher:
        df = fetcher.get_bars(symbol, frequency=frequency, offset=offset)

    if df is None or df.empty:
        print("获取数据失败！")
        result['error'] = "获取数据失败"
        return result

    print(f"获取到 {len(df)} 条数据\n")

    # 2. 计算信号
    print("正在计算信号...")
    calculator = BuySignalCalculator()
    df = calculator.calculate_signals(df)

    # 3. 打印最新状态
    last_row = df.iloc[-1]

    # 4. 打印信号汇总
    plotter = Plotter()
    plotter.print_signal_summary(df, symbol, name)

    # 5. 绘制图表
    if show_chart:
        save_dir = os.path.join(PROJECT_ROOT, "output/charts")
        print(f"正在生成图表，保存至：{save_dir}")
        plotter.plot_buy_signals(
            df=df,
            stock_code=symbol,
            stock_name=name,
            save_dir=save_dir,
            show=False
        )
    else:
        print("跳过图表生成")

    # 记录结果
    result['buy_signal'] = bool(last_row['FILTER_BUY'])
    result['filter_buy_count'] = int((df['FILTER_BUY'] == True).sum())

    # 6. 邮件通知（仅当最新买点触发时）
    if notify and last_row['FILTER_BUY']:
        print("\n正在发送邮件通知...")
        notifier = EmailNotifier()
        notifier.send_buy_signal(
            symbol=symbol,
            name=name,
            signal_info={
                'date': df.index[-1],
                'close': last_row['close'],
                'UP_LINE': last_row['UP_LINE'],
                'DOWN_LINE': last_row['DOWN_LINE'],
            },
            buy_points_count=result['filter_buy_count']
        )



    print(f"\n最新状态，时间{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} :")
    print(f"  开盘价: {last_row['open']:.2f}")
    print(f"  最低价: {last_row['low']:.2f}")
    print(f"  最高价: {last_row['high']:.2f}")
    print(f"  当前最新价（收盘价）: {last_row['close']:.2f}")
    print(f"  策略计算（UP_LINE）: {last_row['UP_LINE']:.2f}")
    print(f"  策略计算（DOWN_LINE）: {last_row['DOWN_LINE']:.2f}")
    print(f"  策略计算（MONEY_COND）: {last_row['MONEY_COND']}")
    print(f"  策略计算（BUY_POINT）: {last_row['BUY_POINT']}")

    print(f"  🚀 实时计算结果（FILTER_BUY）-买入信号: {last_row['FILTER_BUY']}")
    print("计算完成！\n")
    return result


def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def get_default_stock_from_config():
    """从 config.json 获取股票池第一个元素"""
    config = load_config()
    if config and 'stock_pool' in config and len(config['stock_pool']) > 0:
        stock = config['stock_pool'][0]
        return stock.get('symbol'), stock.get('name')
    return None, None


if __name__ == '__main__':
    # 默认只读取第一个stock_pool的元素进行分析
    symbol, name = get_default_stock_from_config()

    if symbol is None or name is None:
        print("配置有误，请检查config.json的stock_pool数组是否包含元素，详情可查看文档：docs/CONFIG.md")
        exit(-1)

    analyze_single_stock(
        symbol=symbol,
        name=name,
        show_chart=True
    )