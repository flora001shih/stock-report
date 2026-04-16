#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美股股市報告 - 每日早上6點發送道瓊指數和台積電ADR漲跌幅
"""
import yfinance as yf
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
import sys
from datetime import datetime, timedelta
import pytz

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
TOKEN_FILE = 'token_gmail.json'
# Recipient email from environment variable or default
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL', 'florashih324@gmail.com')

# Check for GitHub Actions token (base64 encoded)
github_token = os.environ.get('GMAIL_TOKEN')
if github_token:
    import base64
    try:
        token_data = base64.b64decode(github_token).decode('utf-8')
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            f.write(token_data)
        print("Gmail token loaded from GitHub Secrets")
    except Exception as e:
        print(f"Warning: Failed to decode GitHub token: {e}")
LABEL_NAME = '美股'
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.labels', 'https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

# US Market holidays (simplified list for major holidays)
US_MARKET_HOLIDAYS = [
    # 2026
    (2026, 1, 1),   # New Year's Day
    (2026, 1, 19),  # Martin Luther King Jr. Day (third Monday)
    (2026, 2, 16),  # Presidents' Day (third Monday)
    (2026, 5, 25),  # Memorial Day (last Monday)
    (2026, 7, 3),   # Independence Day (observed)
    (2026, 9, 7),   # Labor Day (first Monday)
    (2026, 11, 26), # Thanksgiving Day (fourth Thursday)
    (2026, 12, 25), # Christmas Day
]

def is_us_market_open(date):
    """Check if US stock market was open on the given date"""
    # Check if it's a weekday (0=Monday, 6=Sunday)
    if date.weekday() >= 5:  # Saturday or Sunday
        return False

    # Check if it's a holiday
    return (date.year, date.month, date.day) not in US_MARKET_HOLIDAYS

def get_stock_data(symbol):
    """Get stock data for the given symbol (previous trading day close vs day before)"""
    import pytz

    ticker = yf.Ticker(symbol)

    # Get Taiwan timezone
    taiwan_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taiwan_tz)

    # We want the previous trading day's close price
    # Taiwan 06:00 = US 17:00 previous day (before market opens)
    # So we should get data up to yesterday

    # Set end_date to yesterday (Taiwan time)
    # This ensures we get complete closing data, not intraday
    yesterday = now - timedelta(days=1)

    # Set start_date to 10 days ago to ensure we have enough trading days
    start_date = yesterday - timedelta(days=15)

    # Format dates for yfinance (use UTC to avoid timezone issues)
    start_date_utc = start_date.astimezone(pytz.UTC).strftime('%Y-%m-%d')
    end_date_utc = yesterday.astimezone(pytz.UTC).strftime('%Y-%m-%d')

    hist = ticker.history(start=start_date_utc, end=end_date_utc)

    if len(hist) < 2:
        return None, None, None

    # Get the last two trading days (most recent complete days)
    latest = hist.iloc[-1]
    previous = hist.iloc[-2]

    latest_close = latest['Close']
    previous_close = previous['Close']
    change = latest_close - previous_close
    change_pct = (change / previous_close) * 100

    return latest_close, change, change_pct

def get_or_create_label(service):
    """Get or create the [美股] label"""
    try:
        # Try to find existing label
        labels = service.users().labels().list(userId='me').execute()
        for label in labels.get('labels', []):
            if label['name'] == LABEL_NAME:
                return label['id']
    except:
        pass

    # Create new label
    try:
        label_body = {
            'name': LABEL_NAME,
            'messageListVisibility': 'show',
            'labelListVisibility': 'labelShow'
        }
        label = service.users().labels().create(userId='me', body=label_body).execute()
        return label['id']
    except Exception as e:
        print(f"Warning: Could not create label: {e}")
        return None

def send_email(service, subject, body, label_id=None):
    """Send email with the stock report"""
    from email.mime.text import MIMEText
    import base64

    message = MIMEText(body, 'html', 'utf-8')
    message['to'] = RECIPIENT_EMAIL
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {'raw': raw}

    # Send email
    sent_message = service.users().messages().send(userId='me', body=message_body).execute()
    message_id = sent_message['id']

    # Add label if provided
    if label_id:
        try:
            service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()
        except Exception as e:
            print(f"Warning: Could not add label: {e}")

    return message_id

def get_old_stock_reports(service, label_id, exclude_message_id=None):
    """Get old stock report emails with the [美股] label"""
    try:
        # Search for messages with the [美股] label
        # Use label name for search, not ID
        query = f'label:{LABEL_NAME}'

        # Get messages
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=10
        ).execute()

        messages = results.get('messages', [])

        # Filter out the newly sent message
        if exclude_message_id:
            messages = [m for m in messages if m['id'] != exclude_message_id]

        return messages
    except Exception as e:
        print(f"Warning: Could not search for old emails: {e}")
        return []

def move_to_trash(service, message_ids):
    """Move messages to trash"""
    moved_count = 0
    for msg_id in message_ids:
        try:
            # Get the message to check its current labels
            msg = service.users().messages().get(userId='me', id=msg_id, format='metadata').execute()
            current_label_ids = msg.get('labelIds', [])

            # Remove from INBOX if present
            remove_label_ids = []
            add_label_ids = ['TRASH']

            if 'INBOX' in current_label_ids:
                remove_label_ids.append('INBOX')

            # Modify the message
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={
                    'addLabelIds': add_label_ids,
                    'removeLabelIds': remove_label_ids
                }
            ).execute()

            moved_count += 1
        except Exception as e:
            print(f"Warning: Could not move message {msg_id} to trash: {e}")

    return moved_count

def get_credentials():
    """Get Google API credentials"""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        print("Error: No valid credentials found.")
        print("Please run Google OAuth authorization first.")
        return None

    return creds

def generate_report():
    """Generate the stock report"""
    # Check if US market was open 2 days ago
    # Because we run at 06:00 Taiwan time, which is before US market opens on "yesterday"
    # So we want to report on the previous completed trading day
    taiwan_tz = pytz.timezone('Asia/Taipei')
    today = datetime.now(taiwan_tz).date()
    yesterday = today - timedelta(days=1)
    report_date = today - timedelta(days=2)  # Report on 2 days ago (the last completed trading day)

    if not is_us_market_open(report_date):
        print(f"US market was closed on {report_date}. Skipping report.")
        return None

    # Get stock data
    # Dow Jones Industrial Average: ^DJI
    # TSMC ADR: TSM
    dow_close, dow_change, dow_change_pct = get_stock_data('^DJI')
    tsm_close, tsm_change, tsm_change_pct = get_stock_data('TSM')

    if dow_close is None or tsm_close is None:
        print("Error: Could not get stock data.")
        return None

    # Format the report
    dow_color = '#22c55e' if dow_change >= 0 else '#ef4444'
    tsm_color = '#22c55e' if tsm_change >= 0 else '#ef4444'
    dow_arrow = '▲' if dow_change >= 0 else '▼'
    tsm_arrow = '▲' if tsm_change >= 0 else '▼'

    # Format subject: [[美股04/14]道瓊▲ 317.74 (0.66%).台積電▲ $10.32 (2.79%)]
    date_str = report_date.strftime('%m/%d')
    subject = f"[[美股{date_str}]道瓊{dow_arrow} {abs(dow_change):,.2f} ({abs(dow_change_pct):.2f}%).台積電{tsm_arrow} ${abs(tsm_change):.2f} ({abs(tsm_change_pct):.2f}%)]"

    body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .header {{ background-color: #1e40af; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; max-width: 600px; margin: 0 auto; }}
        .stock-card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; margin: 15px 0; }}
        .stock-name {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
        .price {{ font-size: 24px; font-weight: bold; }}
        .change {{ font-size: 16px; margin-top: 5px; }}
        .positive {{ color: #22c55e; }}
        .negative {{ color: #ef4444; }}
        .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>📊 美股日報</h2>
        <p>{report_date.strftime('%Y年%m月%d日')}</p>
    </div>
    <div class="content">
        <div class="stock-card">
            <div class="stock-name">道瓊工業指數 (DJI)</div>
            <div class="price">{dow_close:,.2f}</div>
            <div class="change {'positive' if dow_change >= 0 else 'negative'}">
                {dow_arrow} {abs(dow_change):,.2f} ({abs(dow_change_pct):.2f}%)
            </div>
        </div>

        <div class="stock-card">
            <div class="stock-name">台積電 ADR (TSM)</div>
            <div class="price">${tsm_close:.2f}</div>
            <div class="change {'positive' if tsm_change >= 0 else 'negative'}">
                {tsm_arrow} ${abs(tsm_change):.2f} ({abs(tsm_change_pct):.2f}%)
            </div>
        </div>

        <div class="footer">
            此郵件由自動化系統發送 | 生成時間: {datetime.now(taiwan_tz).strftime('%Y/%m/%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""

    return subject, body

def main():
    """Main function"""
    print("=" * 60)
    print("美股股市報告")
    print("=" * 60)
    print()

    # Generate report
    result = generate_report()
    if result is None:
        print("No report generated. Market was likely closed.")
        return

    subject, body = result
    print(f"Report generated for: {datetime.now(pytz.timezone('Asia/Taipei')).date()}")
    print()

    # Get credentials
    creds = get_credentials()
    if not creds:
        return

    # Build Gmail service
    service = build('gmail', 'v1', credentials=creds)

    # Get or create label
    print("Checking/creating [美股] label...")
    label_id = get_or_create_label(service)
    print(f"Label ID: {label_id}")
    print()

    # Send email
    print("Sending email...")
    message_id = send_email(service, subject, body, label_id)
    print(f"Email sent successfully! Message ID: {message_id}")
    print()

    # Move old stock reports to trash
    if label_id:
        print("Checking for old stock reports...")
        old_messages = get_old_stock_reports(service, label_id, exclude_message_id=message_id)

        if old_messages:
            print(f"Found {len(old_messages)} old stock report(s), moving to trash...")
            old_message_ids = [m['id'] for m in old_messages]
            moved_count = move_to_trash(service, old_message_ids)
            print(f"Successfully moved {moved_count} old report(s) to trash.")
        else:
            print("No old stock reports found.")
    else:
        print("Skipping old email cleanup (label not created)")

if __name__ == '__main__':
    main()
