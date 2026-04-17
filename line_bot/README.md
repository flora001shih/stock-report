# 📱 LINE Bot 家用記帳

透過 LINE App 快速記帳，資料自動同步到 Google Sheets！

## ✨ 功能特點

- 📱 **LINE 介面** - 在手機上用 LINE 即可記帳
- 🔄 **自動同步** - 記帳資料自動寫入 Google Sheets
- 🚀 **觸發式執行** - 使用 GitHub Actions，無需常駐伺服器
- 🔒 **安全加密** - 所有金鑰透過 GitHub Secrets 管理

## 🏗️ 系統架構

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  S23 Ultra  │───→│ LINE Platform│───→│ Webhook     │───→│ GitHub       │───→│ Google      │
│  (LINE App) │    │              │    │ Server      │    │ Actions      │    │ Sheets      │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘    └─────────────┘
```

## 📝 使用方法

### 記帳格式

```
記帳 人物 明細 金額 [日期]
```

### 範例

| 指令 | 說明 |
|------|------|
| `記帳 友方 午餐 -150` | 友方今天花 150 元 |
| `記帳 一銀 南方莊園票券 1390` | 一銀花 1390 元買票券 |
| `記帳 昇華 自带杯退费 +5` | 昇華退費 5 元 |

### 支援的人物

- `友方` - 友方的帳戶
- `一銀` - 家庭一銀刷卡
- `昇華` - 昇華的帳戶

## 🚀 快速開始

### 1. 創建 LINE Channel

前往 [LINE Developers Console](https://developers.line.biz/console/) 創建 Messaging API Channel。

### 2. 設定 GitHub Secrets

在 GitHub Repository Settings → Secrets 中添加：

| Secret 名稱 | 說明 |
|-------------|------|
| `LINE_CHANNEL_SECRET` | LINE Channel Secret |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel Access Token |
| `GITHUB_TOKEN` | GitHub Personal Access Token (需 repo 權限) |
| `GOOGLE_CREDENTIALS` | Google Service Account JSON (Base64 編碼) |

### 3. 部署 Webhook Server

推薦使用 **Render.com** (免費)：

```bash
# 連接 GitHub Repository 後，設定：
# Root Directory: line_bot
# Build Command: pip install -r requirements.txt
# Start Command: gunicorn app:app
```

添加環境變數：
```
LINE_CHANNEL_SECRET=your_secret
LINE_CHANNEL_ACCESS_TOKEN=your_token
GITHUB_TOKEN=your_github_pat
GITHUB_REPO=your-username/your-repo
```

### 4. 設定 LINE Webhook

在 LINE Developers Console：
- Webhook URL: `https://your-app-url.com/webhook`
- 勾選 "Use webhook"
- 點擊 Verify

### 5. 測試

在 LINE 中搜尋你的 Bot 並發送：
```
記帳 友方 測試 -1
```

## 📁 檔案結構

```
line_bot/
├── app.py                 # LINE Bot 主程式
├── requirements.txt       # Python 依賴
├── .env.example          # 環境變數範例
├── README.md             # 本文件
└── DEPLOYMENT.md         # 詳細部署指南

.github/
└── workflows/
    └── accounting.yml     # GitHub Actions 工作流

scripts/
└── line_bot_accounting.py # 記帳處理腳本
```

## 🔧 本地開發

### 安裝依賴

```bash
pip install -r requirements.txt
```

### 設定環境變數

```bash
cp .env.example .env
# 編輯 .env 填入實際值
```

### 啟動伺服器

```bash
python app.py
```

Webhook 將在 `http://localhost:5000/webhook` 運行。

### 使用 ngrok 測試

```bash
ngrok http 5000
```

將 ngrok URL 設定到 LINE Webhook。

## 📖 完整文檔

詳見 [DEPLOYMENT.md](DEPLOYMENT.md) 了解完整部署步驟、故障排除和安全建議。

## 🛠️ 技術棧

- **LINE Messaging API** - LINE Bot 平台
- **Flask** - Web 框架
- **GitHub Actions** - 工作流自動化
- **Google Sheets API** - 資料儲存

## 📄 授權

MIT License
