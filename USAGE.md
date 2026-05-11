# 股票资讯系统使用指南

## 一、快速开始 (5 分钟上手)

### 步骤 1: 安装依赖

```bash
cd stock-news-system
pip install -r requirements.txt
```

### 步骤 2: 配置环境变量

复制并编辑 `.env` 文件：

```bash
cp .env.example .env
```

**必须配置的项目**:

```env
# 1. Claude API 密钥 (用于智能摘要)
ANTHROPIC_API_KEY=sk-ant-api-xxxxxxxxxxxxx

# 2. 微信推送 (任选其一)
# 方案 A: Server 酱 (最简单)
SERVERCHAN_SENDKEY=SCTxxxxxxxxxxxxx

# 方案 B: Gewebot
# GEWE_BOT_URL=http://localhost:9500
# GEWE_BOT_TOKEN=your_token
```

### 步骤 3: 初始化并运行

```bash
# 初始化数据库
python -m config.database

# 测试运行一次
python main.py run

# 启动定时任务
python main.py schedule
```

### 步骤 4: 启动 Web 管理后台 (可选)

```bash
python -m web.app
```

访问 http://localhost:8000

---

## 二、微信推送配置详解

### 方案 A: Server 酱 (推荐)

1. 访问 https://sct.ftqq.com/
2. 微信扫码登录
3. 点击 "SendKey" 获取密钥
4. 填入 `.env` 文件的 `SERVERCHAN_SENDKEY`

**优点**: 配置简单，无需额外服务
**缺点**: 每日限额 10 条

### 方案 B: Gewebot

1. 部署 Gewebot 服务
   ```bash
   # Docker 部署
   docker run -d --name gewe bot=your_bot_token
   ```

2. 配置 `.env`:
   ```env
   GEWE_BOT_URL=http://localhost:9500
   GEWE_BOT_TOKEN=your_token
   ```

**优点**: 无限制，功能强大
**缺点**: 需要额外部署服务

### 方案 C: WeChatFerry

1. 下载 WeChatFerry: https://github.com/lich0821/WeChatFerry
2. 运行服务端
3. 配置 `.env`:
   ```env
   WCF_HOST=127.0.0.1
   WCF_PORT=8080
   ```

---

## 三、股票管理

### 通过 Web 界面管理

1. 访问 http://localhost:8000/stocks
2. 点击 "+ 新增" 添加股票
3. 填写信息:
   - 股票名称 (必填): 如 "首程控股"
   - 股票代码 (可选): 如 "00666.HK"
   - 市场：港股/美股/A 股/一级市场

### 通过数据库管理

```bash
# 连接数据库
sqlite3 data/stock_news.db

# 添加股票
INSERT INTO stocks (name, code, market) VALUES ('特斯拉', 'TSLA', 'US');

# 禁用股票
UPDATE stocks SET enabled = 0 WHERE name = '宝龙地产';

# 删除股票
DELETE FROM stocks WHERE name = '壁仞科技';
```

---

## 四、定时任务配置

### 修改执行时间

默认每日 6:00 执行，确保 8:30 前完成。

**方法 1: Web 界面**
- 访问 http://localhost:8000/settings
- 修改 "任务执行时间"

**方法 2: 编辑 .env**
```env
CRON_HOUR=5    # 改为 5 点执行
CRON_MINUTE=30 # 5:30 执行
```

### 手动触发

```bash
# 立即执行一次
python main.py run

# 或在 Web 界面点击 "立即执行"
```

---

## 五、日志查询

### Web 界面查询

访问 http://localhost:8000/logs

- 任务日志：查看每次采集任务的执行情况
- 推送记录：查看微信推送历史
- 时间筛选：支持最近 1/7/30 天

### 日志文件

```bash
# 查看最新日志
tail -f logs/app.log

# 查看错误日志
grep ERROR logs/app.log
```

---

## 六、常见问题

### Q1: 未采集到任何新闻

**原因**:
- 网络连接问题
- 股票名称不正确
- 平台 API 临时故障

**解决**:
1. 检查网络连接
2. 确认股票名称准确
3. 查看日志获取详细错误
4. 稍后重试

### Q2: 推送失败

**检查清单**:
1. `.env` 中推送配置是否正确
2. Server 酱 SendKey 是否有效
3. Gewebot 服务是否运行
4. 查看错误日志

### Q3: 摘要生成失败

**原因**: Claude API 不可用

**解决**:
1. 检查 `ANTHROPIC_API_KEY` 配置
2. 系统会自动降级到关键词摘要
3. 不影响正常推送

### Q4: 如何添加更多数据源？

在 `collectors/` 目录下新建采集器：

```python
# collectors/your_source.py
from collectors.base import BaseCollector, NewsItem

class YourSourceCollector(BaseCollector):
    def get_source_name(self) -> str:
        return "你的数据源名称"

    async def collect(self, stock_list, date_range):
        # 实现采集逻辑
        news_list = []
        # ...
        return news_list
```

然后在 `collectors/__init__.py` 中导出。

---

## 七、系统监控

### 成功率监控

访问 http://localhost:8000/api/status

```json
{
  "enabled_stocks": 5,
  "success_jobs_24h": 1,
  "failed_jobs_24h": 0,
  "success_rate": 100.0
}
```

### 告警通知

系统在以下情况发送告警:
- 任务执行失败
- 推送失败 (达到最大重试次数)
- 数据采集异常

告警方式：微信推送 + 邮件 (可选)

---

## 八、性能优化

### 启用 Redis 缓存

```env
REDIS_URL=redis://localhost:6379/0
```

### 调整并发数

编辑 `main.py`:
```python
# 修改批次大小
summarizer = NewsSummarizer(batch_size=20)  # 默认 10
```

### 数据库维护

定期清理旧数据:
```sql
-- 删除 30 天前的新闻
DELETE FROM news WHERE publish_time < datetime('now', '-30 days');
```

---

## 九、技术支持

### 错误日志

遇到问题请先查看日志:
```bash
# 应用日志
cat logs/app.log

# 数据库操作日志
sqlite3 data/stock_news.db "SELECT * FROM job_logs ORDER BY created_at DESC LIMIT 10;"
```

### 提交问题

请提供以下信息:
1. 错误日志内容
2. `.env` 配置 (隐藏敏感信息)
3. 问题复现步骤
