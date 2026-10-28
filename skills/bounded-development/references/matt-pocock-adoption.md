# Matt Pocock skills 適配紀錄

## 版本基準
2026-10-28 官方 GitHub API 與 release 頁核對：最新正式發行 **v1.3.1**，2026-10-04T12:48:18Z 發布，固定 commit `24fe0ef7737efae15c87225755e9f6f5965e4888`。當日 main 為 `59db609eb1e18aaf59b63284d0e52255aff0c63c`（2026-10-27），已有後續提交，但不把 main 當作另一個已發行版本。未發現新版正式 release；這是查詢日快照，非永久結論。

P019 0.2.0 已採用 v1.3.0 的規格、小步、兩軸審閱、證據與復盤。本輪不把既有方法當作全新功能，僅補新版差異及 ChatGPT 適配。未執行第三方 installer，未整套安裝來源 Skills，也沒有把來源的外部指令當本專案授權。

## 採用與取捨
| 來源方法 | 本庫處理 |
|---|---|
| implement-spec 的依賴圖與可開始任務 | 採完整小步、前置條件、整合後驗證；預設單一 AI 依序，不強制多代理、worktree 或 tracker |
| 整合分支與 PR 分開 | PR 是交付選項，是否 main 依實際授權與專案規則；不把開 PR 當測試已過 |
| diagnosing-bugs | 採可重現症狀、縮小案例、可否證假設、一次一變因、回歸證據；不採無限探測或固定數百次重播 |
| to-tickets／tdd | 保留能展示的完整路徑及獨立預期；小型改字不強迫寫測試或多一道確認 |
| code-review | 維持需求／規則雙軸；同 AI 與獨立審閱明確區分，不自動派代理 |
| pr／retro | 採小圖、前後證據、可逆性與影響；復盤優先既有工具，沒有真實問題不累加指令 |
| v1.3.1 的實際 Skill 呼叫修正 | 提及名稱不等於載入；只用宿主可用入口。人手啟動的外部 Skill 不假裝可自動叫用 |
| GLOSSARY／setup 等來源慣例 | 讀既有文件即可，不自動改檔名或強迫 ChatGPT 裝 Claude 環境 |

## 完整來源與授權
以下原文已讀；本包為自行撰寫的繁體中文方法適配，未打包來源程式或大段原文。來源 MIT（Copyright 2026 Matt Pocock）。若日後直接複製 substantial portions，須隨包保留原 LICENSE；pr 原方法另註 Dex Horthy／Humanlayer show-me credit，直接移植時不得遺漏。

- [正式發行與變更](https://github.com/mattpocock/skills/releases/tag/v1.3.1)
- [implement-spec](https://github.com/mattpocock/skills/blob/24fe0ef7737efae15c87225755e9f6f5965e4888/skills/engineering/implement-spec/SKILL.md)
- [to-tickets](https://github.com/mattpocock/skills/blob/24fe0ef7737efae15c87225755e9f6f5965e4888/skills/engineering/to-tickets/SKILL.md)
- [tdd](https://github.com/mattpocock/skills/blob/24fe0ef7737efae15c87225755e9f6f5965e4888/skills/engineering/tdd/SKILL.md)
- [diagnosing-bugs](https://github.com/mattpocock/skills/blob/24fe0ef7737efae15c87225755e9f6f5965e4888/skills/engineering/diagnosing-bugs/SKILL.md)
- [code-review](https://github.com/mattpocock/skills/blob/24fe0ef7737efae15c87225755e9f6f5965e4888/skills/engineering/code-review/SKILL.md)
- [pr](https://github.com/mattpocock/skills/blob/24fe0ef7737efae15c87225755e9f6f5965e4888/skills/engineering/pr/SKILL.md)
- [retro](https://github.com/mattpocock/skills/blob/24fe0ef7737efae15c87225755e9f6f5965e4888/skills/engineering/retro/SKILL.md)
- [LICENSE](https://github.com/mattpocock/skills/blob/24fe0ef7737efae15c87225755e9f6f5965e4888/LICENSE)
- [show-me credit](https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md)

指定 YouTube（QqhyqMvdx5Q）完整 zh-TW 字幕已讀，共 280 段，涵蓋 0～642.239 秒；未播放影像／音訊。影片描述的是 1.3 方向，版本判斷仍以官方 release 為準。不把影片提到的加速或自動化效果當作本庫保證。

其他比較：Superpowers 的根因與完成證據、GSD 的分階段續接、BMAD 的依規模規劃。僅作取捨參考，未安裝或併入框架依賴；主方法仍以 P019 與上表為準。
