# 云端部署方案

为了让系统 24 小时自动运行而无需开电脑，需要将系统部署到云端服务器。

## 方案对比

| 方案 | 价格 | 难度 | 推荐度 |
|------|------|------|--------|
| GitHub Actions | 免费 (2000 分钟/月) | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 腾讯云轻量服务器 | ¥24/月 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 阿里云 ECS | ¥30/月 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Railway/Render | 免费额度 | ⭐⭐ | ⭐⭐⭐ |
| 微信云托管 | ¥10/月 | ⭐⭐ | ⭐⭐⭐⭐ |

---

## 方案一：GitHub Actions (推荐 - 完全免费)

### 优势
- 完全免费，每月 2000 分钟执行额度
- 无需维护服务器
- 自动执行，无需开电脑
- 代码更新自动同步

### 部署步骤

#### 1. 创建 GitHub 仓库

```bash
# 初始化 git 仓库
cd stock-news-system
git init
git add .
git commit -m "Initial commit"

# 创建 GitHub 仓库后推送
# git remote add origin https://github.com/yourname/stock-news-system.git
# git push -u origin main
```

#### 2. 配置 GitHub Secrets

在 GitHub 仓库设置中配置 Secrets:
- Settings → Secrets and variables → Actions
- 添加以下 secrets:
  - `ANTHROPIC_API_KEY`: Claude API 密钥
  - `SERVERCHAN_SENDKEY`: Server 酱推送密钥

#### 3. 创建工作流文件

系统已提供 `.github/workflows/daily_job.yml`

#### 4. 推送代码

```bash
git add .
git commit -m "Add GitHub Actions workflow"
git push
```

### 执行时间
默认每日 06:00 (北京时间) 执行

---

## 方案二：腾讯云轻量服务器 (最稳定)

### 购买指引
1. 访问 https://cloud.tencent.com/product/lighthouse
2. 选择轻量应用服务器
3. 选择镜像：Ubuntu 22.04
4. 选择配置：2 核 2G 即可 (¥24/月)
5. 购买时长：建议选择 1 年更优惠

### 部署步骤

#### 1. 连接服务器

```bash
# Windows 使用 PowerShell 或下载 Xshell
ssh root@你的服务器 IP
```

#### 2. 安装环境

```bash
# 更新系统
apt update && apt upgrade -y

# 安装 Python
apt install python3 python3-pip -y

# 安装 Git
apt install git -y
```

#### 3. 部署代码

```bash
# 克隆代码
git clone https://github.com/yourname/stock-news-system.git
cd stock-news-system

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 4. 配置环境变量

```bash
# 创建 .env 文件
cat > .env << EOF
ANTHROPIC_API_KEY=你的密钥
SERVERCHAN_SENDKEY=你的推送密钥
DATABASE_PATH=./data/stock_news.db
LOG_LEVEL=INFO
EOF
```

#### 5. 设置定时任务

```bash
# 编辑 crontab
crontab -e

# 添加以下行 (每日 6:00 执行)
0 6 * * * cd /root/stock-news-system && /root/stock-news-system/venv/bin/python main.py run >> logs/cron.log 2>&1
```

#### 6. 后台运行 Web 服务 (可选)

```bash
# 使用 systemd 管理
cat > /etc/systemd/system/stock-news.service << EOF
[Unit]
Description=Stock News Web Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/stock-news-system
ExecStart=/root/stock-news-system/venv/bin/python -m web.app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl enable stock-news
systemctl start stock-news
```

---

## 方案三：微信云托管 (推荐国内用户)

### 优势
- 官方支持，稳定可靠
- 价格低廉 (约 ¥10/月)
- 无需备案
- 内网访问微信生态

### 部署步骤

1. 访问微信云托管官网：https://cloud.weixin.qq.com
2. 创建环境
3. 选择「容器部署」
4. 上传代码或连接 GitHub
5. 配置环境变量
6. 设置定时触发器

---

## 方案四：Railway (海外免费)

### 部署步骤

1. 访问 https://railway.app
2. 用 GitHub 账号登录
3. New Project → Deploy from GitHub repo
4. 选择你的仓库
5. 配置环境变量
6. 添加 Cron 插件设置定时任务

---

## 推荐配置总结

### 个人使用 (零成本)
**GitHub Actions** - 完全免费，无需服务器

### 稳定运行 (低成本)
**腾讯云轻量服务器** - ¥24/月，24 小时运行，还可运行其他服务

### 微信生态集成
**微信云托管** - 与微信深度集成，推送更稳定

---

## 迁移现有数据

如果已有本地数据需要迁移：

```bash
# 导出数据库
sqlite3 data/stock_news.db ".dump" > backup.sql

# 在服务器导入
sqlite3 data/stock_news.db < backup.sql
```

---

## 监控和告警

### 配置邮件告警

在 `.env` 中添加:

```env
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
SMTP_USER=your_qq_email@qq.com
SMTP_PASSWORD=your_auth_code
ALERT_EMAIL=your_qq_email@qq.com
```

### 微信告警 (额外通知)

关注「PushPlus」公众号获取 token:

```env
PUSHPLUS_TOKEN=your_pushplus_token
```
