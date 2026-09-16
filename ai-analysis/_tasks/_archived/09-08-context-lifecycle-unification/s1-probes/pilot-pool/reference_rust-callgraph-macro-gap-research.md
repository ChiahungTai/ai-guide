---
name: reference_rust-callgraph-macro-gap-research
description: Rust call graph macro/dispatch 缺口生態研究——W6 關帳：殘餘≈0 不建（空白＝無價值非無人做）
metadata:
  node_type: memory
  type: reference
  originSessionId: sess_c16a8998-b4b5-41c2-8bf4-1322cfd50753
---

2026-08-28 網路研究（W6「語法層互補面」評估前置，user 指示先查再評）。結論四條＋來源。

## 1. 問題是真且工業級未解

- **CodeQL Rust**（語意引擎+macro 展開路線）：[issue #20643](https://github.com/github/codeql/issues/20643)「macro calls 低百分比帶 call target」＝他們的**品質指標**；[#19966](https://github.com/github/codeql/issues/19966)「macro expansion failed warnings」＝展開失敗的碼不可見→缺邊；[社群](https://users.rust-lang.org/t/github-warning-low-rust-analysis-quality/137911)抱怨「Low Rust analysis quality」警告連哪個 macro 失敗都不知道。
- **cargo-call-stack**（build 層路線，[japaric](https://github.com/japaric/cargo-call-stack)）：明文警告 indirect calls（fn pointer／trait object／closure）缺邊、macro-heavy 專案圖不完整；[internals 討論](https://internals.rust-lang.org/t/a-benchmark-for-rust-call-graph-generators/11273)嘗試 benchmark 連跑都跑不動（工具成熟度缺口）。
- **rust-analyzer 自身 macro 展開有錯例**：[#13075](https://github.com/rust-lang/rust-analyzer/issues/13075)、[#20037](https://github.com/rust-lang/rust-analyzer/issues/20037)（rayon `multizip_impls!` 不完全展開）——**「升級 RA 榨乾」存在天花板**，不會全解。scip-rust（sourcegraph）底層就是 RA＝同限制。

## 2. 語法互補層（syn/token-walk 對 SCIP 面的互補 producer）＝生態空白

- **semgrep（tree-sitter 系）**：macro body 是 opaque `token_tree`——[#3513](https://github.com/semgrep/semgrep/issues/3513)「cannot match macro call」＋[#9700](https://github.com/semgrep/semgrep/issues/9700)（patterns nested in macros **靜默漏抓**＝false negative）；[Kudelski 研究](https://kudelskisecurity.com/research/advancing-rust-support-in-semgrep)確認架構根因＝tree-sitter 語法不解析 macro 內容。
- **沒人**把 syn-based 語法掃描做成 SCIP/語意索引的互補邊源——W6 若建＝生態首例（Python 側先例＝我們自己的 py_calls/ruff-parse，見 [[cr-live-faces-roadmap]]（pyrefly 段））。

## 3. token-stream 深挖（macro 展開體內呼叫抽取）有標準路徑

proc-macro2/syn 社群日常：[`syn::parse2`＋`ExprCall` 迭代](https://docs.rs/syn)（[proc-macro 開發實務](https://users.rust-lang.org/t/need-help-writing-a-proc-macro-parsing-a-function-body/39221)、[TokenStream 處理](https://www.reddit.com/r/rust/comments/nogtpx/how_can_i_process_the_tokenstream_in_a/)）——W6 最大工程風險點可行；但 syn 看到 macro 是 `TokenStream` 非 AST（手走 token），這是 syn vs tree-sitter 的**唯一實質取捨**（tree-sitter 的 macro body 同樣是 token tree）。

## 4. 最完整＝build 層但編譯耦合

[RFC #59412](https://github.com/rust-lang/rust/issues/59412)（call graph 資訊入 LLVM IR）：穩健來源只有機器碼＋post-monomorphization LLVM IR（macro 已展開、泛型已單態化）——但編譯耦合＋生態無穩定 project-level 工具＝重量級。[Ferrous Systems callgraph 驗證導向](https://ferrous-systems.com/blog/callgraph-analysis/)＝嵌入式「證明某函式不被呼叫」的顧問級應用。

## 對 W6 的映射（已摺進評估弧 kickoff，見 [[project_cr-live-faces-roadmap]]）

「RA 榨乾」有天花板（§1）→ spike 仍值得（蒸發多少量化）但別指望全解；syn-based 互補＝填生態空白（§2）；macro 深挖工程可行（§3）；build 層維持否決（§4，先前裁決不變）。

## 閉環（2026-08-28 W6 spike 消費本研究完畢）

生態級缺口真實，但**兩個真實消費 repo 量測殘餘趨近零**（NT 高信心 ≈0-1 pairs／mosaic name-form 111 pairs≈0.4%）——「生態空白＝首例機會」的價值假設被自己的 spike 否定：問題形態真實 ≠ 我們的 repo 有需求。兩個面特性新知：**①RA 1.97.1→1.98.0 對 NT 重生 index 零新增 attribution**（近 byte 等長 280,867,623 vs 280,864,173 bytes、重生 466s——短期版本升級非殘餘解）；**②RA SCIP 輸出幾乎零 std-method occurrences**（全 NT index is_ok=0/unwrap=0/len=1 vs 源碼數千次使用）——macro 內 std 呼叫在 index 與「漏掉」不可區分（occurrence-attribution oracle 只對 workspace 符號有效）、語法層「恢復」大宗其實是正確略過的外部呼叫。數字與建議詳 [[project_cr-live-faces-roadmap]] W6 段。
