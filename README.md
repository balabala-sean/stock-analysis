# Stock Analysis

量化交易的分析和预警工具，采用了均值回归策略，用于识别股票买入时机，支持股池批量分析和邮件通知功能。

提供了以下的功能：

- 通达信(tdx)数据的实时/历史拉取（无需安装客户端）

- 买点策略 : 基于均值回归策略的实现（可以自行优化）

- 可视化 : 基于实时数据生成分析图表（含自定义的因子计算结果）

- 后台静默运行，实时email进行信号的触达

- 5分钟快速上手量化开发（高/中/低频，可以根据配置文件的k线的时间周期进行调整，未提供券商柜台的交易/仓位管理，可以自行开发）

---

## 概念解释

| 名称             | 说明                                                                                                                                                          |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **通达信 (数据源)**  | 国内最主流的股票交易行情软件。提供实时行情（A股/港股/期货）、历史K线、技术指标分析、交易下单功能。本项目通过其免费的数据接口来获取股票行情。(相较akshare、yfinance等，通达信在数据质量/网络传输上都更加稳定可靠，可以达到商用的程度，量化专业版也可以采用QMT/JoinQuant等付费解决方案 |
| **mootdx**     | 本项目核心依赖的Python 第三方库，封装通达信数据协议。支持获取实时行情、历史K线、指数数据，覆盖标准市场（股票）和扩展市场（期货）。                                                                                       |
| **K线 (OHLCV)** | 股票价格可视化表示，每根K线包含：Open（开盘价）、High（最高价）、Low（最低价）、Close（收盘价）、Volume（成交量）。周期可设为1分钟/5分钟/日线/周线等。                                                                   |
| **买点策略**       | 买点信号策略，通过两个维度判断买入时机：(1)价格的均值回归来计算顶底摆动区间，(2)慢速趋势指标增强判断价格的转折点，同时满足条件时产生买入信号。 均值回归是目前A股市场一种主流的买点策略（策略的实现方案上大同小异，只是策略内部使用的因子不同）                                 |
| **卖点策略**       | 本项目未提供卖点策略，卖点在量化交易领域存在非一致性的特征（业内难题），有较多的个性化因素。建议：入门的卖点策略可以尝试均值回归进行实现（例如归一化的值大于90，能达到实盘够用的程度，非最佳的卖点策略，存在优化空间）。                                               |
| **邮件通知**       | 当识别到最新买点时，自动发送邮件通知用户，方便及时跟踪买入信号。需配置 config.json 文件。                                                                                                         |
| **股池**         | 股票池配置，在 config.json 中定义待监控的股票列表，支持批量分析多只股票。                                                                                                                 |


---


## 安装依赖（macOS）

(如果没安装uv)，先安装uv:
```bash
brew install uv

#验证安装成功
uv --version
```

(如果已安装uv)，可跳过上一步，克隆项目后，进入到项目目录下
```bash
# 在项目目录下执行
uv sync

# 激活 venv 的 Python 环境
source .venv/bin/activate
```

---


## 配置文件

### 创建配置文件

首次使用前，需要从示例文件创建配置文件：(docs目录下提供了2套配置文件，一套是最小版，一套是完整版)

```bash
cp docs/config.json.minimal config.json
```
> **config.json的详细配置说明请参考：** [docs/CONFIG.md](docs/CONFIG.md)

---

## 使用方法

### 1. 使用示例脚本

#### 单只股票分析

```bash
uv run python -m examples.single_stock_analysis
```
运行后会看到输出：
```text
最新状态:
  开盘价: 30.01
  最低价: 29.70
  最高价: 30.02
  当前最新价（收盘价）: 29.70
  策略计算（UP_LINE）: 76.24
  策略计算（DOWN_LINE）: 75.38
  策略计算（MONEY_COND）: False
  策略计算（BUY_POINT）: False
  🚀 实时计算结果（FILTER_BUY）-买入信号: False
计算完成！
```
- ` 🚀 实时计算结果（FILTER_BUY）-买入信号: False`，代表当前时间的实时买点信号计算结果，**true则代表命中买点，false代表未命中（该策略信号在回测历史三年走势时，胜率在70%以上，且在2025年进行了实盘交通验证，如果要优化可以根据自己的因子进行扩展，如需进行实盘交易要关注股池的选择）**
- 在output/charts目录下会生成实时分析的图片，图片中标注了买点信号，是**绿色图标**的五角星（buy signal）
- 单只个股分析，如果config.json中的stock_pool是多个元素，会默认读取config.json的stock_pool第一个元素进行分析，如果要使用批量功能，请使用下文的**股池批量分析**

#### 股池批量分析

```bash
uv run python -m examples.pool_analysis
```

从 `config.json` 读取股池配置进行批量分析。

#### 信号输出类型（⚠️⚠️️重要⚠️⚠️️）

批量分析完成后，会输出两种类型的信号：

| 信号类型       | 说明 |
|------------|------|
| **买点信号**   | 当前触发买入信号，满足策略条件，建议重点关注 |
| **低位关注信号** | 价格处于低位区间，未来可能产生买点信号，建议提前关注 |

### 2. 命令行运行（后台持续计算）

```bash
# 运行股池分析（从 config.json 读取配置，推荐参考docs/config.json.full进行完整配置）
uv run python src/main.py
```

**后台运行示例：**

```bash
# 后台运行（每小时执行一次，需在 config.json 中设置 app_main.interval_seconds=3600）
nohup uv run python src/main.py > output/logs/analysis.log 2>&1 &

# 查看运行日志
tail -f output/logs/analysis.log

# 停止后台运行
# 找到进程 ID
ps aux | grep main.py
# 终止进程
kill <PID>
```

程序会自动：
1. 从 `config.json` 读取股池配置
2. 遍历分析每只股票（使用各自的 `frequency` 和 `offset`）
3. 根据 `chart.enabled` 决定是否生成图表
4. 如果 `email.enabled=true` 且触发买点，发送邮件通知，**如果希望当天的email通知要对信号过滤去重，可以自行加cache进行去重和拦截**
5. 如果 `app_main.interval_seconds>10`，等待指定秒数后重复执行


**注意事项：**
- mootdx API 最大返回 800 条数据，日期范围过大时会报错
- 建议日线范围不超过 3 年，分钟线范围不超过几天
- 支持三种日期格式：字符串 `'YYYY-MM-DD'`、`datetime` 对象、`date` 对象

### 4. 运行测试

```bash
uv run pytest tests/ -v
```

---

## 项目结构

```
stock-analysis/
├── src/                         # 核心功能包
│   ├── conf/                    # 配置管理包
│   │   ├── __init__.py
│   │   └── config.py            # 配置读取器
│   ├── data_kline/             # K线数据拉取包
│   │   ├── __init__.py
│   │   └── fetcher.py          # DataFetcher 类
│   ├── strategy/               # 策略包
│   │   ├── __init__.py
│   │   ├── base.py             # 抽象基类定义
│   │   ├── vba/                # VBA 辅助函数
│   │   │   ├── __init__.py
│   │   │   └── vba_func.py     # SMA/EMA 函数
│   │   ├── indicator/          # 指标计算器
│   │   │   ├── __init__.py
│   │   │   ├── slow_trend_line.py  # 慢速趋势线计算
│   │   │   └── price_mean.py       # 价格均值回归指标
│   │   └── buy/                # 信号计算器
│   │       ├── __init__.py
│   │       └── signal_calculator.py  # 买入信号计算
│   ├── notify/                 # 邮件通知包
│   │   ├── __init__.py
│   │   └── email_notifier.py   # EmailNotifier 类
│   ├── visualization/          # 可视化包
│   │   ├── __init__.py
│   │   └── plotter.py          # Plotter 类
│   └── main.py                 # 主程序入口
├── examples/                    # 使用示例
│   ├── single_stock_analysis.py  # 单只股票分析
│   └── pool_analysis.py          # 股池批量分析
├── tests/                       # 单元测试
│   ├── test_data_kline.py
│   ├── test_strategy.py
│   └── test_visualization.py
├── docs/                        # 文档目录
│   ├── CONFIG.md                # 配置文件详细说明
│   ├── config.json.minimal      # 最小配置示例
│   └── config.json.full         # 完整配置示例
├── output/                      # 输出目录
│   ├── charts/                  # 图表保存位置
│   └── logs/                    # 后台运行日志
└── config.json                  # 实际配置文件（需用户创建）
```

---

## 模块关系图

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│                     (程序入口)                              │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│    conf     │     │   data_kline    │     │  strategy   │
│  (配置管理) │     │   (K线数据)     │     │  (策略计算) │
└─────────────┘     └─────────────────┘     └─────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   Config    │     │  DataFetcher    │     │BuySignal-   │
│ - get()     │     │ - get_bars()    │     │Calculator   │
│ - reload()  │     │ - get_index_    │     │ - calculate │
│             │     │   _bars()       │     │   _signals()│
└─────────────┘     └─────────────────┘     └─────────────┘
        │                     │                     │
        │                     ▼                     │
        │             ┌─────────────┐               │
        │             │ mootdx API  │               │
        │             │(通达信数据源)│               │
        │             └─────────────┘               │
        │                                           │
        └──────────────────┬────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
      ┌─────────────┐ ┌───────────┐ ┌─────────────┐
      │visualization│ │  notify   │ │ config.json │
      │  (可视化)   │ │(邮件通知) │ │  (配置文件) │
      └─────────────┘ └───────────┘ └─────────────┘
              │            │
              ▼            ▼
      ┌─────────────┐ ┌───────────┐
      │   Plotter   │ │EmailNotifier│
      │ - plot_buy_ │ │ - send_buy_ │
      │   signals() │ │   signal()  │
      └─────────────┘ └───────────┘
```

---

## 数据流程

```
程序启动 (main.py)
       │
       ▼
从 config.json 读取配置
       │
       ├─► stock_pool (股池列表)
       ├─► email.enabled (邮件开关)
       ├─► chart.enabled (图表开关)
       ├─► app_main.interval_seconds (运行间隔)
       │
       ▼
run_pool() 遍历股池
       │
       └─► 对每只股票执行 run_single()
              │
              ▼
       DataFetcher.get_bars() ──────► 获取 K 线数据 (OHLCV)
              │
              ▼
       BuySignalCalculator.calculate_signals()
              │
              ├─► SlowTrendLineIndicator  ──► UP_LINE, DOWN_LINE
              ├─► PriceMeanIndicator      ──► MONEY_COMING, MONEY_LIVING
              │
              ▼
       合成信号：
         1. MONEY_COND (资金条件：10日内触发≥5次)
         2. UP_LINE_COND (慢速趋势金叉且≤25)
         3. BUY_POINT (两者同时满足)
         4. FILTER_BUY (间隔≥5周期)
              │
              ▼
       Plotter.print_signal_summary()  ──► 打印信号统计
              │
              ▼
       【如果 chart.enabled=true】
              │
              └─► Plotter.plot_buy_signals() ──► 绘制 K 线图 + 买入标记
                     │
                     └─► 保存到 output/charts/
              │
              ▼
       【如果 email.enabled=true 且 FILTER_BUY=True】
              │
              └─► EmailNotifier.send_buy_signal() ──► 发送邮件通知
              │
              ▼
       【股池模式】输出汇总报告
              │
              ▼
       【如果 interval_seconds > 10】
              │
              └─► 等待指定秒数后重复执行
```

---

## 策略包结构说明

策略包 (`src/strategy/`) 采用分层架构设计：

### 抽象基类 (`base.py`)

| 基类 | 抽象方法 | 说明 |
|------|----------|------|
| `BaseIndicator` | `calculate(df, **kwargs)` | 指标计算器基类 |
| `BaseSignalCalculator` | `calculate_signals(df)` | 信号计算器基类 |
| | `get_signals(df)` | 获取最新信号状态 |
| | `is_signal_triggered(df)` | 判断信号是否触发 |

### 目录结构

```
strategy/
├── base.py              # 抽象基类定义
├── vba/                 # VBA 辅助函数
│   └── vba_func.py      # sma_without_zero_reset(), ema()
├── indicator/           # 指标计算器（继承 BaseIndicator）
│   ├── slow_trend_line.py  # SlowTrendLineIndicator
│   └── price_mean.py       # PriceMeanIndicator
└── buy/                 # 信号计算器（继承 BaseSignalCalculator）
    └── signal_calculator.py  # BuySignalCalculator
```

### 扩展指南

**添加新指标：**

```python
from src.strategy import BaseIndicator
from pandas import DataFrame

class MyCustomIndicator(BaseIndicator):
    def calculate(self, df: DataFrame, **kwargs) -> DataFrame:
        # 实现指标计算逻辑
        df['MY_INDICATOR'] = ...
        return df
```

**添加新信号计算器：**

```python
from src.strategy import BaseSignalCalculator
from pandas import DataFrame

class MyCustomSignalCalculator(BaseSignalCalculator):
    def calculate_signals(self, df: DataFrame) -> DataFrame:
        # 实现信号计算逻辑
        ...

    def get_signals(self, df: DataFrame) -> dict:
        ...

    def is_signal_triggered(self, df: DataFrame) -> tuple:
        ...
```

---

## 注意事项

1. **速率限制**：通达信服务器有请求频率限制，所有 API 调用已内置 `time.sleep(0.5)` 延迟，避免被断开连接
2. **股票代码格式**：不需要加 `sh/sz` 前缀，mootdx 会自动处理（6 开头=上海，0/3 开头=深圳）
3. **投资风险**：本工具仅供学习研究，不构成投资建议
4. **配置安全**：config.json 包含敏感信息，请勿提交到 Git 仓库（已在 .gitignore 中排除）

---

## 依赖说明

| 库 | 用途 |
|----|------|
| mootdx | 通达信数据接口封装 |
| pandas | 数据处理与分析 |
| numpy | 数值计算 |
| mplfinance | K 线图可视化 |

邮件通知和配置管理使用 Python 标准库，无需额外依赖。

---

## 许可证

MIT License
