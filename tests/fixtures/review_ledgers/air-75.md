# Post-Build 工作帳本（air-75）——docs-mode 雙審查

## Identity

- task baseline：`e20e39f`（卡 desc）
- reviewed：`696665b`＋uncommitted `skills/post-build/SKILL.md`（政策翻轉擴充段）
- 範圍：`git diff e20e39f..HEAD`（卡檔）＋uncommitted（SKILL 一檔）；非本弧項：無
- writer：Muse `bamboo-ananke`（AIR-75 owning session）

## Muse Findings（job-mtwffiao-lo5ukv，PASS＋3🟢）

| id | 內容 | 決策 | 狀態 | 驗證式 |
|---|---|---|---|---|
| U1 | `projection consumers` 撞既有 projection 兩義 | ✅（execution-plan:174／html-mode:87 已讀，碰撞成立；改名政策投影面） | implemented | `rg -n 投影 skills/execution-plan/SKILL.md skills/_common/illustrate-html-mode.md` |
| U2 | `consumer concept` 無範圍界定 | ✅（半句界定，零風險） | implemented | 同檔 :76 已讀 |
| U3 | 反掃面未點名 skills/ | ✅（四 specimen 殘留面多在 skills/，屬實） | implemented | 同檔 :76 已讀 |
| — | 合規項：舊 gate 一字未動／卡三必有／refs 雙值／無 single-source 重複 | ✅（確認，muse 已附機械證據） | verified | — |

## Codex Findings（job-mtwfflnz-cxekxi，NEEDS-FIX→全採納重寫）

| id | 內容 | 決策 | 狀態 |
|---|---|---|---|
| X1 | 觸發非機械（LLM 判 invoke → false-skip） | ✅（自承：原文確由 LLM 先判） | implemented（機械 candidate detector 先行） |
| X2 | consumer scan 已有 owner＋ai-rules 名詞灌 cross-repo | ✅（四處引用親驗全實：ai-behavior:7／iw-SKILL:318／boot:26／bp-AGENTS:5,24） | implemented（只編排＋委派，硬編碼面全刪） |
| X3 | 三態不窮盡 | ✅（設計判斷成立） | implemented（加 `unverified`≠收斂） |
| X4 | 時間標 vs 元資訊禁令 | ✅（iw-SKILL:351-365 親驗） | implemented（provenance 依載體規則） |
| S | 多一 `。`（byte-identity） | ✅ | implemented（另起段，舊行機械比對一致） |

## Codex Followup（重寫後）

- old-tail-identical: True（e20e39f 原句逐字在場）／new-stages: True／ai-rules-nouns-gone: True／pytest 289 綠
- muse U1–U3 已被重寫吸收（`政策投影面` 一詞隨硬編碼面刪除；concept 界定／catch-all 覆 skills/ 意圖保留在新③）
- 殘留 open＝0
