# S2 Report：座標系擴充——pilot 最小條目化

> 依 s2-ep.md；S1 裁定 (a)（採 B 作載入優化）後執行。

## 必要常駐集合定稿（12 條，S1 初判→定稿，無增刪）
`s1-probes/necessity-set.md` 凍結版即定稿：必中 5（commit 門／雙防護／收尾鏈／無版本備份／跨 workspace）＋高頻護欄 7。S1 pilot 十二臂行為＋仲裁無反證，user 已確認方法（裁定 (a) 附帶）。

## 適用層與 scope
| 集合 | 層 | scope |
|---|---|---|
| 必中 5 | user floor 常駐 | 全任務（漏掉即違規/不可逆） |
| 高頻護欄 7 | user floor 常駐 | 本 session 高頻（本輪 ai-rules 弧實證） |
| 其餘 128 條 | 按需（inventory＋工作節點） | 任務關鍵詞／節點觸發 |

## floor 預算
B-face 實測 3,649B（A-face 32,502B，8.9×）；muse trusted user-floor ≤50KB ——餘量充足，無超額處置需求。低頻不可漏約束已在集合內，不因預算裁掉。

## 改寫清單：空（附理由）
S3 pilot 消費的是必要集合（投影器輸入）＋層級重分配（docs），不消費 rules frontmatter rank/desc；rule 欄位機制歸 S3 全量／S5 定型時才需要。pilot 最小＝零 rule 改寫，非 16 條全改（codex 已驗此方向）。

## 擴展範圍登記（待 S3/S4 後，不在本段）
- rules/ 16 條 frontmatter（rank＋觸發 desc）→ S5 規模 rollout 時。
- on-demand 下沉 skill 確認（指針＋取用路徑）→ 有候選條目時逐項開。
- skills catalog／agents registry 文法對齊 → S6。

## S3 交接勾選
- [x] 必要集合＋層級/scope 清單可直接消費
- [x] floor 預算無超額
- [x] 無遺留 rule 改寫依賴（S3 可直接開工）
