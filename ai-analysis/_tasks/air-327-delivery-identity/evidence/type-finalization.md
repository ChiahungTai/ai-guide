# AIR-327 annotation-only finalization bounded receipt

WT `/Users/ctai/Github/ai-guide-air-327`、branch `air-327`，開工已核 pwd/toplevel/branch/wt-identity；baseline `7dbfd020fec402ca3c0eabb2c55a5752ae6e2057`。只修改 `tests/test_arc_handback_join.py:64` 一行 annotation；未改 body/assertions、其他 source、config、init/stubs、board、memory，未 commit/stage 或 delegation。所有其他既有弧變更保留。parent 管獨立 delta review 與 commit。

## Exact delta

```diff
--- before/tests/test_arc_handback_join.py
+++ after/tests/test_arc_handback_join.py
@@ -61,7 +61,7 @@
     return rc, buf_out.getvalue(), buf_err.getvalue()


-def _handback_with(tmp_path: Path, **overrides: dict) -> Path:
+def _handback_with(tmp_path: Path, **overrides: object) -> Path:
     doc = _load(HANDBACK_PASS)
     doc.update(overrides)
     return _write_json(tmp_path / "handback.json", doc)
```

`**overrides: object` 表示每個 override value 可為 JSON fixture 實際使用的 string/list/dict 等物件；並非每個 value 都必須是 dict。未引入 Any/ignore 或改變執行邏輯。

機械證據 `.agent-tmp/air327-type-exact-diff.log`：以唯一新行逆換舊行後，SHA-256 完全吻合本次修改前 bytes；不只比對 HEAD 累積 diff。

- before：`3e134d209acf1a079ea1c1695b1780d9d3e000ea10bb84cc07553f6b84553536`
- after：`a0c7db63576b242c6bbeb4b7a8d738ac49fec7afea1e575d4c1c5f927d38eeed`

## 指令與結果

1. `uv run ruff check scripts/arc_manifest.py scripts/arc_handback_join.py tests/test_arc_manifest.py tests/test_arc_handback_join.py` → exit0，All checks passed（air327-type-ruff.log）。
2. `MYPYPATH=tests uv run --with mypy mypy --explicit-package-bases scripts/arc_manifest.py scripts/arc_handback_join.py tests/test_arc_manifest.py tests/test_arc_handback_join.py` → **exit1，3 errors in tests/conftest.py**（air327-type-mypy.log）。使用 MYPYPATH，未使用 PYTHONPATH、未加 init/stubs/ignore。
3. `uv run pytest tests/test_arc_manifest.py tests/test_arc_handback_join.py --basetemp=.agent-tmp/air327-writer/pytest-type-finalization -q` → exit0，**96 passed**（air327-type-pytest.log）。
4. `git diff --check` → exit0。
5. `git diff --exit-code HEAD -- tests/conftest.py` → exit0，該 helper 與 HEAD 相同，確認非本弧新增變更；staged diff 空。

## Escalation：scoped mypy 尚未全綠

原 air327-commit-mypy.log 中 `_handback_with` 的 override arg-type errors 與 conftest import-not-found 已消失。正確 discovery 後，mypy 新暴露下列 **HEAD 既有** helper issues：

```text
tests/conftest.py:14: Argument 1 to module_from_spec has incompatible type ModuleSpec | None; expected ModuleSpec [arg-type]
tests/conftest.py:15: Item None of ModuleSpec | None has no attribute loader [union-attr]
tests/conftest.py:15: Item None of Loader | Any | None has no attribute exec_module [union-attr]
Found 3 errors in 1 file (checked 4 source files)
```

依本次工單「If more issues escalate, no scope expansion」，未修 conftest、未 ignore、未縮小檢查來造綠。annotation-only 交付完成；**mypy prerequisite 仍受這三項阻擋，交 parent 裁決**。沒有執行 commit/merge；未重做 full-suite/CR/其他收尾編排。
