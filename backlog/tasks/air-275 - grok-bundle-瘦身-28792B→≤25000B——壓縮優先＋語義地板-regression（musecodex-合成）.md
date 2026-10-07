---
id: AIR-275
title: 'grok bundle 瘦身 28,792B→≤25,000B——壓縮優先＋語義地板 regression（muse+codex 合成）'
status: Done
assignee: []
created_date: '2026-10-07 14:08'
updated_date: '2026-10-07 21:59'
labels:
  - grok
dependencies: []
references:
  - scripts/deploy_agents.py
ordinal: 266000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
grok 端 rule bundle 28,792B（93.7%，超 WARN 線 2,680B）——四端 deployed 完全同構，瘦身同時救 muse 30KiB 安全面。muse＋codex 兩方案合成（分歧：下沉 vs 壓縮優先——取 codex 壓縮優先＋muse 不可動清單為地板；目標取 codex 嚴值 ≤25,000B）。

**做什麼（Wave 1）**：七檔 full rules 壓縮＋selective 下沉——collaboration（−350~500）／context-management（−500~700，steering/freshness/checkpoint floor 留）／design-thinking（−450~600，deep-thinking/arch-thinking sink）／edit-discipline（−200~300）／must-execute（−150~250，實跑義務留）／quality-constraints（−450~650，data-integrity/fail-loud floor 留）／acceptance-evidence（deep-body 下沉 −300~450，S/H/I/N floor 逐字留）。目標 −3.0~3.7KB → ≤25,000B；不足時 Wave 2（guide micro＋symbol-query wording）。
**不做什麼**：outward／tool-discipline／bridge-dispatch／model-routing／已 pointer 化四檔凍結（AIR-252 教訓：pointer 化丟 semantic floor）；rules/AGENTS.md／bash-hard-rules／code-edit-constraints 不碰（0B bundle 省益）；scope 分叉否決。

```mermaid
flowchart LR
  b["bundle 28,792B 93.7%"] --> w1["Wave1 七檔壓縮＋selective 下沉"]
  w1 --> t["≤25,000B"]
  w1 --> f["語義地板 regression 釘死"]
  t --> p["fresh grok probe 無方向退化"]
```
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
【Wave 1 milestone 收口——commit 09a3563e】bundle 28,792→27,780B（−1,012B，93.7%→90.4%）＋judge 五修（AGPL 可研究句/回 MIN 句/message_id 條件/回信段歸位/arch-thinking 指針，+70B→27,852B deployed）。全鏈：consultation（muse job-muy62n5v ✓／codex job-muy62n82 sandbox-error——3.5.0 升級剪除）→實作→tri 審查（muse muy7gzjb＋codex muy7gzkr＋GLM job-muy7h01r 全 approve-with-findings、無方向衝突）→marshal 依共識直接套用五處 Low 措辭修（免 judge——tri 收斂無分歧）。【主 AC ≤25,000B 未達＝結構性】floor 逐字釘死＋兩候選反向定義源＋凍結面——Wave 2（outward 等凍結面解凍）等 user 另議。【程序記錄】作者自報 /tmp diff 側檔即比即刪（三面掃描無殘留）；計數修正：pointer 化 6 檔（卡文 4）／未動 12 檔（申報 11）。【receipt】.agent-tmp/post-build-receipts/air-275.json
<!-- SECTION:NOTES:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 AC1 Wave 1 七檔壓縮落地（−1,012B 機械對帳；四端 size gate 綠）
- [x] #2 AC2 語義地板錨點全數在場（三腿重構 21/21/25 全 PASS；AIR-252 E1 模式排除——sink 四處實承載）
- [x] #3 AC3 tri 審查全 approve-with-findings、無方向衝突；judge 裁決 findings 處置
- [x] #4 AC4 主 AC ≤25,000B 未達（結構性）——user 裁決「先90%」收 Wave 1 milestone，Wave 2 凍結面解凍另議
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
grok bundle 瘦身 Wave 1 milestone 收口（user 裁決「先90%」＋本日「可以先關掉」——主 AC ≤25,000B 歸 Wave 2 延後另議）：bundle 28,792→27,780B（−1,012B，93.7%→90.4%）＋judge 五修（AGPL 可研究句/回 MIN 句/message_id 條件/回信段歸位/arch-thinking 指針）＝27,852B deployed。全鏈：consultation（muse job-muy62n5v ✓／codex job-muy62n82 sandbox-error 未產 verdict）→實作→tri 審查（muse muy7gzjb＋codex muy7gzkr＋GLM job-muy7h01r 全 approve-with-findings、無方向衝突）→marshal 依共識套用五處 Low 措辭修（免 judge——tri 收斂）。【Wave 2 登記】凍結面解凍（outward 5,602B 等）需 user 明示範圍另議——muse 端離實測截斷線 32,000B 尚有 ~4.1KB，不急。

```mermaid
flowchart LR
  b["bundle 28,792B 93.7%"] --> w1["Wave1 七檔壓縮 −1,012B"]
  w1 --> j["judge 五修"]
  j --> d["27,780B 90.4% milestone 收口"]
  d -. "Wave 2 凍結面解凍 另議" .-> w2["≤25,000B"]
```
<!-- SECTION:FINAL_SUMMARY:END -->
