"""identity_pointer hook 契約測試（AIR-286）.

驗證式（GLM 五測之 ④⑤；oracle＝I 級——契約單一源即 hooks/identity_pointer.py
docstring＋scripts/session_discovery.py 指針節 docstring）：
- stdin payload（session_id＋cwd）→ per-cwd pointer 檔 atomic 寫
  （pid 後綴 tmp＋os.replace；檔 0600／目錄 0700；無 .tmp 殘留）；
  檔名＝sha256(realpath(cwd))、內容＝seam 指針 schema。
- 恆 exit 0、全靜默（stdout/stderr 空）——壞 JSON／空 stdin／非 dict／
  缺 session_id／缺 cwd／writer 異常皆同（AIR-135 條 3 advisory；
  降級可觀測性歸 whoami 讀側 identity_source 標記）。
- symlinked cwd 解析 realpath 後與實路徑寫同一指針檔。
- last-writer-wins：同 cwd 二次寫入覆蓋 session_id。
- 註冊面（⑤）：governance/registrations/zcode.json 合法 JSON 且
  PreToolUse 恰一 identity_pointer 無 matcher 條目；
  manifest [surfaces.hooks].scripts 列 hooks/identity_pointer.py；
  install.render 展開後無殘留 placeholder。
"""

import hashlib
import json
import os
import stat
import tomllib
from pathlib import Path

from conftest import load_module

_hook = load_module("hooks/identity_pointer.py")
_install = load_module("governance/install.py")
_seam = load_module("scripts/session_discovery.py")  # IDENTITY_DIR_ENV 常數源

SID = "sess_pointer-0001"
CWD = "/Users/ctai/Github/ai-guide"


def _payload(sid: object = SID, cwd: object = CWD) -> str:
    return json.dumps({"session_id": sid, "cwd": cwd, "hook_event_name": "PreToolUse"})


def _pointer_path(state_dir: Path, cwd: str = CWD) -> Path:
    # 注入語義＝identity 目錄本身（取代 `_default_identity_dir()` 整個推導
    # ——同 seam sidecar 注入慣例）；檔名＝sha256(realpath(cwd))。
    real = os.path.realpath(cwd)
    digest = hashlib.sha256(real.encode("utf-8")).hexdigest()
    return state_dir / f"{digest}.json"


class TestHookWritePath:
    def test_valid_payload_writes_pointer_atomic_and_quiet(
        self, tmp_path: Path, capsys
    ) -> None:
        state_dir = tmp_path / "state"
        rc, out = _hook.run(_payload(), writer=_hook.make_writer(state_dir))
        assert rc == 0
        assert out == ""
        assert capsys.readouterr() == ("", "")
        path = _pointer_path(state_dir)
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert doc["session_id"] == SID
        assert doc["harness"] == "zcode"
        assert doc["cwd_realpath"] == CWD
        assert doc["schema_version"] == 1
        assert isinstance(doc["updated_at_us"], int)
        assert list(path.parent.glob("*.tmp")) == []  # atomic：無 tmp 殘留

    def test_pointer_file_0600_dir_0700(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "state"
        _hook.run(_payload(), writer=_hook.make_writer(state_dir))
        path = _pointer_path(state_dir)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700

    def test_symlinked_cwd_resolves_to_same_pointer(self, tmp_path: Path) -> None:
        real = tmp_path / "real-ws"
        real.mkdir()
        link = tmp_path / "link-ws"
        link.symlink_to(real)
        state_dir = tmp_path / "state"
        write = _hook.make_writer(state_dir)
        _hook.run(_payload(cwd=str(real)), writer=write)
        _hook.run(_payload(cwd=str(link)), writer=write)
        # 兩次寫入落同一檔（realpath 對齊）——末次內容可讀
        path = _pointer_path(state_dir, cwd=str(real))
        assert json.loads(path.read_text(encoding="utf-8"))["cwd_realpath"] == str(real)

    def test_last_writer_wins_overwrites_session_id(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "state"
        write = _hook.make_writer(state_dir)
        _hook.run(_payload(sid="sess_first"), writer=write)
        _hook.run(_payload(sid="sess_second"), writer=write)
        path = _pointer_path(state_dir)
        assert json.loads(path.read_text(encoding="utf-8"))["session_id"] == "sess_second"

    def test_camel_case_session_id_accepted(self, tmp_path: Path) -> None:
        """sessionId 容器鍵 fallback（compat 雙讀慣例——ZCode 恆 snake，
        fallback 屬預鋪）。"""
        state_dir = tmp_path / "state"
        rc, _ = _hook.run(
            json.dumps({"sessionId": SID, "cwd": CWD}),
            writer=_hook.make_writer(state_dir),
        )
        assert rc == 0
        doc = json.loads(_pointer_path(state_dir).read_text(encoding="utf-8"))
        assert doc["session_id"] == SID


class TestHookSilentFailOpen:
    """恆 (0, "")——壞 stdin／缺欄位／非字串／writer 異常皆不寫不響
    （AIR-135 條 3 advisory）。"""

    def test_bad_json_silent_no_write(self, tmp_path: Path, capsys) -> None:
        state_dir = tmp_path / "state"
        assert _hook.run("{not json", writer=_hook.make_writer(state_dir)) == (0, "")
        assert list(state_dir.glob("*.json")) == []
        assert capsys.readouterr() == ("", "")

    def test_empty_stdin_silent_no_write(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "state"
        assert _hook.run("", writer=_hook.make_writer(state_dir)) == (0, "")
        assert _hook.run("   \n", writer=_hook.make_writer(state_dir)) == (0, "")
        assert list(state_dir.glob("*.json")) == []

    def test_non_dict_payload_silent_no_write(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "state"
        write = _hook.make_writer(state_dir)
        assert _hook.run("[1,2,3]", writer=write) == (0, "")
        assert _hook.run('"str"', writer=write) == (0, "")
        assert list(state_dir.glob("*.json")) == []

    def test_missing_or_non_string_fields_silent_no_write(self, tmp_path: Path) -> None:
        state_dir = tmp_path / "state"
        write = _hook.make_writer(state_dir)
        for payload in (
            json.dumps({"cwd": CWD}),  # 缺 session_id
            json.dumps({"session_id": SID}),  # 缺 cwd
            json.dumps({"session_id": "", "cwd": CWD}),  # 空 sid
            json.dumps({"session_id": 123, "cwd": CWD}),  # 非字串 sid
            json.dumps({"session_id": SID, "cwd": ""}),  # 空 cwd
        ):
            assert _hook.run(payload, writer=write) == (0, ""), payload
        assert list(state_dir.glob("*.json")) == []

    def test_writer_crash_swallowed_silent_exit0(self, tmp_path: Path) -> None:
        """核心寫入失敗（OSError 等）——advisory 護甲：恆 (0, "")。"""

        def boom(sid: str, cwd: str) -> bool:
            raise OSError("disk gone")

        assert _hook.run(_payload(), writer=boom) == (0, "")

    def test_core_load_failure_swallowed_silent_exit0(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """核心載入失敗（rollback 窗 scripts 檔異動等）——同款護甲。"""

        def broken_loader():
            raise ImportError("core unavailable")

        monkeypatch.setattr(_hook, "_load_core", broken_loader)
        assert _hook.run(_payload()) == (0, "")

    def test_main_stdin_contract_exit_zero_always(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        # main() 走內建 writer（writer=None→預設 identity dir）——env 注入
        # tmp，禁寫真實 user state。
        monkeypatch.setenv(_seam.IDENTITY_DIR_ENV, str(tmp_path / "state"))
        for raw in ("{bad", "", _payload()):
            monkeypatch.setattr(
                "sys.stdin", type("S", (), {"read": staticmethod(lambda r=raw: r)})()
            )
            assert _hook.main() == 0


class TestRegistration:
    """⑤ 註冊面：模板 JSON 合法＋條目在場＋manifest scripts 列＋render 展開。"""

    def _zcode_template(self) -> dict:
        raw = (_install.MANIFEST_PATH.parent / "registrations" / "zcode.json").read_text()
        return json.loads(raw)  # 合法 JSON 即過

    def _identity_hooks(self, tpl: dict) -> list[tuple[dict, dict]]:
        hits: list[tuple[dict, dict]] = []
        for group in tpl["events"].get("PreToolUse", []):
            for hook in group.get("hooks", []):
                if any(
                    a.endswith("hooks/identity_pointer.py") for a in hook.get("args", [])
                ):
                    hits.append((group, hook))
        return hits

    def test_pretooluse_entry_present_no_matcher(self) -> None:
        hits = self._identity_hooks(self._zcode_template())
        assert len(hits) == 1  # 恰一條目
        group, hook = hits[0]
        assert "matcher" not in group  # 省略＝匹配全部工具（心跳完備）
        assert hook["type"] == "process"
        assert hook["command"] == "{{HOOK_PYTHON}}"
        assert hook["timeoutMs"] == 10000

    def test_manifest_scripts_lists_hook(self) -> None:
        manifest = tomllib.loads(_install.MANIFEST_PATH.read_text(encoding="utf-8"))
        scripts = manifest["surfaces"]["hooks"]["scripts"]
        assert scripts.count("hooks/identity_pointer.py") == 1

    def test_render_expands_placeholders(self) -> None:
        raw = (_install.MANIFEST_PATH.parent / "registrations" / "zcode.json").read_text()
        rendered = _install.render(raw)
        assert "{{REPO}}" not in rendered
        assert "{{HOOK_PYTHON}}" not in rendered
        assert "identity_pointer.py" in rendered
