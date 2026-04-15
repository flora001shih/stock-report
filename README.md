# 美股報告自動發送系統 (GitHub Actions 版本)

## 功能說明

使用 GitHub Actions 自動發送美股報告到 Gmail，包含：
- 道瓊工業指數 (DJI) 的漲跌幅
- 台積電 ADR (TSM) 的漲跌幅
- 郵件會自動加上 **[美股]** 標籤
- 發送新郵件後，自動將舊郵件移到垃圾桶

## 優勢

✅ **雲端執行** - 不需要電腦開機也能發送
✅ **完全免費** - GitHub Actions 公開 repository 免費
✅ **自動定時** - 每天台灣時間早上 6:00 自動執行

## 設置步驟

### 1. 創建 GitHub Repository

1. 前往 https://github.com/new
2. 創建一個新的公開 repository (例如: `stock-report`)
3. 記下您的 repository URL

### 2. 設置 GitHub Secrets

在 GitHub repository 中：
1. 點擊 **Settings** → **Secrets and variables** → **Actions**
2. 點擊 **New repository secret**

添加以下兩個 Secrets：

| Secret 名稱 | Secret 值 |
|-------------|-----------|
| `GMAIL_TOKEN` | 查看 `gmail_token_base64.txt` 文件的內容 |
| `RECIPIENT_EMAIL` | `florashih324@gmail.com` (或您的目標 Email) |

### 3. 推送代碼到 GitHub

在 `C:\Claude_Test_Lab` 目錄執行：

```bash
git init
git add .
git commit -m "Initial commit: Stock report with GitHub Actions"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

請將 `YOUR_USERNAME` 換成您的 GitHub 用戶名，`YOUR_REPO` 換成您的 repository 名稱。

### 4. 驗證設置

1. 推送後，前往 GitHub repository 的 **Actions** 頁面
2. 應該會看到 **「美股報告」** workflow
3. 點擊 **「Run workflow」** 手動測試
4. 確認每天 UTC 22:00 (台灣時間早上 6:00) 會自動執行

## 時間說明

- **執行時間**: 每天 UTC 22:00
- **台灣時間**: 每天 06:00 (UTC+8)
- **原因**: GitHub Actions 使用 UTC 時區

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `.github/workflows/stock_report.yml` | GitHub Actions 工作流程配置 |
| `stock_report.py` | 主程式 - 獲取股價並發送郵件 |
| `gmail_auth.py` | Gmail API 授權腳本 (本地測試用) |
| `setup_github_actions.py` | 生成 GitHub Secrets 設置說明 |
| `gmail_token_base64.txt` | Base64 編碼的 Gmail token (用於 GitHub Secrets) |

## 注意事項

1. **Gmail token 有效期**: OAuth token 通常 7 天後會過期，建議定期重新生成
2. **美股交易日判斷**: 週末和美股假期不會發送報告
3. **郵件清理**: 每次發送新郵件後，舊郵件會自動移到垃圾桶

## 本地測試

如果需要在本地測試：

```bash
# 重新授權 (如果 token 過期)
python gmail_auth.py

# 執行測試
python stock_report.py
```

## 故障排除

### 問題：GitHub Actions 執行失敗
- 檢查 GitHub Secrets 是否正確設置
- 檢查 Gmail token 是否過期 (重新執行 `python setup_github_actions.py`)

### 問題：收不到郵件
- 檢查 Gmail 垃圾信箱
- 檢查 Actions 頁面的執行日誌

### 問題：股價數據獲取失敗
- yfinance 服務可能暫時無法使用，請稍後再試

## 授權

本項目使用以下開源套件：
- yfinance
- google-api-python-client
- pytz
