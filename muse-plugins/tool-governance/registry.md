# bundled／同功能 skill 重疊 registry — muse 端

> AIR-97 S2。目的：muse bundled skills 與 ai-guide 部署 skills 功能重疊時，臨場裁決依優先句（`ai-development-guide.md`「Session 開場導引」skill 優先序 bullet）取 ai-guide；本表登記已知重疊對供對帳與複審。優先句機制＝source-side 宣告（隨 deploy 進 bundle），本表是維護面文檔、不進 bundle。

## 優先句

「skill 方法論衝突時，ai-guide 部署的 skills 優先於 harness 內建／marketplace bundled 同功能 skill。」

唯一存在於 `ai-development-guide.md`（rg 命中應＝1；手改 `~/.config/muse/AGENTS.md` 會被 deploy 覆蓋——正名在源不在檔）。

## 重疊對

| bundled skill（muse） | ai-guide skill | 說明 |
|---|---|---|
| plan | execution-plan | EP/規劃方法論以 ai-guide 為準 |
| git | commit | commit 紀律與流程以 ai-guide 為準 |
| python-env | tool-discipline（Python 命令執行節） | uv run 強制等以 ai-guide rule 為準 |
| durable-test-collateral | test-driven-development | 測試留存判準以 ai-guide 為準 |
| workflow-authoring | workflow 政策（skills 寫作治理） | instruction/skill 寫作以 instruction-writing 為準 |

## re-discovery 對帳命令

```bash
muse skills list                      # bundled 面
ls ~/.local/share/muse/skills/bundled/muse-core/skills/   # bundled 實體目錄
ls ~/.agents/skills/ ~/.zcode/skills/                     # ai-guide 部署面
```

## 最後驗證依據（防語義漂移——codex advisory R1）

- 驗證日期：2026-09-15（AIR-97 S2 建檔）
- bundled 清單來源：`ls ~/.local/share/muse/skills/bundled/muse-core/skills/`（當日實測）
- 判準：上表任一對若 bundled 端改名／拆分／功能消失，或 ai-guide 端 skill 改名，本表須同批更新；優先句本身只在優先「方向」失效時才修（機制變更另案）。
