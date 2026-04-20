#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord Bot 本地測試
檢查 Bot 能否正常連接 Discord
"""
import os
import sys

# Windows UTF-8 輸出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
GH_TOKEN = os.environ.get('GH_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO')

print("=" * 60)
print("Discord Bot - 環境檢查")
print("=" * 60)
print()

# 檢查 DISCORD_BOT_TOKEN
if DISCORD_BOT_TOKEN:
    print(f"✅ DISCORD_BOT_TOKEN: 已設定 (長度: {len(DISCORD_BOT_TOKEN)})")
else:
    print("❌ DISCORD_BOT_TOKEN: 未設定")
    print("   請在 .env 檔案中設定 DISCORD_BOT_TOKEN")

# 檢查 GH_TOKEN
if GH_TOKEN:
    print(f"✅ GH_TOKEN: 已設定 (長度: {len(GH_TOKEN)})")
else:
    print("❌ GH_TOKEN: 未設定")
    print("   請在 .env 檔案中設定 GH_TOKEN")

# 檢查 GITHUB_REPO
if GITHUB_REPO:
    print(f"✅ GITHUB_REPO: {GITHUB_REPO}")
else:
    print("⚠️  GITHUB_REPO: 未設定 (將使用預設值)")

print()
print("=" * 60)

# 如果有缺失的環境變數，提醒用戶
if not DISCORD_BOT_TOKEN or not GH_TOKEN:
    print("\n⚠️  發現缺失的環境變數！")
    print("\n請複製 .env.example 為 .env 並填入正確的值：")
    print("  cp .env.example .env")
    print()
    sys.exit(1)

print("✅ 環境檢查通過！")
print()
print("📝 Discord 測試指令：")
print("  !記帳 今天 友方 晚餐炒麵 100")
print("  !記帳 昨天 一銀 南方莊園票券 1390")
print("  !記帳 友方 午餐 -50")
print("  !說明")
print()
print("=" * 60)
print()

# 嘗試導入 Discord 模組
try:
    import discord
    print("✅ discord.py 模組已安裝")
except ImportError:
    print("❌ discord.py 模組未安裝")
    print("   請執行: pip install -r requirements.txt")
    sys.exit(1)

# 檢查是否有 .env 檔案
if os.path.exists('.env'):
    print("✅ .env 檔案存在")
else:
    print("❌ .env 檔案不存在")
    print("   請執行: cp .env.example .env")
    sys.exit(1)

print()
print("=" * 60)
print("準備啟動 Discord Bot...")
print("=" * 60)
print()

# 嘗試啟動 Bot
try:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = discord.Client(intents=intents)

    @bot.event
    async def on_ready():
        print(f"✅ Bot 已上線！")
        print(f"   名稱: {bot.user.name}")
        print(f"   ID: {bot.user.id}")
        print(f"   連接伺服器數: {len(bot.guilds)}")
        print()
        print("🎮 可以在 Discord 中測試以下指令：")
        print("   !記帳 今天 友方 晚餐炒麵 100")
        print("   !記帳 昨天 一銀 南方莊園票券 1390")
        print("   !記帳 友方 午餐 -50")
        print("   !說明")

    bot.run(DISCORD_BOT_TOKEN)
except Exception as e:
    print(f"❌ 啟動失敗: {e}")
    print()
    print("可能的原因：")
    print("1. DISCORD_BOT_TOKEN 不正確")
    print("2. 網路連線問題")
    print("3. Discord 服務暫時無法使用")
    sys.exit(1)
