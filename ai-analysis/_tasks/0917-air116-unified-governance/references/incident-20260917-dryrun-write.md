# 事故報告：1201 dry-run 真寫入 live config（AIR-116 S2 測試期）

> 2026-09-17 12:01 前後。發現者＝自建 hash guard（TC-3 逐字元對比）。已全額復原（位元組完全一致）。

## 時間軸

1. S2 `install.py` 核心完成後跑 TC-3（`--dry-run --surface all` 前後 shasum 對比）。
2. **防線警報**：CC/ZCode config hash 變了——dry-run 真寫入。
3. 損害盤點：CC `settings.json`（真實目標）被寫；ZCode `config.json` 被寫；codex **未被觸**（tomllib parse 驗證在寫入前攔下 merge 壞輸出——transaction 防線有效，但攔下的是裸 traceback 不是 fail-loud 訊息）；`setup-memory-symlinks.sh --apply` 被誤觸發（ZCode memory symlink 重連，結果＝正規布局）；muse plugins install/approve 被誤執行（冪等重裝，無害）。
4. 復原：CC 自寫前 `.bak`（`485c2ba1`）cp 回 ✓；ZCode 無可用 `.bak`（見複合故障）→ 剝污染鍵語義還原 → 寫入後 **ZCode runtime 立即以自家序列化器重寫**，最終 shasum `68dfbe65`＝事故前值，位元組完全復原 ✓。
5. 根因修復＋重測：TC-3 重跑 PASS（byte-equal＋零新 .bak）；TC-1 真安裝兩跑全 noop PASS。

## 根因（四 bug 複合）

| # | bug | 機制 |
|---|-----|------|
| A | mode 字串不匹配 | `flags[0]` 取 argparse attribute 名 `dry_run`（底線），所有分支比對 `"dry-run"`（連字號）→ 永不命中 → dry-run 掉進真安裝路徑 |
| B | merge_root 未接線 | merge 在 **config 根層**操作而非 manifest 宣告的 `hooks` 子樹 → 套件鍵散落頂層（`enabled`／event map 出現在根層） |
| C | codex 切塊粒度 | handler 子表 `[[hooks.X.hooks]]` 被切成獨立 block → `SessionEnd.hooks`／`Stop.hooks` identity 碰撞 → 交叉替換壞 TOML（parse 驗證攔下，未落盤）＋前導註解複製不截斷 |
| D | prune 政策 | `.bak-*` glob 把**他弧手工備份**算進 3 份額度＋按檔名排序（最新備份排最前）→ 自己剛寫的備份被自己刪 → ZCode 一度無 bak 可還原 |

## 修復（全部固化為結構，非紀律）

- mode 歸一化（`replace("_", "-")`）。
- merge 必在 `merge_root` 子樹內操作；子樹缺席（乾淨機器）語義明確。
- codex group 級切塊：group header 吸收 handler 子表＋前導 `# ai-guide` 註解（自前一 holder **實際搬移**非複製）；模板 identity 碰撞即拒合併。
- `.bak` 自家後綴 `-gov`＋mtime 排序 prune（他弧備份不入額度）。
- 通用 preimage 防線（所有 config 面）：**ZCode runtime 會併發重寫 config.json（本事故實證）**——寫入前 live≠preimage 即 fail/retry。
- 結構性斷言：`apply_text_change`（唯一寫入 chokepoint）入口 `_DRY_RUN → raise`——路由 bug 再怎麼錯都**到不了寫入**。

## 教訓（對應 acceptance-evidence）

1. 「我寫的碼＋我跑的測試」自證不可靠——TC-3 hash guard（獨立機械證據）抓到 Writer 自己的 bug。
2. 測試的零寫入斷言（hash 前後對比）是 dry-run 唯一可信證據層。
3. 併發寫入者是隱藏面：codex（`[hooks.state]`）之外，ZCode runtime 也會重寫自己的 config——安裝器的 lost-update 防線必須涵蓋所有 machine-local 面。
