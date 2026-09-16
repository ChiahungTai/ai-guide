---
name: reference_memory-index-load-truncation
description: memory 索引截斷定案——兩端同 200 行／25,000 字元（UTF-16）；「Claude 量 bytes」是欄位名誤讀；gate 分級 chars/lines 硬、bytes INFO
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_07836405-5f73-4d17-9619-5456406f7cd3
---

MEMORY.md 索引 session 啟動載入的截斷語義（2026-09-03 反組譯雙端 binary、CLI 三版〔2.1.247/250/251〕同構定案）。**兩端同語義＝200 行 或 25,000 字元（UTF-16 code units，CJK 一字計 1）**，任一超限截斷＋附 WARNING（非靜默；尾端條目不載）：

- ZCode（`zcode.cjs`）：`Vut=200`／`mre=25e3`——`Wut()` 以 `t.length` 比較
- Claude（`~/.local/share/claude/versions/<v>`）：`YD=200`／`GF=25000`——`mLe()` 回傳 `{trimmed, lineCount:Pn(t,'\n')+1, byteCount:t.length}`
- 「25KB」假象＝兩端警告皆以 25000/1024 格式化顯示 "24.4KB"（`Gut`/`Ft` formatBytes）——顯示層誤導，量測層兩端皆 chars

## 兩階段錯誤軌跡（方法論教訓，勿重蹈）

1. 原始錯誤：「前 200 行或 25KB 先到為準／靜默不載」（單位與行為都不對）
2. **翻案又錯**（本 session 09-03）：我宣稱「Claude 量 bytes（TextEncoder）」——把 `byteCount` 欄位名當計量方式；`Pn=new TextEncoder` 在**另一 scope 屬 crypto**（minified 跨 scope 撞名），mLe scope 的 Pn 是行計數器。fresh-eyes 審查 agent 抽全函數體釘死 `byteCount:t.length` 才翻回。教訓：**欄位名≠計量方式**；minified binary 反組譯要追到「值怎麼算」不是「值叫什麼」；跨 scope 同名符號是系統性誤導源
3. 驗證命令自帶陷阱：內嵌重跑命令 `.{100}YD=200,GF=25000.{100}` 實跑 **0 hits**（常數前綴僅 ~81 字元）——量詞須彈性 `.{0,100}`；且 `rg ... | head; echo $?` 抓到的是 head 的 exit 非 rg 的（pipe 蓋 exit code 同族）

重跑驗證（drift 防護）：`rg -a -o '.{30}mre=[0-9*]+.{30}' /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs`；`rg -a -o '.{0,100}YD=200,GF=25000.{0,60}' ~/.local/share/claude/versions/<最新版>`；計量實作＝perl 抽 `function mLe\(e\)\{.{0,300}`。

## gate 分級（09-03 裁決「zcode 優先」；同日晚間 amendment）

- **硬 gate**＝chars **22,500**（真線 90%；09-03 晚 18,500→22,500，user：「可放寬到 90%，只要寫入原則改好」）／lines 190——fail-loud exit 1、不寫入、`_regen-failed`
- **bytes >24,000 → [INFO] 縱深預警**：照常寫入 exit 0——bytes 非任何端實際截斷線，純提前折射（CJK 一字 3B）
- **寫入端 desc 硬限 100**（09-03 晚 P1：hook `DESC_LIMIT` 120→100 對齊紀律值；generator `TRUNCATE_DESC` 同步——常數變更連動 fixture 重算：截 100 使索引行變短，SM-3 n=70→80、SM-9 n=160→178 才回 gate 邊界）
- **夜間收斂＝流出腿**（「有進有出才是對的」）：每日 cron（automation-751ecce2、23:40、ai-rules 池）輕掃＋波段收斂；週日治理 cron＝健檢腿。機制記憶在 memory-audit SKILL 層 3「夜間收斂＝流出腿」段
- gate fail-loud 保留 last-good＋手寫被 hook 擋 → 任何 gate 值都無法讓索引越過真實截斷線——常數距離＝收斂節奏旋鈕。首波 severity 分級 commit `bb295f8`；22,500 放寬 commit `00490d9`（含 **SM-9 chars gate 邊界錨**——fresh-eyes F-1 揭 chars 路徑原零覆蓋；四路徑測試錨齊：chars 邊界/bytes-info/lines/frontmatter）。執行狀態見 [[gate-severity-solidification-queue]]。觸線順序參考：pool CJK 密度 ~1.35B/char 下 25,000 chars ≈ 34KB 檔案大小

## 治理層是自建 code（harness 只給儲存層）

`_generate_index.py` 是**我們的**（ai-rules 資產 `skills/memory-audit/scripts/generate_index.py`，08-30 治理弧 `6bc36aa` 落地；cp+mv 部署成各池副本）。harness 原生只有：池＋啟動載入＋截斷——索引怎麼來/會不會爆/爆了誰知道，全不管。generator 補三職：投影（frontmatter→索引行，條目檔唯一寫入點、手寫被 PreToolUse hook 擋）／防線（三 gate）／自動化（Stop hook 每 turn 結束 regen）。反事實＝56.6KB 事故世界（肥索引→截斷→查重漏→重複寫→更肥正回授）。定位一句：**寫入紀律（hook）→投影（generator＋gate）→收斂（夜間 cron）三層全是我們的；harness 只有最粗的截斷線**。

## desc 截斷層（generator `TRUNCATE_DESC=100`）——機制與取捨

索引行＝`- [name](file.md) - <desc>`，除 name 外整行是 desc＝**條目唯一的召回鍵**（session 只看得到索引行；召回＝LLM 讀索引行決定讀哪條，非全文搜索）。desc >100 時 generator 投影前 99 字＋「…」——**截索引行不截檔案**；被截尾段若含觸發詞，該條對該查詢等於不存在（「檔案裡還在，但沒人找得到」）。

- **為何截**：索引是全池共用限量預算（desc 是行主要成分——866 字 desc 實證一條吃 3.5% 預算）；desc 長度是公共財不是條目私事
- **為何截而非 regen-fail**：一條違規不懲罰全池——fail 會讓所有新條目 orphan；截斷＝局部犧牲保全局更新
- **TRUNCATE 是 hook 的兜底**（hook 三洞：harness 自動萃取繞過工具不觸發／subagent 寫入／歷史存量）——理想態 hook 生效時投影永遠完整，截斷只在失守時保護索引
- **desc 治理的消費者是我們三層（投影/召回/gate 預算），不是 CC/ZCode**——harness 只看 200 行/25,000 chars；「有 hook 擋為何還有 121 進場」＝三洞的答案；harness 萃取寫壞的靠夜間 cron 輕掃常態收斂，手動修是治標

## 待辦

- **mosaic 勘正待轉達**：mosaic `_audit-state.md` 09-03 段與池內 `reference-zcode-platform` §20 記了「Claude 25,000 bytes」——需改「兩端皆 25,000 chars」
- ref-docs/harness/contracts.md 補「auto-memory 載入截斷」小節（雙端對照＋重跑命令；文檔化不落任何 AGENTS.md——跨 repo 基建行為，家已定＝generator 註解/SKILL/rule 三層）
- Claude binary 相鄰常數未深挖：`rWt=4*GF`（100,000）、`zTe=200`、`eY=4096`（疑單條 entry 讀取限）
