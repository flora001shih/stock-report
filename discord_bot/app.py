#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord Bot - 家用記帳
接收 Discord 訊息並觸發 GitHub Actions
"""
import os
import sys

# Windows UTF-8 輸出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import json
import hmac
import hashlib
import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# Discord 設定
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

# GitHub 設定
GH_TOKEN = os.environ.get('GH_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'flora-wu/C--Claude-Test-Lab')

# Discord Bot 設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


def trigger_github_action(user_id, display_name, message_text):
    """觸發 GitHub Actions 工作流"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
    payload = {
        "event_type": "accounting_request",
        "client_payload": {
            "user_id": str(user_id),
            "display_name": display_name,
            "message": message_text,
            "timestamp": int(__import__('time').time())
        }
    }

    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 204:
            return True, "已成功觸發記帳流程"
        else:
            return False, f"觸發失敗: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"觸發時發生錯誤: {str(e)}"


@bot.event
async def on_ready():
    """Bot 啟動時執行"""
    print(f"✅ {bot.user.name} 已上線！")
    print(f"📱 Discord ID: {bot.user.id}")
    print(f"📊 正在監聽 {len(bot.guilds)} 個伺服器")


@bot.event
async def on_command_error(ctx, error):
    """指令錯誤處理"""
    if isinstance(error, commands.CommandNotFound):
        pass  # 忽略不存在的指令
    else:
        print(f"❌ 指令錯誤: {error}")


@bot.command(name='記帳', aliases=['jizhang', 'accounting'])
async def accounting(ctx, date: str = None, person: str = None, detail: str = None, amount: int = None):
    """
    記帳指令
    格式: !記帳 [日期] [人物] [明細] [金額]

    範例:
    !記帳 今天 友方 晚餐炒麵 100
    !記帳 昨天 一銀 南方莊園票券 1390
    !記帳 友方 午餐 -50
    """

    # 如果沒有提供所有參數，顯示幫助
    if not all([person, detail, amount is not None]):
        help_text = """📝 **記帳指令說明**

**格式：**
`!記帳 [日期] [人物] [明細] [金額]`

**範例：**
• `!記帳 今天 友方 晚餐炒麵 100`
• `!記帳 昨天 一銀 南方莊園票券 1390`
• `!記帳 友方 午餐 -50` (日期預設今天)

**支援人物：**
• 友方
• 一銀
• 昇華

**日期：**
• `今天` 或 `今日` - 預設
• `昨天` 或 `昨日`
• `明天`
• `YYYY/MM/DD` - 指定日期

**⚠️ 重要：**
• 日期決定記帳位置（哪個月份欄位）
• 例如：今天是 5 月 1 日，記「昨天」會記到 4 月欄位
"""
        await ctx.send(help_text)
        return

    # 預設日期為今天
    if not date:
        date = "今天"

    # 構建記帳訊息
    message_text = f"記帳 {person} {detail} {amount} {date}"

    # 取得使用者資訊
    user_id = ctx.author.id
    display_name = ctx.author.display_name

    print(f"📩 收到記帳請求: {message_text}")
    print(f"👤 來自: {display_name} (ID: {user_id})")

    # 發送處理中訊息
    processing_msg = await ctx.send("📝 正在處理您的記帳請求，請稍候...")

    # 觸發 GitHub Actions
    success, message = trigger_github_action(user_id, display_name, message_text)

    # 更新回覆訊息
    if success:
        reply_text = f"""✅ **記帳請求已送出！**

📅 日期: {date}
👤 人物: {person}
📝 明細: {detail}
💰 金額: {amount}

執行結果將會通知您。
"""
    else:
        reply_text = f"""❌ **記帳請求失敗**

錯誤訊息: {message}

請稍後再試或聯絡管理員。
"""

    await processing_msg.edit(content=reply_text)


@bot.command(name='說明', aliases=['usage', 'info'])
async def show_help(ctx):
    """顯示幫助訊息"""
    help_text = """👋 **歡迎使用家用記帳 Discord Bot！**

**📝 使用方法：**

**記帳指令：**
`!記帳 [日期] [人物] [明細] [金額]`

**範例：**
• `!記帳 今天 友方 晚餐炒麵 100`
• `!記帳 昨天 一銀 南方莊園票券 1390`
• `!記帳 友方 午餐 -50` (日期預設今天)

**支援人物：**
• 友方
• 一銀
• 昇華

**日期：**
• `今天` / `今日` - 預設
• `昨天` / `昨日`
• `明天`
• `YYYY/MM/DD` - 指定日期

**⚠️ 重要：**
• 日期決定記帳位置（哪個月份欄位）
• 例如：今天是 5 月 1 日，記「昨天」會記到 4 月欄位
• 不指定日期預設為「今天」

**📚 其他指令：**
• `!說明` - 顯示此幫助訊息
• `!記帳` - 顯示記帳指令說明

---
資料會自動同步到您的 Google Sheets 📊
"""
    await ctx.send(help_text)


@bot.event
async def on_message(message):
    """處理所有訊息"""
    # 忽略 Bot 自己的訊息
    if message.author.bot:
        return

    # 處理指令
    await bot.process_commands(message)


if __name__ == '__main__':
    # 檢查 Token
    if not DISCORD_BOT_TOKEN:
        print("❌ 錯誤: 請設定 DISCORD_BOT_TOKEN 環境變數")
        exit(1)

    # 檢查 GitHub Token
    if not GH_TOKEN:
        print("❌ 錯誤: 請設定 GH_TOKEN 環境變數")
        exit(1)

    print("🚀 啟動 Discord Bot...")
    bot.run(DISCORD_BOT_TOKEN)
