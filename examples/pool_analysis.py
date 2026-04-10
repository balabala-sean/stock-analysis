"""
示例：股池批量分析（含可视化）

在项目根目录运行：
    python -m examples.pool_analysis
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from src.data_kline import DataFetcher
from src.strategy import BuySignalCalculator
from src.visualization import Plotter
from src.notify import EmailNotifier
from src.conf import get_stock_pool


def analyze_single_stock(fetcher: DataFetcher, symbol: str, name: str, frequency: int = 4, offset: int = 300, notify: bool = False):
    """
    单只股票完整分析（内部使用）

    Args:
        fetcher: DataFetcher 实例（由外层传入，避免频繁创建连接）
        symbol: 股票代码
        name: 股票名称
        frequency: K 线周期
        offset: 数据条数
        notify: 是否启用邮件通知

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
    print(f"\n最新状态:")
    print(f"  UP_LINE: {last_row['UP_LINE']:.2f}")
    print(f"  DOWN_LINE: {last_row['DOWN_LINE']:.2f}")
    print(f"  MONEY_COND: {last_row['MONEY_COND']}")
    print(f"  BUY_POINT: {last_row['BUY_POINT']}")
    print(f"  FILTER_BUY: {last_row['FILTER_BUY']}")

    # 4. 打印信号汇总
    plotter = Plotter()
    plotter.print_signal_summary(df, symbol, name)

    # 5. 绘制图表
    save_dir = os.path.join(PROJECT_ROOT, "output/charts")
    print(f"正在生成图表，保存至：{save_dir}")
    plotter.plot_buy_signals(
        df=df,
        stock_code=symbol,
        stock_name=name,
        save_dir=save_dir,
        show=False
    )

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

    print("完成！\n")
    return result


def analyze_pool(notify: bool = False):
    """
    股池批量分析

    Args:
        notify: 是否启用邮件通知

    Returns:
        list: 所有股票的分析结果
    """
    stock_pool = get_stock_pool()

    if not stock_pool:
        print("错误：股池为空，请先在 config.json 中配置 stock_pool")
        return []

    print(f"\n{'#'*60}")
    print(f"股池批量分析，共 {len(stock_pool)} 只股票")
    print(f"{'#'*60}\n")

    results = []
    buy_signals = []

    # 创建 DataFetcher 连接
    fetcher = DataFetcher()

    try:
        for i, stock in enumerate(stock_pool, 1):
            symbol = stock.get('symbol')
            name = stock.get('name')
            frequency = stock.get('frequency', 4)
            offset = stock.get('offset', 300)

            if not symbol or not name:
                print(f"警告：第 {i} 只股票配置不完整，跳过")
                continue

            print(f"[{i}/{len(stock_pool)}] 分析 {symbol} - {name}")
            result = analyze_single_stock(fetcher, symbol, name, frequency, offset, notify)
            results.append(result)

            if result['buy_signal']:
                buy_signals.append(result)
    finally:
        # 显式关闭连接
        fetcher.close()

    # 汇总报告
    print(f"\n{'#'*60}")
    print("股池分析汇总")
    print(f"{'#'*60}")
    print(f"分析总数：{len(results)}")
    print(f"触发买点：{len(buy_signals)}")

    if buy_signals:
        print("\n触发买点的股票：")
        for r in buy_signals:
            print(f"  - {r['symbol']} {r['name']}")

    print(f"\n{'#'*60}\n")

    return results


if __name__ == '__main__':
    # 从 config.json 读取股票列表进行批量分析
    # notify=True 启用邮件通知（需先配置 config.json）
    analyze_pool(notify=False)