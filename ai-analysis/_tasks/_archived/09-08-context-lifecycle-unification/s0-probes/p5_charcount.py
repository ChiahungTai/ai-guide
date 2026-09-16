"""P5 helper: char-count validation of the 10 after descs (report table source)."""

AFTER = [
    "當你要 commit 而無 user 本 session 原話授權時：停——自主/resume 模式≠免確認；條件式授權過了即執行，勿重問",
    "當你要 git add/commit 時：並行 session 共用 tree——先 log/status 對帳、具名 add、看 diff --cached 全容，數量不符即停",
    "當 user 要 review／implement 派工時：雙家族平行——muse bridge＋GLM agent 同時背景跑，回來 judge-review 合併",
    "當你要派 agent／選 model 時：主軸＝harness（user 開發入口）→use case；額度與模型現值查 model-routing skill，勿憑記憶",
    "當你 spawn agent 寫 EP／報告時：prompt 內調查＝編號宣稱清單（C1..）＋條款「逐項機械驗證、推翻附證據」，禁當事實餵",
    "當你收到 handoff／relay／通知要接手時：其現況描述是過時快照——第一動機械驗證磁碟/git 實況，勿照描述行動",
    "當你要 review／評論／引用產物檔時：先 Read 磁碟當前版——平行 session 可能已全文覆寫，記憶＝歷史",
    "當你改動很小（quick-fix）想跳過審查時：不行——post-build 收尾鏈照跑；gate 跳過須明示，測試綠≠可免審",
    "當你要派發 codex／muse／subagent 或依舊慣例決策時：先重讀現行治理檔條文——記憶與 commit 標題≠條文現況",
    "當你要 Write 全檔重寫既有檔時：base 須本 session 全文 Read——context 副本會被 elide，片段/diff 空是假陰性",
]
ok = True
for i, s in enumerate(AFTER, 1):
    passed = len(s) <= 100
    ok = ok and passed
    print(f"#{i:02d} len={len(s):>3} {'PASS' if passed else 'FAIL'}  {s[:24]}")
print("ALL:", "PASS" if ok else "FAIL")
