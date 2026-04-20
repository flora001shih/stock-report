# 🎮 Discord Bot 家用記帳

透過 Discord 快速記帳，資料自動同步到 Google Sheets！

## ✨ 功能特點

- 🎮 **Discord 介面** - 在手機上用 Discord 即可記帳
- 🔄 **自動同步** - 記帳資料自動寫入 Google Sheets
- 🚀 **觸發式執行** - 使用 GitHub Actions，無需常駐伺服器
- 🔒 **安全加密** - 所有金鑰透過 GitHub Secrets 管理

## 🏗️ 系統架構

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Discord    │───→│ Discord Bot  │───→│ GitHub      │───→│ Google      │
│  App        │    │              │    │ Actions      │    │ Sheets      │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

## 📝 使用方法

### 記帳指令

```
!記帳 [日期] [人物] [明細] [金額]
```

### 範例

| 指令 | 說明 |
|------|------|
| `!記帳 今天 友方 晚餐炒麵 100` | 友方今天花 100 元 |
| `!記帳 昨天 一銀 南方莊園票券 1390` | 一銀昨天花 1390 元（記到昨天的月份欄位） |
| `!記帳 友方 午餐 -50` | 友方今天花 50 元（日期預設今天） |

**⚠️ 重要：日期決定記帳位置**
- 日期決定了資料會寫入**哪個月份的欄位**
- 例如：今天是 5 月 1 日，但你記「昨天」，會記到 4 月欄位
- 不指定日期預設為「今天」

### 支援的人物

- `友方` - 友方的帳戶
- `一銀` - 家庭一銀刷卡
- `昇華` - 昇華的帳戶

## 🚀 快速開始

### 1. 設定 GitHub Secrets

在 GitHub Repository Settings → Secrets 中添加：

| Secret 名稱 | 說明 |
|-------------|------|
| `DISCORD_BOT_TOKEN` | Discord Bot Token |
| `GH_TOKEN` | GitHub Personal Access Token (需 repo 權限) |
| `GOOGLE_CREDENTIALS` | Google Service Account JSON (Base64 編碼) |

### 2. 部署 Discord Bot

推薦使用 **Render.com** (免費)：

```bash
# 連接 GitHub Repository 後，設定：
# Root Directory: discord_bot
# Build Command: pip install -r requirements.txt
# Start Command: python app.py
```

添加環境變數：
```
DISCORD_BOT_TOKEN=your_token
GH_TOKEN=your_github_pat
GITHUB_REPO=your-username/your-repo
```

### 3. 邀請 Bot 到伺服器

使用 Discord Bot 建立器邀請 Bot：
- 需要權限: `Send Messages`、`Read Messages`、`Embed Links`

### 4. 測試

在 Discord 中發送：
```
!記帳 友方 測試 -1
```

## 📁 檔案結構

```
discord_bot/
├── app.py                 # Discord Bot 主程式
├── requirements.txt       # Python 依賴
├── .env.example          # 環境變數範例
├── README.md             # 本文件
└── QUICKSTART.md         # 快速開始指南

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

### 啟動 Bot

```bash
python app.py
```

## 🛠️ 技術棧

- **Discord.py** - Discord Bot 框架
- **GitHub Actions** - 工作流自動化
- **Google Sheets API** - 資料儲存

## 📄 授權

MIT License
