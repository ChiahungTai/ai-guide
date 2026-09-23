# AIR-174 — governance hook runtime 統一到 uv-managed Python 3.12

> **ep_type**: implementation
> **author_family**: codex

## 實作總覽

目前三個 harness 的 tracked hook registrations 使用 bare `python3`；本機實際落到 macOS CommandLineTools Python 3.9.6，而 repo runtime contract 已是 Python >=3.12。這次把 hook runtime ownership 收回 governance installer：安裝／check／verify 時由 installer 用 uv 查找已安裝的 managed Python 3.12，render 成絕對 interpreter path；hook fire 本身不再依賴 uv、PATH、project discovery 或 cache。

已決策：不改 `/usr/bin/python3`、不改 user PATH、不採每次 hook 都 `uv run`。Muse read-only review 實測指出 per-fire `uv run` 會新增 cache 初始化 fail-open 與 timeout tail，故採 install-time resolve + direct interpreter。

## UC 盤點

- 更新既有能力：governance installer 對 CC／ZCode／Codex hook registrations 的生成、check、verify。
- 更新 runtime contract：shared Python hooks 的部署 interpreter 從 system Python 3.9 改為 uv-managed Python 3.12。
- 不新增 user-facing command；`governance/install.py` 仍是唯一安裝入口。

## Scenario Matrix

| 場景 | 觸發 | 預期行為 | 驗證 |
|---|---|---|---|
| 正常 render | 已安裝 uv-managed 3.12 | `{{HOOK_PYTHON}}` 展開為絕對 3.12 interpreter | unit test + dry-run |
| managed 3.12 缺席 | installer render/check/install | fail-loud，提示先 `uv python install 3.12` | unit test |
| hook behavior | deny/allow fixture | 3.12 與既有 3.9 baseline 的 stdout/exit/副作用等價 | focused hook tests + entrypoint matrix |
| derived config | install/check | CC/ZCode/Codex live config 都使用同一 resolved interpreter | `--dry-run`/`--check` |
| rollback/mixed session | 舊 config 尚在場 | source 暫不使用 3.10+ only syntax，舊 session 仍可跑 | 3.9 syntax parse tests 保留 |

## 測試規劃

- TC1（S：repo runtime policy + installer ownership）：render 必須展開 hook interpreter token，不能殘留 bare `python3`。
- TC2（S：部署 runtime contract）：resolver 只接受 uv-managed Python 3.12，缺席 fail-loud。
- TC3（S：verify truthfulness）：`probe_pipe_payload()` 必須用 resolver 的 interpreter，不得再用 bare `python3`。
- TC4（H：既有 hook 行為）：既有 3.9 entrypoint 行為與 3.12 entrypoint 對關鍵 deny/allow fixtures 等價。

## 實作段落

### S1 — installer runtime token

- 在 `governance/install.py` 新增 cached resolver；以 `uv python find --managed-python --no-python-downloads --no-project --no-config --no-cache 3.12` 解析 installed interpreter。
- 新增 `{{HOOK_PYTHON}}` render token；缺 uv／缺 3.12／輸出非絕對 executable 都 fail-loud。
- `probe_pipe_payload()` 改用同一 resolver。

### S2 — tracked registrations 與 runtime contract

- CC/Codex command string 改成 `{{HOOK_PYTHON}} <hook>`；ZCode process `command` 改成 token。
- `hooks/AGENTS.md`、compact restore registration/protocol 與 hook runtime comments 改成 3.12 部署契約；暫時保留 3.9 syntax compatibility tests，避免 mixed-session rollback 失效。

### S3 — 驗證與 deployment readiness

- focused pytest：governance check/verify + hooks 相關測試。
- `governance/install.py --surface hooks --dry-run`、`--check`、`--verify`；authoring WT 只做 dry-run/check，live install 等 merge 後 canonical 執行。
- post-build：Muse + Codex independent review，Muse judge；控制面四欄 receipt 齊全後才具 landing eligibility。

## 整合策略

baseline: 7016266e61afc050062e1254ccd1ddcd7c52e33d

不改 hook 業務邏輯與 harness event mapping。active machine configs 是 derived state，不在 card WT 手改；source 收斂後由 canonical installer 投影。這次不升 hook source 語法 floor，先只換 runtime ownership。

## 接手 amendment：639a479b 三方審查修復（中間檢查點）

使用者授權「你直接修就好，他沒在做事了。」本段把先前「不改 hook 業務邏輯」的範圍限縮：加入三方報告要求的既有契約修復，runtime migration 的既有修改保留，不重做或視為已驗收。接手時 AIR-174 原 task 已 interrupted、bridge ledger 各 job 均 completed；修復前 working diff 與六個目標檔存於 `.agent-tmp/review-639a479b-repair/`。

- Memory admission：description key normalization／value selection 與 generator 的既有解析相容；Write、Edit 的 `description :` 禁止值不能漏攔，合法值仍可寫。
- Compact：完整注入 envelope 才排除；一般 user／assistant 提及 marker 必須保留，以真實 entrypoint 輸出 roundtrip 驗證遞迴抑制。
- Instruction：rules-reminder 引用 tool-discipline；python-standards 明確尊重 hook owner runtime 相容契約。

分類 `boundary`（admission gate 與 instruction 語義），review 需獨立 fresh、intent 與跨家族第二意見。原生 worker 採 inherit binding，Role=Implementer、authority 限四個 hook/test 檔與兩個 instruction 檔的互斥 write scope；hooks/AGENTS.md 另授權單句同步。collection owner 為本 task 持有的 native agent handles。

驗證先 RED/GREEN focused tests，再 hook/governance consumer regression、全套件與 bundle dry-run。只在 WT authoring；不把 639a479b hardening 當作 3.12 migration 已完成，不安裝 live config、不結案、不提交。

### Amendment 結算（本次修復完成）

三項必修與 fresh review 追加的 CR-only newline 繞過均已修復。最終 focused 230 passed；consumer 589 passed／1 intentional skip；full 2030 passed／2 intentional skips；Python 3.12.13／3.9.6 direct entrypoint 均驗；四檔 Ruff／format／mypy 通過。Fresh＋intent＋Muse instruction 外審收斂，七個目標檔 hash 已核對，其他既有 migration diff byte-identical。完整命令、skip 理由、review 裁決、四欄回執與未部署界線見 [review-639a479b-repair.md](review-639a479b-repair.md)。此結算只覆蓋 review-repair，不取代 AIR-174 migration 整體落地驗收。

## 最終落地結算

本弧完整整合範圍與裁決以 [landing.md](landing.md) 為最終回執；原 rules/hooks hardening 保全、三項必修、runtime migration、CC parity 及 Codex ownership IR1/IR2 均已完成，2083 passed／2 intentional skips。前述不結案／不提交是歷史修復檢查點；使用者後續明確授權修好合併，故本次完成 card Done、commit 與 main 收線。live registration/bundle deployment 仍 pending，未宣稱實機驗收。
