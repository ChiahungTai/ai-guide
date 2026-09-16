# execution-plan 檢查點

已完成本項文件契約審查；非 runtime 驗收。

合理設計：規劃自足、致命假設先 POC、blueprint 禁直接 implement、段落有依賴錨點。這些保留，不建議重做整個 EP 系統。

## EP1 — Important / confirmed：simple 路徑繞過它聲稱唯一的 invariant 防線

證據：skills/execution-plan/SKILL.md:48 明定 simple 不寫 EP；203-214 把 Invariant Impact 放在 EP 段落元素內；210 更明說單檔單位轉換 fix 可判 simple、此元素是其唯一結構化防線。

最小反例：單檔張/股轉換修正被判 simple → 無 EP → 沒有 §1b → implement 的「段有此元素時」RED 強化不觸發。宣称唯一防線卻掛在已被入口排除的 artifact 上。

否證：高風險應升級 full、會計/風控/共用層已明列不得 simple；但原文刻意保留了非這三類的 silent-corruption simple 例子，因此無法靠泛用高風險原則消除這個本地矛盾。

建議：讓 invariant 盤點在 scope 分流前發生；可選「命中即升 standard」或「simple 也保留輕量 invariant 聲明」。不要用全文 EP 當唯一承載。

驗收：單檔單位轉換、純 leaf typo、共用會計修復三個場景走分流，前者與後者均有可定位 invariant/驗證義務，leaf 不被迫寫 EP。

## EP2 — Suggestion / evidence-based：需求邊界沒有明確的跨 artifact 保留義務

spec:76-85、95-105 產 Always/Ask First/Never 與成功條件；EP:11、195 指定引用 UC/SM；段落 Context 與輸出 schema 未明列 spec 邊界。背景資訊可承載，所以不宣稱一定遺失；但標榜 self-contained 的段落只交給另一 session 時，保留負向需求依賴 writer 自覺。

建議：在既有 Context 明確繼承相關需求約束、標明技術裁量與需人決策邊界，不新增大型表格。驗收：spec 的 Never「不改 live 下單」能在獨立段落被 builder/reviewer 找到。

## 設計觀察

Self-Contained 不等於沒有依賴。頂部「完全獨立」可理解為 context 自足，已有語義約束/段落依賴欄位足以否證「它不能表達依賴」的指控。真正應檢查的是獨立消費某段時能否拿到必要前置與禁區。
