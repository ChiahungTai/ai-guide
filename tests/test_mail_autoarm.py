"""mail_autoarm hook 測試（AIR-318——夜間通信鏈 v1 SessionStart 面）。

涵蓋：
- marker 三態（同 marshal-governance 慣例）：absent＝零輸出、valid
  （JSON 物件且 protocol==1）＝偵測、malformed（壞 JSON／非物件／缺
  protocol／protocol!=1／protocol=true 陷阱）＝fail-loud 提示（exit 0
  不擋 session start——大聲＝additionalContext 可見，非靜默當 absent）。
- 偵測面分流：desired=stopped（停哨權威）與 armed_at 新鮮（< 輪詢週期
  ×門牌數×3）＝靜默不動；state 缺席／stale＝advisory 一行（帶 repo
  身份＋start 命令＋mail-watch 協議提示）。AIR-328 誠實面：缺哨
  advisory＝「尚未掛哨」需啟動指示，禁宣稱「已為…掛哨」（negative
  predicate 釘死；provenance=S——EP 段落 2／TC4 凍結驗收）。
- hook 紅線：零 dutymail 呼叫、零寫入（測試零 face runner 注入即證——
  run() 契約無 runner 參數可碰 face）；身份/state 讀面全隔離（tmp git
  repo＋XDG_STATE_HOME monkeypatch，禁碰真 repo 根與真 store）。
- payload 容錯：空 stdin／壞 JSON／非 SessionStart／缺 cwd＝靜默 exit 0。
- 3.9 語法 floor（hooks/AGENTS.md rollback floor——test_governance_check
  C4 同款 gate 另有全域掃描，此處單檔釘）。

測試形態：load_module 載 hooks/mail_autoarm.py（conftest 同款）；核心
（mail_waiter＋duty_receive）經其內部 importlib 載入——tmp git repo 的
common-dir 推導真跑 git（身份面真證），state 面走 --state-dir／XDG
注入零真 store 往返。
"""

import ast
import json
import os
import subprocess
import time

from conftest import REPO_ROOT, load_module

mod = load_module("hooks/mail_autoarm.py")


def _payload(cwd, event="SessionStart"):
    return json.dumps({"hook_event_name": event, "cwd": str(cwd)})


def _git_repo(tmp_path, name="autoarm-repo"):
    repo = tmp_path / name
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    return repo


def _write_marker(repo, doc, raw=None):
    agents = repo / ".agents"
    agents.mkdir(exist_ok=True)
    path = agents / "mail-autoarm.json"
    path.write_text(
        raw if raw is not None else json.dumps(doc), encoding="utf-8"
    )
    return path


def _seed_watcher_state(xdg, identity, desired="running", armed_at=None,
                        generation=3):
    """seed per-repo watcher state（mail_waiter 佈局——測試隔離面）。"""
    state_dir = (
        xdg / "ai-guide" / "mail-waiter" / identity
    )
    state_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "desired": desired,
        "generation": generation,
        "armed_at": armed_at if armed_at is not None else time.time(),
        "addresses": {
            identity: {"cursor": None, "accepted_cursor": None,
                       "last_event_seq": 0}
        },
        "last_exit": None,
        "last_round_failed": False,
    }
    (state_dir / "state.json").write_text(json.dumps(doc), encoding="utf-8")
    return state_dir / "state.json"


# ── marker 三態 ───────────────────────────────────────────────────────


class TestMarkerThreeStates:
    def test_absent_marker_silent(self, tmp_path):
        repo = _git_repo(tmp_path)
        code, out = mod.run(_payload(repo))
        assert code == 0
        assert out == ""

    def test_valid_minimal_marker_enables_detection(self, tmp_path):
        repo = _git_repo(tmp_path)
        _write_marker(repo, {"protocol": 1})
        assert mod.marker_state(str(repo)) == "valid"

    def test_valid_marker_extra_keys_tolerated(self, tmp_path):
        repo = _git_repo(tmp_path)
        _write_marker(repo, {"protocol": 1, "note": "future"})
        assert mod.marker_state(str(repo)) == "valid"

    def test_malformed_bad_json_fail_loud(self, tmp_path):
        repo = _git_repo(tmp_path)
        _write_marker(repo, None, raw="{not json")
        code, out = mod.run(_payload(repo))
        assert code == 0  # 不擋 session start
        assert "fail-loud" in out
        assert "malformed" in out
        assert "mail-autoarm.json" in out  # 指到檔路徑——可修復

    def test_malformed_non_dict_fail_loud(self, tmp_path):
        repo = _git_repo(tmp_path)
        _write_marker(repo, None, raw="[1, 2]")
        _code, out = mod.run(_payload(repo))
        assert "fail-loud" in out

    def test_malformed_missing_or_wrong_protocol_fail_loud(self, tmp_path):
        for doc in ({}, {"protocol": 2}, {"protocol": "1"}):
            repo = _git_repo(tmp_path)
            _write_marker(repo, doc)
            _code, out = mod.run(_payload(repo))
            assert "fail-loud" in out, doc

    def test_malformed_protocol_bool_trap_fail_loud(self, tmp_path):
        """True == 1 等值陷阱——protocol=true 須 malformed（顯式排除）。"""
        repo = _git_repo(tmp_path)
        _write_marker(repo, None, raw='{"protocol": true}')
        assert mod.marker_state(str(repo)) == "malformed"
        _code, out = mod.run(_payload(repo))
        assert "fail-loud" in out

    def test_malformed_linked_worktree_marker_at_primary_root(
        self, tmp_path,
    ):
        """linked worktree cwd 也讀 primary root 的 marker（common-dir
        推導——身份/佈局單一源）。"""
        repo = _git_repo(tmp_path, "wt-root")
        _write_marker(repo, None, raw="nope")
        subprocess.run(
            ["git", "-C", str(repo), "worktree", "add", "-q",
             str(tmp_path / "linked"), "-b", "wt-linked"],
            check=True,
        )
        _code, out = mod.run(_payload(tmp_path / "linked"))
        assert "fail-loud" in out


# ── 偵測面分流（marker valid）────────────────────────────────────────


class TestDetectionRouting:
    def test_cold_state_prints_advisory_with_start_command(
        self, tmp_path, monkeypatch,
    ):
        repo = _git_repo(tmp_path)
        xdg = tmp_path / "xdg"
        monkeypatch.setenv("XDG_STATE_HOME", str(xdg))
        _write_marker(repo, {"protocol": 1})
        code, out = mod.run(_payload(repo))
        assert code == 0
        assert "[mail-autoarm]" in out
        # AIR-328 誠實 advisory（provenance=S——EP 段落 2／TC4 凍結驗收）：
        # 缺哨＝需啟動指示，禁宣稱已掛哨
        assert "尚未掛哨" in out
        assert "已為" not in out  # negative predicate——假成功宣稱禁出場
        assert "autoarm-repo" in out  # 身份＝repo basename
        assert "scripts/mail_waiter.py start" in out  # arm 命令＝start 形
        assert "worker" in out  # mail-watch 協議提示在場

    def test_fresh_worker_silent(self, tmp_path, monkeypatch):
        repo = _git_repo(tmp_path)
        xdg = tmp_path / "xdg"
        monkeypatch.setenv("XDG_STATE_HOME", str(xdg))
        _write_marker(repo, {"protocol": 1})
        _seed_watcher_state(xdg, "autoarm-repo", desired="running",
                            armed_at=time.time())
        code, out = mod.run(_payload(repo))
        assert code == 0
        assert out == ""

    def test_stale_worker_prints_advisory(self, tmp_path, monkeypatch):
        repo = _git_repo(tmp_path)
        xdg = tmp_path / "xdg"
        monkeypatch.setenv("XDG_STATE_HOME", str(xdg))
        _write_marker(repo, {"protocol": 1})
        _seed_watcher_state(
            xdg, "autoarm-repo", desired="running",
            armed_at=time.time() - 10 * 60.0,  # 遠超 60s×1×3
        )
        _code, out = mod.run(_payload(repo))
        assert "尚未掛哨" in out  # AIR-328——stale＝尚未掛哨，非已掛哨
        assert "已為" not in out  # negative predicate（provenance=S：TC4）

    def test_stopped_flag_respected_silent(self, tmp_path, monkeypatch):
        """desired=stopped＝user 停哨權威——即使 armed_at 也不 re-arm
        advisory（不動）。"""
        repo = _git_repo(tmp_path)
        xdg = tmp_path / "xdg"
        monkeypatch.setenv("XDG_STATE_HOME", str(xdg))
        _write_marker(repo, {"protocol": 1})
        _seed_watcher_state(xdg, "autoarm-repo", desired="stopped",
                            armed_at=time.time() - 10 * 60.0)
        code, out = mod.run(_payload(repo))
        assert code == 0
        assert out == ""

    def test_corrupt_state_treated_as_cold_advisory(
        self, tmp_path, monkeypatch,
    ):
        repo = _git_repo(tmp_path)
        xdg = tmp_path / "xdg"
        monkeypatch.setenv("XDG_STATE_HOME", str(xdg))
        _write_marker(repo, {"protocol": 1})
        state_file = _seed_watcher_state(xdg, "autoarm-repo")
        state_file.write_text("{broken", encoding="utf-8")
        _code, out = mod.run(_payload(repo))
        assert "尚未掛哨" in out  # AIR-328——損壞 state 照缺哨誠實提示
        assert "已為" not in out  # negative predicate（provenance=S：TC4）

    def test_zero_face_calls_zero_writes(self, tmp_path, monkeypatch):
        """hook 紅線：全程零 dutymail 呼叫、零 state 寫入——advisory 跑
        完 watcher state bytes 不變（唯讀面）。"""
        repo = _git_repo(tmp_path)
        xdg = tmp_path / "xdg"
        monkeypatch.setenv("XDG_STATE_HOME", str(xdg))
        _write_marker(repo, {"protocol": 1})
        state_file = _seed_watcher_state(
            xdg, "autoarm-repo", armed_at=time.time() - 10 * 60.0
        )
        before = state_file.read_bytes()
        mod.run(_payload(repo))
        assert state_file.read_bytes() == before
        assert not (xdg / "ai-guide" / "mail-waiter" / "other-repo").exists()


# ── payload 容錯（fail-soft 面）───────────────────────────────────────


class TestPayloadTolerance:
    def test_empty_stdin_silent_exit0(self):
        assert mod.run("") == (0, "")

    def test_bad_json_silent_exit0(self):
        assert mod.run("{oops") == (0, "")

    def test_non_dict_payload_silent_exit0(self):
        assert mod.run("[1]") == (0, "")

    def test_other_event_silent_exit0(self, tmp_path):
        assert mod.run(_payload(tmp_path, event="PreToolUse")) == (0, "")

    def test_missing_cwd_silent_exit0(self):
        code, out = mod.run('{"hook_event_name": "SessionStart"}')
        assert (code, out) == (0, "")

    def test_non_git_cwd_with_no_marker_silent(self, tmp_path):
        plain = tmp_path / "plain"
        plain.mkdir()
        assert mod.run(_payload(plain)) == (0, "")

    def test_real_entrypoint_devnull_exit0_zero_output(self):
        """驗證 3 同款：uv run python hooks/mail_autoarm.py < /dev/null
        → exit 0 零輸出（absent marker 預設路徑——空 stdin 早退）。"""
        proc = subprocess.run(
            ["uv", "run", "python", "hooks/mail_autoarm.py"],
            cwd=str(REPO_ROOT),
            stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=120,
        )
        assert proc.returncode == 0
        assert proc.stdout == ""


# ── 3.9 語法 floor（hooks/AGENTS.md rollback floor）───────────────────


def test_hook_parses_under_py39_grammar():
    source = (REPO_ROOT / "hooks" / "mail_autoarm.py").read_text(
        encoding="utf-8"
    )
    ast.parse(source, filename="hooks/mail_autoarm.py")  # 當前 runtime
    ast.parse(source, filename="hooks/mail_autoarm.py",
              feature_version=(3, 9))  # rollback floor
