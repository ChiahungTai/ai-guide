---
name: project_archify-illustrate-html-mode-eval
description: 人類 viewport 線三弧終態——B 軸受眾模型、illustrate html-mode（archify）、報告殼 template AIR-23、成本檢討吸收 AIR-30
metadata:
  node_type: memory
  type: project
  originSessionId: sess_da1739eb-475e-45a3-80cf-531cd44124c7
  merged_from: [project_illustrate-html-mode-archify, project_layer3-viewport-restructure, b-axis-human-acceptance-roadmap, project_ui-visual-verify-solidification]
---

merged_from: archify-cost-review-0905, air-23-illustrate-shell-template

人類 viewport 線三弧（html-mode 本體／殼 template AIR-23／成本檢討 AIR-30）全收案終態：B 軸→layer 3→illustrate html-mode→ui-visual-verify→template 化→成本吸收。

### project_archify-illustrate-html-mode-eval

**B 軸受眾模型（頂層脊柱，已入 root AGENTS.md）**

- 命令按產出受眾分，非生命週期階段：LLM 執行鏈（ep-review/code-review/audit-test/judge-review，機器自讀自判）vs 人類 viewport（人用大原則判讀）。**一檔兩受眾必然 token 牆——單檔單受眾**（human-review 三度重建又棄實證）
- 人補 LLM blind spot：缺 whole picture→重造既有；抓不準意圖→偏方向。**優先級：方向 >> 品質**——viewport 傾斜方向驗證，code 品質交 LLM 鏈
- 三層介入（獨立性遞增）：same-session 自判→跨 session 第二意見→layer 3 人類 viewport 三命令。理論底層（A/B 軸、L1-L6）住 rules/acceptance-evidence.md；B 軸 L4-L6（末端 SM 場景、可觀察性合約、介入點前移 RED）仍為設計方向——**mock 循環論證也適用 demo**（AI demo 演示 AI 認為對的），驗收必含錯誤/邊界場景

**layer 3 三命令（bd580b8）**

- **debrief**（行動後改動理解）：七段倒金字塔（意圖/行為黑盒子/前後差異/檔案地圖/波及缺口/驗證證據 demo-checklist＋NONE 逼問/認知誤差點）＋fallback 鏈 working tree→staged→HEAD~1
- **smell-detector**（行動前壞味道）：SKILL.md＋zoom.md（6 判準，預設）＋baseline.md（廣角盤點，opt-in）
- **illustrate**（結構 viewport）：city map/重用枚舉＋drift detection；三時點 pre-EP 軟 gate/post-EP/post-build；無參數改委派 debrief
- **命名病根教訓＝命名觀看者而非動作**（human-review 產出怪＝genre mismatch）；三舊目錄刪除不留相容層

**illustrate html-mode × archify（收案）**

- **價值定案**：HTML＝一次性人類 viewport（re-onboard/講解/分享）、Mermaid＝repo 生態（diff/AI 消費/沉澱）——**受眾分流非取代**；價值排序 dataflow > architecture > workflow > sequence。驗收 persona＝懂專案、沒跟過討論的人類冷開只看 HTML（vision-review 讀 3 PNG）
- **落地（opt-in）**：觸發＝明示 `html`；@dir＝mode B（先讀真實結構再畫）vs 純主題＝mode D 概念圖。guard＝**單圖 validate 12 止損**（實證收斂恰在第 12 輪）——**設計參數必須回對實證成本表校準**（EP review 🔴 抓出初版 guard=6 與 pilot 證據矛盾）
- **產物家**：repo root `arch-report/<主題>/`＋index.html；git 只收 JSON IR（~4KB）＋receipt——HTML ~720KB/顆不進（git 比例 175:1）本地再生；**確定性再生實證**：`git clean -Xf` 全砍後 deliver×3 sha256 一致（user 親手砍檔驗證 AI 宣稱——user 會動手驗）
- **CC/ZCode 共通拓撲三鐵律**：①**引擎永不裝成 skill**（觸發詞重疊＋repo 污染）②版本凍結 clone、`git pull` 唯一更新動詞（notification-only 永不自動安裝——frozen snapshot＋sha receipt 與「默默換版」互斥）③全 harness 同路徑——**「裝給某一家」不存在**（skills 穿 symlink 全家可見＋污染版控）
- **雙層評測關鍵**：殺手級＝**節點護照**（repo@revision＋真實檔案路徑＋出入向 edge label）；locale enum 僅 en/zh-CN＝結構性約束；legend kind 語彙錯位→殼層補對照卡不改圖
- **Authoring 教訓**（單一源 `skills/_common/illustrate-html-mode.md`，此處只留索引）：CJK sublabel 字級殺手、寧窄勿寬；grid 只適合鄰接鏈；dataflow 跨 ≥3 stage 長邊死結；**deliver 非零退出保留 stale 舊產物**（visual-check 驗的是舊圖不作數）；2-lane 扇入再插單源節點 solver 必無解

**ui-visual-verify 固化（視覺判讀路由）**

- **路由終態**：視覺判讀→vision-review agent（合約式 dispatch：視覺錨點＋verdict 格式＋read-only），**禁主 session 直接 Read 圖檔**——圖像 token 全量駐留主 context 多張即灌爆（GLM 5.3 實測）。**差距不在模型能力，在 agent loop 查證迴路＋合約紀律**（單發 MCP：CJK 誤讀、答不出互 clip；agent：截切＋跨圖佐證＋「畫面內無 X 則宣稱無從核實」）
- skill＝編排層 vs vision-review agent＝判讀層；ui-collab＝互動期 vs 本 skill＝驗收期
- **視覺錨點升級**：repo 有結構化規格單一源時錨點直接投影該檔（aria `.spec`）、**caller 禁手寫預期**——根治＝「不手寫」而非「更小心寫」（手寫副本必然漂移）
- **Self-driven app probe（進階形態）**：一被測 app 一 agent 端到端自主（起 app→playwright→截圖→判讀）、合約五要素（入口+port/操作清單+腳本骨架/視覺錨點+形態對照/產物隔離+verdict 格式）
- 附帶教訓：零直呼≠零消費（UI 工廠鏈 filter trap）；**新 skill 固化時 allow-list 是獨立必跑步**（skill_allowlist_coverage invariant 兩度抓漏）；vision-review 曾退化 stream 掛死 18 分鐘（transient 重派即癒，非 profile 問題）

### air-23-illustrate-shell-template

- 起源：user 問 illustrate html 要不要基本網頁 template（左折疊 sidebar＋右內容）。定調：殼規格本來就是此布局，真缺口＝布局/視覺決策以 prose 承載、每次建殼 AI 重推導 ~200 行 HTML＝drift 機會（AIR-14 首屏圖隱藏實證）→抽共用 template、AI 只填 slot，AIR-14 類 bug 從「靠 session 記性」變「結構上不可能」
- **凍結決策（勿重辯）**：template 落 `skills/_common/`（殼帶 ai-rules 工作流語義，不落 archify repo）；以 done/09-03-air13 index.html 為 de-facto 視覺基準（dark #0d1117、sidebar 264px、iframe `calc(100vh - 190px)` min 640、`?embed=1`、`go()`＋hash restore）；折疊＝CSS class 切換、**禁觸發 iframe 重載**；降級統一＝同 template `.frame-wrap.degraded` slot（不留第二套殼 codepath）；不做 manifest 產生器（YAGNI）；done/ 舊殼不動
- **語義邊界（S2 手術刀）**：只搬「殼長什麼樣」（布局值→template），「殼該說什麼」（內容篩選/雙向一致性/掛點生命週期/產物放置）留 prose 政策層
- **archify「缺場」是 09-04 首掃誤判**——只查 skills 根、漏偵測順序第 2 步 repo clone（clone 在場＋doctor 全綠；EP review F1 🔴 糾正——**錯誤環境事實會固化進殼敘事，偵測照 illustrate-html-mode 偵測順序全跑**）
- 終態（AIR-23 Done）：template 落 `skills/_common/illustrate-report-shell.html`（SLOT 出貨 gate＋三條硬約束註解在檔頭）；EP 歸檔 `ai-analysis/_tasks/_archived/09-04-illustrate-shell-template/`；殼產線後續演化見下方 AIR-30。分工慣性（glm 寫 EP、muse implement）見 [[reference_external-runtime-delegation-family]]

### archify-cost-review-0905

- 起因：user 09-05「archify 效果不錯但**畫太久、成本太高**」→4 flash 平行鑑識→09-06 deep-work 全管線吸收（AIR-30）
- **鑑識結論**：三天 ~3.1-3.3h、~20min/圖、~21.3M input tok；**93-100% wall time 是 LLM 生成**（CLI 全秒級）；黑洞＝high thoughtLevel 巨型生成（39K tok/15.2min 重寫 5.4KB JSON——燒在「validate 建議值直接抄就夠」的座標上）；窗口 4-16 validate 輪/圖；結構 M1-M12 倍增器（每圖完整週期線性放大、殼三波重寫、vision 逐張派發）
- **成本光譜三錨點**：kchart（bokeh Panel 互動＋standalone 靜態）~8s/案**機械渲染**、LLM 只在判讀端｜mermaid 宣告式 **1 輪**｜archify LLM 產線 **~9 輪 ~20min/圖**。選型判準因此加**成本軸**：資料綁定圖走機械渲染器、宣告式結構圖走 mermaid、無通道大圖才值回 archify 迴圈
- 三弧同構（archify 補審/kchart 驗收鏈/MOS-42 vision 契約）收斂到「機械渲染→flash vision 契約判讀→回數字驗證→人類板」；三衝突：C1 class 兩層調和、C2 locale（省略＋揭露）、C3 git policy
- user 打包授權（未逐項裁 D1-D5，傾向可否決）＋追加指示：①不派外部家族（純 in-harness GLM）②archify 非必要不用③mermaid HTML 顯示定案單一源④**無縫融合一體**驗收（同主題/透明底/同字體/自適應/無 iframe 痕跡）⑤可查網路
- **吸收終態（AIR-30，commit `128186e` 20 檔）**：`skills/diagram-selection/SKILL.md` 單一源（判準四問＋9 載體對照＋跨載體共性池）；mermaid 殼內嵌（渲染雙路徑 mmdc/CDN×三嵌法；**`-I <svgId>` 官方解方——id/marker/style selector 全改寫，帶唯一 id 可多張 inline**，POC vision 3/3 PASS）；illustrate-html-mode 兩軸分層（圖型軸=diagram-selection、概念軸=html-mode）＋**hook 1 骨架制**（渲染管線圖延 hook 2 一次產，職責落 post-build/implement/CLAUDE.md）＋**guard 分層（>4 輪回改 spec）**＋rounds ledger 進機械底稿源；archify-gen role D2 12 條＋幾何前移＋止損 pointer（sync 投影 body identical）；gitignore 補 arch-report svg＋.mmd 進 git；memory 四條目修正（air-23 缺場誤判、quality-bar 口徑、-I 解方、mmd source）；AIR-26 degraded 槽 mermaid 換裝＋vision PASS
- **教訓（build review 外部視角全抓出）**：寫規則者踩規則（POC 句日期＋統計）、單一源宣言同句自帶數字、判準反用（反指標當理由）、同弧知識回寫漏檔
- 殘餘：user 翻案 EP 未決項（C3 git policy、SF7）；MOS-42 ②③④⑥（回測語意陷阱/單位單一源/point-in-time/探索↔正式化）另弧收 trading-analysis——**AIR-31 已結（09-06 `3535bd8`，含⑤漏網 raw/adjusted 條併③——EP review F4 查證 AIR-30 實未收此條）**；精確統計數字不進 skill。kchart 分析落點：判讀＝kbar-form-analysis、定位＝diagram-selection、marking 明細住 mosaic

關聯：[[feedback_shell-diagram-quality-bar]]、[[feedback_engine-skill-trigger-collision]]、[[diagram-tool-selection]]、[[adjudication-materials-then-ask]]
