#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地測試 LINE Bot 記帳功能
"""
import os
import sys
import subprocess

# 切換到專案根目錄
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("LINE Bot 記帳 - 本地測試")
print("=" * 60)

# 測試用例
test_cases = [
    {
        "name": "基本記帳 - 友方午餐",
        "user_id": "test_user_001",
        "display_name": "測試使用者",
        "message": "記帳 友方 午餐 -150"
    },
    {
        "name": "記帳 - 一銀票券（含日期）",
        "user_id": "test_user_002",
        "display_name": "一銀測試",
        "message": "記帳 一銀 南方莊園一日遊票券 1390 今天"
    },
    {
        "name": "記帳 - 昇華退費",
        "user_id": "test_user_003",
        "display_name": "昇華測試",
        "message": "記帳 昇華 自带杯退费 +5"
    },
    {
        "name": "記帳 - 指定日期",
        "user_id": "test_user_004",
        "display_name": "日期測試",
        "message": "記帳 友方 晚餐 -200 2026/04/17"
    },
]

results = []

for i, test in enumerate(test_cases, 1):
    print(f"\n[{i}/{len(test_cases)}] 測試: {test['name']}")
    print(f"訊息: {test['message']}")

    # 執行記帳腳本
    cmd = [
        sys.executable,
        'scripts/line_bot_accounting.py',
        '--user-id', test['user_id'],
        '--display-name', test['display_name'],
        '--message', test['message']
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        success = result.returncode == 0
        output = result.stdout

        if success:
            print(f"✅ 成功")
            print(f"輸出: {output.strip()}")
        else:
            print(f"❌ 失敗")
            print(f"錯誤: {result.stderr}")

        results.append({
            "name": test['name'],
            "success": success,
            "output": output
        })

    except subprocess.TimeoutExpired:
        print("⏱️ 超時")
        results.append({
            "name": test['name'],
            "success": False,
            "output": "執行超時"
        })
    except Exception as e:
        print(f"💥 錯誤: {str(e)}")
        results.append({
            "name": test['name'],
            "success": False,
            "output": str(e)
        })

# 總結
print("\n" + "=" * 60)
print("測試總結")
print("=" * 60)

passed = sum(1 for r in results if r['success'])
total = len(results)

print(f"通過: {passed}/{total}")

for r in results:
    status = "✅" if r['success'] else "❌"
    print(f"{status} {r['name']}")

print("\n請檢查你的 Google Sheets 確認記帳是否成功寫入。")
print("=" * 60)
