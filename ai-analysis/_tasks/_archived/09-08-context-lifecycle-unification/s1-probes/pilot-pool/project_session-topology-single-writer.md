---
name: project_session-topology-single-writer
description: ai-rules 檔案單一寫入者拓撲＋hub-relay 工作法——寫入面/執行面邊界、授權不跨 session、複掃防線
metadata:
  node_type: memory
  type: project
  originSessionId: sess_d8de15e8-a98d-4c74-b58e-b5ba869564d7
---

**定案（user 裁示）**：ai-rules 檔案（skills/rules/code_reality）**單一寫入者＝ai-rules session**；codetour/mosaic 等 session＝執行端——ai-rules session 交代任務（驗證、dogfood、fix），執行端做完反饋，user 轉傳。

**Why**：根因是混寫事件——消費端 session 把泛化改動未經 review 直接寫進 ai-rules working tree；寫入權與規範 context 錯配（改 skill 的 session 沒載 ai-rules 寫作紀律）。單一寫入者把 concurrent modification 從「靠紀律避免」變「結構上不存在」；執行端=witness、ai-rules session=distiller，天然 Writer/Reviewer 分離。

**How to apply**：①執行端反饋格式＝機械證據（path:line、統計）＋proposed patch；②制度化＝consumer 入口文檔各一行（全域 bundle 不承載——空間稀缺）；③拓撲是**雙向對稱**：ai-rules session 跑**別的 repo** 的工作也止步 findings＋handoff 交付該 repo session 執行——審查 spawn 時預期 writer session 並行活躍（findings 行號是快照，handoff 要求接手方 rg 重新定位；檔案 mtime 是「能否動手」的機械信號）。

## hub-relay 工作法（穩態化）

**形態**：ai-rules session＝coordination hub（產 handoff→收回執→機械驗證〔relay claim＝快照〕→翻真相源文檔＋deploy→產下一個 handoff→roadmap 打勾）；**user＝郵差**（每輪兩次貼上：去程 handoff、回程回執）；執行端 session 自跑 build／審查／commit gate。**user 的第三能力＝app 層操作**（plugin 刷新等 GUI 動作 hub 接不到；「更新了」回報即觸發 hub 收尾）。細則：①雙向——執行端可反向派工給 ai-rules；②hub 可唯讀旁觀執行端 session（telemetry DB peek tail）；③資料丟失級緊急事項標 handoff 最頂。機制段已寫入 cr-lsp-replacement-roadmap（見 [[project_cr-live-faces-roadmap]]）。

**標準形態＝「執行端草稿進樹＋hub 審查結算」**：執行端（如 code-reality session）直接寫好 ai-rules 翻轉 diff＋跑 deploy，commit gate 留 hub——hub 審查補洞＋結算 commit。此為「草稿進樹」小額先例的擴大版，非拓撲破壞。**hub 審查不是橡皮章**（實際出貨：rule↔skill 鏡像漏翻位點、roadmap 狀態演進 drift、binary 落後一版、GUI-store 位置宣稱錯誤）——收回執後對 roadmap 做 consistency 全文複查是必要步（狀態演進只有 hub 視角看得到）。

## 邊界精化（各實例收斂）

- **工具執行 vs 檔案編輯**：單一寫入者管的是檔案編輯與 commit，不是工具執行——跨 repo 跑工具（重建另一 repo 的 db、產物落該 repo `.agent-tmp` scratch）不觸碰 tracked 檔案不越界；**能單貼一個 repo session 就不拆貼**（拆貼只在需另一 repo session 判斷/編輯其檔案時）。
- **user 明示授權可跨越**：user 原話授權下的小額設定檔跨 repo 編輯可做（先例：4 repo `.mcp.json` 批改）——拓撲是預設邊界非硬牆，但改動留各 repo working tree、commit gate 仍歸各 repo session。
- **muse 互動 session＝user 授權的第三類 writer（09-08 實證）**：user 直接在 muse session 做 ai-rules 工作（EP review 修正直接進 working tree）——產出品質可高（findings 表/結構修正全可用）但 muse 的 rules context 受 64KiB 截斷＝規範遵循有結構性缺口（算術鬆 ~2.3KB、findings 狀態欄過時類小錯）；user 慣例＝主 session 複審其 edits、不合理可回退（「你看一下他的修改，不合理你可以改回去」）。複審焦點＝數值算術與狀態一致性（被截掉的 quality-constraints/tool-discipline 正是這面）。
- **不明 working-tree diff 先歸屬對帳再歸因他人**：疑似並行 session 的改動，先與自己早前動作機械對帳（git log＋自己未提交遺留）——09-08 兩檔「muse 的修改」實為自己 git mv 順序陷阱遺漏的未提交編輯（見 [[git-mv-nesting-and-verification-traps]] 第 5 條）；歸因錯了複審方向就錯。
- **指派語的具體度決定處理面半徑**：user 直接指派「做 post-build＋commit 提案」→ 跨 repo 唯讀審查可做到提案級；跨 repo 檔案寫入與 commit 執行永遠等 user 原話。
- **symlink 陷阱**：跨 repo session 經 `~/.zcode/agents` symlink 的「本地」寫入會實際落 ai-rules tree（誤診型非故意越界）——實驗性 agent 定義前先驗 symlink 指向（[[agents-registry-split-design]]（溯源段））。
- **memory 池寫入者破口（09-07 觀察，歸因未定）**：本日弧 `project_*` 條目非 owning session 寫入（originSessionId 標其 id 但無該 Write 記錄；mtime 對應弧活動時段、內容正確無害）——疑 user 另一 session 或某機制做弧進行記錄；單一寫入者拓撲對 memory 池的涵蓋未證實，再現時先對帳 write 清單＋mtime 歸因再處置（2.8 池對帳閘門的掃描面會撈到這類條目，歸屬判斷需知此現象）。
- **commit gate 迴路定式**：relay session 不能代授權——commit 等級的 user 原話必須在檔案所屬 session 給（[[commit-consent-in-autonomous-mode]]）。
- **demand-pull 機制（user 治理裁示：加值工具弧由消費端觸發非工具方中央規劃）**：消費端 session 在**自己的** `backlog/` 開 `[cr-demand]` 卡（觸發場景＋實證缺口＋期望能力——寫自己的檔案不越界）；hub relay 收尾時 sweep 消費 repo → roadmap 需求收件匣 → user 裁決排程。參照 GitHub issues / inner-source 模式；discoverability 接線在 crg-query SKILL GATE 段。

## 迴路教訓（多輪實證的橫式）

- **「relay 交付＋接收方獨立複掃」每輪實際出貨**——relay 條款「多出來的才處理」讓接收方有權處理預期外 hit 而不越權：consistency gate 抓 frontmatter 舊分工、複掃抓殘留與偵測鍵過時、drift 掃描抓「定義源翻轉時教『怎麼刷新』的消費端文件」同步漂移。實例群見 [[relay-claims-verify-current-state]]。
- **rule↔skill 鏡像陳述是定義翻轉的系統性漏點**（[[feedback_drift-scan-include-variants]]）。
- **Edit 撞 "file modified since read"（並行 session 同檔）＝re-Read 後重套即可，非衝突信號**；並行活躍時 mtime 是機械信號（[[cr-live-faces-roadmap]]）。
- **跨 session 審查的 context 來源＝ReadSessionContext**（lite 摘要＋diff 雙源 review 即可判收編，不必直讀 transcript）——消費端 session 經 user 授權落草稿於 working tree、hub 指名 sess_id 查討論脈絡後收編，已實證。
- 消費端教訓回流收編的放置學：**單點收編消費端真相源最短鏈路**（如就緒等待契約歸 skills/ui-collab；always-on bundle 預算稀缺不入 rule）。

相關：[[project_blueprint-bootstrap-design]]、[[project_cr-live-faces-roadmap]]、[[commit-consent-in-autonomous-mode]]、[[relay-claims-verify-current-state]]
