# AIR-28 驗證證據（tracked——殼的回源錨；命令＋exit code＋關鍵輸出節錄）

> 本檔是 shell `index.html` 驗證宣稱的持久底稿（機械底稿規則——數據宣稱只從此帶入）。`.agent-tmp/` 下的完整輸出為 ephemeral 詳情（post-build 清理），本檔承載可追查的最小證據集。baseline 9cebabd；EP @ 9aa852b（blob edef9e12）。

## 1. 機械複驗 7/7 PASS

七項：殘留掃描／HIGH SIGNAL 單源／projection map 集合相等／contract 表引用存在性／investigator schema／effort 對譯表／消費側單源。完整命令與逐項輸出＝`.agent-tmp/air28-verify.out`（ephemeral）——末行 `7/7 PASS`。

- 第 7 項（消費側單源）首輪 FAIL（agent-workflow 消費側前言重述表欄位 schema）→ 修復後**同命令重跑**轉 PASS——時序：平行 session 12:11 底稿 FAIL → 12:4x 修 agent-workflow → 重跑刷新。judge 採納 codex R5 的處方（修驗證合約本身，非只改報告）。
- 殘留掃描命令：`rg -n "errorIds|Sentry|Statsig|logForDebugging|logEvent" skills/ rules/ agents/ hooks/` → 零命中（exit 1）。
- projection map 集合相等：`diff <(rg -o '^\| ([a-z-]+) \| (shared/|zcode/)' -r '$1' agents/AGENTS.md | sort -u) <(ls agents/zcode/ | sed 's/\.md$//' | sort -u)` → 空 diff（10=10）。

## 2. cross-verify L4（詳情落檔 `.agent-tmp/cross-verify/`，ephemeral）

- **試跑 1**（git＋memory 軸；問題：impl-flash 納管狀態）→ **corroborated**：untracked（`git status --porcelain` → `??`）、零 commit 紀錄（`git log --all -- <path>` 空）、memory 池記「待 AIR-28 S1 併入」。log 軸旁證：`.muse-bridge/jobs/job-mtnnzoez-jp8nq6.jsonl` 內嵌建立 diff，blob `9017fa2` ＝ `git hash-object` 現值（零修改機械證明）。
- **試跑 2**（db 軸拔源）→ investigator 回報 `[WARN] 源缺場：軸 unverified`＋逐字錯誤訊息（`unable to open database`），未換源未腦補——SM-9 端到端成立。

## 3. CC 端 L4 雙面（claude 2.1.261）

- unknown-name：`claude --agent nonexistent-xyz-agent --bg "…"` → warning `no agent named`＋報 backgrounded（id 8059fcd4）→ 該 id 隨即查無（`claude agents --json` 無此列、logs 報 control socket ENOENT）——session 立即退出（SM-10）。
- named agent：`claude --agent code-reviewer --bg "唯讀讀檔回報"` → session 主體 `@code-reviewer`（glm-5.3/xhigh）、正確回報首行標題、零檔案修改、`claude stop` 乾淨——讀取型可回收成立；寫入型回收與 rules/ auto-commit override 未驗證。

## 4. runtime modelID 抽查（`~/.zcode/cli/db/db.sqlite` model_usage；注意 `~/.zcode/cli/db.sqlite` 為 0-byte 殘檔）

```sql
SELECT agent, model_id, variant, status FROM model_usage
WHERE started_at > (strftime('%s','now')-86400)*1000 AND agent='zcode-agent' ORDER BY started_at DESC;
```
→ 多筆 `GLM-5.3-Flash`（model pin 逐字達 wire ✓）；`variant='max'`＝sticky user reasoningLevel 蓋過定義值 `high`（已知 open bug 家族 #339/#306——09-05 新數據點；flip 實驗仍 open）。

## 5. 部署與閘門

- `uv run python scripts/deploy_agents.py` → exit 0、`[OK] deployed to 3/3`；三 bundle `cmp` 兩兩一致 PASS。
- `uv run python skills/scan-project/scripts/check_single_source.py` → `critical: 0`（cross-verify allow-list 已補 settings.json〔gitignored〕；剩 2 important 為 pre-existing：kbar-form-analysis／modern-cli-preference，非本弧）。

## 6. 雙家族 review（post-build，user 指定派發）

- muse：bridge `task`（job-mtnw1xgm-13tzyp，exit 0）——9 findings；codex：companion `task --model gpt-5.6-sol --effort xhigh`（exit 0）——9 findings（3 critical）。judge 18 條合併去重：✅15＋✅已執行 3＋⚠️1——全數落地；修復清單見 EP 對照段（完成報告）。
- GLM in-harness 3-perspective：額度降級（1308 窗口至 16:02）——由雙外部替補（user 指定），顯式記錄非靜默。
