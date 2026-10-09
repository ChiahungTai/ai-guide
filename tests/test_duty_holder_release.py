"""duty holder release hook 測試（AIR-288 judge MF1(i)——bridge item 6(a)
SessionEnd 面）。

契約：SessionEnd payload → session_id → state 檔 live token →
`holder release --address --token`（fail-soft——release 失敗不擋
session 收尾，exit 恆 0）；成功後 state 檔移除（session 終局）。
無 session_id／非 SessionEnd 事件／壞 JSON／無 state＝零呼叫零輸出；
`--address` 給定且與 state address 不符＝拒釋（防跨 address 誤釋）。
註冊面斷言：codex/grok SessionEnd 各一條＋manifest scripts 登記
（ZCode 無 SessionEnd 事件——harness 限制，接管走 death-evidence，
單一源＝scripts/duty_receive.py `_holder_death_evidence`）。

測試全走 injectable runner＋fake state（tmp_path）——不碰真 store。
"""

import json
import os
import tomllib

import pytest
from conftest import REPO_ROOT, load_module

core = load_module("scripts/duty_receive.py")
hook = load_module("hooks/duty_holder_release.py")

ADDR = "ai-guide-marshal"


def _stdin(event="SessionEnd", session_id="sess-end-1"):
    return json.dumps(
        {"hook_event_name": event, "session_id": session_id}
    )


def _seed_state(state_dir, sid, address=ADDR, token="tok-live", epoch=4):
    path = core.state_path(sid, state_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"address": address, "epoch": epoch, "token": token}, fh)
    return path


def _ok(result):
    return json.dumps({"schemaVersion": 1, "ok": True, "result": result})


def _seq_runner(steps):
    calls = []

    def run(argv):
        calls.append(list(argv))
        if len(calls) > len(steps):
            raise AssertionError("unexpected call: " + repr(list(argv)))
        step = steps[len(calls) - 1]
        if isinstance(step, Exception):
            raise step
        return step

    run.calls = calls
    return run


def _face_err(code="stale-epoch", error_class="fencing"):
    return core.DutymailFaceError(
        code=code, error_class=error_class, message="typed failure",
        retryable=False, exit_code=5,
    )


class TestReleaseHookRun:
    def test_sessionend_releases_with_live_token(self, tmp_path, capsys):
        """SessionEnd＋state 有 live token → release 呼叫（帶 state 的
        address＋token）、state 檔移除、exit 0、stdout 恆空。"""
        state_dir = str(tmp_path / "state")
        spath = _seed_state(state_dir, "sess-end-1")
        runner = _seq_runner([
            _ok({"addressId": "a1", "fencedBatches": []}),
        ])
        code, out = hook.run(
            _stdin(), runner=runner, state_dir=state_dir,
        )
        assert code == 0 and out == ""
        assert runner.calls == [
            ["holder", "release", "--address", ADDR,
             "--token", "tok-live"],
        ]
        assert not os.path.exists(spath)

    def test_no_session_id_silent_noop(self, tmp_path):
        """無 session_id＝零 state 定位、零 face 呼叫。"""
        runner = _seq_runner([])
        code, out = hook.run(
            json.dumps({"hook_event_name": "SessionEnd"}),
            runner=runner, state_dir=str(tmp_path),
        )
        assert code == 0 and out == ""
        assert runner.calls == []

    def test_non_sessionend_event_noop(self, tmp_path):
        """非 SessionEnd 事件（Stop 等）＝零呼叫（release 只掛 session
        終局——每輪 release 會毀值星連續性，judge 對 atexit 的否決
        同理適用）。"""
        runner = _seq_runner([])
        code, out = hook.run(
            _stdin(event="Stop"), runner=runner, state_dir=str(tmp_path),
        )
        assert code == 0 and out == ""
        assert runner.calls == []

    def test_bad_json_silent(self, tmp_path):
        runner = _seq_runner([])
        code, out = hook.run(
            "{not-json", runner=runner, state_dir=str(tmp_path),
        )
        assert code == 0 and out == ""
        assert runner.calls == []

    def test_no_state_noop(self, tmp_path):
        """session 從未值星（無 state 檔）＝無可釋出、零呼叫。"""
        runner = _seq_runner([])
        code, out = hook.run(
            _stdin(), runner=runner, state_dir=str(tmp_path),
        )
        assert code == 0 and out == ""
        assert runner.calls == []

    def test_face_failure_fail_soft_state_kept(self, tmp_path, capsys):
        """release face 失敗 → exit 0（不擋 session 收尾）＋stderr 一行
        （fail-soft）、state 保留（death-evidence 接管兜底）。"""
        state_dir = str(tmp_path / "state")
        spath = _seed_state(state_dir, "sess-end-1")
        runner = _seq_runner([_face_err()])
        code, out = hook.run(
            _stdin(), runner=runner, state_dir=state_dir,
        )
        assert code == 0 and out == ""
        assert os.path.exists(spath)
        err = capsys.readouterr().err
        assert "fail-soft" in err

    def test_address_mismatch_refuses_release(self, tmp_path, capsys):
        """--address 給定且與 state address 不符＝拒釋（零 face 呼叫
        ＋stderr 一行；防跨 address 誤釋——state dir 跨 checkout 共享）。"""
        state_dir = str(tmp_path / "state")
        spath = _seed_state(state_dir, "sess-end-1", address="other-addr")
        runner = _seq_runner([])
        code, _out = hook.run(
            _stdin(), runner=runner, state_dir=state_dir, address=ADDR,
        )
        assert code == 0 and _out == ""
        assert runner.calls == []
        assert os.path.exists(spath)
        assert "拒釋" in capsys.readouterr().err

    def test_address_match_releases(self, tmp_path):
        """--address 給定且吻合＝照常釋出（註冊面顯式宣告 address 的
        正常路徑）。"""
        state_dir = str(tmp_path / "state")
        spath = _seed_state(state_dir, "sess-end-1")
        runner = _seq_runner([
            _ok({"addressId": "a1", "fencedBatches": []}),
        ])
        code, _out = hook.run(
            _stdin(), runner=runner, state_dir=state_dir, address=ADDR,
        )
        assert code == 0
        assert not os.path.exists(spath)


class TestRegistrationWiring:
    def _codex(self):
        return tomllib.loads(
            (REPO_ROOT / "governance" / "registrations" / "codex.toml")
            .read_text(encoding="utf-8")
        )

    def _grok(self):
        return json.loads(
            (REPO_ROOT / "governance" / "registrations" / "grok.json")
            .read_text(encoding="utf-8")
        )

    def _release_cmds(self, groups):
        hits = []
        for g in groups:
            for h in g.get("hooks", []):
                cmd = h.get("command", "")
                if "duty_holder_release.py" in cmd:
                    hits.append((h, cmd))
        return hits

    def test_codex_sessionend_release_wired(self):
        """MF1(i)：codex SessionEnd 面 release hook 恰一條、帶 --address
        （與收信 hook 同 address 慣例）、有 timeout。"""
        hits = self._release_cmds(self._codex()["hooks"]["SessionEnd"])
        assert len(hits) == 1
        h, cmd = hits[0]
        assert "ai-guide-marshal" in cmd
        assert h.get("timeout")

    def test_grok_sessionend_release_wired(self):
        """MF1(i)：grok SessionEnd 面 release hook 恰一條、帶 --address。"""
        hits = self._release_cmds(self._grok()["hooks"]["SessionEnd"])
        assert len(hits) == 1
        h, cmd = hits[0]
        assert "ai-guide-marshal" in cmd
        assert h.get("timeout")

    def test_manifest_lists_release_hook(self):
        """manifest scripts 登記（governance install 識別面）。"""
        manifest = tomllib.loads(
            (REPO_ROOT / "governance" / "manifest.toml")
            .read_text(encoding="utf-8")
        )
        scripts = manifest["surfaces"]["hooks"]["scripts"]
        assert "hooks/duty_holder_release.py" in scripts

    def test_zcode_has_no_release_entry(self):
        """ZCode 無 SessionEnd 事件（harness 限制，governance/README.md）
        ——zcode.json 無 release 條目是正確形態（接管＝death-evidence，
        單一源＝scripts/duty_receive.py）。若未來 ZCode 補 SessionEnd
        事件，本 pin 應隨事件面有意識更新。"""
        zc = json.loads(
            (REPO_ROOT / "governance" / "registrations" / "zcode.json")
            .read_text(encoding="utf-8")
        )
        assert "duty_holder_release.py" not in json.dumps(zc)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
