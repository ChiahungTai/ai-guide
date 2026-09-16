---
name: feedback_judge-review-stays-main-agent
description: judge-review 固定主 agent 執行——user 裁定不派給另一個
  agent／家族跑（會出事）；跨家族只用在審查側（dual-family review），不在裁決側
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_75794c58-c131-4e06-8e87-b809c2b15d0d
---

user 裁定（2026-09-04）：judge-review 維持主 agent（跑 post-build 的 session）執行，**不**派給另一個 agent／家族（如 muse/codex 當 judge）——「這我覺得會出事」。

**Why:** 裁決者需要 build context（EP 意圖）才能判 intent drift；judge 是「實作工程師裁決審查者 findings」的方向，與 Writer/Reviewer 分離禁令（禁審自己 code）方向相反不衝突。家族多樣性的價值在審查側（產出不同視角的 findings），不在裁決側——裁決靠查證（rules/collaboration-constraints 反 Sycophancy），換家族不增加查證品質。

**How to apply:** 討論 review 鏈派發時，家族軸（[[feedback_dual-family-review-dispatch]]）只套用在審查側（GLM in-harness + muse second-opinion 平行產 findings）；judge-review 一律主 agent。勿再提案「judge 交接契約」或外部家族 judge——external-runtime routing（model-routing skill）只定義 reviewer 交接，沒有 judge 交接，這是刻意缺口不是遺漏。
