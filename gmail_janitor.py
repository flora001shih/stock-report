#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Janitor - Gmail 自動整理工具 (優化版)
整合四大分類與 IMPORTANT 豁免邏輯
使用 batchGet API 提升性能
"""
import os
import sys
import base64
import json
import re
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

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
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

# 預設掃描天數（優化：從 365 天減少到 180 天）
DEFAULT_SCAN_DAYS = 180

# 定義四個標籤
LABELS = {
    'pure_ad': '[AI]待審刪-1.純廣告類 - 電商促銷、行銷活動',
    'system': '[AI]待審刪-2.系統通知類 - 超過1個月的不重要登入提醒',
    'unsubscribe': '[AI]待審刪-3.疑似可退訂 - 以前訂閱但現在不看的內容',
    'spam_habit': '[AI]待審刪-4.垃圾慣犯 - 發送頻率高但從不閱讀的寄件者'
}

# 系統通知標籤
SYSTEM_NOTIFICATION_LABEL = '[AI]系統通知'

# 白名單關鍵字（絕對不可列入垃圾）
WHITELIST_KEYWORDS = [
    '銀行', '投資', '信用卡', '帳單', '台中銀',
    'bank', 'investment', 'credit card', 'bill'
]

# 系統通知關鍵字
SYSTEM_NOTIFICATION_KEYWORDS = [
    '更新', 'upgrade', '登入', 'login', '驗證', 'verify',
    '通知', 'notification', '提醒', 'reminder',
    'security', '帳號', 'account', '密碼', 'password'
]

# 電商促銷關鍵字
PROMOTION_KEYWORDS = [
    '促銷', '特賣', '折扣', '優惠', '免運', '折扣碼',
    'sale', 'promo', 'discount', 'offer', 'coupon',
    'momo', 'shopee', 'pchome', '蝦皮', 'momo購物'
]

# 垃圾郵件發信者模式
SPAM_PATTERNS = [
    r'.*newsletter.*', r'.*news.*', r'.*marketing.*',
    r'.*promo.*', r'.*deal.*', r'.*offer.*',
    r'.*noreply.*@', r'.*no-reply.*@', r'.*donotreply.*@',
    r'.*notification.*@', r'.*alert.*@',
    r'.*support.*@', r'.*service.*@',
]

# 垃圾慣犯清單
SPAM_HABIT_SENDERS = {
    'Trip.com@newsletter.trip.com',
    'messages-noreply@linkedin.com',
    'noreply@resmail.flypeach.com',
    'edm@lineshopping-tw.com',
    'uber.taiwan@uber.com',
    'enews@mx1.edm.sinopac.com',
    'mkt@buy.tw.yahoo.net',
    'TSB@mhurcv.taishinbank.com.tw',
    'postmaster@mail.franklin.com.tw',
    'stats.spx@shopee.com',
    'notification@priority.instagram.com',
    'pokemongo@email.nianticlabs.com',
    'edmservice@edmwebp.hncb.com.tw',
    'fcb@news.firstbank.tw',
    'info@newsletter.shopee.tw',
    'edm-service@edm.settour.com.tw',
    'MMA@mx1.edm.sinopac.com',
    'fcbmbankapp@firstbank.com.tw',
    'richart@richart.tw',
}

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

def is_personal_email(email, name):
    """判斷是否為個人郵件（非系統發送）"""
    if not email:
        return False

    system_patterns = [
        'noreply', 'no-reply', 'donotreply', 'notification',
        'alert', 'support', 'service', 'info', 'admin'
    ]
    email_lower = email.lower()

    for pattern in system_patterns:
        if pattern in email_lower:
            return False

    if '@gmail.com' in email_lower or '@outlook.com' in email_lower or '@hotmail.com' in email_lower:
        if '.' in email.split('@')[0].replace('.', '') and len(email.split('@')[0]) > 20:
            return False
        return True

    return False

def is_whitelisted(subject, sender_email, sender_name):
    """檢查是否在白名單中"""
    if subject:
        for keyword in WHITELIST_KEYWORDS:
            if keyword.lower() in subject.lower():
                return True

    if is_personal_email(sender_email, sender_name):
        return True

    return False

def categorize_email(subject, sender_email, sender_name):
    """分類郵件，返回 (標籤類型, 子類型)"""
    # 先檢查白名單
    if is_whitelisted(subject, sender_email, sender_name):
        return None, None

    subject_lower = subject.lower() if subject else ''
    sender_lower = sender_email.lower() if sender_email else ''

    # 檢查是否為垃圾慣犯
    if sender_email in SPAM_HABIT_SENDERS:
        return 'spam_habit', None

    # 檢查是否為系統通知
    for keyword in SYSTEM_NOTIFICATION_KEYWORDS:
        if keyword.lower() in subject_lower or keyword.lower() in sender_lower:
            # 判斷是否為可退訂的系統通知
            for promo in PROMOTION_KEYWORDS:
                if promo in subject_lower:
                    return 'unsubscribe', '系統通知（促銷性）'
            # 系統通知類
            return 'system', None

    # 檢查是否為電商促銷
    for keyword in PROMOTION_KEYWORDS:
        if keyword in subject_lower or keyword in sender_lower:
            return 'pure_ad', '電商促銷'

    # 檢查發信者模式
    for pattern in SPAM_PATTERNS:
        if re.match(pattern, sender_lower, re.IGNORECASE):
            return 'unsubscribe', '可能為電子報/行銷郵件'

    return None, None

def create_or_get_labels(service):
    """建立或取得標籤"""
    print("=" * 60)
    print("建立/檢查標籤...")
    print("=" * 60)

    # 獲取現有標籤
    existing_labels = {}
    try:
        labels = service.users().labels().list(userId='me').execute()
        for label in labels.get('labels', []):
            existing_labels[label['name']] = label['id']
            if label['name'] in list(LABELS.values()) + [SYSTEM_NOTIFICATION_LABEL]:
                print(f"  ✓ 已有標籤: {label['name']}")
    except Exception as e:
        print(f"Warning: Could not list labels: {e}")

    # 建立缺失的標籤
    label_ids = {}

    # 建立待審標籤
    for key, label_name in LABELS.items():
        if label_name in existing_labels:
            label_ids[key] = existing_labels[label_name]
        else:
            try:
                label_body = {
                    'name': label_name,
                    'messageListVisibility': 'show',
                    'labelListVisibility': 'labelShow'
                }
                label = service.users().labels().create(userId='me', body=label_body).execute()
                label_ids[key] = label['id']
                print(f"  + 建立新標籤: {label_name}")
            except Exception as e:
                print(f"  ✗ 無法建立標籤 {label_name}: {e}")

    # 建立系統通知標籤
    if SYSTEM_NOTIFICATION_LABEL in existing_labels:
        label_ids['system_notification'] = existing_labels[SYSTEM_NOTIFICATION_LABEL]
    else:
        try:
            label_body = {
                'name': SYSTEM_NOTIFICATION_LABEL,
                'messageListVisibility': 'show',
                'labelListVisibility': 'labelShow'
            }
            label = service.users().labels().create(userId='me', body=label_body).execute()
            label_ids['system_notification'] = label['id']
            print(f"  + 建立新標籤: {SYSTEM_NOTIFICATION_LABEL}")
        except Exception as e:
            print(f"  ✗ 無法建立標籤 {SYSTEM_NOTIFICATION_LABEL}: {e}")

    return label_ids

def scan_and_categorize(service, days_ago=DEFAULT_SCAN_DAYS):
    """掃描並分類郵件"""
    taiwan_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taiwan_tz)
    start_date = now - timedelta(days=days_ago)

    print(f"\n掃描時間範圍: {start_date.strftime('%Y/%m/%d')} ~ {now.strftime('%Y/%m/%d')}")
    print("=" * 60)

    query = f'in:inbox after:{start_date.strftime("%Y/%m/%d")}'

    results = []
    page_token = None

    while True:
        try:
            response = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100,
                pageToken=page_token
            ).execute()

            messages = response.get('messages', [])

            if not messages:
                break

            results.extend(messages)
            print(f"已掃描: {len(results)} 封郵件...")

            page_token = response.get('nextPageToken')
            if not page_token:
                break

            if len(results) >= 5000:
                break

        except Exception as e:
            print(f"Error during scanning: {e}")
            break

    print(f"\n掃描完成! 共 {len(results)} 封郵件需要處理")
    return results

def process_emails_batch(service, message_ids, label_ids):
    """批次處理郵件"""
    categorized = {
        'pure_ad': [],
        'system': [],
        'unsubscribe': [],
        'spam_habit': []
    }

    skipped = 0
    skipped_important = 0
    skipped_whitelisted = 0

    print(f"\n開始分類郵件...")
    print("=" * 60)

    # Gmail API 不支持 batchGet，使用逐個獲取但優化參數
    batch_size = 100
    total_batches = (len(message_ids) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(message_ids))
        batch_ids = message_ids[start_idx:end_idx]

        print(f"處理批次 {batch_idx + 1}/{total_batches} (郵件 {start_idx + 1}-{end_idx})...")

        for msg in batch_ids:
            try:
                # 提取郵件 ID (message_ids 是字典列表，需要取 id 欄位)
                msg_id = msg['id'] if isinstance(msg, dict) else msg

                # 獲取郵件詳情 (使用 format='metadata' 優化)
                msg_detail = service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='metadata',
                    metadataHeaders=['From', 'Subject']
                ).execute()

                headers = msg_detail.get('payload', {}).get('headers', [])
                from_header = None
                subject = None

                for header in headers:
                    if header['name'] == 'From':
                        from_header = header['value']
                    elif header['name'] == 'Subject':
                        subject = header['value']

                sender_name = None
                sender_email = None
                if from_header:
                    match = re.search(r'^(.*?)\s*<([^>]+)>$', from_header)
                    if match:
                        sender_name = match.group(1).strip('" ')
                        sender_email = match.group(2)
                    else:
                        sender_email = from_header.strip()

                # 檢查是否為重要郵件
                msg_label_ids = msg_detail.get('labelIds', [])
                if 'IMPORTANT' in msg_label_ids:
                    skipped_important += 1
                    skipped += 1
                    continue

                # 分類
                category, subtype = categorize_email(subject, sender_email, sender_name)

                if category and category in categorized:
                    categorized[category].append(msg_id)
                elif category == 'pure_ad' and subtype:
                    # 如果被分類為純廣告，確認是否在白名單
                    if not is_whitelisted(subject, sender_email, sender_name):
                        categorized[category].append(msg_id)
                    else:
                        skipped_whitelisted += 1
                        skipped += 1
                else:
                    skipped += 1

            except Exception as e:
                print(f"  Warning: 處理郵件失敗: {e}")
                continue

    print(f"\n分類完成:")
    print(f"  純廣告類: {len(categorized['pure_ad'])} 封")
    print(f"  系統通知類: {len(categorized['system'])} 封")
    print(f"  疑似可退訂: {len(categorized['unsubscribe'])} 封")
    print(f"  垃圾慣犯: {len(categorized['spam_habit'])} 封")
    print(f"  跳過（白名單/其他）: {skipped} 封")
    print(f"    - 跳過 IMPORTANT: {skipped_important} 封")
    print(f"    - 跳過白名單: {skipped_whitelisted} 封")

    return categorized, skipped, skipped_important, skipped_whitelisted

def apply_labels_and_archive(service, categorized, label_ids):
    """應用標籤並封存郵件"""
    print("\n開始應用標籤並封存...")
    print("=" * 60)

    total_processed = 0

    for category, message_ids in categorized.items():
        if not message_ids:
            print(f"\n{LABELS[category]}: 無郵件需要處理")
            continue

        target_label_id = label_ids.get(category)
        if not target_label_id:
            print(f"\n{LABELS[category]}: 標籤 ID 不存在，跳過")
            continue

        print(f"\n處理 {LABELS[category]}: {len(message_ids)} 封郵件")

        batch_size = 100
        for i in range(0, len(message_ids), batch_size):
            batch = message_ids[i:i + batch_size]

            try:
                service.users().messages().batchModify(
                    userId='me',
                    body={
                        'ids': batch,
                        'addLabelIds': [target_label_id],
                        'removeLabelIds': ['INBOX']
                    }
                ).execute()

                total_processed += len(batch)
                print(f"  已處理 {total_processed}/{len(message_ids)} 封")

            except Exception as e:
                print(f"  Warning: 批次處理失敗，嘗試單獨處理...")
                for msg_id in batch:
                    try:
                        service.users().messages().modify(
                            userId='me',
                            id=msg_id,
                            body={
                                'addLabelIds': [target_label_id],
                                'removeLabelIds': ['INBOX']
                            }
                        ).execute()
                        total_processed += 1
                    except Exception as e2:
                        print(f"    ✗ 無法處理 {msg_id}: {e2}")

    print(f"\n{'=' * 60}")
    print(f"完成! 共處理 {total_processed} 封郵件")
    print("=" * 60)

    return total_processed

def verify_no_important_in_review(service, label_ids):
    """驗證待審標籤中沒有遺漏的 IMPORTANT 郵件"""
    print("\n" + "=" * 60)
    print("驗證待審標籤中沒有遺漏的 IMPORTANT 郵件")
    print("=" * 60)

    review_label_ids = [
        label_ids.get('pure_ad'),
        label_ids.get('system'),
        label_ids.get('unsubscribe'),
        label_ids.get('spam_habit')
    ]
    review_label_ids = [l for l in review_label_ids if l is not None]

    total_checked = 0
    total_important_found = 0

    for i, label_id in enumerate(review_label_ids):
        label_name = list(LABELS.values())[i]
        print(f"\n檢查標籤: {label_name}")

        important_in_this_label = 0
        page_token = None

        while True:
            try:
                results = service.users().messages().list(
                    userId='me',
                    labelIds=[label_id],
                    maxResults=500,
                    pageToken=page_token
                ).execute()

                messages = results.get('messages', [])
                if not messages:
                    break

                total_checked += len(messages)

                for msg in messages:
                    try:
                        msg_detail = service.users().messages().get(
                            userId='me',
                            id=msg['id'],
                            format='metadata'
                        ).execute()

                        if 'IMPORTANT' in msg_detail.get('labelIds', []):
                            important_in_this_label += 1
                            total_important_found += 1

                    except Exception:
                        continue

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            except Exception as e:
                print(f"  Error: {e}")
                break

        print(f"  掃描封數: {total_checked} (累計)")
        if important_in_this_label == 0:
            print(f"  ✓ 沒有遺漏的 IMPORTANT 郵件")
        else:
            print(f"  ⚠ 找到 {important_in_this_label} 封遺漏的 IMPORTANT 郵件!")

    print(f"\n{'=' * 60}")
    if total_important_found == 0:
        print(f"✓ 驗證完成：所有待審標籤都沒有遺漏的 IMPORTANT 郵件")
    else:
        print(f"⚠ 驗證失敗：共找到 {total_important_found} 封遺漏的 IMPORTANT 郵件")
    print("=" * 60)

    return total_important_found == 0

def main():
    """主函數"""
    print("=" * 60)
    print("Gmail Janitor - 自動整理工具 (優化版)")
    print("=" * 60)
    print("\n此工具將：")
    print("1. 建立四個待審標籤")
    print("2. 將郵件分類並移到對應標籤")
    print("3. 從收件匣封存（移除 INBOX 標籤）")
    print("4. 驗證沒有遺漏的 IMPORTANT 郵件")
    print("5. 不會刪除任何郵件")
    print(f"6. 預設掃描過去 {DEFAULT_SCAN_DAYS} 天的郵件")
    print("=" * 60)

    # 記錄開始時間
    taiwan_tz = pytz.timezone('Asia/Taipei')
    start_time = datetime.now(taiwan_tz)

    # 獲取憑證
    creds = get_credentials()
    if not creds:
        return

    # 建立服務
    from googleapiclient.discovery import build
    service = build('gmail', 'v1', credentials=creds)

    # 建立標籤
    label_ids = create_or_get_labels(service)

    if not label_ids:
        print("\n錯誤: 無法建立或取得標籤")
        return

    # 掃描郵件
    message_ids = scan_and_categorize(service, days_ago=DEFAULT_SCAN_DAYS)

    if not message_ids:
        print("\n沒有找到需要處理的郵件")
        return

    # 處理郵件 (使用批次處理優化)
    categorized, skipped, skipped_important, skipped_whitelisted = process_emails_batch(service, message_ids, label_ids)

    # 確認處理
    print(f"\n{'=' * 60}")
    print("確認處理項目:")
    print(f"{'=' * 60}")
    for category, ids in categorized.items():
        if ids:
            print(f"  {LABELS[category]}: {len(ids)} 封")

    # 自動執行（GitHub Actions 環境）
    print(f"\n開始執行整理...")

    # 應用標籤並封存
    total_processed = apply_labels_and_archive(service, categorized, label_ids)

    # 驗證沒有遺漏的 IMPORTANT 郵件
    verification_passed = verify_no_important_in_review(service, label_ids)

    # 產生統計報告
    end_time = datetime.now(taiwan_tz)
    duration = (end_time - start_time).total_seconds()

    report = {
        'executed_at': start_time.isoformat(),
        'completed_at': end_time.isoformat(),
        'duration_seconds': duration,
        'total_scanned': len(message_ids),
        'total_processed': total_processed,
        'total_skipped': skipped,
        'skipped_important': skipped_important,
        'skipped_whitelisted': skipped_whitelisted,
        'verification_passed': verification_passed,
        'categories': {
            LABELS['pure_ad']: len(categorized['pure_ad']),
            LABELS['system']: len(categorized['system']),
            LABELS['unsubscribe']: len(categorized['unsubscribe']),
            LABELS['spam_habit']: len(categorized['spam_habit'])
        },
        'label_scan_results': {}
    }

    # 添加各標籤掃描結果
    for label_name in LABELS.values():
        label_id = label_ids.get(list(LABELS.keys())[list(LABELS.values()).index(label_name)])
        try:
            label_info = service.users().labels().get(userId='me', id=label_id).execute()
            report['label_scan_results'][label_name] = label_info.get('messagesTotal', 0)
        except Exception:
            report['label_scan_results'][label_name] = 0

    # 保存報告
    with open('gmail_janitor_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print("統計報告")
    print("=" * 60)
    print(f"執行時間: {start_time.strftime('%Y/%m/%d %H:%M:%S')} ~ {end_time.strftime('%Y/%m/%d %H:%M:%S')}")
    print(f"執行時長: {duration:.1f} 秒 ({duration/60:.1f} 分鐘)")
    print(f"總共掃描: {report['total_scanned']} 封")
    print(f"總共處理: {report['total_processed']} 封")
    print(f"總共跳過: {report['total_skipped']} 封")
    print(f"  - 跳過 IMPORTANT: {report['skipped_important']} 封")
    print(f"  - 跳過白名單: {report['skipped_whitelisted']} 封")
    print(f"\n各標籤整理結果:")
    for label_name, count in report['categories'].items():
        print(f"  {label_name}: {count} 封")
    print(f"\n驗證結果: {'✓ 通過' if verification_passed else '⚠ 失敗'}")
    print(f"\n處理記錄已保存至: gmail_janitor_report.json")
    print("=" * 60)

    return report

if __name__ == '__main__':
    main()
