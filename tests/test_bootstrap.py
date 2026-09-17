"""scripts/bootstrap.py 編排器測試（AIR-110；R2 修復批語義）。

HOME-shim sandbox 模式（AIR-116 先例：load_module＋monkeypatch＋
monkeypatch.setenv("HOME")——tests/test_check_single_source.py AIR-120 同款）。
子進程全走 module 屬性錄影（recorder），argv 層接線另以 sys.executable 整跑一腿。
冪等語義：編排器無狀態＝重跑同 argv 序列；installer noop 由 AIR-116 自身冪等保證。

R2 裁決語義（勿重辯）：
- codex#1 monitor 入編排：Phase 2＝all 成功後跑 monitor；Phase 4 含 monitor --check。
- codex#2 --approved＝resume：跳過 Phase 2（preflight→直接 Phase 4）；禁先裝再當已批准。
- codex#3 hooksPath：Phase 1 WARN；Phase 4 完成檢查 FAIL（completion exit 非零）。
- codex#4 muse CLI 缺席＝preflight FAIL。
- codex#8 linked worktree（git-common-dir 含 worktrees）＝preflight FAIL。
"""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from conftest import load_module

boot = load_module("scripts/bootstrap.py")
BOOTSTRAP_PATH = Path(__file__).resolve().parents[1] / "scripts" / "bootstrap.py"


def _sandbox_green(
    tmp_path: Path,
    monkeypatch,
    git_rc: int = 1,
    git_out: str = "",
    git_dir: str = ".git",
    git_common: str = ".git",
) -> list:
    """preflight 全綠沙箱：.git＋settings.json 在場、uv/muse 在 PATH、子進程錄影。

    git_rc=1（hooksPath 未設）→ preflight WARN 不擋；安裝/探針類一律回 0。
    git_dir/git_common 預設＝primary checkout 形態（兩 flag 同值——canonical
    probe PASS；實測：linked worktree 的 --git-dir 含 worktrees 節、
    --git-common-dir 恆回主 repo .git）。
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
        if argv[:3] == ("git", "rev-parse", "--git-dir"):
            return SimpleNamespace(returncode=0, stdout=f"{git_dir}\n", stderr="")
        if argv[:3] == ("git", "rev-parse", "--git-common-dir"):
            return SimpleNamespace(returncode=0, stdout=f"{git_common}\n", stderr="")
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


# ── R2 codex#4／codex#8：外部執行檔＋canonical checkout preflight ──


def test_preflight_muse_missing_fail_loud(tmp_path, monkeypatch, capsys):
    """codex#4：muse CLI 缺席＝preflight FAIL（installer memory face 前置）。"""
    (tmp_path / ".git").mkdir()
    (tmp_path / "settings.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(boot, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        boot,
        "shutil",
        SimpleNamespace(which=lambda n: "/usr/local/bin/uv" if n == "uv" else None),
    )
    monkeypatch.setattr(
        boot,
        "subprocess",
        SimpleNamespace(
            run=lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="")
        ),
    )
    rc = boot.main(["--dry-run"])
    assert rc != 0
    out = capsys.readouterr().out
    assert "先安裝 Muse CLI（訂閱載具）再跑" in out


def test_preflight_card_worktree_fail_loud(tmp_path, monkeypatch, capsys):
    """codex#8（機制按 git 實測修正）：linked worktree 判定＝--git-dir 含
    worktrees 節／與 --git-common-dir 不等＝FAIL——card WT 安裝會在共享 home
    config 留重複 group、symlink 指向 WT 生命週期路徑。實測形態：
    --git-dir=<main>/.git/worktrees/<name>、--git-common-dir=<main>/.git。"""
    worktree_dir = "/opt/src/ai-guide/.git/worktrees/air-110"
    calls = _sandbox_green(
        tmp_path, monkeypatch,
        git_dir=worktree_dir, git_common="/opt/src/ai-guide/.git")
    rc = boot.main(["--dry-run"])
    assert rc != 0
    out = capsys.readouterr().out
    assert "canonical primary checkout" in out
    assert worktree_dir in out  # 診斷帶實際 git-dir
    assert ("git", "rev-parse", "--git-dir") in calls  # probe 真跑
    assert ("git", "rev-parse", "--git-common-dir") in calls


def test_preflight_primary_checkout_passes(tmp_path, monkeypatch, capsys):
    """primary checkout（--git-dir 與 --git-common-dir 同值）＝PASS 不擋。"""
    _sandbox_green(tmp_path, monkeypatch, git_dir="/opt/src/ai-guide/.git",
                   git_common="/opt/src/ai-guide/.git")
    assert boot.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert any("PASS" in line and "canonical" in line for line in out.splitlines())


# ── --dry-run：零安裝執行、印計畫 ─────────────────────────────────


def test_dry_run_zero_execution_prints_plan(tmp_path, monkeypatch, capsys):
    calls = _sandbox_green(tmp_path, monkeypatch)
    rc = boot.main(["--dry-run"])
    assert rc == 0
    non_git = [
        c for c in calls if c[0] != "git"
    ]  # 唯讀 preflight（git config/rev-parse 查詢）以外零執行
    assert non_git == []
    out = capsys.readouterr().out
    assert "governance/install.py" in out  # 計畫含 installer 命令（文字非執行）
    assert "--surface monitor" in out  # codex#1：計畫含 monitor 裝載＋monitor check
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


# ── Phase 2/3：installer 透傳＋monitor 入編排＋approve 暫停點（拍板④）──


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
    assert len(install_calls) == 2  # codex#1：Phase 2＝all＋monitor 各恰一次
    assert install_calls[0][-2:] == ("--surface", "all")
    assert install_calls[1][-2:] == ("--surface", "monitor")
    assert not any("--verify" in c or "--check" in c for c in calls)  # Phase 4 未觸


def test_phase2_monitor_after_all(tmp_path, monkeypatch, capsys):
    """codex#1：primary Phase 2＝--surface all 成功後再跑 --surface monitor。"""
    calls = _sandbox_green(tmp_path, monkeypatch)
    rc = boot.main([])
    assert rc == 0
    install_calls = [c for c in calls if "governance/install.py" in c]
    assert install_calls[0][-2:] == ("--surface", "all")
    assert install_calls[1][-2:] == ("--surface", "monitor")


def test_phase2_exit_passthrough(tmp_path, monkeypatch, capsys):
    (tmp_path / ".git").mkdir()
    (tmp_path / "settings.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(boot, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        boot, "shutil", SimpleNamespace(which=lambda n: "/usr/local/bin/uv")
    )

    def fake_run(argv, **kw):
        if argv[:3] == ("git", "rev-parse", "--git-common-dir") or argv[:3] == (
            "git", "rev-parse", "--git-dir"
        ):
            return SimpleNamespace(returncode=0, stdout="/opt/r/.git\n", stderr="")
        if "governance/install.py" in argv:
            return SimpleNamespace(returncode=2, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(boot, "subprocess", SimpleNamespace(run=fake_run))
    monkeypatch.setenv("HOME", str(tmp_path))
    assert boot.main([]) == 2  # installer exit 透傳


def test_phase2_monitor_failure_passthrough(tmp_path, monkeypatch):
    """codex#1 附：monitor 腿失敗＝exit 透傳（all 成功後 monitor rc=5）。"""
    (tmp_path / ".git").mkdir()
    (tmp_path / "settings.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(boot, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        boot, "shutil", SimpleNamespace(which=lambda n: "/usr/local/bin/uv")
    )

    def fake_run(argv, **kw):
        if argv[:2] == ("git", "config"):
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        if argv[:3] in (("git", "rev-parse", "--git-common-dir"),
                        ("git", "rev-parse", "--git-dir")):
            return SimpleNamespace(returncode=0, stdout="/opt/r/.git\n", stderr="")
        if "governance/install.py" in argv and argv[-1] == "monitor":
            return SimpleNamespace(returncode=5, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(boot, "subprocess", SimpleNamespace(run=fake_run))
    monkeypatch.setenv("HOME", str(tmp_path))
    assert boot.main([]) == 5


# ── Phase 4/5：--approved resume＋全探針＋完成檢查＋冪等重跑 ──────


def test_approved_skips_phase2(tmp_path, monkeypatch, capsys):
    """codex#2：--approved＝resume——跳過 Phase 2（preflight→直接 Phase 4），
    installer 呼叫僅限 --verify/--check 形態（禁「先裝再當已批准」路徑）。"""
    calls = _sandbox_green(tmp_path, monkeypatch, git_rc=0, git_out=".githooks")
    rc = boot.main(["--approved"])
    assert rc == 0
    installer_calls = [c for c in calls if "governance/install.py" in c]
    assert installer_calls  # Phase 4 probes 有跑
    assert all("--verify" in c or "--check" in c for c in installer_calls)


def test_approved_runs_all_probes_and_external_list(tmp_path, monkeypatch, capsys):
    calls = _sandbox_green(tmp_path, monkeypatch, git_rc=0, git_out=".githooks")
    rc = boot.main(["--approved"])
    assert rc == 0
    out = capsys.readouterr().out
    for probe in (
        ("governance/install.py", "--verify"),
        ("governance/install.py", "--check"),
        ("governance/install.py", "monitor", "--check"),  # codex#1 monitor probe
        ("hooks/verify-memory-topology.sh",),
        ("skills/scan-project/scripts/check_single_source.py",),
    ):
        assert any(all(part in c for part in probe) for c in calls), probe
    assert "PASS" in out
    assert ".githooks" in out  # hooksPath 輸出探針
    assert "memory-spine" in out  # spine degraded 檢查（缺席皆報告非擋）
    assert "delegate-bridge" in out  # 面外：跨 repo 工具
    assert "code-reality" in out
    assert "backlog-cleanup" in out  # 面外：G5 已版控（muse F-2）
    assert "deploy/backlog-cleanup.plist" in out


def test_phase4_hooks_path_completion_fail(tmp_path, monkeypatch, capsys):
    """codex#3：Phase 1 維持 WARN；Phase 4 完成檢查升 FAIL——未設 .githooks＝
    completion exit 非零，訊息指修復指令。"""
    _sandbox_green(tmp_path, monkeypatch, git_rc=1, git_out="")  # hooksPath 未設
    rc = boot.main(["--approved"])
    assert rc != 0
    out = capsys.readouterr().out
    assert "WARN" in out  # Phase 1 WARN 不擋（preflight 已過）
    fail_lines = [ln for ln in out.splitlines() if "FAIL" in ln and "hooksPath" in ln]
    assert fail_lines  # Phase 4 完成檢查 FAIL
    assert "core.hooksPath .githooks" in out  # 修復指令


def test_spine_present_reports_pass(tmp_path, monkeypatch, capsys):
    _sandbox_green(tmp_path, monkeypatch, git_rc=0, git_out=".githooks")
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
    """冪等＋resume（codex#2）：兩輪 --approved 的 uv 呼叫 argv 序列逐字相同、
    兩輪皆全綠 exit 0，且皆不含裸 install 形態（Phase 2 已跳過）。"""
    calls = _sandbox_green(tmp_path, monkeypatch, git_rc=0, git_out=".githooks")
    assert boot.main(["--approved"]) == 0
    capsys.readouterr()
    uv_seq_1 = [c for c in calls if c[0] == "uv"]
    assert all(
        "--verify" in c or "--check" in c
        for c in uv_seq_1
        if "governance/install.py" in c
    )
    n_after_first = len(calls)
    assert boot.main(["--approved"]) == 0  # 重跑：installer noop、全 probe 綠
    uv_seq_2 = [c for c in calls[n_after_first:] if c[0] == "uv"]
    assert uv_seq_2 == uv_seq_1
    assert len(uv_seq_1) >= 4  # verify＋check＋monitor check＋check_single_source
