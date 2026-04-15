#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
List recent Google Drive files
"""
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_FILE = r'C:\Claude_Test_Lab\token_calendar.json'  # Use existing token

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

def list_recent_files(limit=10):
    """List recent files from Google Drive"""
    creds = get_credentials()
    if not creds:
        return

    service = build('drive', 'v3', credentials=creds)

    # Search for files, sorted by modified time
    results = service.files().list(
        pageSize=limit,
        fields="nextPageToken,files(id,name,modifiedTime,webViewLink,mimeType)",
        orderBy="modifiedTime desc",
        q="trashed=false"
    ).execute()

    files = results.get('files', [])

    print("=" * 60)
    print(f"最近修改的 {len(files)} 個 Google Drive 檔案")
    print("=" * 60)
    print()

    if not files:
        print("沒有找到檔案")
        return

    for i, file in enumerate(files, 1):
        name = file.get('name', '(無名稱)')
        modified = file.get('modifiedTime', '(未知時間)')
        mime_type = file.get('mimeType', '(未知類型)')
        link = file.get('webViewLink', '(無連結)')

        # Format modified time
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
            # Convert to Taiwan time
            import pytz
            taiwan_tz = pytz.timezone('Asia/Taipei')
            dt_taiwan = dt.astimezone(taiwan_tz)
            modified_str = dt_taiwan.strftime('%Y/%m/%d %H:%M')
        except:
            modified_str = modified

        print(f"{i}. {name}")
        print(f"   修改時間: {modified_str}")
        print(f"   類型: {mime_type}")
        print(f"   連結: {link}")
        print()

def main():
    """Main function"""
    list_recent_files(limit=10)

if __name__ == '__main__':
    main()
