# GitHub Actions 快速部署指南

## 5 分钟完成部署，之后每天自动运行

### 第 1 步：创建 GitHub 仓库

1. 访问 https://github.com
2. 点击右上角 "+" → "New repository"
3. 仓库名：`stock-news-system` (或你喜欢的名字)
4. 设为 **Public** 或 **Private** 都可以
5. 点击 "Create repository"

### 第 2 步：上传代码

在该项目目录下执行：

```bash
# 初始化 git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit"

# 关联远程仓库 (替换 yourname 为你的 GitHub 用户名)
git remote add origin https://github.com/yourname/stock-news-system.git

# 推送
git push -u origin main
```

如果遇到分支名称问题，使用：
```bash
git branch -M main
git push -u origin main
```

### 第 3 步：配置 API 密钥

1. 进入你的 GitHub 仓库页面
2. 点击 **Settings** (设置)
3. 左侧菜单选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**

添加以下 2 个密钥：

| Name | Value |
|------|-------|
| `ANTHROPIC_API_KEY` | 你的 Claude API 密钥 |
| `SERVERCHAN_SENDKEY` | 你的 Server 酱推送密钥 |

### 第 4 步：测试运行

1. 在仓库页面点击 **Actions** 标签
2. 左侧点击 "Daily Stock News Collection"
3. 点击右侧的 **Run workflow** 按钮
4. 等待约 2-5 分钟，看到绿色 ✅ 表示成功

### 第 5 步：验证推送

检查你的微信是否收到推送消息。如果收到，说明部署成功！

---

## 后续使用

### 修改股票列表

编辑 `config/settings.py` 中的 `default_stocks` 列表，然后推送：

```bash
git add config/settings.py
git commit -m "Update stock list"
git push
```

### 修改执行时间

编辑 `.github/workflows/daily_job.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: "0 22 * * *"  # 改为其他时间
```

**cron 表达式说明**（使用 UTC 时间）：
- `0 22 * * *` = 北京时间 06:00
- `0 23 * * *` = 北京时间 07:00
- `30 22 * * *` = 北京时间 06:30

### 查看执行日志

1. 访问 https://github.com/yourname/stock-news-system/actions
2. 点击任意一次运行记录
3. 查看详细信息

### 手动触发

随时可以点击 **Actions** → **Run workflow** 手动执行一次

---

## 常见问题

### Q: GitHub Actions 是什么？

GitHub 提供的自动化服务，可以在云端定时执行代码，无需你自己的电脑开机。

### Q: 免费额度够用吗？

每月 2000 分钟，每次执行约 3-5 分钟，每日执行一次约消耗 150 分钟/月，完全够用。

### Q: 代码更新后会自动生效吗？

是的，每次 push 后，第二天的定时任务会自动使用最新代码。

### Q: 如何临时停止任务？

在仓库页面 → Settings → Actions → 禁用仓库

### Q: 收不到推送怎么办？

1. 检查 Actions 日志确认任务是否成功
2. 检查 Server 酱密钥是否正确
3. 查看日志中的错误信息

---

## 无需再开电脑！

完成以上配置后：
- ✅ 每天自动执行
- ✅ 微信自动收到推送
- ✅ 无需开电脑
- ✅ 完全免费
