---
name: at-skill-zcode-cron-gaps
description: ZCode cron 落差定案集：session 綁定兩形態／冷 landing 禁多步／殘留判讀＋開放項待分辨
metadata:
  node_type: memory
  type: project
  originSessionId: sess_28481aba-d95d-4522-b592-f92d6bca93ce
---

/at 於 ZCode 可跑（CronCreate/CronList 原生相容）；平台行為會演進——結論附日期條件，翻案即改。（09-08 蒸餾：已解項留結論，開放項原樣）

> merged_from: feedback_scheduled-checks-on-demand, 2026-09-07 cluster-merge wave

## 定案（結論收案，細節查 commit/skill）

1. **/at 落差已修**（2114f5f，08-16）：相對時間移除（YAGNI＋roll-a-year hazard）；生命週期分流（CC 綁 session／ZCode workspace 持久、completed 留存須 CronDelete）；「host 開啟」非 terminal。
2. **session 綁定兩形態**：①fired 血緣——pending/completed 在場皆鎖，刪該 session 記錄即釋放（09-01 推翻「fire 後釋放」；usage-ping ZCode 降 1 rung，「同批×N」不可行）；②creator 所有權——建過活躍排程的 session 刪記錄仍鎖（09-04），唯一解新 chat；被擋→寫 handoff→乾淨 session 代建。
3. **冷 landing 禁多步**：self-rescheduling chain 棄用（08-20，冷 context 重複首工具 50 次燒斷）；叫醒型零工具一行 landing、多步分析型 skill 化（prompt 瘦身 Skill 調用＋SKILL 自足＋allowlist）。
4. **能力邊界**：interval 上限 200；cron 是日曆網格非累加；recurring 佔 1 名額優於 one-shot 階梯；prompt 內嵌模板不調 Skill。**上限 20 全域計數**（completed 亦佔；滿載唯一路 user 手清）。
5. **排程定位**：cron 是無人值守兜底非執行閘——機械檢查落地當場手跑（09-03 糾正）。

## 開放項（現行弧線，勿當已解）

- **creator-bound delivery（09-06，待分辨）**：creator 存活時 one-shot fire 進 creator 對話執行非新 session——cron 當新鮮快照載具失效（標 same-snapshot confounder）；新鮮判決唯一路＝user 重啟 app 續接。
- **keep-awake 作用域未驗**；**跨 workspace 刪不到**＝平台事實（user 手動；`cross-workspace-actions-user-handles`）。
- **miss 判讀**：no-turn miss 呈 completed＋runCount 0＋無 lastRunAt——残留判讀不信 runCount/lastRunAt（真 fire 兩值可靠，09-05 互證）。
- **報告標頭幻覺**：cron session 自寫時間/觸發源不可信——prompt 明令 `date` 取實際時間（AIR-17 卡記，automation prompt 待修）。
- **drift 殘餘**：usage-ping skill「週期模式」ZCode 綁定括註（08-19 舊模型）與 9/1 模型矛盾，待改。
- **usage-ping 接力弧（進行中）**：fire→刪舊 completed→建下一發同 session 循環；輸入 raw 邊界默認＋1min；sentinel 重疊落地確認 by design。細節見 [[at-usage-reset-continuation]]。09-07/09-08 三輪接力零失誤（16:28/02:09/17:18 落地，零工具一行 landing 續證可靠）。
- **completed 記錄自滅（09-08 觀察，歸因未定）**：前日 completed one-shot 記錄（02:09 rung、13:01 補派）次日 13:03 CronList 已不見、無人 CronDelete——與定案 4「completed 佔名額不自動刪」矛盾；候選歸因＝TTL 自清/app 重啟/user 手清。記錄不在場＝同 session CronCreate 直接过（再證「記錄在場才鎖」模型）。

**How**：多排程 skill ZCode 端「同批僅一條」降級；殘留判讀見開放項。相關 [[consistency-gate-not-optional]]、[[zcode-hooks-porting]]、[[cross-workspace-actions-user-handles]]、[[feedback_fix-immediately-not-defer]]。
