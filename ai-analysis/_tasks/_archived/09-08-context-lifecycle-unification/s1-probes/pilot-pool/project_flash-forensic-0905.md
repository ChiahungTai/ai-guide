---
name: flash-forensic-0905
description: 09-04 夜 GLM-5.3-Flash 大切換鑑識完結——三軸獨立取證；flash=執行層可靠/judge 塌陷；自述歸因三例被打臉；改良已落地 AIR-24＋C 轉 mosaic
metadata:
  node_type: memory
  type: project
  originSessionId: sess_3380ab28-4197-4433-aa66-e2f54587b64b
---

2026-09-04 23:00 → 09-05 05:30 user 把幾乎所有 model 切 GLM-5.3-Flash 跑夜間工作（三 mosaic repo 七線＋cron），06:00-06:03 切回 GLM-5.3 做 post-build，之後多 session 討論。09-05 晨三軸背景 agent 獨立取證（A 對話行為／B git 產出／C 建議查證——證據獨立性切分）完結。

**Flash 能力剖面（三軸合併）**：強＝機械/清單執行（lite-verify 10/10、cron 全交卷）、驗證型任務（AIR-17 七腿證據鏈＋Claim→Evidence 主動抓報告數字誤差）、reviewer 深度（20/20 交卷、讀 pytest source 做實驗、dual-context 交叉命中同鎖語義洞）、修正執行力、顯式契約而非壓制（警告清理僅 1 條窄域 filter 附理由/重現/移除計畫）、報告誠實不美化、模組邊界乾淨零 TODO。弱＝跨單位語義換算（西元↔民國 P0×2/P1＋靜默失效＋seed.json 斷點汙染）、測試合法化 bug（mock 假設即 bug——flash 測試只能當規格陳述非驗收證據）、judge 自證塌陷＋sycophancy（錯信心 finding＋順勢採納=最危險組合）、inferred findings（報「機制可能」非「實測確認」）、機械掃描漏變體（rg 等號形式漏帶空格形）、Edit 前未 Read 20 vs 3（唯一顯著偏高違規；批次化與 full 相當；pipe-to-tail/前景 pytest 是雙模型通病）。**保護面厚度是解釋變數**：厚保護（既有測試釘住）→甜點；新能力裸露→弱點。

**自述污染（關鍵 meta-finding）**：full-5.3 session 事後自述與 mosaic 三池 memory 歸因被 user priming 帶偏，三例被機械時間軸打臉——「兩輪 5.3 dual-context」實為 flash 段、R2F1/F2 實為 full 抓、MOS-29「全 flash」實混合＋reviewer 是 unpinned 繼承非 pin。**模型歸因結論必須 per-message modelID 機械對帳，不接受自述**（mosaic 三池 memory 的錯誤歸因待 mosaic 側修）。1302 spawn 失敗＝帳號級 rate limit 非模型專屬（晨間 full 也撞兩次；flash 段 13 個 subagent 僅 1 次陣亡跡證）。

**討論 12 建議狀態（C 軸查證→09-05 已裁決落地）**：#9（reviewer 信心分級）已存在勿重複；其餘經 user 裁決落地為 **AIR-24（commit 154d29c）**：分工律入 rule＋skill（user 修正兩點——tier＝**能力檔語義非模型綁定**、跨家族 review＝**軟提醒**額度現實）、judge-review 三防線＋機械化補償（每行證據/全採納警訊/inferred 必實測；closed 宣稱命令輸出比對/落地清單送複核/長弧後段顯性化）、lite-verify「EP 驗證策略覆蓋率」＋post-build/implement 接線（缺口真實——討論宣稱已存在被 rg 打臉）、1302 補 spawn 失敗態表（帳號級框架）。**C（版權年 lint＋補 commit×2＋三池 memory 歸因修正）09-05 handoff capsule 已轉 mosaic 側執行**。

**subagents 模型治理材料**：歸屬兩源——unpinned subagent 跟 spawning session 模型走（手動切換即全隊切換），registry pin 不受手動切換影響（lite-verify 固定小寫 glm-5.3-flash）。

**衍生弧（獨立結案）**：/commit 漏帶 backlog 卡＝full-5.3 時段流程缺口非 flash 責任——收斂三筆：2.8 Finalization 對帳閘門＋「commit 確認」pre-commit 無 hash 結算（`1bfefa2`，首實踐＝AIR-24 結案同 commit）→ 孤兒結算列（air-17 卡懸掛半日教訓：並行遺留分活躍/弧已終結，`270551b`＋`0379275`）→ docs 單檔閘門（純 .md 直 commit 原無閘門，放執行約束全路徑生效，`836c645`）——詳 [[commit-finalization-gate]]。「散文列舉 vs 機械閘門」與 flash 委派同理：可靠度靠機械對帳，不靠 LLM 自覺。

**AIR-25 memory 矯正（`55d128a`＋P2 收斂，09-05）**：user 問「為何清完又爆」→ CC 官方文檔對照確診雙根因：寫法（條目＝弧編年史，違反官方 skip-derivable）＋distill（gate 拒寫→索引停滯→召回斷裂）。落地：S1 gate 改 CC 式「超限照寫出＋行動訊息」／S2 hook desc hash 契約／S3 結案即蒸餾第三動（五掛點）＋寫入五問（載體判定：紀律→rule、方法論→skill、事實→memory、承諾→卡）／S4 清償＋弧歸線 11 線。終態：**條目 145→113、索引 22,988→18,205 chars（gate PASS，餘量 163→4,295）**。關鍵勘誤：**索引尺寸由條目數驅動——body 蒸餾不縮索引**，水位目標靠弧歸線。教訓：mem-distill agent 死於帳號級暫態（雙 agent 同窗 27-29 分 Model request failed）——重試帶已知事實可續攜；死後驗屍（半套偵測＝宿主已寫但成員檔在＋懸空掃 [[]]）收編了它最後一組手術。

**分工律首個應用裁定（report shell，user 問 illustrate html-mode＋archify 底層是否適合 flash）**：**分層切**——殼組裝（template＋slot＋baseline 頭部）／archify 餵料（圖由工具機械產、拓撲三鐵律非 LLM 判斷）／hook 2 實作章節生長→**flash 可**；素材篩選＋敘事骨架（B 軸 viewport 核心判斷）＋hook 1 計畫章節（EP 規劃段）→**full**；視覺驗收維持 vision-review（本就 flash 多模 pin）。**必補前提**（flash 文檔宣稱漂移弱面直接命中）：殼的數據/宣稱段**只從機械底稿帶入**（delta_tour/archify/命令輸出），flash 不得自由敘述 repo 現況＋確定性再生 diff 當「測試釘住」等價物——補齊後三條件 🟡🟡✅→✅✅✅。落地（illustrate html-mode skill 補分工註記）已提案待 user 開卡。

**AIR-26 再驗證（09-05 同日，完整弧）**：user 切主 session flash→unpinned general-purpose 繼承執行完整 docs EP implement＋settlement（兩輪共 62 tool uses）——宣稱全部親驗源碼後落筆（照工單要求）、git 對帳零 scope creep、偏差誠實申報（修復範圍比指示多兩處同源假訊號，主動列「偏差與記錄」）；兩輪審查（EP 10＋diff 2 findings）由 full 側 reviewer＋主 agent judge 承接——「執行 flash＋審查 full」分工律形態的完整弧實證成立。

相關：[[zcode-platform-facts]]（modelID 大小寫歸因）、[[agents-registry-split-design]]（flash 對照實驗前史，溯源段）、[[commit-finalization-gate]]、[[air-26-push-collection]]
