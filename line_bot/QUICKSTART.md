# 🚀 LINE Bot 記帳 - 快速設定指南

## 需要準備的東西

✅ [ ] LINE 開發者帳號
✅ [ ] GitHub 帳號
✅ [ ] Render.com 帳號 (免費)
✅ [ ] Google Sheets API 憑證 (你已經有了)

---

## 第一步：創建 LINE Channel (5分鐘)

1. 開啟 [https://developers.line.biz/console/](https://developers.line.biz/console/)
2. 點擊「Start using LINE Developers API」
3. 登入你的 LINE 帳號
4. 點擊「Create new provider」→ 輸入名稱 (如「家用記帳」)
5. 點擊「Create a Channel」→ 選擇「Messaging API」
6. 填寫 Channel 名稱 (如「記帳小助手」)
7. 同意條款並建立

**重要：記錄以下三個值**
- `Channel ID`
- `Channel Secret` (在 Basic settings)
- `Channel Access Token` (在 Messaging API → 發行)

---

## 第二步：設定 GitHub Secrets (5分鐘)

前往你的 GitHub Repository → Settings → Secrets and variables → Actions → New repository secret

### 需要新增的 Secrets：

| 名稱 | 值 | 獲取方式 |
|------|-----|----------|
| `LINE_CHANNEL_SECRET` | (從第一步複製) | LINE Developers → Basic settings |
| `LINE_CHANNEL_ACCESS_TOKEN` | (從第一步複製) | LINE Developers → Messaging API → 發行 |
| `GITHUB_TOKEN` | (需創建) | 見下方說明 |
| `GOOGLE_CREDENTIALS` | (需編碼) | 見下方說明 |

### 創建 GITHUB_TOKEN

1. 前往 GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 點擊「Generate new token」
3. 選擇權限：勾選 `repo` (全部)
4. 複製 token（只會顯示一次！）

### 編碼 GOOGLE_CREDENTIALS

**Windows:**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\Claude_Test_Lab\flora-gae11-48f2f2e53de7.json")) | clip
```

**貼上**剪貼簿的內容到 GitHub Secret `GOOGLE_CREDENTIALS`

---

## 第三步：部署到 Render.com (5分鐘)

1. 前往 [https://render.com/](https://render.com/)
2. 點擊「Sign Up」並用 GitHub 登入
3. 點擊「New +」→「Web Service」
4. 選擇你的 Repository
5. 填寫設定：

```
Name: line-bot-accounting
Root Directory: line_bot
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

6. 添加環境變數（點擊「Advanced」→「Add Environment Variable」）：

| Key | Value |
|-----|-------|
| `LINE_CHANNEL_SECRET` | (你的 LINE Channel Secret) |
| `LINE_CHANNEL_ACCESS_TOKEN` | (你的 LINE Channel Access Token) |
| `GITHUB_TOKEN` | (你的 GitHub PAT) |
| `GITHUB_REPO` | (你的帳號/倉庫名，如: username/repo-name) |
| `GITHUB_WORKFLOW_ID` | `accounting.yml` |

7. 點擊「Create Web Service」
8. 等待部署完成（約2-3分鐘）
9. **複製 Web Service URL** (如: https://line-bot-accounting.onrender.com)

---

## 第四步：設定 LINE Webhook (2分鐘)

1. 回到 [LINE Developers Console](https://developers.line.biz/console/)
2. 選擇你的 Channel
3. 點擊左側「Messaging API」
4. 找到「Webhook settings」
5. 將 Webhook URL 設為：
   ```
   https://你的app-url.com/webhook
   ```
   (例如: https://line-bot-accounting.onrender.com/webhook)
6. 勾選「Use webhook」
7. 點擊「Verify」應該顯示「Success」

---

## 第五步：測試！ (1分鐘)

### 在手機上測試

1. 開啟 LINE App
2. 搜尋你的 Bot (可以掃描 QR Code 或搜尋 LINE ID)
3. 點擊「加入好友」
4. 發送測試訊息：
   ```
   記帳 友方 測試 -1
   ```

5. 應該收到回覆：✅ 記帳成功！

### 驗證結果

開啟你的 Google Sheets `家用記帳合併`，應該看到新記錄已加入。

---

## ✅ 完成！

現在你可以隨時在 LINE 上記帳了！

### 常用指令

| 指令 | 說明 |
|------|------|
| `記帳 友方 午餐 -150` | 友方今天花 150 元（預設今天） |
| `記帳 一銀 南方莊園票券 1390` | 一銀今天花 1390 元（預設今天） |
| `記帳 昇華 晚餐 -200 昨天` | 昇華昨天花 200 元（記到昨天的月份欄位） |
| `記帳 友方 早餐 -50 2026/04/16` | 友方在 2026/04/16 花 50 元 |

**⚠️ 重要：日期決定記帳位置**
- 日期決定了資料會寫入**哪個月份的欄位**
- 例如：今天是 5 月 1 日，但你記「昨天」，會記到 4 月 30 日（4 月欄位）
- 不指定日期預設為「今天」

---

## 🔍 故障排除

### Webhook 驗證失敗
- 確認 Webhook URL 正確
- 確認 Render 服務已啟動
- 等待 1-2 分鐘後重試

### 沒有收到回覆
- 檢查 GitHub Actions 是否執行 (Repository → Actions)
- 確認 GITHUB_TOKEN 有 repo 權限
- 檢查 GOOGLE_CREDENTIALS 是否正確

### Google Sheets 沒有更新
- 確認日期對應當前月份
- 確認欄位沒有填滿 (第15-49列)

---

## 📞 需要幫助？

查看 [DEPLOYMENT.md](DEPLOYMENT.md) 了解詳細設定步驟和故障排除。
