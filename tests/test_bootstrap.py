"""scripts/bootstrap.py 編排器測試（AIR-110）。

HOME-shim sandbox 模式（AIR-116 先例：load_module＋monkeypatch＋
monkeypatch.setenv("HOME")——tests/test_check_single_source.py AIR-120 同款）。
子進程全走 module 屬性錄影（recorder），argv 層接線另以 sys.executable 整跑一腿。
冪等語義：編排器無狀態＝重跑同 argv 序列；installer noop 由 AIR-116 自身冪等保證。
"""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from conftest import load_module

boot = load_module("scripts/bootstrap.py")
BOOTSTRAP_PATH = Path(__file__).resolve().parents[1] / "scripts" / "bootstrap.py"


def _sandbox_green(
    tmp_path: Path, monkeypatch, git_rc: int = 1, git_out: str = ""
) -> list:
    """preflight 全綠沙箱：.git＋settings.json 在場、uv 在 PATH、子進程錄影。

    git_rc=1（hooksPath 未設）→ preflight WARN 不擋；安裝/探針類一律回 0。
    HOME 指沙箱 → spine 檢查缺席（degraded WARN 非擋）。
    """
    (tmp_path / ".git").mkdir()
    (tmp_path / "settings.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(boot, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        boot, "shutil", SimpleNamespace(which=lambda n: "/usr/local/bin/uv")
    )
    calls: list = []

    def fake_run(argv, **kw):
        calls.append(tuple(argv))
        if argv[:2] == ("git", "config"):
            return SimpleNamespace(returncode=git_rc, stdout=git_out, stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(boot, "subprocess", SimpleNamespace(run=fake_run))
    monkeypatch.setenv("HOME", str(tmp_path))
    return calls


# ── G1 secrets fail-loud（拍板①）──────────────────────────────────


def test_g1_missing_settings_fail_loud(tmp_path, monkeypatch, capsys):
    (tmp_path / ".git").mkdir()  # settings.json 缺席＝secrets 未拷
    monkeypatch.setattr(boot, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        boot, "shutil", SimpleNamespace(which=lambda n: "/usr/local/bin/uv")
    )
    monkeypatch.setattr(
        boot,
        "subprocess",
        SimpleNamespace(
            run=lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="")
        ),
    )
    rc = boot.main([])
    assert rc != 0
    out = capsys.readouterr().out
    assert "settings.json" in out
    assert str(tmp_path) in out  # 引導印出實際 repo 路徑
    assert "拷" in out or "copy" in out.lower()


def test_preflight_uv_missing_fail_loud(tmp_path, monkeypatch, capsys):
    (tmp_path / ".git").mkdir()
    (tmp_path / "settings.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(boot, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(boot, "shutil", SimpleNamespace(which=lambda n: None))
    monkeypatch.setattr(
        boot,
        "subprocess",
        SimpleNamespace(
            run=lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="")
        ),
    )
    rc = boot.main([])
    assert rc != 0
    assert "uv" in capsys.readouterr().out


def test_preflight_missing_git_fail_loud(tmp_path, monkeypatch, capsys):
    (tmp_path / "settings.json").write_text(
        "{}\n", encoding="utf-8"
    )  # 無 .git＝非 repo
    monkeypatch.setattr(boot, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        boot, "shutil", SimpleNamespace(which=lambda n: "/usr/local/bin/uv")
    )
    monkeypatch.setattr(
        boot,
        "subprocess",
        SimpleNamespace(
            run=lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="")
        ),
    )
    rc = boot.main([])
    assert rc != 0
    assert ".git" in capsys.readouterr().out


# ── --dry-run：零安裝執行、印計畫 ─────────────────────────────────


def test_dry_run_zero_execution_prints_plan(tmp_path, monkeypatch, capsys):
    calls = _sandbox_green(tmp_path, monkeypatch)
    rc = boot.main(["--dry-run"])
    assert rc == 0
    non_git = [
        c for c in calls if c[0] != "git"
    ]  # 唯讀 preflight（git config 查詢）以外零執行
    assert non_git == []
    out = capsys.readouterr().out
    assert "governance/install.py" in out  # 計畫含 installer 命令（文字非執行）
    assert "verify-memory-topology" in out
    assert "check_single_source" in out


# ── --role secondary：僅介面（拍板②）─────────────────────────────


def test_role_secondary_interface(tmp_path, monkeypatch, capsys):
    calls = _sandbox_green(tmp_path, monkeypatch)
    rc = boot.main(["--role", "secondary"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "本弧未實作" in out
    assert "介面" in out
    assert calls == []  # 零子進程


def test_secondary_subprocess_smoke():
    r = subprocess.run(
        [sys.executable, str(BOOTSTRAP_PATH), "--role", "secondary"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0
    assert "本弧未實作" in r.stdout


# ── Phase 2/3：installer 透傳＋approve 暫停點（拍板④）────────────


def test_approve_pause_without_flag(tmp_path, monkeypatch, capsys):
    calls = _sandbox_green(tmp_path, monkeypatch)
    rc = boot.main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "/hooks" in out  # CC 目視
    assert "codex" in out and "trust" in out.lower()
    assert "ZCode" in out and "session" in out
    assert "--approved" in out  # 續跑指引
    install_calls = [c for c in calls if "governance/install.py" in c]
    assert len(install_calls) == 1  # Phase 2 真跑恰好一次
    assert install_calls[0][-2:] == ("--surface", "all")
    assert not any("--verify" in c for c in calls)  # Phase 4 未觸（無 --approved）


def test_phase2_exit_passthrough(tmp_path, monkeypatch, capsys):
    (tmp_path / ".git").mkdir()
    (tmp_path / "settings.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(boot, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        boot, "shutil", SimpleNamespace(which=lambda n: "/usr/local/bin/uv")
    )

    def fake_run(argv, **kw):
        if "governance/install.py" in argv:
            return SimpleNamespace(returncode=2, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(boot, "subprocess", SimpleNamespace(run=fake_run))
    monkeypatch.setenv("HOME", str(tmp_path))
    assert boot.main([]) == 2  # installer exit 透傳


# ── Phase 4/5：--approved 全探針＋面外清單＋冪等重跑 ──────────────


def test_approved_runs_all_probes_and_external_list(tmp_path, monkeypatch, capsys):
    calls = _sandbox_green(tmp_path, monkeypatch, git_rc=0, git_out=".githooks")
    rc = boot.main(["--approved"])
    assert rc == 0
    out = capsys.readouterr().out
    for probe in (
        ("governance/install.py", "--verify"),
        ("governance/install.py", "--check"),
        ("hooks/verify-memory-topology.sh",),
        ("skills/scan-project/scripts/check_single_source.py",),
    ):
        assert any(all(part in c for part in probe) for c in calls), probe
    assert "PASS" in out
    assert ".githooks" in out  # hooksPath 輸出探針
    assert "memory-spine" in out  # spine degraded 檢查（缺席皆報告非擋）
    assert "delegate-bridge" in out  # 面外：跨 repo 工具
    assert "code-reality" in out
    assert "backlog-cleanup" in out  # 面外：G5 另 flash


def test_spine_present_reports_pass(tmp_path, monkeypatch, capsys):
    _sandbox_green(tmp_path, monkeypatch)
    spine = tmp_path / ".agents" / "memory-spine" / "index.md"
    spine.parent.mkdir(parents=True)
    spine.write_text("x\n", encoding="utf-8")
    rc = boot.main(["--approved"])
    assert rc == 0
    out = capsys.readouterr().out
    assert any("memory-spine" in line and "PASS" in line for line in out.splitlines())


def test_verify_probe_fail_exits_nonzero(tmp_path, monkeypatch, capsys):
    (tmp_path / ".git").mkdir()
    (tmp_path / "settings.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(boot, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        boot, "shutil", SimpleNamespace(which=lambda n: "/usr/local/bin/uv")
    )

    def fake_run(argv, **kw):
        if argv[:2] == ("git", "config"):
            return SimpleNamespace(returncode=0, stdout=".githooks", stderr="")
        if "--verify" in argv:  # installer --verify 腿 FAIL
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(boot, "subprocess", SimpleNamespace(run=fake_run))
    monkeypatch.setenv("HOME", str(tmp_path))
    rc = boot.main(["--approved"])
    assert rc != 0
    assert "FAIL" in capsys.readouterr().out


def test_idempotent_rerun_same_sequence_and_green(tmp_path, monkeypatch, capsys):
    """冪等：兩輪 --approved 的 uv 呼叫 argv 序列逐字相同、兩輪皆全綠 exit 0。"""
    calls = _sandbox_green(tmp_path, monkeypatch, git_rc=0, git_out=".githooks")
    assert boot.main(["--approved"]) == 0
    capsys.readouterr()
    uv_seq_1 = [c for c in calls if c[0] == "uv"]
    n_after_first = len(calls)
    assert boot.main(["--approved"]) == 0  # 重跑：installer noop、全 probe 綠
    uv_seq_2 = [c for c in calls[n_after_first:] if c[0] == "uv"]
    assert uv_seq_2 == uv_seq_1
    assert len(uv_seq_1) >= 4  # Phase 2 真跑＋verify＋check＋check_single_source
