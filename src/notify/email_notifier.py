# -*- coding: utf-8 -*-
"""
邮件通知器 - 发送买点信号邮件通知
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Tuple

from src.conf import get_email_config, is_email_enabled


class EmailNotifier:
    """邮件通知器"""

    def __init__(self, config_path: str = "config.json"):
        """
        初始化邮件通知器

        Args:
            config_path: 配置文件路径
        """
        self.config = get_email_config(config_path)
        self.enabled = is_email_enabled(config_path)

    def is_configured(self) -> bool:
        """检查是否已配置邮件且已启用"""
        return self.enabled and self.config is not None

    def send_buy_signal(
        self,
        symbol: str,
        name: str,
        signal_info: dict,
        buy_points_count: int = 0
    ) -> bool:
        """
        发送买点信号邮件

        Args:
            symbol: 股票代码
            name: 股票名称
            signal_info: 信号信息字典，包含 date、close、UP_LINE、DOWN_LINE 等
            buy_points_count: 历史买点总数

        Returns:
            发送成功返回 True，失败返回 False
        """
        if not self.config:
            print("警告：邮件未配置，请先创建 config.json")
            return False

        if not self.enabled:
            print("提示：邮件通知已禁用（config.json 中 email.enabled = false）")
            return False

        subject, body = self._build_email_content(symbol, name, signal_info, buy_points_count)

        try:
            return self._send_email(subject, body)
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False

    def _build_email_content(
        self,
        symbol: str,
        name: str,
        signal_info: dict,
        buy_points_count: int
    ) -> Tuple[str, str]:
        """
        构建邮件内容

        Args:
            symbol: 股票代码
            name: 股票名称
            signal_info: 信号信息
            buy_points_count: 历史买点总数

        Returns:
            (邮件主题, 邮件正文)
        """
        date = signal_info.get('date', datetime.now())
        if hasattr(date, 'strftime'):
            date_str = date.strftime('%Y-%m-%d %H:%M')
        else:
            date_str = str(date)

        close = signal_info.get('close', 0)
        up_line = signal_info.get('UP_LINE', 0)
        down_line = signal_info.get('DOWN_LINE', 0)

        subject = f"[买点信号] {symbol} - {name}"

        body = f"""
股票买点信号通知

股票信息：
  代码：{symbol}
  名称：{name}

买点详情：
  日期：{date_str}
  收盘价：{close:.2f}
  UP_LINE：{up_line:.2f}
  DOWN_LINE：{down_line:.2f}

统计信息：
  历史买点总数：{buy_points_count}

---
本邮件由 Stock Analysis 系统自动发送，仅供参考，不构成投资建议。
"""

        return subject, body

    def _send_email(self, subject: str, body: str) -> bool:
        """
        发送邮件

        Args:
            subject: 邮件主题
            body: 邮件正文

        Returns:
            发送成功返回 True
        """
        smtp_server = self.config['smtp_server']
        smtp_port = self.config['smtp_port']
        use_ssl = self.config.get('use_ssl', False)
        username = self.config['username']
        password = self.config['password']
        to_addr = self.config['to_addr']

        # 构建邮件
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = ', '.join(to_addr)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # 发送邮件
        if use_ssl:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(username, password)
                server.sendmail(username, to_addr, msg.as_string())
        else:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(username, to_addr, msg.as_string())

        print(f"邮件发送成功：{subject}")
        return True