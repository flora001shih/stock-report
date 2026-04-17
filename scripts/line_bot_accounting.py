#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LINE Bot 記帳處理腳本
接收來自 LINE Bot 的記帳請求並寫入 Google Sheets
"""
import os
import sys
import json
import argparse
import base64
from datetime import datetime
import pytz

# Windows UTF-8 輸出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 解碼 Google Credentials
google_creds = os.environ.get('GOOGLE_CREDENTIALS', '')
if google_creds:
    try:
        creds_data = base64.b64decode(google_creds).decode('utf-8')
        with open('flora-gae11-48f2f2e53de7.json', 'w', encoding='utf-8') as f:
            f.write(creds_data)
    except:
        pass

# Google Sheets 設定
SPREADSHEET_ID = '1J-Ia3CLNJxGL26zacWdj-85jsK_5NaS92OZRhoOyzUA'
SHEET_NAME = '家用記帳合併'
CREDENTIALS_FILE = 'flora-gae11-48f2f2e53de7.json'

# 月份欄位對應表
MONTH_COLUMNS = {
    1:  {'友方': ('ED', 'EG'), '一銀': ('EH', 'EK'), '昇華': ('EL', 'EO')},
    2:  {'友方': ('DR', 'DT'), '一銀': ('DV', 'DX'), '昇華': ('DZ', 'EB')},
    3:  {'友方': ('DF', 'DI'), '一銀': ('DJ', 'DM'), '昇華': ('DN', 'DQ')},
    4:  {'友方': ('CT', 'CW'), '一銀': ('CX', 'DA'), '昇華': ('DB', 'DE')},
    5:  {'友方': ('CH', 'CK'), '一銀': ('CL', 'CP'), '昇華': ('CR', 'CS')},
    6:  {'友方': ('BV', 'BW'), '一銀': ('BX', 'CB'), '昇華': ('CC', 'CG')},
    7:  {'友方': ('BJ', 'BM'), '一銀': ('BN', 'BR'), '昇華': ('BT', 'BU')},
    8:  {'友方': ('AX', 'BA'), '一銀': ('BB', 'BG'), '昇華': ('BH', 'BI')},
    9:  {'友方': ('AL', 'AO'), '一銀': ('AR', 'AV'), '昇華': ('AW', 'AW')},
    10: {'友方': ('Z', 'AC'),  '一銀': ('AD', 'AH'),  '昇華': ('AI', 'AK')},
    11: {'友方': ('N', 'Q'),   '一銀': ('R', 'V'),   '昇華': ('W', 'Y')},
    12: {'友方': ('B', 'E'),   '一銀': ('F', 'I'),   '昇華': ('J', 'M')},
}

# 人物名稱對應
PERSON_MAP = {
    '友方': '友方',
    '一銀': '家庭一銀刷卡',
    '昇華': '昇華',
}

# 初始化 Google Sheets API
def get_sheets_service():
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    if not os.path.exists(CREDENTIALS_FILE):
        print("錯誤: 找不到 Google Credentials 檔案")
        return None

    creds = Credentials.from_service_account_file(CREDENTIALS_FILE)
    service = build('sheets', 'v4', credentials=creds)
    return service


# 解析日期
def parse_date(date_str):
    """解析日期字串，返回 (年, 月, 日)"""
    taiwan_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taiwan_tz)

    if not date_str or date_str in ['今天', '今日']:
        return now.year, now.month, now.day

    # 昨天
    if date_str in ['昨天', '昨日']:
        from datetime import timedelta
        yesterday = now - timedelta(days=1)
        return yesterday.year, yesterday.month, yesterday.day

    # 明天
    if date_str == '明天':
        from datetime import timedelta
        tomorrow = now + timedelta(days=1)
        return tomorrow.year, tomorrow.month, tomorrow.day

    # 支援多種格式: 2026/04/17, 2026/4/17, 04/17, 4/17
    parts = date_str.replace('/', '-').split('-')

    if len(parts) == 3:
        # 完整日期: YYYY-MM-DD
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    elif len(parts) == 2:
        # 僅月日: MM-DD (假設當年)
        year = now.year
        month, day = int(parts[0]), int(parts[1])
    else:
        return None, None, None

    return year, month, day


# 解析記帳訊息
def parse_accounting_message(message):
    """解析記帳訊息，返回 (人物, 明細, 金額, 日期, date_str原文)"""
    # 基本格式: "記帳 人物 明細 金額 [日期]"
    # 範例: "記帳 友方 午餐 -150"
    # 範例: "記帳 一銀 南方莊園一日遊票券 1390 今天"
    # 範例: "記帳 昇華 晚餐 -200 昨天" (記到昨天的月份欄位)
    # ⚠️ 重要: 日期決定了記帳位置（哪個月份的欄位）

    # 移除記帳關鍵字
    msg = message
    for keyword in ['記帳', '幫我記帳', '幫我記錄']:
        msg = msg.replace(keyword, '').strip()

    # 簡單分詞（根據空格分割）
    parts = msg.split()

    if len(parts) < 3:
        return None, None, None, None, None

    # 解析人物
    person = parts[0]
    if person not in PERSON_MAP:
        # 嘗試別名
        if person == '家庭一銀刷卡':
            person = '一銀'
        elif person not in PERSON_MAP:
            return None, None, None, None, None

    # 解析金額（最後一個數字）
    amount = None
    for i in range(len(parts) - 1, 0, -1):
        if parts[i].replace('-', '').replace('+', '').isdigit():
            amount = int(parts[i])
            break

    if amount is None:
        return None, None, None, None, None

    # 解析明細（人物後到金額前）
    detail = ' '.join(parts[1:parts.index(str(amount))]) if str(amount) in parts else ''

    # 解析日期（檢查是否包含日期關鍵字）
    date_str = None
    date_keywords = ['今天', '今日', '明天', '昨天', '昨日']
    for keyword in date_keywords:
        if keyword in msg:
            date_str = keyword
            break

    # 檢查日期格式 (YYYY/MM/DD 或 MM/DD)
    import re
    date_pattern = r'\d{1,4}[/-]\d{1,2}[/-]\d{1,2}'
    date_match = re.search(date_pattern, msg)
    if date_match:
        date_str = date_match.group().replace('/', '-')

    # 如果沒有指定日期，預設為「今天」
    if date_str is None:
        date_str = '今天'

    # 解析日期
    year, month, day = parse_date(date_str)
    if year is None:
        return None, None, None, None, None

    return person, detail, amount, (year, month, day), date_str


# 尋找空白列
def find_empty_row(service, spreadsheet_id, range_name):
    """尋找指定範圍內的第一個空白列（第 15-49 列）"""
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    # 檢查第 15-49 列
    for i in range(14, min(49, len(values))):
        if not values[i] or all(not cell.strip() for cell in values[i]):
            return i + 1  # 返回 1-based 列號

    # 如果都填滿了
    return None


# 寫入記帳資料
def write_expense(service, person, detail, amount, date, date_str_original):
    """寫入記帳資料到 Google Sheets"""
    year, month, day = date

    # 檢查月份對應
    if month not in MONTH_COLUMNS:
        return False, f"不支援的月份: {month}"

    # 獲取欄位
    person_full = PERSON_MAP.get(person, person)
    if person_full not in MONTH_COLUMNS[month]:
        return False, f"不支援的人物: {person_full}"

    date_col, amount_col = MONTH_COLUMNS[month][person_full]

    # 構建範圍
    range_name = f"{SHEET_NAME}!{date_col}15:{amount_col}49"
    empty_row = find_empty_row(service, SPREADSHEET_ID, range_name)

    if empty_row is None:
        return False, f"該人物（{person_full}）已經沒有空白處可填"

    # 準備寫入資料
    date_value = f"{year}/{month}/{day}"
    values = [[date_value, detail, str(amount), '']]

    # 寫入
    update_range = f"{SHEET_NAME}!{date_col}{empty_row}:{amount_col}{empty_row}"
    body = {'values': values}

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=update_range,
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

    # 顯示清楚的月份資訊
    month_text = f"{month}月"

    return True, f"✅ 記帳成功！\n\n📅 日期: {date_value} ({date_str_original})\n🗓️ 月份: {month_text}\n👤 人物: {person_full}\n📝 明細: {detail}\n💰 金額: {amount}"


def main():
    parser = argparse.ArgumentParser(description='LINE Bot 記帳處理')
    parser.add_argument('--user-id', required=True, help='使用者 ID')
    parser.add_argument('--display-name', required=True, help='顯示名稱')
    parser.add_argument('--message', required=True, help='訊息內容')

    args = parser.parse_args()

    print(f"========================================")
    print(f"記帳請求來自: {args.display_name} ({args.user_id})")
    print(f"訊息內容: {args.message}")
    print(f"========================================")

    # 解析記帳訊息
    person, detail, amount, date, date_str_original = parse_accounting_message(args.message)

    if person is None:
        result = {
            'success': False,
            'error': '無法解析記帳訊息',
            'message': args.message
        }
        print("❌ 無法解析記帳訊息")
        print("\n正確格式範例：")
        print("• 記帳 友方 午餐 -150              (預設今天)")
        print("• 記帳 一銀 南方莊園票券 1390 今天 (記到今天)")
        print("• 記帳 昇華 晚餐 -200 昨天       (記到昨天的月份欄位)")
        print("• 記帳 友方 早餐 -50 2026/04/16   (記到指定日期)")
        print("\n⚠️ 重要提示：")
        print("• 日期決定了記帳位置（哪個月份的欄位）")
        print("• 如果記「昨天」，會記到昨天的月份欄位")
        print("• 不指定日期預設為「今天」")
    else:
        # 寫入 Google Sheets
        service = get_sheets_service()
        if service is None:
            result = {
                'success': False,
                'error': '無法連接 Google Sheets'
            }
            print("❌ 無法連接 Google Sheets")
        else:
            success, message = write_expense(service, person, detail, amount, date, date_str_original)
            result = {
                'success': success,
                'message': message,
                'person': person,
                'detail': detail,
                'amount': amount,
                'date': date
            }
            print(message)

    # 保存結果到 JSON
    with open('accounting_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 返回狀態
    if result.get('success'):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
