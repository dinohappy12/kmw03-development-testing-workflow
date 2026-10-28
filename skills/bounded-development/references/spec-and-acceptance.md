# 規格、完整小步與白話驗收

## 規格先留下可觀察條件
先讀本次需求、現行方法、既有驗收和部署界線。用短表：編號／誰要完成什麼／既有資料／預期成果／驗法／決策狀態。把真的未知留待補；例子與測試用價格不是本人真實商業條件。規格變更記理由及受影響項，不讓實作過程默默改目標。

小修正通常直接用一張表及一個案例；跨多輪／多模組才拆任務，記前置依賴及各自能展示的成果。不強制GitHub Issues或大量文件，沿用專案測試資料夾即可。任務／規格不構成發布授權。

## 驗法按證據層次選擇
1. 來源／格式：檔案、版本、JSON、連結、文字區塊結構；程式可查。
2. 工具實作：真的讀取／生成／寫入／回讀的結果；計畫和fixture不是實際帳號證據。
3. 語意／視覺：少量實際樣本，記誰審、看了什麼；同AI的自評不冒稱獨立測試。
4. 使用環境：本人手機／帳號／新對話實際操作；本機通過不能覆蓋。

每個完成條件先選能觀察結果的最高合適入口。例如文章可複製，要看實際三篇輸出是否三塊，不只看SKILL.md寫了可複製。LINE主文與接龍要查同區塊，不能分別找到四個字就通過。工具規則新增後要有故意錯的樣本，證明檢查會拒絕已知失敗。

## 測試執行器與續接
執行：`python scripts/run_bounded.py plan.json --state state.json --report report.json`。三檔必須不同位置；state與report是專案工作紀錄，不放進公共包。

每個commands項目含穩定id、argv字串陣列及可選timeout。預設最多30秒；若需90秒，填`"timeout":90,"timeout_reason":"此整合案例含已知等待，允許最多90秒"`。空理由仍封頂30秒，所有情形受剩餘總預算限制；180秒是預設總執行額度，不是每步時間或整段聊天時間。超時與工具啟動失敗皆屬未完成，不能當作品內容已判錯。

需要修正計畫時，保留同一state/report，執行時加`--revision-reason "修正命令參數，驗收條件不變"`。會保存前後plan hash、理由與已耗額度；不增加原budget、不改案例id、不清失敗數。原版state須先用原計畫讀取遷移才能修訂；已有兩敗或用盡輪數／時間仍停止。真正新增範圍另外記決策，不用新檔名逃避原停止條件。

工具啟動失敗會留下launch_error及當輪紀錄，timeout會留下command_timeout；進行中意外中斷則下次回報interrupted_run，先確認程序是否仍在運行、實際用時與結果，再人工核對紀錄續接，禁止直接刪state重跑。這些紀錄須由AI解讀，使用者只需讀白話結果。

## 複製結構檢查器
CLI：python scripts/check_copy_blocks.py --artifact OUTPUT.md --contract CONTRACT.json

支援text／markdown／無語言程式碼區塊與宿主writing區塊。JSON條件：
- copy_block_count：預期獨立區塊數。
- required_same_block：字串群組陣列；每群都須在同一區塊出現。
- first_block_suffix：第一塊必須以此精確文末結束，例如接龍及三個空白欄位。
- forbidden_in_blocks：禁止出現在可貼用區塊的明確字串。

範例條件可寫copy_block_count為2，required_same_block含商品名／指定訂購網址，或first_block_suffix為接龍換行1.換行2.換行3.。條件必須在看結果前從需求決定，不為通過而放寬。工具只讀檔及輸出JSON、exit0／1，不改成品、不叫模型、不自動修正或攔截聊天介面；按需接到既有預算執行器。

## 兩軸審閱
需求軸：各編號的符合／部分／不符／未測與證據。
規則軸：正式來源、資料真實、格式、素材、工具／費用／授權與發布。
各自保留問題；未測不得填通過。可由當前AI依序審閱，名稱如「同AI需求審閱／同AI規則審閱」。不預設另開兩個模型；獨立代理只有本次明確授權且必要時才使用。

## 一頁白話驗收單
- 現在可以試什麼？一行說成果與版本。
- 流程：小圖或一行路徑，指出這次真正改的地方。
- 結果表：需求編號／實際結果／證據／通過或待確認。
- 本人試用：一至三個動作、預期看到什麼；不要讓人重做AI已驗的每一個格式檢查。
- 影響與還原：改哪些模組、是否影響已確認內容、能否還原；檔案版本可退不代表已發布訊息或收款也能退。
- 狀態：human_review_required；未測環境和真正卡點。發布是後續獨立條件。

「快速」以降低閱讀與重複操作為目標，不承諾秒數、零錯誤或某模型方案等價。人確認一版不代表所有產業／裝置／帳號皆測過。

## 本輪採用來源
2026-10-18核對Matt Pocock skills v1.3.0，將理念改寫為本庫的G槽／Skill與教學驗收方法；沒有安裝或執行外部技能。
- https://github.com/mattpocock/skills/tree/v1.3.0
- 規格：https://github.com/mattpocock/skills/blob/v1.3.0/skills/engineering/to-spec/SKILL.md
- 完整小步：https://github.com/mattpocock/skills/blob/v1.3.0/skills/engineering/to-tickets/SKILL.md
- 行為驗證：https://github.com/mattpocock/skills/blob/v1.3.0/skills/engineering/tdd/SKILL.md
- 分軸審閱：https://github.com/mattpocock/skills/blob/v1.3.0/skills/engineering/code-review/SKILL.md
- 小圖／證據／影響：https://github.com/mattpocock/skills/blob/v1.3.0/skills/engineering/pr/SKILL.md
- 復盤：https://github.com/mattpocock/skills/blob/v1.3.0/skills/engineering/retro/SKILL.md
來源MIT授權；本檔為方法轉譯，檢查器自行撰寫。若後續複製來源程式或大段原文，須依原LICENSE保留著作權及許可文字。影片完整中文字幕已讀，指定5:29附近談驗收證據：https://www.youtube.com/watch?v=QqhyqMvdx5Q&t=329s 。
