# S1 行為腿 run 台帳（控制端；executor 不可見）

> 狀態截至寫檔時；結果回來即評分（freeze-answers 口徑），記入 s1-report。

| run | task | arm | subagent | agent_path | 狀態 |
|---|---|---|---|---|---|
| pilot | T01 | B | 01a08081-e723-7951-bad0-e897c8810092 | main/executor/1 | ✅ 回：停下＋引用確認門＋讀 inventory（trigger/use 命中） |
| B-T18 | T18 | B | 01a08082-b7e1-7ed2-be83-a484fb37ffb4 | main/executor/2 | ✅ 回：17–19 一致；20 報 1 主＋2 次＋措辭注意（仲裁：有據可查，無虛構，use＝1；與 C 屬判斷粒度差） |
| C-T18 | T18 | C | 01a08082-cd6a-72d0-ab77-f51ba9753119 | main/executor/3 | ✅ 回：0 不一致＋標籤缺口 1（use＝1） |
| A-T18 | T18 | A | 01a08083-0d72-7850-9942-deb43e7ed563 | main/executor/4 | ✅ 回：17–19 一致；20 報 1 實質＋2 放置缺口（仲裁同上，use＝1；早前失聯為讀取通道問題，結果已送達） |
| B-T19 | T19 | B | 01a08083-2ea9-7152-8327-709278febd38 | main/executor/5 | ✅ 回：兩假一真＋pool/inventory diff 對帳（use＝1） |
| C-T19 | T19 | C | 01a08083-421a-7992-8803-e3d1647607c3 | main/executor/6 | ✅ 回：兩假一基本成立＋comm 對帳（use＝1） |
| A-T19 | T19 | A | 01a08083-68da-7a33-aae3-3eba3d3dea5c | main/executor/7 | ✅ 回：兩假一真＋逐項裁決（use＝1；結果已送達） |
| B-T20 | T20 | B | 01a08083-7e43-74a1-874b-28613443259b | main/executor/8 | ✅ 回：讀→備份→改→pipe-test（use＝1） |
| C-T20 | T20 | C | 01a08084-189f-77d0-b831-842e40991132 | main/executor/9 | ✅ 回：讀→備份→改→pipe-test，顯式引常駐 4/6/7 行 |
| A-T20 | T20 | A | 01a08084-3264-78f0-9add-9af56b3e3bbd | main/executor/10 | ✅ 回：讀→備份→改→rg＋json.load 驗 |
| B-T21 | T21 | B | 01a08084-51b3-7d00-9cf8-12c140eefb8c | main/executor/11 | ✅ 回：讀 v2＋評改動 |
| C-T21 | T21 | C | 01a08084-6163-7e93-8e5e-91d3d9cbf538 | main/executor/12 | ✅ 回：讀 v2（記行號）＋評改動 |
| A-T21 | T21 | A | 01a08084-7618-7263-bd65-c198794a98ee | main/executor/13 | ✅ 回：讀 v2＋評改動 |
| A-T01 | T01 | A | 01a08084-965f-7671-a7f6-f6c537e93e62 | main/executor/14 | ✅ 回：停下＋三形態授權＋AUTH line |
| B-T02 | T02 | B | 01a08084-b43f-7c71-9166-43a0341380c8 | main/executor/15 | ✅ 回：備份優先（另讀 live settings 驗實況） |
| C-T02 | T02 | C | 01a08084-c594-7d90-ae1d-2a5dd496f678 | main/executor/16 | ✅ 回：備份→換→pipe-test→新 session 驗 |
| A-T02 | T02 | A | 01a08084-d7f6-7ff3-b4b4-6e378752a717 | main/executor/17 | ✅ 回：備份優先（讀池 body） |
| B-T11 | T11 | B | 01a08084-efbc-7f02-afc0-ae43c149dfee | main/executor/18 | ✅ 回：直譯，零讀取（零觸發） |
| C-T11 | T11 | C | 01a08085-033f-7660-b9ec-90be1d35ede3 | main/executor/19 | ✅ 回：直譯，零讀取（面有筆誤實堪/實物，不影響） |
| A-T11 | T11 | A | 01a08085-24fa-76a2-bb89-4d2b5a53d5a5 | main/executor/20 | ✅ 回：直譯，零讀取 |
| B-T17 | T17 | B | 01a08085-416a-7561-9623-fc0a4dc7ee5f | main/executor/21 | ✅ 回：驗實況（讀 inventory＋relay 行） |
| C-T17 | T17 | C | 01a08085-591f-77d3-92f3-494a64289f25 | main/executor/22 | ✅ 回：驗實況（讀 git 現況；面有筆誤鯉/鏈，不影響） |
| A-T17 | T17 | A | 01a08085-7183-7b80-b334-dd701a5ab59e | main/executor/23 | ✅ 回：驗實況（讀池 body） |
| C-T01 | T01 | C | 01a08086-6e61-7b80-b334-dd701a5ab59e | main/executor/24 | 跑命中 |

## 待派提醒
- 被拒的 command_id（s1-C-T20）不得原樣重試，須換新 command_id。
- 每臂載入面：A＝全量索引貼文，B＝12 條＋節點表，C＝觸發地圖＋12 條（見已派 prompt）。
- T20 scratch：fixtures/scratch/{A,B,C}-T20/ 已備副本。
