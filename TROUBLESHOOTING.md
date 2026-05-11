# 排查微信推送问题

## 问题：GitHub Actions 显示成功但没收到微信消息

### 可能原因

1. **Server 酱配置错误**
   - SendKey 不正确
   - 没有关注"方糖"公众号

2. **推送代码问题**
   - 可能推送模块没有正确调用

3. **Server 酱服务限制**
   - 新账号需要验证

---

## 排查步骤

### 第 1 步：验证 Server 酱配置

在浏览器打开以下 URL（替换为你的 SendKey）：

```
https://sctapi.ftqq.com/SCT348288TAnib06tVISfWrgSkobqb3jRa.send?title=测试推送&desp=这是一条测试消息
```

如果收到微信消息，说明 Server 酱配置正确。

### 第 2 步：检查是否关注公众号

1. 打开微信
2. 搜索公众号 "方糖"
3. 如果没有关注，请加关注

### 第 3 步：查看 GitHub Actions 日志

1. 访问：https://github.com/heyefei110/stock-news-system/actions
2. 点击最近一次运行记录
3. 查看输出内容

---

## 本地测试

在本地运行一次，看是否能收到推送：

```bash
cd C:\Users\86138\stock-news-system
python main.py run
```

如果本地运行能收到推送，说明配置正确，是 GitHub Actions 的问题。
