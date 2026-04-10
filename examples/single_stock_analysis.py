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
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from src.data_kline import DataFetcher
from src.strategy import BuySignalCalculator
from src.visualization import Plotter
from src.notify import EmailNotifier
from src.conf import get_stock_pool, is_email_enabled, is_generate_chart_enabled


def analyze_single_stock(symbol: str, name: str, frequency: int = 4, offset: int = 300, notify: bool = None, generate_chart: bool = None):
    """
    单只股票完整分析

    Args:
        symbol: 股票代码
        name: 股票名称
        frequency: K 线周期 (默认日线)
        offset: 数据条数 (默认 300 条)
        notify: 是否启用邮件通知（None 时从 config.json 读取）
        generate_chart: 是否生成图表（None 时从 config.json 读取）

    Returns:
        dict: 分析结果
    """
    # 从配置文件读取默认值
    if notify is None:
        notify = is_email_enabled()
    if generate_chart is None:
        generate_chart = is_generate_chart_enabled()

    print(f"\n{'='*60}")
    print(f"策略分析：{symbol} - {name} (周期={frequency}, 数据量={offset})")
    print(f"邮件通知：{'已启用' if notify else '已禁用'}")
    print(f"生成图表：{'已启用' if generate_chart else '已禁用'}")
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
    if generate_chart:
        save_dir = os.path.join(PROJECT_ROOT, "output/charts")
        save_path = plotter.plot_buy_signals(
            df=df,
            stock_code=symbol,
            stock_name=name,
            save_dir=save_dir,
            frequency=frequency,
            offset=offset
        )
        if save_path:
            print(f"图表已保存至：{save_path}")
    else:
        print("图表生成已禁用（config.json: chart.enabled=false）")

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


def get_default_stock_from_config():
    """从 config.json 获取股票池第一个元素（含完整配置）"""
    stock_pool = get_stock_pool()
    if stock_pool and len(stock_pool) > 0:
        stock = stock_pool[0]
        return (
            stock.get('symbol'),
            stock.get('name'),
            stock.get('frequency', 4),
            stock.get('offset', 300)
        )
    return None, None, 4, 300


if __name__ == '__main__':
    # 从 config.json 读取股票池第一个元素的完整配置
    symbol, name, frequency, offset = get_default_stock_from_config()

    if symbol is None or name is None:
        print("配置有误，请检查config.json的stock_pool数组是否包含元素，详情可查看文档：docs/CONFIG.md")
        exit(-1)

    analyze_single_stock(
        symbol=symbol,
        name=name,
        frequency=frequency,
        offset=offset
    )