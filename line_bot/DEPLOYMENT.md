# LINE Bot 家用記帳 - 部署指南

## 📋 概述

這個 LINE Bot 系統讓你可以透過手機 LINE App 快速記帳，資料會自動寫入你的 Google Sheets。

```
S23 Ultra (LINE) → LINE Platform → Webhook Server → GitHub Actions → Google Sheets
```

---

## 🔧 設定步驟

### 第一步：創建 LINE Channel

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 登入並創建新的 Provider
3. 在 Provider 下創建新的 **Messaging API Channel**
4. 記錄以下資訊：
   - **Channel ID**
   - **Channel Secret**
   - **Channel Access Token** (需發行)

---

### 第二步：設定 GitHub Secrets

在你的 GitHub Repository 中，需要加入以下 Secrets：

| Secret 名稱 | 說明 | 如何獲取 |
|-------------|------|----------|
| `LINE_CHANNEL_SECRET` | LINE Channel Secret | LINE Developers Console → Basic settings |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel Access Token | LINE Developers Console → Messaging API → 發行 |
| `GITHUB_TOKEN` | GitHub Personal Access Token | GitHub Settings → Developer settings → Personal access tokens |
| `GOOGLE_CREDENTIALS` | Google Service Account JSON (Base64編碼) | 見下方說明 |

#### 設定 GOOGLE_CREDENTIALS

你的 Google Credentials 檔案需要先進行 Base64 編碼：

**Windows:**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\flora-gae11-48f2f2e53de7.json")) | clip
```

**macOS/Linux:**
```bash
base64 -i flora-gae11-48f2f2e53de7.json | pbcopy
```

然後將剪貼簿內容貼到 GitHub Secret `GOOGLE_CREDENTIALS` 中。

---

### 第三步：部署 LINE Bot (選擇平台)

#### 選項 A：Render.com (推薦 - 免費)

1. 前往 [Render.com](https://render.com/) 並註冊
2. 連接你的 GitHub Repository
3. 創建新的 **Web Service**
4. 設定：
   - **Root Directory**: `line_bot`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. 添加環境變數：
   ```
   LINE_CHANNEL_SECRET = (你的 LINE Channel Secret)
   LINE_CHANNEL_ACCESS_TOKEN = (你的 LINE Channel Access Token)
   GITHUB_TOKEN = (你的 GitHub PAT，需要 repo 權限)
   GITHUB_REPO = (你的 GitHub 倉庫名稱，如: username/repo-name)
   GITHUB_WORKFLOW_ID = accounting.yml
   ```
6. 部署完成後，記下 Web Service 的 URL

#### 選項 B：Heroku

1. 安裝 Heroku CLI
2. 登入：`heroku login`
3. 創建 App：`heroku create your-app-name`
4. 設定環境變數：
   ```bash
   heroku config:set LINE_CHANNEL_SECRET="xxx"
   heroku config:set LINE_CHANNEL_ACCESS_TOKEN="xxx"
   heroku config:set GITHUB_TOKEN="xxx"
   heroku config:set GITHUB_REPO="username/repo-name"
   ```
5. 部署：`git push heroku main`

#### 選項 C：Railway.app

1. 連接 GitHub Repository
2. 選擇 `line_bot` 目錄
3. 添加環境變數
4. 部署

---

### 第四步：設定 LINE Webhook

1. 回到 [LINE Developers Console](https://developers.line.biz/console/)
2. 選擇你的 Channel
3. 進入 **Messaging API** 設定
4. 在 **Webhook** 區域：
   - 將 Webhook URL 設為：`https://你的app-url.com/webhook`
   - 勾選 **Use webhook**
5. 點擊 **Verify** 確認連線

---

## 📱 手機端測試 (S23 Ultra)

### 測試步驟：

1. **搜尋 LINE Official Account**
   - 打開 LINE App
   - 搜尋你的 LINE Bot ID 或 QR Code
   - 選擇「加入好友」

2. **發送測試訊息**
   - 輸入：`記帳`
   - 應該收到回覆說明使用方法

3. **實際記帳測試**
   ```
   記帳 友方 午餐 -150
   ```
   或
   ```
   記帳 一銀 南方莊園一日遊票券 1390 今天
   ```

4. **驗證結果**
   - 檢查你的 Google Sheets `家用記帳合併`
   - 應該看到新記錄已加入

---

## 📝 記帳格式

### 基本格式
```
記帳 人物 明細 金額 [日期]
```

### 範例
| 指令 | 說明 |
|------|------|
| `記帳 友方 午餐 -150` | 友方今天花 150 元吃午餐 |
| `記帳 一銀 南方莊園票券 1390 今天` | 一銀今天買 1390 元票券 |
| `記帳 昇華 自带杯退费 +5` | 昇華今天退費 5 元 |
| `記帳 友方 晚餐 -200 明天` | 友方明天花 200 元吃晚餐 |

### 人物
- `友方` - 友方的帳戶
- `一銀` - 家庭一銀刷卡
- `昇華` - 昇華的帳戶

### 日期格式
- `今天` 或 `今日` - 今天
- `2026/04/17` - 指定日期
- `04/17` - 當年指定月日
- 省略 - 預設今天

---

## 🔍 故障排除

### 1. Webhook 驗證失敗
- 檢查 LINE_CHANNEL_SECRET 是否正確
- 確認 Webhook URL 可公開存取
- 確認 HTTPS 憑證有效

### 2. GitHub Actions 未觸發
- 檢查 GITHUB_TOKEN 是否有 `repo` 權限
- 確認 GITHUB_REPO 格式正確 (owner/repo)
- 檢查 GitHub Actions workflow 是否已啟用

### 3. Google Sheets 寫入失敗
- 檢查 GOOGLE_CREDENTIALS 是否正確編碼
- 確認 Service Account 有權限存取該 Spreadsheet
- 檢查月份欄位對應是否正確

### 4. 記帳訊息無法解析
- 確認格式正確：`記帳 人物 明細 金額`
- 確認人物名稱正確（友方、一銀、昇華）
- 確認金額是數字

---

## 📊 查看執行記錄

### GitHub Actions 日誌
1. 前往你的 GitHub Repository
2. 點擊 **Actions** 標籤
3. 選擇最新的 `家用記帳 - LINE Bot 觸發` workflow
4. 查看詳細執行記錄

### LINE Bot 日誌
- Render.com: Dashboard → Logs
- Heroku: `heroku logs --tail`
- Railway.app: Dashboard → Logs

---

## 🔒 安全建議

1. **不要**將任何金鑰提交到 Git
2. 定期輪換 Access Token
3. 使用 GitHub Actions 的 Secrets，不要在程式碼中硬編碼
4. 限制 LINE Bot 的使用權限（只讓特定帳號使用）

---

## 📞 技術支援

如有問題，請檢查：
1. GitHub Actions 執行記錄
2. LINE Bot 平台日誌
3. Google Cloud Console 活動記錄
