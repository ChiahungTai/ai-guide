# 主 session EP findings 的外部審查（唯讀、有界）

repo `/Users/ctai/Github/ai-guide`，任務家 `ai-analysis/_tasks/09-15-development-workflow-redesign/`。Reviewer/findings、decision floor、review_findings qualification；無 disposition/apply。禁止寫任何檔/memory/git/部署，禁止再委派，不跑測試，不看 HTML，不重開已 verified 的 F1–F6／M1–M4。

脈絡：`references/review-main-session.md` 是 staged findings（N1–N8＋S1），user 明示「外部審查＋裁定後才回寫 EP」。你是外部審查腿：逐條檢查 finding 是否成立、建議修法是否足夠，供主 session 裁定。

read-set：`references/review-main-session.md`；`ep.md`（被點名段落＋S1–S4 修改要點與 manifest）；`git log --oneline 0bbddb1..HEAD` 與 `git status`（當前 HEAD `2d1c432`、working tree clean）。

關鍵時序（findings 定稿於 09-15 17:53，之後 repo 又前進，請逐條對現況驗證而非照抄 staged 證據）：

- AIR-96 已 Done（`b68b7d0`）：五項全落地，#3 bundle 瘦身＝`09e08ab`（33,013→30,088B，36KiB gate 89%→81.6% WARN 消失）——N1 建議句「持有中（#1/#2/#5 已 commit，#3/#4 未落地）」本身已過時，請提出現況下 EP 該怎麼寫（含 `ep.md` :42/:334/:344/:346/:358 與 UC 盤點 :105 的「dirty」指涉；並判斷原建議的 #3 順序/size gate 協調條款在卡已收、餘裕 81.6% 下還需要什麼形態）。
- AIR-97 已開卡又結案（`2d1c432`）：動了 `skills/CLAUDE.md`、`ai-development-guide.md`、`rules/AGENTS.md`、`rules/bridge-dispatch.md`、`rules/tool-discipline.md`、`skills/bridge-dispatch/SKILL.md`、`skills/tool-discipline/SKILL.md`、`skills/model-routing/{SKILL.md,catalog.toml}`、`scripts/sync_agents.py`——N4/N5 的行錨與命中面請對當前版本重驗（主 session 已複驗 `max-agents` 仍命中 `skills/CLAUDE.md`＋`skills/deep-work/SKILL.md`，EP:204「由 S2 接完」矛盾仍在）。
- AIR-60 仍 To Do（S2/S3 開工前 owner 對帳義務不變）。

輸出：N1–N8＋S1 逐條 verdict（agree／disagree／agree-with-modification）＋一句理由＋現況證據錨點；對 N1 給出你建議的 EP 替代句；如有對當前 HEAD 的新 Important finding（限本 EP 文件 vs repo 現況一致性，含 manifest/錨點因 AIR-96/97 需再修者），附反例證據。不擴張到流程方向重辯、runtime 實作或成本效果。
