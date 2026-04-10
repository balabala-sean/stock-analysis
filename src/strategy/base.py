# -*- coding: utf-8 -*-
"""
策略包 - 抽象接口定义
"""

from abc import ABC, abstractmethod
from pandas import DataFrame
from typing import Dict, Tuple, Any


class BaseIndicator(ABC):
    """
    指标计算器抽象基类

    所有指标计算器都应继承此基类，实现 calculate 方法
    """

    @abstractmethod
    def calculate(self, df: DataFrame, **kwargs) -> DataFrame:
        """
        计算指标

        Args:
            df: 包含 OHLCV 数据的 DataFrame
            **kwargs: 指标参数

        Returns:
            添加了指标列的 DataFrame
        """
        pass

    def get_name(self) -> str:
        """
        获取指标名称

        Returns:
            指标名称字符串
        """
        return self.__class__.__name__


class BaseSignalCalculator(ABC):
    """
    信号计算器抽象基类

    所有信号计算器都应继承此基类
    """

    @abstractmethod
    def calculate_signals(self, df: DataFrame) -> DataFrame:
        """
        计算信号

        Args:
            df: 包含 OHLCV 数据的 DataFrame

        Returns:
            添加了信号列的 DataFrame
        """
        pass

    @abstractmethod
    def get_signals(self, df: DataFrame) -> Dict[str, Any]:
        """
        获取最新信号状态

        Args:
            df: 包含 OHLCV 数据的 DataFrame

        Returns:
            字典包含最新信号状态和指标值
        """
        pass

    @abstractmethod
    def is_signal_triggered(self, df: DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        判断信号是否触发

        Args:
            df: 包含 OHLCV 数据的 DataFrame

        Returns:
            (是否触发信号，信号详情字典)
        """
        pass

    def get_name(self) -> str:
        """
        获取计算器名称

        Returns:
            计算器名称字符串
        """
        return self.__class__.__name__