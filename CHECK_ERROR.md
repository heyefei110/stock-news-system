# 请按照以下步骤获取错误详情

## 1. 访问 Actions 页面
https://github.com/heyefei110/stock-news-system/actions

## 2. 点击失败的运行记录
点击最新的那次运行（显示红色 ❌ 或 Failed）

## 3. 点击 "collect-and-push" 任务
在任务列表中点击 "collect-and-push"

## 4. 向下滚动查看错误信息
找到显示错误的部分，通常会有类似：
- `Error: Process completed with exit code 1`
- 或者 Python 报错信息

## 5. 复制错误信息
请把完整的错误信息复制给我，包括：
- 安装依赖时的错误（如果有）
- Python 代码执行的错误
- 任何 Exception 或 Traceback

---

## 常见问题预判

可能是以下原因之一：

### 1. 依赖安装失败
```
ERROR: Could not find a version that satisfies the requirement...
```

**解决**: 修改 requirements.txt

### 2. simhash 库安装失败（常见）
```
error: command 'gcc' failed
```

**解决**: simhash 需要编译，GitHub Actions 环境可能缺少依赖

### 3. Python 代码执行错误
```
ModuleNotFoundError: No module named 'xxx'
```

**解决**: 缺少依赖或导入错误

---

请把错误日志发给我，我帮你修复！
