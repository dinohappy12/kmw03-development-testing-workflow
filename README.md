# 黃嘉偉KMW03開發測試助手

**測試版｜Plugin 0.1.0｜Skill 0.3.0**

協助把需求整理成小步、檢查實際工具能力、定位問題、節制測試，最後交付白話驗收。先建議適合的模型及思考程度，請使用者依帳號實際選項手動切換。

## 安裝試用

1. [下載完整外掛 ZIP](dist/KMW03-development-testing-0.1.0.zip)。
2. 在 ChatGPT 的「外掛程式」選擇「新增 → 上傳外掛程式封存檔」，選擇下載的 ZIP；依畫面操作並確認儲存。
3. 新對話選用「黃嘉偉KMW03開發測試助手」，輸入：「我要修改一個既有技能，先建議模型，再幫我整理規格與有限測試。」

是否可上傳、儲存、執行程式與讀寫檔案，取決於帳號及當前工具權限。只有真實儲存並回讀後，才能稱帳號安裝完成。本版本尚待新對話、手機及學生帳號實測。新專案可使用手機對話規劃；本機檔案、程式與 GitHub 操作須有對應工具及授權。

## 內容與來源

- 主技能：[SKILL.md](skills/bounded-development/SKILL.md) 與 [啟動設定](skills/bounded-development/agents/openai.yaml)。
- 參考資料、有限測試執行器與複製結構檢查器均放在 skills/bounded-development 內；必要檔案已包含於 ZIP。
- 改編方法參考 [Matt Pocock skills v1.3.1](https://github.com/mattpocock/skills/releases/tag/v1.3.1)，詳見包內來源適配記錄；本版不依賴安裝其工具。
- P019 是老師維護的正式母版；此倉庫與 ZIP 是交付副本。

此倉庫為公開內容。請勿將學生私人資料、金鑰、帳號資訊或工作中產生的測試結果加入。

