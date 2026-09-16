---
name: underscore-prefix-sort-cross-tool
description: 底線前綴目錄跨工具排序實測——VSCode 聚頂✓/Finder 忽略前導底線✗/ls 視 locale；_ 業界語義=私有框架保留非釘頂
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_89592a9f-fbba-4b02-ade1-3b58b15bfd54
---

目錄命名用前綴「釘頂」前的必查事實（2026-09-02 查證，mosaic `_work/` 設計案）：

- **VSCode explorer**：case-insensitive 排序，`_` 排所有字母前 → 底線目錄聚頂 ✓
- **macOS Finder**：localized collation 在主層級**忽略前導底線**——`__pycache__` 排在 "P"、`_archive` 散進 "A"；無設定可改，社群定論解法只有改名
- **終端 `ls`**：C locale byte-wise 成立；macOS UTF-8 collation 可能同 Finder 忽略標點
- **`_` 前綴業界語義**：私有／框架保留（Jekyll `_posts`/`_layouts`、Python `_internal`、Sass `_partial`）——排序釘頂不是主流含義，屬 solo 開發者個人慣例（HN in-repo `_meta/` journal 同款）
- **成熟 repo 通則**：不玩排序遊戲——root 極小化＋公認名（docs/examples/scripts/tests）＋點綴目錄放工具狀態（.github/.vscode）；數字前綴只用於「順序本身是語義」的內容（課程章節）

**設計含義**：要跨工具保證聚在一起 → 傘形單目錄（包含聚類，非 collation 賭局）；平面底線叢集只在「VSCode 是唯一瀏覽面」時成立。

來源：Apple StackExchange #320966、Apple Discussions #7602542、StackOverflow #62333831、JosephGuadagno VSCode sort article、VSCode issue #90217。

相關：[[mosaic-ai-analysis-directory-review]]、[[user-project-first-containment]]
