# 配置文件说明

## 创建配置文件

首次使用前，需要从示例文件创建配置文件：

```bash
cp docs/config.json.full config.json
```

## 配置示例文件

| 文件 | 说明 |
|------|------|
| [config.minimal.json](config.minimal.json) | 最小配置示例 |
| [config.full.json](config.full.json) | 完整配置示例 |

---

## 配置文件结构

```json
{
  "email": {
    "enabled": false,
    "smtp_server": "smtp.example.com",
    "smtp_port": 25,
    "use_ssl": false,
    "username": "your_email@example.com",
    "password": "your_password_or_app_token",
    "to_addr": ["recipient1@example.com"]
  },
  "stock_pool": [
    {"symbol": "600621", "name": "华鑫股份"},
    {"symbol": "600036", "name": "招商银行", "frequency": 5, "offset": 200},
    {"symbol": "000001", "name": "平安银行", "frequency": 4}
  ],
  "chart": {
    "enabled": true
  },
  "app_main": {
    "interval_seconds": 0
  }
}
```

---

## 邮件配置 (email)

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| enabled | boolean | 是 | false | 是否启用邮件通知。设为 `true` 时，触发买点会发送邮件 |
| smtp_server | string | 是 | - | SMTP 服务器地址，如 `smtp.163.com`、`smtp.qq.com` |
| smtp_port | integer | 是 | - | SMTP 端口，常见端口：25、465、587 |
| use_ssl | boolean | 否 | false | 是否使用 SSL 加密连接。端口 465 通常为 `true`，端口 25/587 通常为 `false` |
| username | string | 是 | - | 发件人邮箱账号 |
| password | string | 是 | - | 邮箱授权码（**非登录密码**）。QQ/163 等邮箱需在设置中生成授权码 |
| to_addr | array | 是 | - | 收件人邮箱列表，支持多个收件人 |

### 常见邮箱 SMTP 配置

| 邮箱服务 | smtp_server | smtp_port | use_ssl | 备注 |
|---------|-------------|-----------|---------|------|
| 163 邮箱 | smtp.163.com | 25 | false | 需使用授权码 |
| 163 邮箱 | smtp.163.com | 465 | true | SSL 加密方式 |
| QQ 邮箱 | smtp.qq.com | 465 | true | 需使用授权码 |
| Gmail | smtp.gmail.com | 587 | false | 需启用 starttls |
| Outlook | smtp.office365.com | 587 | false | 需启用 starttls |

---

## 股池配置 (stock_pool)

`stock_pool` 是一个数组，每项代表一只待监控的股票：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| symbol | string | 是 | - | 股票代码，**无需**添加 `sh`/`sz` 前缀。6 开头为上海，0/3 开头为深圳 |
| name | string | 是 | - | 股票名称，用于显示和邮件通知 |
| frequency | integer | 否 | 4 | K 线周期。4=日线，5=周线，6=月线，详见下方周期表 |
| offset | integer | 否 | 300 | 获取的历史数据条数，影响分析的时间范围 |

### K 线周期参数 (frequency)

| 值 | 周期 | 适用场景 |
|----|------|----------|
| 0 | 1 分钟 | 日内短线交易 |
| 1 | 5 分钟 | 日内短线交易 |
| 2 | 15 分钟 | 日内波段交易 |
| 3 | 60 分钟 | 短线波段交易 |
| 4 | 日线 | 中短线投资（**默认**） |
| 5 | 周线 | 中线投资 |
| 6 | 月线 | 长线投资 |

---

## 图表配置 (chart)

| 字段 | 类型 | 必填 | 默认值 | 说明                                                         |
|------|------|------|--------|------------------------------------------------------------|
| enabled | boolean | 否 | true | 是否生成 K 线图表。设为 `false` 可提高运行速度，节省磁盘空间，实盘的情况下，后台运行建议设置为false |

---

## 主程序配置 (app_main)

| 字段 | 类型 | 必填 | 默认值 | 说明                                                          |
|------|------|------|-----|-------------------------------------------------------------|
| interval_seconds | integer | 否 | 60  | 后台运行间隔（秒）。`-1`代表只运行一次后即退出；大于`10`代表每隔指定秒数循环运行（**必须大于 10 秒**） |

### 后台运行示例

| interval_seconds | 行为 |
|------------------|------|
| 60 | 每 1 分钟运行一次（最小推荐值） |
| 300 | 每 5 分钟运行一次 |
| 3600 | 每小时运行一次 |
| 86400 | 每天运行一次 |

**注意：** `interval_seconds` 如果是正整数则必须 > 10 秒（负数仅代表运行1次），否则程序会报错退出。这是为了避免请求频率过高被通达信服务器拒绝（实际环境下，如果中低频，建议配置300，即5分钟运行一次）。

---

## 配置示例

### 最小配置（仅股池，不启用邮件）

```json
{
  "email": {
    "enabled": false
  },
  "stock_pool": [
    {"symbol": "600621", "name": "华鑫股份"}
  ]
}
```

### 完整配置（启用邮件，后台运行，多只股票）

```json
{
  "email": {
    "enabled": true,
    "smtp_server": "smtp.163.com",
    "smtp_port": 25,
    "use_ssl": false,
    "username": "your_email@163.com",
    "password": "your_auth_code",
    "to_addr": ["receiver@example.com"]
  },
  "stock_pool": [
    {"symbol": "600621", "name": "华鑫股份"},
    {"symbol": "600036", "name": "招商银行", "frequency": 5, "offset": 200},
    {"symbol": "000001", "name": "平安银行", "frequency": 4, "offset": 500}
  ],
  "chart": {
    "enabled": true
  },
  "app_main": {
    "interval_seconds": 3600
  }
}
```

### 后台运行配置（每小时执行一次，不生成图表）

```json
{
  "email": {
    "enabled": true,
    "smtp_server": "smtp.163.com",
    "smtp_port": 25,
    "use_ssl": false,
    "username": "your_email@163.com",
    "password": "your_auth_code",
    "to_addr": ["receiver@example.com"]
  },
  "stock_pool": [
    {"symbol": "600621", "name": "华鑫股份"},
    {"symbol": "600036", "name": "招商银行"}
  ],
  "chart": {
    "enabled": false
  },
  "app_main": {
    "interval_seconds": 3600
  }
}
```

---

## 注意事项

- `config.json` 包含敏感信息（邮箱授权码），已在 `.gitignore` 中排除，请勿提交到 Git 仓库
- 股池模式会使用每只股票各自配置的 `frequency` 和 `offset`，未配置则使用默认值（`frequency=4`、`offset=300`）
- 邮件通知通过 `email.enabled` 控制开关，设为 `true` 时触发买点会自动发送邮件