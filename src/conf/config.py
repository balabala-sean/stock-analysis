# -*- coding: utf-8 -*-
"""
配置管理模块 - 统一读取 config.json
"""

import json
import os
from typing import Optional, List, Dict

# 默认配置值
DEFAULT_FREQUENCY = 4
DEFAULT_OFFSET = 300


class Config:
    """配置管理类"""

    _instance: Optional['Config'] = None
    _config_path: str = "config.json"
    _config: Optional[Dict] = None

    def __new__(cls, config_path: str = "config.json"):
        """单例模式，确保全局只有一个配置实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config_path = config_path
            cls._load_config()
        return cls._instance

    @classmethod
    def _load_config(cls):
        """加载配置文件"""
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(cls._config_path):
            # 尝试从项目根目录查找
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cls._config_path = os.path.join(project_root, cls._config_path)

        if os.path.exists(cls._config_path):
            with open(cls._config_path, 'r', encoding='utf-8') as f:
                cls._config = json.load(f)
        else:
            cls._config = None

    @classmethod
    def reload(cls, config_path: str = "config.json"):
        """重新加载配置"""
        cls._config_path = config_path
        cls._load_config()

    @classmethod
    def get(cls, key: str, default=None) -> Optional[Dict]:
        """获取配置项"""
        if cls._config is None:
            return default
        return cls._config.get(key, default)

    @classmethod
    def is_loaded(cls) -> bool:
        """检查配置是否已加载"""
        return cls._config is not None

    @classmethod
    def get_all(cls) -> Optional[Dict]:
        """获取全部配置"""
        return cls._config


def get_config(config_path: str = "config.json") -> Config:
    """获取配置实例"""
    return Config(config_path)


def get_stock_pool(config_path: str = "config.json") -> List[Dict]:
    """
    获取股票池配置（填充默认值）

    Args:
        config_path: 配置文件路径

    Returns:
        股票池列表，每项包含 symbol、name、frequency、offset
        示例: [{'symbol': '600621', 'name': '华鑫股份', 'frequency': 4, 'offset': 300}, ...]
    """
    config = get_config(config_path)
    stock_pool = config.get('stock_pool', [])

    if not stock_pool:
        return []

    # 填充默认值
    result = []
    for stock in stock_pool:
        result.append({
            'symbol': stock.get('symbol'),
            'name': stock.get('name'),
            'frequency': stock.get('frequency', DEFAULT_FREQUENCY),
            'offset': stock.get('offset', DEFAULT_OFFSET)
        })

    return result


def get_email_config(config_path: str = "config.json") -> Optional[Dict]:
    """
    获取邮件配置

    Args:
        config_path: 配置文件路径

    Returns:
        邮件配置字典
    """
    config = get_config(config_path)
    return config.get('email')


def is_email_enabled(config_path: str = "config.json") -> bool:
    """
    检查邮件通知是否启用

    Args:
        config_path: 配置文件路径

    Returns:
        True 如果邮件通知启用且配置完整
    """
    email_config = get_email_config(config_path)
    if email_config is None:
        return False
    return email_config.get('enabled', False)


def is_generate_chart_enabled(config_path: str = "config.json") -> bool:
    """
    检查是否生成图表

    Args:
        config_path: 配置文件路径

    Returns:
        True 如果需要生成图表
    """
    config = get_config(config_path)
    chart_config = config.get('chart', {})
    return chart_config.get('enabled', True)


def get_interval_seconds(config_path: str = "config.json") -> int:
    """
    获取后台运行时间间隔（秒）

    Args:
        config_path: 配置文件路径

    Returns:
        运行间隔（秒），如果是负数则代表只运行1次

    Raises:
        ValueError: 如果 interval_seconds 大于 0 但小于等于 10
    """
    config = get_config(config_path)
    app_main_config = config.get('app_main', {})
    interval_seconds = app_main_config.get('interval_seconds', 60)

    # 验证：如果启用后台运行，间隔必须大于 10 秒
    if 0< interval_seconds < 10:
        raise ValueError(
            f"配置错误：app_main.interval_seconds = {interval_seconds}，"
            f"后台运行间隔必须大于 10 秒（当前设置过短会导致频繁请求被服务器拒绝）"
        )

    return interval_seconds