# 配置指南 - 通义千问 + Server 酱

## 一、获取通义千问 API 密钥

### 步骤 1：访问阿里云控制台

打开网址：https://dashscope.console.aliyun.com/apiKey

### 步骤 2：登录/注册账号

1. 使用阿里云账号登录
2. 如果没有账号，点击"免费注册"
3. 需要完成实名认证（中国大陆用户需要身份证号）

### 步骤 3：开通 DashScope 服务

1. 首次使用需要开通服务
2. 点击"开通服务"
3. 绑定支付宝（用于扣费，但有免费额度）

### 步骤 4：创建 API Key

1. 点击"创建新的 API Key"
2. 输入名称（如：stock-news-system）
3. 复制生成的密钥（类似 `sk-xxxxxxxxxxxxxxxx`）

**重要**：API Key 只显示一次，请妥善保存！

### 步骤 5：查看免费额度

通义千问免费额度（2024 年政策）：
- qwen-turbo: 免费额度充足，个人使用足够
- qwen-plus: 有一定免费额度
- qwen-max: 较少免费额度

**推荐模型**：`qwen-plus`（性价比高）

---

## 二、获取 Server 酱推送密钥

### 步骤 1：访问官网

打开网址：https://sct.ftqq.com/

### 步骤 2：微信扫码登录

1. 打开网站后用微信扫码
2. 授权登录

### 步骤 3：关注公众号

关注"方糖"公众号（接收推送消息）

### 步骤 4：获取 SendKey

1. 点击页面右上角的 **SendKey**
2. 复制类似 `SCTxxxxxxxxxxxxxxxxx` 的字符串

### 步骤 5：测试推送

在浏览器打开以下 URL 测试：
```
https://sctapi.ftqq.com/你的 SendKey.send?title=测试推送&desp=这是一条测试消息
```

如果微信收到消息，说明配置成功！

---

## 三、配置 GitHub Secrets

### 进入设置页面

1. 访问你的 GitHub 仓库：https://github.com/heyefei110/stock-news-system
2. 点击 **Settings**（设置）标签
3. 左侧菜单选择 **Secrets and variables** → **Actions**

### 添加密钥

点击 **New repository secret**，添加以下 2 个密钥：

| Name | Value |
|------|-------|
| `DASHSCOPE_API_KEY` | 通义千问 API 密钥（步骤一获取） |
| `SERVERCHAN_SENDKEY` | Server 酱 SendKey（步骤二获取） |

---

## 四、本地测试（可选）

### 创建本地 .env 文件

在项目根目录创建 `.env` 文件：

```env
# 通义千问 API
DASHSCOPE_API_KEY=sk-你的密钥

# Server 酱推送
SERVERCHAN_SENDKEY=SCT_你的密钥

# 系统设置
DATABASE_PATH=./data/stock_news.db
LOG_LEVEL=INFO
```

### 运行测试

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -m config.database

# 执行一次采集任务
python main.py run
```

检查微信是否收到推送。

---

## 五、费用说明

### 通义千问费用

| 模型 | 价格（元/千 tokens） | 免费额度 |
|------|---------------------|----------|
| qwen-turbo | 约 0.002 | 充足 |
| qwen-plus | 约 0.01 | 有一定额度 |
| qwen-max | 约 0.04 | 较少 |

**估算**：每条新闻摘要约 100-200 tokens，每日 20 条新闻约 2000-4000 tokens
- 每日费用：约 0.01-0.04 元
- 每月费用：约 0.3-1.2 元

### Server 酱费用

- 完全免费（个人版）
- 每日限额 10 条消息（足够推送汇总后的资讯）

---

## 六、常见问题

### Q1: API Key 无效？

**检查**：
- 是否完整复制了密钥（包含 `sk-` 前缀）
- 是否开通了 DashScope 服务
- 账号是否完成实名认证

### Q2: Server 酱收不到推送？

**检查**：
- 是否关注了"方糖"公众号
- SendKey 是否正确复制
- 在浏览器测试 URL 是否能收到

### Q3: 免费额度用完怎么办？

**通义千问**：
- 绑定支付宝，自动按量计费（很便宜）
- 或切换到 `qwen-turbo` 模型（更便宜）

**Server 酱**：
- 个人版每日 10 条限额
- 如果超出，考虑升级到付费版

---

## 七、完整的 GitHub 配置清单

在 https://github.com/heyefei110/stock-news-system/settings/secrets/actions 添加：

```
DASHSCOPE_API_KEY = sk-xxxxxxxxxxxxxxxxxxxxxxxx
SERVERCHAN_SENDKEY = SCTxxxxxxxxxxxxxxxxxxxxxxx
```

**完成！** 之后每天 6:00 自动执行，微信自动收到推送。
