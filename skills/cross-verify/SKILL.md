---
name: cross-verify
description: "當你要對一個問題做多源交叉查證時。/cross-verify <問題> [軸清單]——軸群（db/git/log/memory/cr/web）平行取證→交叉對帳→verdict＋unverified 標記。源枚舉制（web 軸須顯式點名才存在）；源缺場該軸 unverified 不阻斷合成。產出軌道①（可直接餵 judge-review）。"
argument-hint: "<問題> [軸:db,git,log,memory,cr,web]"
---

# /cross-verify — 多源交叉查證

單一問題的證據強度來自**獨立源的交叉**——單軸取證易被該源的盲區綁架（telemetry 只記 session 視角、memory 條目反映寫入當下、git 只見 committed）。本命令把「多源查證」固化為可重跑流程：軸群平行取證 → 交叉對帳 → 合成。

**受眾＝軌道①**（LLM 執行鏈）：產出是結構化 verdict，直接餵 `/judge-review` 當裁決材料；非人類 viewport（渲染類走 `/illustrate`）。源枚舉制吸收自 deep-research 教訓（自由 web 發散搜尋體感差）；GLM-5.3-Flash 鑑識弧（db/git/memory 三軸模型歸因對帳）為原型「真實案例」。

## 輸入（源枚舉制）

問題＋**軸清單**（顯式枚舉；省略時預設 `git,memory` 並印出所用軸清單）：

| 軸 | 源 | 缺場判定（spawn 前預檢） |
|----|----|------------------------|
| git | repo 歷史與工作樹 | 非 git repo |
| db | ZCode telemetry db.sqlite（per-message modelID／session 記錄） | db 路徑不存在 |
| log | 應用／工具 log（路徑隨問題給） | 指定檔不存在 |
| memory | memory 池條目（形態：repo `.agents/memory/` 主體或 `~/.zcode/cli/memories/projects/<proj>/memory/`〔多為 symlink 指主體〕；**檢索入口＝B 形態池 `_inventory.md`／A 形態池 MEMORY.md**——B 形態 `_inventory.md` 為全量 desc 投影、MEMORY.md 僅常駐定額（漏掃 _inventory.md 即漏證據）；A 形態池 MEMORY.md 即全量索引、可無 _inventory.md——形態判定見 [memory-audit](../memory-audit/SKILL.md)；`rg -i <關鍵詞> _inventory.md` 定位後 Read 條目檔 body） | 池路徑不存在 |
| cr | code-reality graph（refs／callers／impact_radius） | index 缺場／MCP 未連線 |
| web | 外部網路查證 | **未顯式點名＝軸不存在**（禁擅自加） |

## 流程

1. **源可用性預檢**：逐軸機械檢查上表缺場判定 → 缺場軸記 `[WARN] degraded：<軸> unverified（源缺場）`，**不派發該軸、不阻斷後續**
2. **平行取證**：每可用軸 spawn 一個 `cross-verify-investigator`（單一參數化 agent 檔，軸＝prompt 參數；背景群，spawn 規範見 [agent-workflow](../agent-workflow/SKILL.md)）。prompt 含：問題、軸、源路徑（db 檔／log 檔／memory 池／repo_root）、產出落點 `.agent-tmp/cross-verify/<run-id>/<axis>.md`。**落檔制**：findings 先落檔——session 中斷後新 session 從檔案接手，不靠對話記憶
   - CC 端：同方法論；`cross-verify-investigator` 全 registry 生成在場（roles/ 單一源雙投影）——CC `--agent` 可直接引用，或以 Agent tool spawn-time model 派發同內容 prompt（model 供給＝model-routing catalog，registry 部署預設＝agents/presets.toml）
3. **交叉對帳**：收各軸報告（直接讀落檔），逐條宣稱 vs 機械證據對照：跨軸一致 → `corroborated`；衝突 → 標 `conflict`（兩方證據並列，**不自行裁決**——同 dual-context 紀律，裁決交 judge）；僅單軸支持 → `single-source`
4. **合成**：verdict（問題的直接回答）＋逐條信心標記（corroborated / single-source / conflict / unverified）＋機械錨點（file:line／commit sha／jobId）＋unverified 軸清單。**unverified 不阻斷合成**——結論明確標「哪些部分缺源支撐」
5. **下游**：產出餵 `/judge-review`；findings 錨點的批次屬實性驗證（若需）歸 lite-verify（口徑統一：investigator 產證據、lite-verify 驗錨、judge 裁決——三方職責不互踩）

## 輸出格式

```
## Cross-verify Verdict — <問題>
軸清單：<列用到的軸>｜unverified：<缺場軸>

| # | 宣稱 | 證據（節錄） | 錨點 | 信心 |
|---|------|-------------|------|------|
| 1 | ... | ... | file:line / sha / jobId | corroborated |

結論：<一句話 verdict；conflict/unverified 的影響明示>
```
