#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 全球生態與趨勢週報
搜尋時區：統計至當週一早上 7:00 為止
"""
import os
import sys
import base64
import json
from datetime import datetime, timedelta
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
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL', 'florashih324@gmail.com')
LABEL_NAME = 'MCP週報'
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.labels',
          'https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

# Search parameters
SEARCH_KEYWORDS = ['mcp-server', 'mcp server', 'model context protocol']
REDDIT_SUBREDDITS = ['ClaudeAI', 'LocalLLaMA']

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

def translate_to_traditional_chinese(text, max_retries=2):
    """Translate text to Traditional Chinese with error handling"""
    if not text or text == '無描述':
        return text

    # Technical terms dictionary for better translation
    tech_terms = {
        'Repository': '程式庫',
        'repositories': '程式庫',
        'server': '伺服器',
        'Server': '伺服器',
        'endpoint': '端點',
        'Endpoint': '端點',
        'authentication': '認證',
        'Authentication': '認證',
        'API': 'API',
        'client': '用戶端',
        'Client': '用戶端',
        'Model': '模型',
        'model': '模型',
        'protocol': '協議',
        'Protocol': '協議',
        'implementation': '實作',
        'Implementation': '實作',
        'integration': '整合',
        'Integration': '整合',
        'MCP': 'MCP (Model Context Protocol)',
        'Model Context Protocol': 'MCP (Model Context Protocol)',
        'Claude': 'Claude',
        'Anthropic': 'Anthropic',
        'tool': '工具',
        'Tool': '工具',
        'extension': '擴充功能',
        'Extension': '擴充功能',
        'plugin': '外掛',
        'Plugin': '外掛',
        'wrapper': '包裝器',
        'Wrapper': '包裝器',
        'interface': '介面',
        'Interface': '介面',
        'provider': '提供者',
        'Provider': '提供者',
        'resource': '資源',
        'Resource': '資源',
    }

    # Pre-process: preserve technical terms
    original_text = text
    placeholders = {}
    for i, (en, tw) in enumerate(tech_terms.items()):
        placeholder = f"__TERM{i}__"
        text = text.replace(en, placeholder)
        placeholders[placeholder] = tw

    for attempt in range(max_retries):
        try:
            # Use deep_translator (more reliable than googletrans)
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source='auto', target='zh-TW')
            translated = translator.translate(text)

            # Post-process: restore technical terms
            for placeholder, term in placeholders.items():
                translated = translated.replace(placeholder, term)

            return translated

        except Exception as e:
            print(f"Warning: Translation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(1)  # Wait before retry
            continue

    # If all attempts failed, return original with note
    return f"{original_text} (自動翻譯暫時不可用)"

def translate_descriptions(repos):
    """Translate descriptions for all repos in batch"""
    print("開始翻譯專案描述...")
    translated_count = 0

    for repo in repos:
        desc = repo.get('description', '')
        if desc and desc != '無描述':
            translated = translate_to_traditional_chinese(desc)
            repo['description_tw'] = translated
            translated_count += 1
        else:
            repo['description_tw'] = desc

    print(f"完成 {translated_count} 個專案描述的翻譯")
    return repos

def search_github_trending_repos(days=7, limit=10):
    """Search GitHub for trending MCP repositories (most stars added in last 7 days)"""
    print("=" * 60)
    print("搜尋 A：本週新秀（過去 7 天新增最多 Star）")
    print("=" * 60)
    print()

    # Use requests to search GitHub
    import requests

    results = []
    seen_repos = set()

    for keyword in SEARCH_KEYWORDS[:2]:  # Limit to avoid rate limiting
        try:
            # Search for repos created or updated recently, sorted by stars
            url = "https://api.github.com/search/repositories"
            params = {
                'q': f'{keyword} language:python',
                'sort': 'stars',
                'order': 'desc',
                'per_page': 30
            }

            headers = {}
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            repos = response.json().get('items', [])

            for repo in repos:
                name = repo.get('full_name')
                if name in seen_repos:
                    continue
                seen_repos.add(name)

                stars = repo.get('stargazers_count', 0)
                description = repo.get('description', '無描述')[:100]
                html_url = repo.get('html_url', '')
                created_at = repo.get('created_at', '')
                updated_at = repo.get('updated_at', '')

                results.append({
                    'name': name,
                    'stars': stars,
                    'description': description,
                    'url': html_url,
                    'created_at': created_at,
                    'updated_at': updated_at
                })

        except Exception as e:
            print(f"Warning: Error searching for '{keyword}': {e}")

    # Sort by stars (as proxy for recent popularity)
    results.sort(key=lambda x: x['stars'], reverse=True)

    return results[:limit]

def search_github_all_time_stars(limit=10):
    """Search GitHub for MCP servers with most historical stars"""
    print("=" * 60)
    print("搜尋 C：全球霸主（歷史總 Star 最高）")
    print("=" * 60)
    print()

    import requests

    results = []
    seen_repos = set()

    for keyword in SEARCH_KEYWORDS:
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                'q': f'{keyword} in:name,description language:python',
                'sort': 'stars',
                'order': 'desc',
                'per_page': 30
            }

            headers = {}
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            repos = response.json().get('items', [])

            for repo in repos:
                name = repo.get('full_name')
                if name in seen_repos:
                    continue
                seen_repos.add(name)

                stars = repo.get('stargazers_count', 0)
                description = repo.get('description', '無描述')[:100]
                html_url = repo.get('html_url', '')

                results.append({
                    'name': name,
                    'stars': stars,
                    'description': description,
                    'url': html_url
                })

        except Exception as e:
            print(f"Warning: Error searching for '{keyword}': {e}")

    # Sort by stars
    results.sort(key=lambda x: x['stars'], reverse=True)

    return results[:limit]

def search_reddit_trending(limit=10):
    """Search Reddit for trending MCP discussions"""
    print("=" * 60)
    print("搜尋 B：社群熱議（Reddit 討論度最高）")
    print("=" * 60)
    print()

    import requests

    # Use Reddit's public JSON API (no auth needed for public subs)
    results = []
    seen_posts = set()

    for subreddit in REDDIT_SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
            response = requests.get(url, headers={'User-Agent': 'MCP-Weekly-Reporter/1.0'})
            response.raise_for_status()

            posts = response.json().get('data', {}).get('children', [])

            for post_data in posts:
                post = post_data.get('data', {})
                title = post.get('title', '')
                url = f"https://reddit.com{post.get('permalink', '')}"
                score = post.get('score', 0)
                comments = post.get('num_comments', 0)

                # Check if post mentions MCP
                if any(keyword.lower() in title.lower() for keyword in SEARCH_KEYWORDS):
                    key = f"{subreddit}_{title}"
                    if key in seen_posts:
                        continue
                    seen_posts.add(key)

                    results.append({
                        'subreddit': subreddit,
                        'title': title,
                        'url': url,
                        'score': score,
                        'comments': comments
                    })

        except Exception as e:
            print(f"Warning: Error searching r/{subreddit}: {e}")

    # Sort by combined engagement (score + comments)
    results.sort(key=lambda x: x['score'] + x['comments'], reverse=True)

    return results[:limit]

def generate_recommendations(all_items):
    """Generate AI career recommendations based on work A context"""
    # This would need user's work A context - for now providing general recommendations
    recommendations = []

    print("=" * 60)
    print("AI 專業建議")
    print("=" * 60)
    print()

    # General recommendations based on the search results
    all_items_flat = []

    for item in all_items.get('trending', []):
        all_items_flat.append({
            'name': item['name'],
            'stars': item.get('stars', 0),
            'description': item['description'],
            'description_tw': item.get('description_tw', ''),
            'url': item['url']
        })

    for item in all_items.get('top_all', []):
        all_items_flat.append({
            'name': item['name'],
            'stars': item.get('stars', 0),
            'description': item['description'],
            'description_tw': item.get('description_tw', ''),
            'url': item['url']
        })

    # Recommend top 3 by stars/popularity
    all_items_flat.sort(key=lambda x: x['stars'], reverse=True)

    for item in all_items_flat[:3]:
        recommendations.append({
            'name': item['name'],
            'url': item['url'],
            'description': item['description'],
            'description_tw': item.get('description_tw', ''),
            'reason': '高人氣且活躍的專案，值得深入了解'
        })

    return recommendations

def generate_html_report(trending, reddit, top_all, recommendations, report_date):
    """Generate HTML format report"""
    # Format date
    date_str = report_date.strftime('%Y年%m月%d日')

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP 全球生態與趨勢週報 - {date_str}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Microsoft JhengHei', 'PingFang TC', sans-serif;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        .header p {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .section {{
            padding: 30px;
            margin: 20px;
            border-radius: 15px;
            border: 2px solid #e0e0e0;
        }}
        .section-title {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            color: #667eea;
            display: flex;
            align-items: center;
        }}
        .section-title::before {{
            content: '';
            width: 12px;
            height: 12px;
            background: #667eea;
            border-radius: 50%;
            margin-right: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #667eea;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .repo-name {{
            font-weight: 600;
            color: #667eea;
        }}
        .repo-stars {{
            background: #ffeaa7;
            color: #d35400;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .rank {{
            display: inline-block;
            width: 30px;
            height: 30px;
            line-height: 30px;
            text-align: center;
            background: #667eea;
            color: white;
            border-radius: 50%;
            font-weight: 700;
            margin-right: 10px;
        }}
        .reddit-subreddit {{
            color: #ff4500;
            font-weight: 600;
        }}
        .reddit-score {{
            background: #ff6b6b;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .recommendation {{
            background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin-top: 10px;
        }}
        .recommendation h3 {{
            margin-top: 0;
            font-size: 18px;
            margin-bottom: 10px;
        }}
        .recommendation-reason {{
            font-style: italic;
            opacity: 0.9;
            margin-top: 10px;
        }}
        .footer {{
            background: #f8f9fa;
            text-align: center;
            padding: 20px;
            font-size: 14px;
            color: #666;
        }}
        a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .description-en {{
            font-weight: 500;
            color: #333;
        }}
        .description-tw {{
            background: #f9f9f9;
            color: #666;
            font-style: italic;
            font-size: 13px;
            padding: 6px 10px;
            border-radius: 6px;
            margin-top: 5px;
            display: block;
        }}
        /* Mobile responsive adjustments */
        @media only screen and (max-width: 600px) {{
            .container {{
                padding: 10px;
            }}
            .header h1 {{
                font-size: 24px;
            }}
            .section {{
                padding: 15px;
                margin: 10px;
            }}
            table {{
                font-size: 12px;
            }}
            th, td {{
                padding: 8px 5px;
            }}
            .description-tw {{
                font-size: 11px;
                padding: 4px 6px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 MCP 全球生態與趨勢週報</h1>
            <p>{date_str} | 每週一早上 8:00 發送</p>
        </div>

        <!-- Section A: 本週新秀 -->
        <div class="section">
            <div class="section-title">A. 本週新秀（過去 7 天新增最多 Star）</div>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>專案名稱</th>
                        <th>功能簡述</th>
                        <th>Star 數</th>
                    </tr>
                </thead>
                <tbody>"""

    for i, repo in enumerate(trending, 1):
        desc_en = repo.get('description', '無描述')
        desc_tw = repo.get('description_tw', '')

        html += f"""
                    <tr>
                        <td><span class="rank">{i}</span></td>
                        <td><a href="{repo['url']}" target="_blank" class="repo-name">{repo['name']}</a></td>
                        <td>
                            <span class="description-en">{desc_en}</span>
                            {f'<span class="description-tw">{desc_tw}</span>' if desc_tw and desc_tw != desc_en else ''}
                        </td>
                        <td><span class="repo-stars">★ {repo['stars']}</span></td>
                    </tr>"""

    html += """
                </tbody>
            </table>
        </div>

        <!-- Section B: 社群熱議 -->
        <div class="section">
            <div class="section-title">B. 社群熱議（Reddit 討論度最高）</div>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>社群</th>
                        <th>標題</th>
                        <th>互動數</th>
                    </tr>
                </thead>
                <tbody>"""

    for i, post in enumerate(reddit, 1):
        engagement = post['score'] + post['comments']
        html += f"""
                    <tr>
                        <td><span class="rank">{i}</span></td>
                        <td><span class="reddit-subreddit">r/{post['subreddit']}</span></td>
                        <td><a href="{post['url']}" target="_blank">{post['title'][:80]}...</a></td>
                        <td><span class="reddit-score">↑ {engagement}</span> (👍{post['score']} 💬{post['comments']})</td>
                    </tr>"""

    html += """
                </tbody>
            </table>
        </div>

        <!-- Section C: 全球霸主 -->
        <div class="section">
            <div class="section-title">C. 全球霸主（歷史總 Star 最高）</div>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>專案名稱</th>
                        <th>功能簡述</th>
                        <th>Star 數</th>
                    </tr>
                </thead>
                <tbody>"""

    for i, repo in enumerate(top_all, 1):
        desc_en = repo.get('description', '無描述')
        desc_tw = repo.get('description_tw', '')

        html += f"""
                    <tr>
                        <td><span class="rank">{i}</span></td>
                        <td><a href="{repo['url']}" target="_blank" class="repo-name">{repo['name']}</a></td>
                        <td>
                            <span class="description-en">{desc_en}</span>
                            {f'<span class="description-tw">{desc_tw}</span>' if desc_tw and desc_tw != desc_en else ''}
                        </td>
                        <td><span class="repo-stars">★ {repo['stars']}</span></td>
                    </tr>"""

    html += """
                </tbody>
            </table>
        </div>

        <!-- AI 專業建議 -->
        <div class="section">
            <div class="section-title">🎯 AI 專業建議（重點推薦）</div>"""

    for i, rec in enumerate(recommendations, 1):
        desc_en = rec.get('description', '無描述')
        desc_tw = rec.get('description_tw', '')

        html += f"""
            <div class="recommendation">
                <h3>{i}. {rec['name']}</h3>
                <p><strong>功能：</strong><span class="description-en">{desc_en}</span></p>
                {f'<p class="description-tw"><strong>功能（中文）：</strong>{desc_tw}</p>' if desc_tw and desc_tw != desc_en else ''}
                <p><strong>功能：</strong>{rec['description']}</p>
                <p><strong>網址：</strong><a href="{rec['url']}" target="_blank">{rec['url']}</a></p>
                <p class="recommendation-reason">💡 {rec['reason']}</p>
            </div>"""

    html += f"""
        </div>

        <div class="footer">
            <p>本報告由自動化系統生成 | 搜尋時區：統計至 {date_str} 週一早上 7:00</p>
            <p>資料來源：GitHub, Reddit | 生成時間：{datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y/%m/%d %H:%M')}</p>
        </div>
    </div>
</body>
</html>"""

    return html

def send_email(service, subject, body, label_id=None):
    """Send email with the report"""
    from email.mime.text import MIMEText
    import base64

    message = MIMEText(body, 'html', 'utf-8')
    message['to'] = RECIPIENT_EMAIL
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {'raw': raw}

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

def get_or_create_label(service):
    """Get or create the [MCP週報] label"""
    try:
        labels = service.users().labels().list(userId='me').execute()
        for label in labels.get('labels', []):
            if label['name'] == LABEL_NAME:
                return label['id']
    except:
        pass

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

def get_mcp_weekly_reports(service):
    """Get all emails with [MCP週報] label"""
    try:
        query = f'label:{LABEL_NAME}'
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=50
        ).execute()

        messages = results.get('messages', [])
        print(f"找到 {len(messages)} 封帶有 '{LABEL_NAME}' 標籤的郵件")

        # Get detailed info for each message (including date and subject)
        message_details = []
        for msg in messages:
            try:
                msg_info = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['Date', 'Subject']
                ).execute()

                headers = msg_info.get('payload', {}).get('headers', [])
                date_str = None
                subject = None

                for header in headers:
                    if header['name'] == 'Date':
                        date_str = header['value']
                    elif header['name'] == 'Subject':
                        subject = header['value']

                # Parse date to datetime for comparison
                from email.utils import parsedate_to_datetime
                date_dt = parsedate_to_datetime(date_str) if date_str else None

                message_details.append({
                    'id': msg['id'],
                    'subject': subject,
                    'date': date_str,
                    'date_dt': date_dt
                })
            except Exception as e:
                print(f"Warning: Could not get details for message {msg['id']}: {e}")

        return message_details
    except Exception as e:
        print(f"Warning: Could not search for MCP weekly reports: {e}")
        return []

def cleanup_old_monthly_reports(service, current_message_id):
    """Clean up old monthly reports, keep only the last one from previous month"""
    all_reports = get_mcp_weekly_reports(service)

    if not all_reports:
        print("沒有找到舊的 MCP 週報郵件")
        return

    # Filter out the newly sent message
    reports = [r for r in all_reports if r['id'] != current_message_id]

    if not reports:
        print("沒有需要清理的舊郵件")
        return

    # Get current month (Taiwan timezone)
    taiwan_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taiwan_tz)
    current_year = now.year
    current_month = now.month

    print(f"當前時間：{now.strftime('%Y/%m/%d %H:%M:%S')}")

    # Categorize reports by month
    reports_by_month = {}

    for report in reports:
        if report['date_dt']:
            # Convert to Taiwan timezone
            if report['date_dt'].tzinfo is None:
                report_date_tz = pytz.utc.localize(report['date_dt']).astimezone(taiwan_tz)
            else:
                report_date_tz = report['date_dt'].astimezone(taiwan_tz)

            report_year = report_date_tz.year
            report_month = report_date_tz.month
            key = (report_year, report_month)

            if key not in reports_by_month:
                reports_by_month[key] = []
            reports_by_month[key].append(report)

    # Process each month's reports
    to_trash = []

    for (year, month), month_reports in sorted(reports_by_month.items()):
        if year == current_year and month == current_month:
            print(f"本月 ({year}/{month}): 保留所有 {len(month_reports)} 封週報")
        else:
            # Previous month or older: keep only the last one
            month_reports_sorted = sorted(month_reports, key=lambda x: x['date_dt'], reverse=True)

            if len(month_reports_sorted) > 1:
                # Keep the first (last sent), move rest to trash
                keep_report = month_reports_sorted[0]
                trash_reports = month_reports_sorted[1:]

                print(f"{year}/{month}: 保留最後一封 (發送於 {keep_report['date_dt'].strftime('%Y/%m/%d %H:%M')})")
                print(f"{year}/{month}: 將 {len(trash_reports)} 封舊郵件移至垃圾桶")

                to_trash.extend([r['id'] for r in trash_reports])
            else:
                print(f"{year}/{month}: 只有 {len(month_reports)} 封週報，保留")

    # Move reports to trash using batchModify if possible
    if to_trash:
        print(f"\n開始移動 {len(to_trash)} 封郵件至垃圾桶...")
        moved_count = 0

        # Process in batches of 50 (Gmail API limit for batchModify)
        batch_size = 50
        for i in range(0, len(to_trash), batch_size):
            batch = to_trash[i:i + batch_size]
            try:
                service.users().messages().batchModify(
                    userId='me',
                    body={
                        'ids': batch,
                        'addLabelIds': ['TRASH'],
                        'removeLabelIds': ['INBOX']
                    }
                ).execute()
                moved_count += len(batch)
            except Exception as e:
                print(f"Warning: Batch modify failed for {len(batch)} messages: {e}")
                # Fallback to individual moves
                for msg_id in batch:
                    try:
                        service.users().messages().modify(
                            userId='me',
                            id=msg_id,
                            body={
                                'addLabelIds': ['TRASH'],
                                'removeLabelIds': ['INBOX']
                            }
                        ).execute()
                        moved_count += 1
                    except Exception as e2:
                        print(f"Warning: Could not move {msg_id} to trash: {e2}")

        print(f"成功移動 {moved_count} 封舊郵件至垃圾桶")
    else:
        print("沒有需要移至垃圾桶的郵件")

def main():
    """Main function"""
    print("=" * 60)
    print("MCP 全球生態與趨勢週報")
    print("=" * 60)
    print()

    taiwan_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(taiwan_tz)

    # Calculate report date (last Monday)
    days_since_monday = now.weekday()  # 0=Monday, 6=Sunday
    if days_since_monday == 0:
        # Today is Monday, report on last week's Monday
        report_date = now - timedelta(days=7)
    else:
        # Report on this week's Monday
        report_date = now - timedelta(days=days_since_monday)

    print(f"報告日期：{report_date.strftime('%Y/%m/%d')}")
    print(f"搜尋截止：{report_date} 早上 7:00")
    print()

    # Search data
    print("開始搜尋數據...")
    print()

    trending = search_github_trending_repos(days=7, limit=10)
    reddit = search_reddit_trending(limit=10)
    top_all = search_github_all_time_stars(limit=10)

    # Translate descriptions to Traditional Chinese
    print()
    translate_descriptions(trending)
    translate_descriptions(top_all)

    all_items = {'trending': trending, 'top_all': top_all}
    recommendations = generate_recommendations(all_items)

    # Generate HTML report
    print()
    print("生成 HTML 報告...")
    html = generate_html_report(trending, reddit, top_all, recommendations, report_date)

    # Send email
    print()
    print("發送郵件...")
    creds = get_credentials()
    if not creds:
        return

    from googleapiclient.discovery import build
    service = build('gmail', 'v1', credentials=creds)

    label_id = get_or_create_label(service)

    date_str = report_date.strftime('%Y/%m/%d')
    subject = f"[MCP週報] 全球熱門伺服器與趨勢彙整 ({date_str})"

    message_id = send_email(service, subject, html, label_id)
    print(f"郵件發送成功！Message ID: {message_id}")

    # Clean up old monthly reports
    print()
    print("=" * 60)
    print("清理舊月度週報")
    print("=" * 60)
    cleanup_old_monthly_reports(service, message_id)

if __name__ == '__main__':
    main()
