# -*- coding: utf-8 -*-
"""
配置包 - 统一配置管理
"""

from .config import (
    Config,
    get_config,
    get_stock_pool,
    get_email_config,
    is_email_enabled,
    is_generate_chart_enabled,
    get_interval_seconds
)

__all__ = [
    'Config',
    'get_config',
    'get_stock_pool',
    'get_email_config',
    'is_email_enabled',
    'is_generate_chart_enabled',
    'get_run_interval'
]