---
surface: code-reality-binary
owner: code-reality repo（binary 安裝真相源＝skills/code-reality/SKILL.md）
---

## touches（候選偵測）

`skills/code-reality/**`、`.code-reality.toml` 變更；收線時另跨 repo 檢查 code-reality HEAD 前進（post-build collect 腿執行）。消費端無上述變更則 N/A。

## probe（唯讀健康探針）

installed binary `--version` provenance vs repo HEAD。

## health 判準

binary 版本可溯源且與管線出版態一致＝healthy；已證偽不健康（binary 缺失／provenance 對不上）＝unhealthy；落後管線待出版裁定＝pending（裁定歸 owner）。
