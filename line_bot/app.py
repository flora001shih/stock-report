#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LINE Bot 橋接程式 - 家用記帳
接收 LINE 訊息並觸發 GitHub Actions
"""
import os
import json
import hmac
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

# LINE 設定
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')

# GitHub 設定
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO = os.environ.get('GITHUB_REPO', '')  # 格式: owner/repo
GITHUB_WORKFLOW_ID = os.environ.get('GITHUB_WORKFLOW_ID', 'accounting.yml')

# 記帳指令關鍵字
ACCOUNTING_KEYWORDS = ['記帳', '幫我記帳', '記錄']


def verify_line_signature(request_body, signature):
    """驗證 LINE Webhook 簽名"""
    if not LINE_CHANNEL_SECRET:
        return False
    hash_value = hmac.new(
        LINE_CHANNEL_SECRET.encode('utf-8'),
        request_body,
        hashlib.sha256
    ).digest()
    return hmac.compare_digest(signature, hash_value)


def trigger_github_action(user_id, display_name, message_text):
    """觸發 GitHub Actions 工作流"""
    import requests

    # GitHub API URL
    url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"

    # 構建 payload
    payload = {
        "event_type": "accounting_request",
        "client_payload": {
            "user_id": user_id,
            "display_name": display_name,
            "message": message_text,
            "timestamp": int(__import__('time').time())
        }
    }

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
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


def reply_to_line(reply_token, text):
    """回覆 LINE 訊息"""
    import requests

    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }

    data = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }

    try:
        requests.post(url, json=data, headers=headers, timeout=5)
    except Exception as e:
        print(f"回覆 LINE 時發生錯誤: {str(e)}")


@app.route('/webhook', methods=['POST'])
def webhook():
    """LINE Webhook 端點"""
    # 獲取請求資料
    request_body = request.get_data(as_text=True)
    signature = request.headers.get('X-Line-Signature', '')

    # 驗證簽名
    if not verify_line_signature(request_body.encode('utf-8'), signature):
        return jsonify({"error": "Invalid signature"}), 400

    # 解析事件
    events = json.loads(request_body).get('events', [])

    for event in events:
        if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
            # 獲取使用者資訊
            source = event.get('source', {})
            user_id = source.get('userId', 'unknown')
            reply_token = event.get('replyToken')
            message_text = event['message']['text']

            # 獲取使用者顯示名稱
            display_name = user_id
            try:
                profile_url = f"https://api.line.me/v2/bot/profile/{user_id}"
                headers = {"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}
                profile_resp = requests.get(profile_url, headers=headers, timeout=5)
                if profile_resp.status_code == 200:
                    display_name = profile_resp.json().get('displayName', user_id)
            except:
                pass

            # 檢查是否為記帳指令
            is_accounting_cmd = any(keyword in message_text for keyword in ACCOUNTING_KEYWORDS)

            if is_accounting_cmd:
                # 觸發 GitHub Actions
                success, message = trigger_github_action(user_id, display_name, message_text)

                # 回覆使用者
                if success:
                    reply_text = f"✅ {message}\n\n📝 記帳請求已送出，請稍候..."
                else:
                    reply_text = f"❌ {message}\n\n請稍後再試或聯絡管理員。"
            else:
                # 非記帳指令
                reply_text = (
                    "👋 你好！我是家用記帳 LINE Bot\n\n"
                    "📝 使用方法：\n"
                    "• 輸入「記帳」開始記帳\n\n"
                    "📋 記帳格式：\n"
                    "記帳 人物 明細 金額 [日期]\n\n"
                    "📅 範例：\n"
                    "• 記帳 友方 午餐 -150              (今天)\n"
                    "• 記帳 一銀 南方莊園票券 1390 今天 (今天)\n"
                    "• 記帳 昇華 晚餐 -200 昨天       (昨天的月份欄位)\n"
                    "• 記帳 友方 早餐 -50 2026/04/16   (指定日期)\n\n"
                    "⚠️ 重要：\n"
                    "• 日期決定記帳位置（哪個月份欄位）\n"
                    "• 不指定日期預設為「今天」\n\n"
                    "👤 支援人物：友方、一銀、昇華"
                )

            reply_to_line(reply_token, reply_text)

    return jsonify({"status": "ok"}), 200


@app.route('/health', methods=['GET'])
def health():
    """健康檢查端點"""
    return jsonify({"status": "healthy"}), 200


@app.route('/', methods=['GET'])
def index():
    """首頁"""
    return """
    <html>
    <head><meta charset="utf-8"><title>家用記帳 LINE Bot</title></head>
    <body>
        <h1>📱 家用記帳 LINE Bot</h1>
        <p>服務運行中！</p>
        <p><a href="/health">健康檢查</a></p>
    </body>
    </html>
    """


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
