"""
配置管理 Web 应用
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sqlite3
from config.database import get_db_connection
from config.settings import settings

app = FastAPI(title="股票资讯系统管理后台")

# 模板配置
templates = Jinja2Templates(directory="web/templates")


class StockConfig(BaseModel):
    """股票配置模型"""
    name: str
    code: Optional[str] = ""
    market: str = "HK"
    enabled: bool = True


class PushConfig(BaseModel):
    """推送配置模型"""
    push_hour: int
    push_minute: int
    cron_hour: int
    cron_minute: int


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """管理后台首页"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取股票列表
    cursor.execute("SELECT * FROM stocks ORDER BY created_at DESC")
    stocks = [dict(row) for row in cursor.fetchall()]

    # 获取最近推送记录
    cursor.execute(
        "SELECT * FROM push_records ORDER BY push_time DESC LIMIT 10"
    )
    push_records = [dict(row) for row in cursor.fetchall()]

    # 获取最近任务日志
    cursor.execute(
        "SELECT * FROM job_logs ORDER BY created_at DESC LIMIT 10"
    )
    job_logs = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stocks": stocks,
        "push_records": push_records,
        "job_logs": job_logs,
        "settings": settings
    })


@app.get("/stocks", response_class=HTMLResponse)
async def stocks_page(request: Request):
    """股票管理页面"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stocks ORDER BY name")
    stocks = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return templates.TemplateResponse("stocks.html", {
        "request": request,
        "stocks": stocks
    })


@app.post("/stocks/add")
async def add_stock(
    name: str = Form(...),
    code: str = Form(""),
    market: str = Form("HK")
):
    """添加股票"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO stocks (name, code, market, enabled)
            VALUES (?, ?, ?, 1)
        """, (name, code, market))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="股票已存在")

    conn.close()
    return RedirectResponse(url="/stocks", status_code=303)


@app.post("/stocks/toggle/{stock_id}")
async def toggle_stock(stock_id: int):
    """切换股票启用状态"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT enabled FROM stocks WHERE id = ?", (stock_id,)
    )
    row = cursor.fetchone()
    if row:
        new_status = 0 if row["enabled"] else 1
        cursor.execute(
            "UPDATE stocks SET enabled = ? WHERE id = ?",
            (new_status, stock_id)
        )
        conn.commit()

    conn.close()
    return RedirectResponse(url="/stocks", status_code=303)


@app.post("/stocks/delete/{stock_id}")
async def delete_stock(stock_id: int):
    """删除股票"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stocks WHERE id = ?", (stock_id,))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/stocks", status_code=303)


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(
    request: Request,
    days: int = 7,
    log_type: str = "job"
):
    """日志查询页面"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cutoff_date = datetime.now()

    if log_type == "job":
        cursor.execute("""
            SELECT * FROM job_logs
            WHERE created_at >= datetime('now', '-{} days')
            ORDER BY created_at DESC
            LIMIT 100
        """.format(days))
        logs = [dict(row) for row in cursor.fetchall()]
    else:
        cursor.execute("""
            SELECT * FROM push_records
            WHERE push_time >= datetime('now', '-{} days')
            ORDER BY push_time DESC
            LIMIT 100
        """.format(days))
        logs = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": logs,
        "days": days,
        "log_type": log_type
    })


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """系统设置页面"""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "settings": settings
    })


@app.post("/settings/push")
async def update_push_settings(
    push_hour: int = Form(...),
    push_minute: int = Form(...),
    cron_hour: int = Form(...),
    cron_minute: int = Form(...)
):
    """更新推送时间设置"""
    # 这里应该更新配置文件或数据库
    # 简化实现，只打印日志
    logger.info(
        f"更新推送时间：{cron_hour}:{cron_minute:02d}, "
        f"推送时限：{push_hour}:{push_minute:02d}"
    )

    return RedirectResponse(url="/settings", status_code=303)


@app.get("/api/status")
async def api_status():
    """API 状态接口"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 统计信息
    cursor.execute("SELECT COUNT(*) FROM stocks WHERE enabled = 1")
    enabled_stocks = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM job_logs WHERE status = 'success' "
        "AND created_at >= datetime('now', '-1 day')"
    )
    success_jobs_24h = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM job_logs WHERE status = 'failed' "
        "AND created_at >= datetime('now', '-1 day')"
    )
    failed_jobs_24h = cursor.fetchone()[0]

    conn.close()

    return {
        "enabled_stocks": enabled_stocks,
        "success_jobs_24h": success_jobs_24h,
        "failed_jobs_24h": failed_jobs_24h,
        "success_rate": (
            success_jobs_24h / (success_jobs_24h + failed_jobs_24h) * 100
            if (success_jobs_24h + failed_jobs_24h) > 0 else 100
        )
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
