#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail 通知發送工具
發送預告和結果通知郵件，自動加上 [AI]系統通知 標籤
"""
import os
import sys
import base64
from datetime import datetime
import pytz

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Check for GitHub Actions token
github_token = os.environ.get('GMAIL_TOKEN')
if github_token:
    try:
        token_data = base64.b64decode(github_token).decode('utf-8')
        with open('token_gmail.json', 'w', encoding='utf-8') as f:
            f.write(token_data)
        print("Gmail token loaded from GitHub Secrets")
    except Exception as e:
        print(f"Warning: Failed to decode GitHub token: {e}")

# Configuration
TOKEN_FILE = 'token_gmail.json'
SCOPES = [
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

# 系統通知標籤
SYSTEM_NOTIFICATION_LABEL = '[AI]系統通知'

def get_credentials():
    """Get Google API credentials"""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        print("Error: No valid credentials found.")
        return None

    return creds

def get_system_notification_label_id(service):
    """獲取或建立 [AI]系統通知 標籤 ID"""
    labels = service.users().labels().list(userId='me').execute()

    # 查找現有標籤
    for label in labels.get('labels', []):
        if label['name'] == SYSTEM_NOTIFICATION_LABEL:
            return label['id']

    # 建立新標籤
    try:
        label_body = {
            'name': SYSTEM_NOTIFICATION_LABEL,
            'messageListVisibility': 'show',
            'labelListVisibility': 'labelShow'
        }
        label = service.users().labels().create(userId='me', body=label_body).execute()
        print(f"✓ 建立新標籤: {SYSTEM_NOTIFICATION_LABEL}")
        return label['id']
    except Exception as e:
        print(f"✗ 無法建立標籤 {SYSTEM_NOTIFICATION_LABEL}: {e}")
        return None

def create_message(to, subject, body):
    """建立郵件訊息"""
    from email.mime.text import MIMEText
    import base64

    message = MIMEText(body, 'plain', 'utf-8')
    message['to'] = to
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def send_email(service, to, subject, body, label_id=None):
    """發送郵件並加上標籤"""
    try:
        message = create_message(to, subject, body)

        # 發送郵件
        sent_message = service.users().messages().send(
            userId='me',
            body=message
        ).execute()

        sent_id = sent_message['id']
        print(f"✓ 郵件已發送 (ID: {sent_id})")

        # 加上系統通知標籤
        if label_id:
            service.users().messages().modify(
                userId='me',
                id=sent_id,
                body={
                    'addLabelIds': [label_id]
                }
            ).execute()
            print(f"✓ 已加上標籤: {SYSTEM_NOTIFICATION_LABEL}")

        return sent_id

    except Exception as e:
        print(f"✗ 發送郵件失敗: {e}")
        return None

def get_user_email(service):
    """獲取用戶自己的郵件地址"""
    try:
        profile = service.users().getProfile(userId='me').execute()
        return profile.get('emailAddress')
    except Exception as e:
        print(f"✗ 無法獲取用戶郵件: {e}")
        return None

def send_warning_notification(service, label_id):
    """發送預告通知郵件"""
    taiwan_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taiwan_tz)

    # 計算執行日期
    if now.month == 6:
        execution_date = datetime(now.year, 6, 30, 8, 0, 0, tzinfo=taiwan_tz)
    else:
        execution_date = datetime(now.year, 12, 31, 8, 0, 0, tzinfo=taiwan_tz)

    days_until = (execution_date - now).days

    subject = "[AI]預告：Gmail 自動整理任務即將執行"
    body = f"""您好，

這是一封來自 Gmail Janitor 的預告通知。

【任務預告】
Gmail 自動整理任務將於 {execution_date.strftime('%Y年%m月%d日 %H:%M')} 台灣時間執行。

【執行項目】
1. 掃描收件匣中過去一年的郵件
2. 將郵件分類為四個待審標籤：
   - [AI]待審刪-1.純廣告類 - 電商促銷、行銷活動
   - [AI]待審刪-2.系統通知類 - 超過1個月的不重要登入提醒
   - [AI]待審刪-3.疑似可退訂 - 以前訂閱但現在不看的內容
   - [AI]待審刪-4.垃圾慣犯 - 發送頻率高但從不閱讀的寄件者
3. 從收件匣封存整理的郵件
4. 驗證沒有遺漏的 IMPORTANT 郵件

【重要說明】
- 此任務不會刪除任何郵件
- 所有被標示為 IMPORTANT 的郵件都會被豁免
- 整理後的郵件會移到對應的待審標籤，請您確認後再決定是否刪除
- 您可以隨時在 Gmail 中查看這些標籤下的郵件

【距離執行還有】
{days_until} 天

如有任何疑問，請查看 GitHub Actions 工作流程。

---
此郵件由 Gmail Janitor 自動發送
發送時間: {now.strftime('%Y/%m/%d %H:%M:%S')} 台灣時間
"""

    user_email = get_user_email(service)
    if not user_email:
        print("✗ 無法獲取用戶郵件地址")
        return False

    return send_email(service, user_email, subject, body, label_id) is not None

def send_result_notification(service, label_id, report_path='gmail_janitor_report.json'):
    """發送結果通知郵件"""
    import json

    # 讀取報告
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except Exception as e:
        print(f"✗ 無法讀取報告: {e}")
        return False

    taiwan_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taiwan_tz)

    # 確定是上半年還是下半年
    executed_at = datetime.fromisoformat(report['executed_at'])
    period = "上半年" if executed_at.month == 6 else "下半年"

    subject = f"[AI]報告：Gmail {period}年度自動整理已完成"

    # 產生郵件內容
    body = f"""您好，

Gmail {period}年度自動整理任務已完成。

【執行時間】
開始: {report['executed_at']}
結束: {report['completed_at']}
時長: {report['duration_seconds']:.1f} 秒

【統計數據】
總共掃描: {report['total_scanned']} 封
總共處理: {report['total_processed']} 封
總共跳過: {report['total_skipped']} 封
  - 跳過 IMPORTANT: {report['skipped_important']} 封
  - 跳過白名單: {report['skipped_whitelisted']} 封

【分類結果】
"""

    for label_name, count in report['categories'].items():
        body += f"{label_name}: {count} 封\n"

    body += f"""
【標籤掃描結果】
"""

    for label_name, count in report['label_scan_results'].items():
        body += f"{label_name}: {count} 封\n"

    body += f"""
【驗證結果】
{'✓ 通過 - 所有待審標籤都沒有遺漏的 IMPORTANT 郵件' if report['verification_passed'] else '⚠ 失敗 - 部分待審標籤中仍發現 IMPORTANT 郵件'}

【後續建議】
1. 請在 Gmail 中查看四個待審標籤下的郵件
2. 確認無誤後，您可以選擇刪除這些郵件
3. 如果發現誤判，可以將郵件移回收件匣並移除對應標籤
4. 建議定期檢查這些標籤，避免累積太多郵件

【重要提醒】
- 此任務不會刪除任何郵件
- 所有被標示為 IMPORTANT 的郵件都會被豁免
- 下一次自動整理將於 {'6月30日' if executed_at.month == 12 else '12月31日'} 執行

---
此郵件由 Gmail Janitor 自動發送
發送時間: {now.strftime('%Y/%m/%d %H:%M:%S')} 台灣時間
"""

    user_email = get_user_email(service)
    if not user_email:
        print("✗ 無法獲取用戶郵件地址")
        return False

    return send_email(service, user_email, subject, body, label_id) is not None

def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='Gmail 通知發送工具')
    parser.add_argument('--type', choices=['warning', 'result'], required=True,
                       help='通知類型: warning=預告通知, result=結果通知')
    parser.add_argument('--report', default='gmail_janitor_report.json',
                       help='結果報告檔案路徑 (僅用於 result 類型)')

    args = parser.parse_args()

    print("=" * 60)
    print("Gmail 通知發送工具")
    print("=" * 60)

    # 獲取憑證
    creds = get_credentials()
    if not creds:
        return False

    # 建立服務
    from googleapiclient.discovery import build
    service = build('gmail', 'v1', credentials=creds)

    # 獲取或建立系統通知標籤
    label_id = get_system_notification_label_id(service)
    if not label_id:
        print("✗ 無法獲取系統通知標籤")
        return False

    # 發送通知
    success = False
    if args.type == 'warning':
        print("\n發送預告通知...")
        success = send_warning_notification(service, label_id)
    else:
        print("\n發送結果通知...")
        success = send_result_notification(service, label_id, args.report)

    print("\n" + "=" * 60)
    if success:
        print("✓ 通知發送成功")
    else:
        print("✗ 通知發送失敗")
    print("=" * 60)

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
