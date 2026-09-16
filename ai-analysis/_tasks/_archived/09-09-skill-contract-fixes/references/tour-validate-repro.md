# tour_validate 中文目錄 bug 重現紀錄（S7）

- 日期：2026-09-09；binary：code-reality（本機當前版）
- 反饋宣稱症狀（mosaic handoff ④，09-08 登記、09-09 重申）：`tour_validate --manifest` 報「有 corpus 目錄但零 .tour 匹配」；`--tours-dir .tours/arch` 顯式亦炸；疑似中文目錄名掃描問題；mosaic 側靠手修 callstack 錨繞過
- 重現結果：**不重現**（文件化調用形態）
  - `code-reality tour_validate --manifest --repo /Users/ctai/Github/mosaic_alpha` → `[OK] tour validate: 205 tours | links=0 filelinks=0 | fails=17`，exit 1
  - `code-reality tour_validate --tours-dir .tours/arch --repo /Users/ctai/Github/mosaic_alpha` → 同上（205 tours、fails=17）
  - 中文目錄（`.tours/arch/資料組裝與擴充/` 等）**正常被掃描與驗證**——FAIL 行正來自中文目錄內的 tours；無零匹配症狀
- 17 個 fails 全部為真錨債：`mosaic_alpha/datasets/future_labels.py` 已刪檔的 stale 錨（05/06.tour 多步）——corpus 債非工具 bug；屬 mosaic 側 post-build 修復閉環範圍
- 處置：S7 降級結案——無可移交 bug（09-08 症狀可能在後續 code-reality 版本已修，或原症狀環境相依——重現僅驗證文件化 `--repo` 形態）；本紀錄留作 code-reality 版本史對照

## Errata（2026-09-09，mosaic MOS-86 形態匹配重現推翻 S7 結論）

S7 重現僅測絕對路徑形態，而反饋 ④ 登記的失敗形態是 `--repo .`（相對）——調用形態不匹配。形態匹配重現（mosaic 09-09，main／offline_backtesting 兩 WT）：`--repo .` → exit 1 `[FAIL] ./.tours 有 corpus 目錄但零 .tour 匹配`；`--repo /abs` → exit 0 `[OK] tour validate: 205 tours | fails=0`。「中文目錄掃描 bug」實為 code-reality 相對路徑零匹配 bug class（08-27 3150e11 已知、acceptance 僅 pin --tours-dir 軸；08-30 bdea1eb 加 loud guard 未根修）。已轉 code-reality repo 根修（user 2026-09-09 裁決）；文檔面先修——post-build SKILL 調用形態改絕對＋禁相對註記。
- **閉環（2026-09-09 晚）**：code-reality v0.6.8 根修發行（`d90d9f9` canonicalize `--repo` at tour trio run() entry、`5938aee` release——真兇＝`strip_prefix` CurDir 組件不匹配，glob 0.3.4 能匹配 `./` 前綴，initial「中文目錄掃描」與「glob 不吃 ./」兩版歸因皆翻案）；release binary 實跑 mosaic 真實語料雙形態 byte-identical（`--repo .` ≡ `--repo /abs`，205 tours fails=0）；post-build SKILL 禁令註記已解除（本機 ≥0.6.8 驗證後）。來源：mosaic backlog `mos-86` 卡 notes 根因判定段（MOS-73=③validator 缺陷＋MOS-74=①docs 鏈未跑雙根因）。
