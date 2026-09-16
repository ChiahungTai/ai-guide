---
name: rg-r-flag-display-replacement
description: rg 旗標陷阱——-rn 是顯示替換（match 成字面 n）、-h=help 非 no-filename（用 -I）、-L=follow；grep 直覺不可遷移
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_e27aeeb3-2707-49ba-bc33-8058dae9b914
---

`rg -rn "pattern"` 的 `-rn` 不是「遞迴＋行號」類直覺組合——`-r` 是 `--replace`（把 match 在**顯示層**替換成替換文本），`-rn`＝`-r n`＝所有匹配顯示成字面 `n`。輸出格式完好、看似真實，但關鍵詞已被改寫——比 truncation 更危險的同族 display masking（給錯的比截斷的更讓人停止往下查）。

**實證（2026-09-05）**：掃 Muse CLI 鏡像 effort 詞彙時，`--reasoning-effort` 顯示成 `--n`、官方註記「Ultra n」、ai-rules 的 `ultracode` 顯示成 `n`——險些據此誤判「文檔用 n 當頂級、bridge 缺詞彙」（實為 CLI `ultra` 詞彙一直在場，詳 [[muse-code-cli-facts]]）。

**第二實例（2026-09-06，跨 session 污染下游）**：mosaic pending-decisions 記載「ai-rules hooks 文件稱 generator 為 `l.py`」名稱 drift 議題——查證為幻覺：正確旗標下文件引用的是 `_generate_index.py` 全名，`l.py`/`n.py` 是各自 session 跑 `rg -r` 顯示替換的產物；我查證時自己也先踩同款（`rg -rn` 把 `_generate_index.py` 顯示成 `n.py`）才認出。**教訓擴展**：別人留下的「怪術語/怪名稱」宣稱，先想顯示替換汙染可能再當議題查。

**第三實例（2026-09-08，-ril 變體——替換文本是整串尾碼）**：`rg -ril "AGENTS" <dir>` 意圖「遞迴+忽略大小寫+檔名清單」，實際 `-r il`＝match 顯示成字面 `il`——muse docs 的 `AGENTS.md` 全顯示成 `il.md`，險些誤判「官方文檔改名 il.md」；事後以 `rg -o "[A-Za-z._-]+\.md" | sort -u` 逐名字面重掃才推翻。組合旗標裡 `-r` 後面的**所有**字母都會被當替換文本，不只單一 `n`。

**防護**：查證語料的 rg 旗標一律分開寫（`-n -C 2`，勿貪短組合）；輸出出現「單字母/短字串當術語、怪副檔名、怪名稱」這類形態＝先懷疑顯示層汙染，用 `-o` 逐字提取或 curl/fetch 原始檔核對再下結論。
