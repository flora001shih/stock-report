# Gmail Janitor - Gmail 自動整理工具

自動將 Gmail 收件匣中的郵件分類並整理到待審標籤，支援定期排程執行與郵件通知。

## 功能特色

- **四種分類標籤**：自動將郵件分類為純廣告、系統通知、疑似可退訂、垃圾慣犯
- **IMPORTANT 豁免**：自動跳過被標示為重要的郵件
- **白名單保護**：銀行、投資、信用卡等重要郵件自動豁免
- **定期排程**：每年 6/30 和 12/31 自動執行整理
- **預告通知**：執行前一週（6/23 和 12/24）發送預告郵件
- **結果報告**：整理完成後發送統計報告郵件
- **不刪除郵件**：僅分類和封存，安全無虞

## 目錄結構

```
.
├── .github/
│   └── workflows/
│       └── gmail_maintenance.yml    # GitHub Actions 工作流程
├── gmail_janitor.py                  # 主要整理腳本
├── send_notification.py             # 郵件通知腳本
├── gmail_restore_important.py        # IMPORTANT 郵件還原工具
├── check_all_labels_important.py     # 檢查標籤工具
└── README.md                         # 本文件
```

## 安裝與設定

### 1. 前置需求

- Python 3.7+
- Gmail API 權限

### 2. 安裝依賴

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib pytz
```

### 3. 設定 Gmail API 憑證

首次執行時需要進行 OAuth 授權：

```bash
python gmail_janitor.py
```

授權完成後，會產生 `token_gmail.json` 檔案。

### 4. GitHub Actions 設定

#### 4.1 將憑證儲存到 GitHub Secrets

1. 將 `token_gmail.json` 的內容進行 Base64 編碼：

```bash
# Linux/Mac
base64 -w 0 token_gmail.json

# Windows PowerShell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("token_gmail.json"))
```

2. 將編碼後的字串複製

3. 到 GitHub 倉庫設定 Secrets：
   - 進入 `Settings` > `Secrets and variables` > `Actions`
   - 點擊 `New repository secret`
   - Name: `GMAIL_TOKEN`
   - Value: 貼上 Base64 編碼的字串
   - 點擊 `Add secret`

#### 4.2 推送檔案到 GitHub

```bash
git init
git add .
git commit -m "Add Gmail Janitor automation"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## 使用方式

### 本地執行

#### 完整整理

```bash
python gmail_janitor.py
```

#### 發送預告通知

```bash
python send_notification.py --type warning
```

#### 發送結果通知

```bash
python send_notification.py --type result
```

### GitHub Actions 自動執行

#### 排程時間

| 類型 | 日期 | 台灣時間 | UTC 時間 |
|------|------|----------|----------|
| 預告通知 | 6月23日 | 08:00 | 00:00 |
| 預告通知 | 12月24日 | 08:00 | 00:00 |
| 正式執行 | 6月30日 | 08:00 | 00:00 |
| 正式執行 | 12月31日 | 08:00 | 00:00 |

#### 手動觸發

1. 到 GitHub 倉庫的 `Actions` 頁面
2. 選擇 `Gmail Maintenance` 工作流程
3. 點擊 `Run workflow`
4. 選擇執行模式：
   - `full`: 完整執行（預告 + 整理 + 結果）
   - `warning`: 僅發送預告
   - `janitor`: 僅執行整理
   - `result`: 僅發送結果

## 分類規則

### 四種標籤

| 標籤名稱 | 說明 | 判斷條件 |
|----------|------|----------|
| [AI]待審刪-1.純廣告類 | 電商促銷、行銷活動 | 包含促銷、特賣、折扣、優惠等關鍵字 |
| [AI]待審刪-2.系統通知類 | 超過1個月的不重要登入提醒 | 包含更新、登入、驗證、通知等系統關鍵字 |
| [AI]待審刪-3.疑似可退訂 | 以前訂閱但現在不看的內容 | 郵件地址包含 newsletter、noreply 等模式 |
| [AI]待審刪-4.垃圾慣犯 | 發送頻率高但從不閱讀的寄件者 | 來自已知垃圾發信者清單 |

### 豁免條件

以下情況郵件會被自動豁免，不會被分類：

1. **標示為 IMPORTANT** 的郵件
2. 包含以下關鍵字：銀行、投資、信用卡、帳單、bank、investment、credit card、bill
3. 來自個人郵件地址（gmail.com、outlook.com、hotmail.com）
4. 來自垃圾慣犯清單的寄件者

## 郵件通知

### 預告郵件

- **標題**: `[AI]預告：Gmail 自動整理任務即將執行`
- **發送時間**: 6月23日 和 12月24日 08:00 台灣時間
- **內容**: 說明將在一週後執行整理任務

### 結果郵件

- **標題**: `[AI]報告：Gmail 半年度自動整理已完成`
- **發送時間**: 6月30日 和 12月31日 整理完成後
- **內容**: 包含統計數據
  - 總共掃描封數
  - 總共處理封數
  - 各標籤分類結果
  - 驗證結果（是否有遺漏的 IMPORTANT 郵件）

### 系統通知標籤

所有由系統自動發送的郵件都會自動加上 `[AI]系統通知` 標籤。

## 統計報告

執行後會產生 `gmail_janitor_report.json` 檔案，包含以下資訊：

```json
{
  "executed_at": "2026-06-30T00:00:00",
  "completed_at": "2026-06-30T00:05:30",
  "duration_seconds": 330.5,
  "total_scanned": 5432,
  "total_processed": 1234,
  "total_skipped": 4198,
  "skipped_important": 56,
  "skipped_whitelisted": 4142,
  "verification_passed": true,
  "categories": {
    "[AI]待審刪-1.純廣告類...": 456,
    "[AI]待審刪-2.系統通知類...": 321,
    "[AI]待審刪-3.疑似可退訂...": 234,
    "[AI]待審刪-4.垃圾慣犯...": 223
  },
  "label_scan_results": {
    "[AI]待審刪-1.純廣告類...": 456,
    "[AI]待審刪-2.系統通知類...": 321,
    "[AI]待審刪-3.疑似可退訂...": 234,
    "[AI]待審刪-4.垃圾慣犯...": 223
  }
}
```

## 故障排除

### 重新授權

如果出現授權錯誤：

```bash
rm token_gmail.json
python gmail_janitor.py
```

### 檢查 IMPORTANT 郵件

檢查待審標籤中是否還有遺漏的 IMPORTANT 郵件：

```bash
python check_all_labels_important.py
```

### 還原 IMPORTANT 郵件

將待審標籤中的 IMPORTANT 郵件還原到收件匣：

```bash
python gmail_restore_important.py
```

## 安全性

- 不會刪除任何郵件
- 所有 IMPORTANT 郵件都會被豁免
- 使用 Gmail 官方 API
- 憑證以 Base64 編碼儲存在 GitHub Secrets
- 支援手動確認後再執行

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

---

**版本**: 1.0.0
**最後更新**: 2026年4月
