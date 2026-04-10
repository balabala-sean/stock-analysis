"""
主程序 - 均值回归策略运行入口

从 config.json 读取股池配置，批量分析并发送邮件通知
支持后台持续运行
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_kline import DataFetcher
from strategy import BuySignalCalculator
from visualization import Plotter
from notify import EmailNotifier
from conf import (
    get_stock_pool,
    is_email_enabled,
    is_generate_chart_enabled,
    get_interval_seconds
)


def run_single(fetcher: DataFetcher, symbol: str, name: str, frequency: int = 4, offset: int = 300,
               notify: bool = False, generate_chart: bool = True):
    """
    运行单只股票策略分析

    Args:
        fetcher: DataFetcher 实例（由外层传入，避免频繁创建连接）
        symbol: 股票代码
        name: 股票名称
        frequency: K 线周期 (默认日线)
        offset: 数据条数 (默认 300 条)
        notify: 是否启用邮件通知
        generate_chart: 是否生成图表

    Returns:
        dict: 包含分析结果
    """
    print(f"\n{'='*60}")
    print(f"策略分析：{symbol} - {name} (周期={frequency}, 数据量={offset})")
    print(f"{'='*60}\n")

    result = {
        'symbol': symbol,
        'name': name,
        'buy_signal': False,
        'watch_signal': False,
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

    # 4. 打印信号汇总
    plotter = Plotter()
    plotter.print_signal_summary(df, symbol, name)

    # 5. 绘制图表（根据配置决定是否生成）
    if generate_chart:
        save_dir = "output/charts"
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
    result['watch_signal'] = (last_row['UP_LINE'] < 15 and last_row['DOWN_LINE'] < 15)
    result['filter_buy_count'] = int((df['FILTER_BUY'] == True).sum())
    result['last_row'] = last_row
    result['df'] = df

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

    print(f" {name}({symbol}) 计算完成！\n")
    return result


def run_pool(fetcher: DataFetcher):
    """
    运行股池批量分析

    Args:
        fetcher: DataFetcher 实例（由 main 传入，整个程序生命周期内复用）

    从 config.json 读取股池配置和邮件开关，遍历分析每只股票
    """
    # 重新加载配置（支持热更新）
    from conf import Config
    Config.reload()

    stock_pool = get_stock_pool()

    if not stock_pool:
        print("错误：股池为空，请先在 config.json 中配置 stock_pool")
        return []

    # 读取配置
    email_enabled = is_email_enabled()
    generate_chart = is_generate_chart_enabled()
    notify = email_enabled

    print(f"\n{'#'*60}")
    print(f"股池批量分析")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"股票数量：{len(stock_pool)}")
    print(f"邮件通知：{'已启用' if email_enabled else '已禁用'}")
    print(f"生成图表：{'已启用' if generate_chart else '已禁用'}")
    print(f"{'#'*60}\n")

    results = []
    buy_signals = []
    watch_signals = []

    for i, stock in enumerate(stock_pool, 1):
        symbol = stock.get('symbol')
        name = stock.get('name')
        frequency = stock.get('frequency', 4)
        offset = stock.get('offset', 300)

        if not symbol or not name:
            print(f"警告：第 {i} 只股票配置不完整，跳过")
            continue

        print(f"[{i}/{len(stock_pool)}] 分析 {symbol} - {name}")
        result = run_single(fetcher, symbol, name, frequency, offset, notify, generate_chart)
        results.append(result)

        if result['buy_signal']:
            buy_signals.append(result)
        if result['watch_signal']:
            watch_signals.append(result)

    # 汇总报告
    print(f"\n{'#'*60}")
    print("股池分析汇总")
    print(f"{'#'*60}")
    print(f"分析总数：{len(results)}")
    print(f"触发买点：{len(buy_signals)}")
    print(f"关注信号（UP_LINE和DOWN_LINE均<15）：{len(watch_signals)}")

    if buy_signals:
        print("\n1.🚀 买点扫描-结果：触发买点的股票如下")
        for r in buy_signals:
            print(f"  - {r['symbol']} {r['name']}")
    else:
        print("\n1.🚀 买点扫描-结果：目前没有触发买点的股票")

    if watch_signals:
        print("\n2.🚀 低位扫描-需要关注的股票如下")
        for r in watch_signals:
            print(f"  - {r['symbol']} {r['name']}")
    else:
        print("\n2.🚀 低位扫描-需要关注的股票：目前没有运行至低位需要关注的股票")

    print(f"\n{'#'*60}\n")

    return results


def main():
    """
    主程序入口 - 从 config.json 读取配置并运行

    程序启动时创建 DataFetcher 连接，程序退出时显式关闭
    """
    run_interval = get_interval_seconds()

    # 程序启动时创建连接
    fetcher = DataFetcher()

    try:
        if run_interval <= 0:
            # 单次运行模式
            print("运行模式：单次执行")
            run_pool(fetcher)
        else:
            # 后台持续运行模式
            print(f"运行模式：后台持续运行，间隔 {run_interval} 秒")
            print("按 Ctrl+C 停止运行\n")

            round_num = 1
            while True:
                try:
                    print(f"\n{'*'*60}")
                    print(f"第 {round_num} 轮分析开始")
                    print(f"{'*'*60}")
                    run_pool(fetcher)

                    # 等待下一轮
                    print(f"等待 {run_interval} 秒后进行下一轮分析...")
                    print("按 Ctrl+C 停止运行\n")
                    time.sleep(run_interval)

                    round_num += 1

                except KeyboardInterrupt:
                    print("\n\n收到停止信号，程序退出")
                    break
                except Exception as e:
                    print(f"\n运行出错：{e}")
                    print(f"等待 {run_interval} 秒后重试...\n")
                    time.sleep(run_interval)
    finally:
        # 程序退出时显式关闭连接
        print("正在关闭数据连接...")
        fetcher.close()
        print("数据连接已关闭")


if __name__ == '__main__':
    main()