# Multi-harness 文檔鏡像

各 harness 官方文檔的 local 鏡像，作為跨 harness（Claude Code / ZCode / Codex / Meta Muse Code）契約的 ground truth，供設計 harness-neutral 規則、跨 harness adapter、或撰寫中性指令時離線查證。

> 搭配 [`contracts.md`](contracts.md)（各 harness 契約對照表）與 [`manifest.json`](manifest.json)（每頁 url / path / sha256 / status）一起用。

## 來源與抓取方式

| harness | 來源站 | 發現機制 | 內容取得 | status |
|---------|--------|---------|---------|--------|
| **claude-code** | code.claude.com | `/llms.txt`（含 Docs + Changelog，給 `.md` 直連）+ `/blog` 索引 | 抓 `.md`；blog 無 `.md` 時 HTML 抽取 | `ok`（verbatim md） |
| **zcode** | zcode.z.ai | 從 `/cn/docs/welcome` SSR nav 抽連結（該站是 Next.js SPA，`/sitemap.xml`/`/llms.txt` 回傳假 shell，不可用） | SSR-HTML 抽取純文字 | `extracted-html`（含 sidebar nav chrome，非 verbatim） |
| **codex** | learn.chatgpt.com | `/docs/llms.txt`（ChatGPT+Codex 合併文檔集 index，列 `.md` 直連；developers.openai.com/codex/* 已 308 導向此） | 抓 `.md`（verbatim）；relpath 去冗餘 `docs/` 前綴 | `ok`（verbatim md） |
| **meta** | dev.meta.ai | `/docs/llms.txt`（站無 root llms.txt，index 在 `/docs/` 下） | 抓 `.md`（verbatim）；relpath 去冗餘 `docs/` 前綴 | `ok`（verbatim md） |

> 四站**都不需 Playwright**：claude/codex/meta 有 markdown 端點，zcode 雖 CSR 但 doc 路由有 SSR 內容 + nav。

## 目錄結構

```
ref-docs/harness/
├── README.md          # 本檔
├── contracts.md       # 各 harness 契約對照表（memory 檔/skill/agent/command/hook/MCP/settings）
├── manifest.json      # 每頁 url/path/sha256/status（refresh 時偵測變化）
├── crawl.py           # 爬蟲（見下）
├── claude-code/       # docs/en/... + blog/...
├── zcode/             # cn/docs/...
├── codex/             # <section>/<page>.md（合併文檔集區段巢狀；relpath 去冗餘 docs/ 前綴）
└── meta/              # <page>.md（Muse Code/Model API/Glimmer；relpath 去冗餘 docs/ 前綴）
```

## Refresh

```bash
uv run python ref-docs/harness/crawl.py                            # 全四站
uv run python ref-docs/harness/crawl.py --source claude-code       # 單站（merge 進既有 manifest，不 clobber 其他）
uv run python ref-docs/harness/crawl.py --source zcode --limit 3   # smoke test
```

- **Deterministic**：只在 sha256 改變時才寫檔 → refresh 只動真的變的頁，diff 最小。
- **manifest merge**：`--source X` 只更新 X（含該源條目自帶的 `generated_at`），保留其他 source 條目與其時間戳——單源刷新不會讓他源共用新時間戳；頂層 `generated_at` 僅代表 manifest 產出時間，**各源新鮮度以 source 條目內的 `generated_at` 為準**。
- **smoke 零寫入**：`--limit` 不寫 manifest **也不寫磁碟鏡像**——抽樣結果覆寫 source entry 會縮小 coverage；只寫磁碟不寫 manifest 則是 integrity split（hash ledger 落後磁碟內容）。smoke 只驗 discover＋fetch 連通。
- **孤兒帳**：refresh 時列出磁碟上有、本次 discovery 沒有的鏡像檔（`[WARN]`）——上游下架或 discovery 變動，去留人工裁定（crawler 不刪）。
- zcode 若日後改版導致 nav 抽不到連結，會印 `[WARN] zcode: seed ... unreachable`——屆時檢查 nav 結構是否變動。

## Provenance / 版權

本目錄內容為各 harness**官方公開文檔的本地鏡像**，僅供離線查證：

- 版權歸各原作者（Anthropic / Z.ai 智譜 / OpenAI / Meta）。鏡像非官方認可、非再授權。
- `claude-code`、`codex`、`meta` 為 verbatim markdown；`zcode` 為 SSR-HTML 抽取的純文字（非 verbatim，含少量 nav chrome）——以 `manifest.json` 的 `status` 欄區分。
- 文檔會 stale。**有疑問以原站為準**；refresh 後 manifest 的 `sha256` 變化可用來追蹤各頁何時變動。
