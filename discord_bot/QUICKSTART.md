# 🚀 Discord Bot 記帳 - 快速設定指南

## 需要準備的東西

✅ [ ] Discord Bot Token (你已經有了！)
✅ [ ] GitHub 帳號
✅ [ ] Render.com 帳號 (免費)
✅ [ ] Google Sheets API 憑證 (你已經有了)

---

## 第一步：設定 GitHub Secrets (5分鐘)

前往你的 GitHub Repository → Settings → Secrets and variables → Actions → New repository secret

### 需要新增的 Secrets：

| 名稱 | 值 | 獲取方式 |
|------|-----|----------|
| `DISCORD_BOT_TOKEN` | 你的 Discord Bot Token | 從 Discord Developer Portal 獲取 |
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

## 第二步：部署到 Render.com (5分鐘)

1. 前往 [https://render.com/](https://render.com/)
2. 點擊「Sign Up」並用 GitHub 登入
3. 點擊「New +」→「Web Service」
4. 選擇你的 Repository
5. 填寫設定：

```
Name: discord-bot-accounting
Root Directory: discord_bot
Build Command: pip install -r requirements.txt
Start Command: python app.py
```

6. 添加環境變數（點擊「Advanced」→「Add Environment Variable」）：

| Key | Value |
|-----|-------|
| `DISCORD_BOT_TOKEN` | 你的 Discord Bot Token |
| `GITHUB_TOKEN` | (你的 GitHub PAT) |
| `GITHUB_REPO` | `flora001shih/C--Claude-Test-Lab` |

7. 點擊「Create Web Service」
8. 等待部署完成（約2-3分鐘）
9. 檢查 Logs 確認 Bot 已上線

---

## 第三步：邀請 Bot 到 Discord 伺服器 (2分鐘)

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
2. 選擇你的 Application (GitHubAccounting_Bot)
3. 點擊「OAuth2」→「URL Generator」
4. 勾選權限：
   - `bot`
   - 在 bot 區塊中勾選：
     - `Send Messages`
     - `Read Messages/View Channels`
     - `Embed Links`

5. 複製生成的邀請 URL
6. 在瀏覽器開啟 URL 並選擇伺服器
7. 點擊「授權」

---

## 第四步：測試！ (1分鐘)

### 在 Discord 中測試

1. 在你的伺服器中找到 Bot
2. 發送測試訊息：
   ```
   !記帳 友方 測試 -1
   ```

3. 應該收到回覆：
   ```
   ✅ 記帳請求已送出！

   📅 日期: 今天
   👤 人物: 友方
   📝 明細: 測試
   💰 金額: -1

   執行結果將會通知您。
   ```

### 驗證結果

開啟你的 Google Sheets `家用記帳合併`，應該看到新記錄已加入。

---

## ✅ 完成！

現在你可以在 Discord 隨時記帳了！

### 常用指令

| 指令 | 說明 |
|------|------|
| `!記帳 今天 友方 晚餐炒麵 100` | 友方今天花 100 元 |
| `!記帳 昨天 一銀 南方莊園票券 1390` | 一銀昨天花 1390 元（記到昨天的月份欄位） |
| `!記帳 友方 午餐 -50` | 友方今天花 50 元（日期預設今天） |
| `!記帳 友方 早餐 -50 2026/04/20` | 友方在 2026/04/20 花 50 元 |
| `!說明` | 顯示幫助訊息 |

**⚠️ 重要：日期決定記帳位置**
- 日期決定了資料會寫入**哪個月份的欄位**
- 例如：今天是 5 月 1 日，但你記「昨天」，會記到 4 月欄位
- 不指定日期預設為「今天」

---

## 🔍 故障排除

### Bot 沒有回應
- 檢查 Render 服務是否已啟動
- 檢查 DISCORD_BOT_TOKEN 是否正確
- 查看服務 Logs

### 記帳失敗
- 檢查 GitHub Actions 是否執行 (Repository → Actions)
- 確認 GITHUB_TOKEN 有 repo 權限
- 檢查 GOOGLE_CREDENTIALS 是否正確

### Google Sheets 沒有更新
- 確認日期對應當前月份
- 確認欄位沒有填滿 (第15-49列)

---

## 📞 需要幫助？

查看 [README.md](README.md) 了解詳細設定步驟和故障排除。
