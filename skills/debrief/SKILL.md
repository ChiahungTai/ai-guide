---
name: debrief
description: "AI 改完 code 想理解改了啥 / what changed / 聽取報告 / 檢查 AI 產出 / brief / debrief——七段理解簡報（意圖/行為黑盒子/前後差異/檔案地圖/波及缺口/驗證證據/認知誤差點）。理解非審判：機器 finding 交 /code-review、結構交 /illustrate。深度選配：日常弧判斷材料（做了什麼/證據/誤差點）由任務家報告殼實作章節吸收（post-build hook 2）；debrief＝模組/檔案級深挖。無參數=簡報 uncommitted 變更（fallback：EP baseline 任務弧，無則 HEAD~1）。"
when_to_use: "After AI coding: understand what changed (behavior / before-after / file map), force runnable evidence per feature (NONE 逼問), surface cognitive gaps. Deep-dive optional — routine judgment material lives in the task-home Report Shell implementation chapter (post-build hook 2). NOT for: diff correctness findings (/code-review), structure viewport (/illustrate), existence skepticism (/smell-detector)."
argument-hint: "無參數=uncommitted | commit hash | branch | --md"
allowed-tools: ["Read", "Grep", "Glob", "Bash", "Agent"]
---

# /debrief — AI 改動理解簡報（行動後聽取報告）

> **受眾：layer 3 人類 viewport / B 軸**。AI coding 任務結束後，把「改了什麼、為什麼、證據在哪、哪裡可能會錯意」渲染成一份人可直接判讀的簡報。與 `/smell-detector`（行動前：壞味道偵測）對仗——偵察在行動前，debrief 在行動後。
>
> **深度選配（弧後敘事政策化）**：日常弧的判斷材料（做了什麼／驗證證據／認知誤差點）已由 Report Shell 實作章節吸收（post-build hook 2 自動、commit 前穩定點，見 [illustrate html-mode](../_common/illustrate-html-mode.md)「殼生命週期掛點」）；debrief 的獨特價值在**模組/檔案級深挖**（波及缺口、hub 波及、跨檔敘事）——user 點名深挖時才跑，跳過不算欠債。
>
> **理解非審判**：不產機器 finding（正確性交 `/code-review`）、不審結構（交 `/illustrate`）、不質疑存在（交 `/smell-detector` zoom）。人在讀簡報的過程中自然完成方向判讀（「這是我要的嗎」）。
>
> 受眾模型見 [AGENTS.md](../../AGENTS.md)「命令的受眾視角」；理論（A/B 軸、證據階層、認知誤差）見 [acceptance-evidence](../../rules/acceptance-evidence.md)。

委託 Skills：
- [rules-reminder](../rules-reminder/SKILL.md) — Bash 規則
- [mermaid](../mermaid/SKILL.md) — MD 模式（`--md` 時）

## 黑盒子（input → output）

- **input**：變更範圍——commit hash / branch 參數指定優先；無參數且 context EP／卡 Plan 記有 baseline（或殼頭可讀）→ 任務弧模式（`git diff <baseline>..HEAD`＋uncommitted，機制見 [code-review](../code-review/SKILL.md)「任務弧模式」）；無任務 baseline → uncommitted 模式（`git diff`＋`git diff --cached`）；uncommitted 亦空 → `git diff HEAD~1` 兜底。弧範圍內的非本弧 commits／uncommitted 檔列「**非本弧項**」清單、不納入簡報主體
- **output**：七段倒金字塔簡報——Console（預設，ASCII 精簡）；`--md` 寫 `ai-analysis/reports/debrief-<scope>.md`（多級標題完整展開，Mermaid 可用）

## grounding 紀律（不是只看 diff 說故事）

先讀受影響檔案的 **baseline（變更前）程式碼**——理解架構、慣例，再讀 diff。只看 diff 會把「融入既有結構的程度」講錯。

## 七段輸出合約（倒金字塔；深度隨改動規模伸縮）

| # | 段 | 內容 |
|---|-----|------|
| 1 | **意圖一句話** | 這次改動解決什麼問題、為什麼改 |
| 2 | **行為黑盒子** | 改動觸及的核心模組/函式：input/output + 演算法；**明確判定「對外行為變了 vs 純結構重構」**（input/output 合約不變時，這句判定本身就是最高價值訊息）。改動以 `.md` 規則/命令為主時，本段渲染 **behavior delta**：AI 讀了改的 rule 後會做什麼不同 + 影響 UC |
| 3 | **前後差異** | 語義 diff——能力/行為的 delta，非行數增減；機械底稿：delta_tour `.tour`（宣稱對照三態＋實際變動模組＋退化/跨面警示；若可跑 code_reality，見下方） |
| 4 | **檔案地圖** | per-file 1-2 行，**按角色分組**（核心邏輯/配套/測試/文檔）——分組顯現改動形狀（「核心其實只有 2 檔，其餘配套」） |
| 5 | **波及與缺口** | 受影響消費者 + 該同步未同步（下游/索引/文件/測試）；hub symbol 波及用 `hub_refs` 聚合（若可跑 code_reality，見下方） |
| 6 | **驗證證據** | demo-checklist：feature → 可跑 target → 覆蓋。**NONE 不掩蓋——「沒 demo = 沒證明完成」** |
| 7 | **認知誤差點** | 主動揭露「我可能哪裡會錯意」：詮釋假設（「你說 X 我理解成 Y」）/ 歧義選擇（「兩種解讀我選 A 因為…」）/ 推斷行為（「spec 沒寫死，我推斷的」）/ 動態漂移（Type B：跨段落目標悄然偏移）。每點附確認問題，人一句「對/不對」校正 |

小改動不硬撐七段全滿——行為段可一句話；大改動每段完整。Console 紀律：精簡章節、禁 Mermaid 語法（md 模式才可用）。第 7 段前三類（詮釋假設/歧義選擇/推斷行為）是靜態詮釋偏差（Type A，單時點）；動態漂移是累積偏移（Type B）——兩型見 [acceptance-evidence skill](../acceptance-evidence/SKILL.md)「Intent Drift 的兩型」。

**code_reality 機械底稿（若 repo 可跑 code_reality——偵測單一真相源見 [code-reality](../code-reality/SKILL.md)）**：第 3 段底稿＝delta_tour 產出（`.tour` description：宣稱對照三態＋實際變動模組＋退化/跨面警示）——持久版**復用** post-build hook 2 產物（單一產點＝post-build 完成；無 post-build 弧＝implement 階段 6 fallback；`.tours/delta/` 進 git）；尚無持久版（弧未收尾）且時點條件成立 → 本命令自產**臨時版**（落 `.agent-tmp/`，不寫持久目錄）。產出機制與時點條件（HEAD == baseline 不產出、stale 跳過）見 [code-review](../code-review/SKILL.md) 模式 B。宣稱抽取只認特定模組路徑前綴——不符前綴的變更宣稱欄恆 NONE，視為「未提供對照」（單欄邊集差異仍可用），不當「EP 無宣稱」解讀。**第 3 段走讀載體＝delta_tour**（UC-B「走讀時」消費點）：時點條件成立時，同組 a/b sidecar 跑 `code-reality delta_tour <a> <b> --ep <ep.md> --repo <repo>`，簡報附產出 `.tour` 路徑＝人類走讀入口（CodeTour vsix panel 點開即走；目錄版控契約見 [tour-bootstrap](../tour-bootstrap/SKILL.md)；a/b 解析真相源——code-review 模式 B）。第 5 段 hub symbol 波及吃 `hub_refs` 聚合（callers/callees 按目錄、test/prod 切分＋hazard 註記——dynamic dispatch「0 refs 可刪」誤判防護，規則見 code-reality skill）。機械產物取代 LLM 逐檔推導，渲染成人類 viewport 仍是本命令職責。未裝、缺 baseline snapshot 或時點不符 → LLM 推導（既有行為不變）。工具用法真相源：[code-reality](../code-reality/SKILL.md) skill。

### 第 6 段 demo target 挑選規則（優先序）

1. `demo_*.py` / `scripts/demo_*.py` / `notebooks/*.ipynb`（既有 demo）
2. 既有 test（`test_<feature>.py`）——可跑驗證
3. 新功能入口 method（`ClassName.method()`）——標「需手動跑 / 無現成 demo」
4. 都沒有 → **NONE** + ⚠️（該 feature 沒證明完成，人該問「這功能怎麼驗？」）

**demo target 用 repo-root 相對路徑**（terminal Cmd+Click 可點開）。覆蓋欄：`full` / `partial`（僅 happy path）/ `NONE`。

**清單完整性**：feature 清單本身可能漏——列表要對照第 4 段檔案地圖，人用 domain 直覺找「改了 code 卻沒被列的功能」。

### 第 2 段 product-type 偵測（不硬套）

| 產品形態 | 觸發 | 第 2 段渲染 |
|----------|------|------------|
| code | `.py`/`.pyx`/`.ts` 等程式碼變更為主 | input/output + 演算法 |
| docs/rules | `.md` 規則/命令/instruction 檔變更為主 | behavior delta + 影響 UC |
| 混合 | code + docs 同改 | 兩種都列 |

## 與其他命令協作

| 想問的問題 | 命令 |
|-----------|------|
| AI 改了啥、證據在哪、哪裡會錯意（行動後） | `/debrief` |
| 哪裡有壞味道（行動前/審既有） | `/smell-detector` |
| 結構長怎樣 | `/illustrate` |
| 改得對不對（機器 finding） | `/code-review` |

## 流程位置

```
/smell-detector（行動前偵察）→ EP（定稿生殼〔hook 1〕）→ /implement → /debrief（深度選配：模組/檔案級深挖；弧後敘事選配不欠債）→ /post-build（機器收尾鏈；完成時殼 refresh〔hook 2〕＝實作章節＋持久 delta tour）→ /commit
```
