# Claude Code 設置備忘錄

> 建立日期: 2026-04-15
> 用戶: flora (florashih324@gmail.com)

---

## GitHub 帳號資訊

| 項目 | 資訊 |
|------|------|
| **GitHub 用戶名** | flora001shih |
| **GitHub Email** | flora001shih@gmail.com |
| **常用 Repository** | https://github.com/flora001shih/stock-report |

### 本地 Git 設定

```bash
git config --global user.email "flora001shih@gmail.com"
git config --global user.name "flora"
```

---

## Google 認證資訊

### 主 Google 帳號
- **Email**: florashih324@gmail.com

### Google Cloud Console 專案
- **專案 ID**: flora-gae11
- **專案編號**: 208749772282
- **客戶端 ID**: 208749772282-dkm7d3tasdl2j1edveurvdk3oum47ia3.apps.googleusercontent.com
- **管理連結**: https://console.cloud.google.com/apis/credentials?project=flora-gae11

### 已啟用的 Google API

| API | 狀態 | 用途 |
|-----|------|------|
| Gmail API | ✅ 已啟用 | 發送美股報告 email |
| Google Sheets API | ✅ 已啟用 | 家用記帳試算表操作 |
| Google Drive API | ✅ 已啟用 | 存取 Google Drive 檔案 |
| Google Calendar API | ✅ 已啟用 | 查詢行事曆 |

**API 管理連結**: https://console.developers.google.com/apis/api?project=flora-gae11

---

## 重要檔案位置

| 檔案 | 位置 | 用途 |
|------|------|------|
| **Google 憑證** | `C:\Claude_Test_Lab\credentials.json` | OAuth 憑證檔案 |
| **Gmail Token** | `C:\Claude_Test_Lab\token_gmail.json` | Gmail API 存取 token |
| **Calendar Token** | `C:\Claude_Test_Lab\token_calendar.json` | Calendar API 存取 token |
| **Sheets Token** | `C:\Claude_Test_Lab\token.json` | Sheets API 存取 token |

> **注意**: 這些 token 檔案不要分享給他人，包含敏感的存取權限

---

## 主要 Google 試算表/檔案

### 璇璇家用記帳表
- **Spreadsheet ID**: `1J-Ia3CLNJxGL26zacWdj-85jsK_5NaS92OZRhoOyzUA`
- **Sheet 名稱**: 家用記帳合併
- **直接連結**: https://docs.google.com/spreadsheets/d/1J-Ia3CLNJxGL26zacWdj-85jsK_5NaS92OZRhoOyzUA/edit

### 家用記帳 Skill
- **位置**: `C:\Users\FW11P\.claude\skills\家用記帳\SKILL.md`
- **版本**: v2.0
- **功能**: 記錄三位家庭成员（友方、一銀、昇華）的收支記錄

---

## 美股報告 GitHub Actions

### Repository
- **名稱**: stock-report
- **URL**: https://github.com/flora001shih/stock-report
- **執行時間**: 每天 UTC 22:00 (台灣時間早上 6:00)

### GitHub Secrets 設定

前往: https://github.com/flora001shih/stock-report/settings/secrets/actions

| Secret 名稱 | 值 |
|-------------|-----|
| `GMAIL_TOKEN` | 基於 `gmail_token_base64.txt` 的 base64 字串 |
| `RECIPIENT_EMAIL` | florashih324@gmail.com |

### 重新生成 Gmail Token (若過期)

```bash
# 1. 刪除舊 token
rm "C:/Claude_Test_Lab/token_gmail.json"

# 2. 重新授權
cd "C:/Claude_Test_Lab"
python gmail_auth.py

# 3. 生成新的 base64
python setup_github_actions.py

# 4. 更新 GitHub Secrets 中的 GMAIL_TOKEN
```

---

## 查詢 Google 雲端檔案

### 方法 1: 使用 Google Drive 網頁介面
前往: https://drive.google.com
登入: florashih324@gmail.com

### 方法 2: 使用 Python 腳本

```bash
cd "C:/Claude_Test_Lab"
python list_drive_files.py
```

### 方法 3: 使用 Claude Code (推薦)

直接對 Claude Code 說：
```
幫我列出 Google 雲端硬碟最近修改的 3 個檔案
```

或
```
幫我列出 Google 雲端硬碟最近查看的檔案
```

Claude Code 會自動執行查詢腳本並顯示結果。

---

## Claude Code 相關

### Claude Code 版本
- **版本**: 2.1.109
- **更新命令**: `npm install -g @anthropic-ai/claude-code@latest`

### Claude Code 配置位置
- **設定檔**: `C:\Users\FW11P\.claude.json`
- **專案設定**: `C:\Claude_Test_Lab\.claude\`

### 已安裝的 Skill

| Skill 名稱 | 路徑 | 用途 |
|------------|------|------|
| 家用記帳 | `C:\Users\FW11P\.claude\skills\家用記帳\` | 家庭收支記錄 |

---

## 常用命令

### Git 推送更新
```bash
cd "C:/Claude_Test_Lab"
git add .
git commit -m "更新說明"
git push
```

### 測試美股報告 (本地)
```bash
cd "C:/Claude_Test_Lab"
python stock_report.py
```

### 重新授權 Gmail
```bash
cd "C:/Claude_Test_Lab"
python gmail_auth.py
```

---

## 重要提醒

1. **Gmail Token 有效期**: OAuth token 通常 7 天後會過期，需要重新授權
2. **GitHub Secrets 安全**: 不要在公開的程式碼中暴露 Secrets
3. **備份重要檔案**: 建議定期備份 `credentials.json` 和相關 token 檔案
4. **API 使用限制**: 注意 Google API 的使用配額

---

## 快速恢復指南 (重裝系統後)

1. **安裝 Claude Code**
   ```bash
   npm install -g @anthropic-ai/claude-code@latest
   ```

2. **設置 Git**
   ```bash
   git config --global user.email "flora001shih@gmail.com"
   git config --global user.name "flora"
   ```

3. **復原重要檔案**
   - 從備份還原 `credentials.json`
   - 從備份還原 `token_*.json` 檔案

4. **重新授權 (若需要)**
   ```bash
   python gmail_auth.py
   ```

5. **測試美股報告**
   ```bash
   python stock_report.py
   ```

---

**最後更新**: 2026-04-15
