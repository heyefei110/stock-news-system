# 快速部署指南（通义千问版）

## 适用于 GitHub 用户名：heyefei110

---

## 第一步：获取两个密钥（5 分钟）

### 1. 通义千问 API 密钥

1. 访问：https://dashscope.console.aliyun.com/apiKey
2. 用阿里云账号登录（没有就注册一个）
3. 开通 DashScope 服务（免费）
4. 点击"创建新的 API Key"
5. **复制密钥**（类似 `sk-xxxxxxxxxx`）

### 2. Server 酱推送密钥

1. 访问：https://sct.ftqq.com/
2. 微信扫码登录
3. 关注"方糖"公众号
4. 点击"SendKey"
5. **复制密钥**（类似 `SCTxxxxxxxxxx`）

---

## 第二步：推送代码到 GitHub（2 分钟）

在该项目目录下打开命令提示符，执行：

```bash
cd C:\Users\86138\stock-news-system

# 关联远程仓库（替换为你的用户名）
git remote add origin https://github.com/heyefei110/stock-news-system.git

# 推送到 GitHub
git push -u origin main
```

如果遇到错误，可能需要先切换分支：
```bash
git branch -M main
git push -u origin main
```

---

## 第三步：配置 GitHub Secrets（2 分钟）

1. 访问：https://github.com/heyefei110/stock-news-system/settings/secrets/actions

2. 点击 **New repository secret**

3. 添加第一个密钥：
   - **Name**: `DASHSCOPE_API_KEY`
   - **Value**: （粘贴通义千问 API 密钥）

4. 添加第二个密钥：
   - **Name**: `SERVERCHAN_SENDKEY`
   - **Value**: （粘贴 Server 酱 SendKey）

---

## 第四步：测试运行（5 分钟）

1. 访问：https://github.com/heyefei110/stock-news-system/actions

2. 左侧点击 **Daily Stock News Collection**

3. 点击右上角的 **Run workflow** 按钮

4. 点击绿色按钮 **Run workflow**

5. 等待 3-5 分钟，看到绿色 ✅ 表示成功

6. 检查微信是否收到推送消息

---

## 第五步：验证成功

如果微信收到类似以下消息，说明部署成功：

```
【股票资讯日报】
推送时间：05-11 08:15
总计：5 只股票，XX 条资讯
========================================

【首程控股】X 条
------------------------------
  1. [09:30] XXXXXXXX
  ...
```

---

## 后续事项

### 每日自动执行

- 执行时间：北京时间 每日 06:00
- 推送时间：08:30 前完成
- 无需开电脑，GitHub Actions 自动运行

### 查看执行记录

随时访问：https://github.com/heyefei110/stock-news-system/actions

### 修改股票列表

编辑 `config/settings.py` 中的 `default_stocks` 列表，然后推送：

```bash
git add config/settings.py
git commit -m "更新股票列表"
git push
```

### 修改执行时间

编辑 `.github/workflows/daily_job.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: "0 21 * * *"  # 改为 05:00 执行
  - cron: "0 22 * * *"  # 改为 06:00 执行（默认）
  - cron: "0 23 * * *"  # 改为 07:00 执行
```

---

## 费用说明

| 项目 | 费用 |
|------|------|
| GitHub Actions | 免费（2000 分钟/月） |
| 通义千问 API | 免费额度 + 约 1 元/月 |
| Server 酱 | 免费 |

**总计**：约 1 元/月

---

## 遇到问题？

### 问题 1：推送失败

检查：
1. Server 酱 SendKey 是否正确
2. 是否关注了"方糖"公众号
3. 在 GitHub Actions 日志中查看错误信息

### 问题 2：API 调用失败

检查：
1. 通义千问 API Key 是否正确
2. 是否开通了 DashScope 服务
3. 账号是否完成实名认证

### 问题 3：Git 推送失败

```bash
# 如果是首次推送，可能需要设置分支
git branch -M main
git push -u origin main
```

---

## 完整配置清单

✅ 通义千问 API 密钥 → GitHub Secret: `DASHSCOPE_API_KEY`
✅ Server 酱 SendKey → GitHub Secret: `SERVERCHAN_SENDKEY`
✅ 代码已推送到 GitHub
✅ 测试运行成功
✅ 微信收到推送

**完成！** 🎉
