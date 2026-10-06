"""governance install.py verify probe 測試（AIR-116 S3——AC-3.3 negative 腿）。

oracle 獨立性：muse probe 判定語義對標 AIR-100 S-E monitor evaluate()
（已吸收——scripts/muse_approve_monitor.py 已退役），非待測實作自證；pipe probe 以真 hook subprocess 實跑＋
放行場景（exit 0）必報 FAIL 防恆綠。codex L1/L2/L3 live 驗收歸 AC-3.2/3.4
receipt（host-level fixture 需真 codex runtime，不入單元測試）。
"""

import json
import subprocess
from types import SimpleNamespace

from conftest import load_module

mod = load_module("governance/install.py")


def _muse_doc(status: str, cap_id: str = "memory-inbox") -> str:
    return json.dumps(
        {
            "runtime_capabilities": [
                {"candidate": {"capability_id": cap_id}, "status": status}
            ]
        }
    )


def _patch_run(monkeypatch, *, returncode=0, stdout="", stderr=""):
    fake = SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=lambda *a, **k: fake))
    # probe_muse 先跑 shutil.which——不 patch 時 muse-less 機器回 GUARD 假紅（review S-5）
    monkeypatch.setattr(
        mod, "shutil", SimpleNamespace(which=lambda name: "/usr/bin/muse")
    )


# ── muse probe（AC-3.3：mock 非 trusted → FAIL）──────────────────


def test_muse_probe_pass_all_trusted(monkeypatch):
    _patch_run(monkeypatch, stdout=_muse_doc("trusted_enabled"))
    assert mod.probe_muse("muse-memory-governance")[0] == "PASS"


def test_muse_probe_non_trusted_is_fail(monkeypatch):
    _patch_run(monkeypatch, stdout=_muse_doc("trusted_disabled"))
    status, detail = mod.probe_muse("muse-memory-governance")
    assert status == "FAIL"
    assert "re-approve" in detail


def test_muse_probe_modified_status_is_fail(monkeypatch):
    _patch_run(monkeypatch, stdout=_muse_doc("modified"))
    assert mod.probe_muse("muse-memory-governance")[0] == "FAIL"


def test_muse_probe_empty_capabilities_fail_closed(monkeypatch):
    _patch_run(monkeypatch, stdout=json.dumps({"runtime_capabilities": []}))
    assert mod.probe_muse("x")[0] == "FAIL"


def test_muse_probe_missing_key_fail_closed(monkeypatch):
    _patch_run(monkeypatch, stdout=json.dumps({"record": {}}))
    assert mod.probe_muse("x")[0] == "FAIL"


def test_muse_probe_bad_json_fail_closed(monkeypatch):
    _patch_run(monkeypatch, stdout="not-json")
    assert mod.probe_muse("x")[0] == "FAIL"


def test_muse_probe_non_dict_payload_fail_closed(monkeypatch):
    _patch_run(monkeypatch, stdout="[1, 2]")
    assert mod.probe_muse("x")[0] == "FAIL"


def test_muse_probe_inspect_nonzero_is_fail(monkeypatch):
    _patch_run(monkeypatch, returncode=1, stderr="boom")
    assert mod.probe_muse("x")[0] == "FAIL"


def test_muse_probe_cli_missing_is_guard(monkeypatch):
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda name: None))
    assert mod.probe_muse("x")[0] == "GUARD"


# ── pipe payload probe（真 hook 實跑＋放行場景必 FAIL 防恆綠）────────


def test_pipe_payload_probe_real_hook_pass():
    status, _ = mod.probe_pipe_payload("hooks/block-memory-index-write.py")
    assert status == "PASS"


def test_pipe_payload_probe_missing_script_is_guard():
    assert mod.probe_pipe_payload("hooks/__no_such_hook__.py")[0] == "GUARD"


def test_pipe_payload_probe_hook_allow_is_fail(monkeypatch):
    """hook 放行（exit 0）時 probe 必報 FAIL——probe 對恆綠免疫的自我驗證。"""

    def fake_run(*a, **k):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=fake_run))
    status, detail = mod.probe_pipe_payload("hooks/block-memory-index-write.py")
    assert status == "FAIL"
    assert "實得 0" in detail


def test_pipe_payload_probe_uses_governance_hook_python(monkeypatch):
    """S oracle: verify must exercise the same interpreter rendered to harnesses."""
    seen: list[list[str]] = []

    def fake_run(argv, **kwargs):
        seen.append(argv)
        return SimpleNamespace(returncode=2, stdout="", stderr="")

    monkeypatch.setattr(
        mod, "resolve_hook_python", lambda: "/tmp/uv-python3.12", raising=False
    )
    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=fake_run))
    status, _ = mod.probe_pipe_payload("hooks/block-memory-index-write.py")
    assert status == "PASS"
    assert seen[0][0] == "/tmp/uv-python3.12"


def test_pipe_payload_probe_timeout_is_fail(monkeypatch):
    def fake_run(*a, **k):
        raise subprocess.TimeoutExpired(cmd="hook", timeout=30)

    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(run=fake_run, TimeoutExpired=subprocess.TimeoutExpired),
    )
    assert mod.probe_pipe_payload("hooks/block-memory-index-write.py")[0] == "FAIL"


def test_pipe_payload_probe_resolver_failure_is_guard(monkeypatch):
    """M1: resolver failure maps to GUARD with the actionable message (no raise)."""

    def _boom():
        raise mod.GovernanceError(
            "找不到已安裝的 uv-managed Python 3.12。"
            "先執行 `uv python install 3.12` 後重跑 governance installer。"
        )

    monkeypatch.setattr(mod, "resolve_hook_python", _boom)
    status, detail = mod.probe_pipe_payload("hooks/block-memory-index-write.py")
    assert status == "GUARD"
    assert "uv python install 3.12" in detail


def test_cmd_verify_resolver_failure_is_guard_not_crash(monkeypatch):
    """M1 CLI boundary: all-GUARD probes exit 2 without traceback."""

    def _boom():
        raise mod.GovernanceError(
            "找不到已安裝的 uv-managed Python 3.12。"
            "先執行 `uv python install 3.12` 後重跑 governance installer。"
        )

    monkeypatch.setattr(mod, "resolve_hook_python", _boom)
    manifest = {
        "probes": {
            name: {
                "type": "pipe-payload",
                "script": "hooks/block-memory-index-write.py",
            }
            for name in ("grok", "zcode", "codex")
        }
    }
    assert mod.cmd_verify(manifest, "hooks") == mod.EXIT_GUARD


# ── codex mixed-rep 掃描（codex ⑦——TC-10 P10-2 報告腿）──────────────


def _group(event: str, matcher: str, script: str) -> str:
    return (
        f'[[hooks.{event}]]\nmatcher = "{matcher}"\n\n'
        f'[[hooks.{event}.hooks]]\ntype = "command"\n'
        f'command = "python3 /Users/x/ai-guide/hooks/{script}"\n\n'
    )


def test_mixed_rep_duplicate_inline_group_warns(tmp_path):
    live = _group("PreToolUse", "apply_patch", "codex_memory_path_deny.py") * 2
    warnings = mod.codex_mixed_rep_warnings(live, codex_home=tmp_path)
    assert any("重複 inline group" in w for w in warnings)


def test_mixed_rep_hooks_json_copy_warns(tmp_path):
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "hooks.json").write_text("{}")
    warnings = mod.codex_mixed_rep_warnings(
        _group("Stop", "", "stop-notification.sh"), codex_home=tmp_path
    )
    assert any("hooks.json copy" in w for w in warnings)


def test_mixed_rep_clean_config_no_warnings(tmp_path):
    (tmp_path / ".codex").mkdir()  # 無 hooks.json
    live = _group("PreToolUse", "apply_patch", "codex_memory_path_deny.py")
    assert mod.codex_mixed_rep_warnings(live, codex_home=tmp_path) == []


# ── codex L2 trust 診斷（HANDLER_HEADER MULTILINE 回歸守衛——
#    缺旗標時 handlers 恆 0、診斷整段消失，live verify 首跑實證）────────


def _codex_toml_with_state(state_key: str) -> tuple[str, str]:
    template = _group("PreToolUse", "apply_patch", "codex_memory_path_deny.py")
    live = f'[hooks.state]\n"{state_key}" = "sha256:abc"\n\n' + template
    return live, template


def test_codex_trust_diagnostics_reports_trusted():
    key = f"{mod.Path.home()}/.codex/config.toml:pre_tool_use:0:0"
    live, tmpl = _codex_toml_with_state(key)
    lines = mod.codex_trust_diagnostics(live, tmpl)
    assert len(lines) == 1
    # 完整字串釘住分類方向——"Trusted" 是 "Untrusted" 的子串，substring 斷言
    # 會讓「恆報 Untrusted」變異體存活（post-build audit C1）
    assert "Trusted(state 在場)" in lines[0] and "pre_tool_use:0:0" in lines[0]


def test_codex_trust_diagnostics_reports_untrusted():
    key = "some-other-source:pre_tool_use:0:0"
    live, tmpl = _codex_toml_with_state(key)
    lines = mod.codex_trust_diagnostics(live, tmpl)
    assert len(lines) == 1
    assert "Untrusted" in lines[0]


def test_codex_trust_diagnostics_multi_handler_keys():
    merged = (
        '[[hooks.PreToolUse]]\nmatcher = "Bash"\n\n'
        '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
        'command = "python3 /Users/x/ai-guide/hooks/block-python-c-comment.py"\n\n'
        '[[hooks.PreToolUse.hooks]]\ntype = "command"\n'
        'command = "python3 /Users/x/ai-guide/hooks/block-python-file-write.py"\n\n'
    )
    live = "[hooks.state]\n\n" + merged
    lines = mod.codex_trust_diagnostics(live, merged)
    assert len(lines) == 2
    assert "pre_tool_use:0:0" in lines[0]
    assert "pre_tool_use:0:1" in lines[1]
    assert all("Untrusted" in ln for ln in lines)


def test_probe_codex_cli_absent_guard_with_l1(tmp_path, monkeypatch):
    """launchd PATH 無 codex 場（live 實證）：GUARD 非 crash，L1 仍如實報告。"""
    tmpl = mod.render(
        (mod.MANIFEST_PATH.parent / "registrations/codex.toml").read_text()
    )
    target = tmp_path / "config.toml"
    target.write_text("[hooks.state]\n\n" + tmpl)
    manifest = {
        "registrations": {
            "codex": {"target": str(target), "template": "registrations/codex.toml"}
        }
    }
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda n: None))
    status, _detail, lines = mod.probe_codex(manifest)
    assert status == "GUARD"
    assert any("[L1] 在場" in ln for ln in lines)
    assert any("[L3] GUARD" in ln for ln in lines)


# ── cmd_verify surface 映射與退出碼 ────────────────────────────────


def test_cmd_verify_no_probe_surfaces_exit_ok():
    manifest = {"probes": {}}
    assert mod.cmd_verify(manifest, "rules") == mod.EXIT_OK
    assert mod.cmd_verify(manifest, "skills") == mod.EXIT_OK


def test_cmd_verify_missing_probe_def_is_fail():
    manifest = {"probes": {}}
    assert mod.cmd_verify(manifest, "memory") == mod.EXIT_DRIFT


# ── AIR-221：--surface monitor＝scheduled passive verify（永不 codex exec）──


def _manifest_four_probes() -> dict:
    return {
        "probes": {
            "grok": {
                "type": "pipe-payload",
                "script": "hooks/block-memory-index-write.py",
            },
            "zcode": {
                "type": "pipe-payload",
                "script": "hooks/block-memory-index-write.py",
            },
            "muse": {"type": "muse-inspect", "plugin_id": "x"},
            "codex": {"type": "codex-three-layer"},
        }
    }


def _patch_local_probes_pass(monkeypatch):
    """grok/zcode/muse 本地面代 PASS——codex 腿走真 probe_codex（受測对象）。"""
    real_run_probe = mod.run_probe

    def fake_run_probe(manifest, name, probe, *, passive=False):
        if name == "codex":
            return real_run_probe(manifest, name, probe, passive=passive)
        return "PASS", "local stub", []

    monkeypatch.setattr(mod, "run_probe", fake_run_probe)


def _codex_config_manifest(tmp_path) -> dict:
    tmpl = mod.render(
        (mod.MANIFEST_PATH.parent / "registrations/codex.toml").read_text()
    )
    target = tmp_path / "config.toml"
    target.write_text("[hooks.state]\n\n" + tmpl)
    return {
        "registrations": {
            "codex": {"target": str(target), "template": "registrations/codex.toml"}
        }
    }


def test_monitor_passive_never_calls_host_fixture(tmp_path, monkeypatch, capsys):
    """AC#1（AIR-221）：scheduled monitor 永不 codex exec——host fixture 一呼叫即 fail。"""

    def _boom(*a, **k):
        raise AssertionError("codex_host_level_fixture must not run in monitor mode")

    manifest = {**_manifest_four_probes(), **_codex_config_manifest(tmp_path)}
    monkeypatch.setattr(mod, "codex_host_level_fixture", _boom)
    _patch_local_probes_pass(monkeypatch)
    # CLI 在場仍不得觸發 L3——monitor 模式與 CLI 存在與否完全解耦
    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(run=lambda *a, **k: SimpleNamespace(
            returncode=1, stdout="", stderr="")),
    )
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda n: "/usr/bin/codex"))
    assert mod.cmd_verify(manifest, "monitor") == mod.EXIT_OK
    assert "manual-only" in capsys.readouterr().out


def test_monitor_cli_absent_is_not_guard(tmp_path, monkeypatch):
    """AC#1：monitor 模式 codex CLI 缺席非 GUARD——L1/L2 皆檔面，CLI 只屬手動 L3。"""
    manifest = {**_manifest_four_probes(), **_codex_config_manifest(tmp_path)}
    _patch_local_probes_pass(monkeypatch)
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda n: None))
    assert mod.cmd_verify(manifest, "monitor") == mod.EXIT_OK


def test_monitor_l1_missing_still_fails(tmp_path, monkeypatch):
    """passive 不是放寬：config target 缺席分支照 FAIL（drift 訊號保留）。"""
    manifest = {**_manifest_four_probes(), **_codex_config_manifest(tmp_path)}
    manifest["registrations"]["codex"]["target"] = str(tmp_path / "absent.toml")
    _patch_local_probes_pass(monkeypatch)
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda n: None))
    assert mod.cmd_verify(manifest, "monitor") == mod.EXIT_DRIFT


def test_monitor_l1_group_missing_real_branch(tmp_path, monkeypatch, capsys):
    """AIR-222 真 L1 缺席（≠上行 target 整檔缺席）：config target 在場且合法、
    刻意刪除一個 owned hook group——probe_codex 走 install.py MISSING 分支
    （`[L1] MISSING`＋FAIL），monitor 路徑映 EXIT_DRIFT。"""
    manifest = {**_manifest_four_probes(), **_codex_config_manifest(tmp_path)}
    target = mod.Path(manifest["registrations"]["codex"]["target"])
    text = target.read_text()
    _preamble, units = mod.codex_group_units(text)
    victim = [u for u in units if u["kind"] == "group"][-1]
    target.write_text(text.replace(victim["text"], "", 1), encoding="utf-8")
    _patch_local_probes_pass(monkeypatch)
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda n: None))
    status, detail, lines = mod.probe_codex(manifest, passive=True)
    assert status == "FAIL"
    assert "層一" in detail
    assert any("[L1] MISSING" in ln for ln in lines)
    assert mod.cmd_verify(manifest, "monitor") == mod.EXIT_DRIFT
    assert "[L1] MISSING" in capsys.readouterr().out


def test_monitor_probe_set_sync_guard(monkeypatch):
    """monitor 面消費同一 probe 集合——manifest 失同步 fail-loud（S-3 同款對帳）。"""
    _patch_local_probes_pass(monkeypatch)
    assert mod.cmd_verify({"probes": {}}, "monitor") == mod.EXIT_GUARD


def test_monitor_pass_makes_no_deny_claim(tmp_path, monkeypatch, capsys):
    """AC#2 措辭：scheduled PASS 尾行不得宣稱 host-level deny 已驗——明示手動 acceptance。"""
    manifest = {**_manifest_four_probes(), **_codex_config_manifest(tmp_path)}
    _patch_local_probes_pass(monkeypatch)
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda n: None))
    assert mod.cmd_verify(manifest, "monitor") == mod.EXIT_OK
    out = capsys.readouterr().out
    assert "手動 acceptance" in out
    assert "deny 生效" not in out


def test_all_surface_still_runs_host_fixture(tmp_path, monkeypatch):
    """AC#2：--surface all＝manual full——L3 照跑且 PASS/GUARD/FAIL 傳播退出碼。"""
    manifest = {**_manifest_four_probes(), **_codex_config_manifest(tmp_path)}
    calls: list[int] = []

    def _fake_fixture(*a, **k):
        calls.append(1)
        return "PASS", "stub canary 未變"

    monkeypatch.setattr(mod, "codex_host_level_fixture", _fake_fixture)
    _patch_local_probes_pass(monkeypatch)
    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(run=lambda *a, **k: SimpleNamespace(
            returncode=1, stdout="", stderr="")),
    )
    monkeypatch.setattr(mod, "shutil", SimpleNamespace(which=lambda n: "/usr/bin/codex"))
    assert mod.cmd_verify(manifest, "all") == mod.EXIT_OK
    assert calls == [1]


def test_cmd_verify_fail_dominates_guard(monkeypatch):
    """GUARD 不得吞 FAIL——worst 語義（install.py cmd_verify docstring 契約）釘住。"""
    manifest = {
        "probes": {
            "grok": {"type": "pipe-payload", "script": "x"},
            "zcode": {"type": "pipe-payload", "script": "x"},
            "codex": {"type": "codex-three-layer"},
        }
    }
    monkeypatch.setattr(
        mod, "run_probe", lambda m, n, p, passive=False: next(_seq)
    )
    _seq = iter([("GUARD", "", []), ("PASS", "", []), ("FAIL", "", [])])
    assert mod.cmd_verify(manifest, "hooks") == mod.EXIT_DRIFT
    _seq = iter([("GUARD", "", []), ("PASS", "", []), ("GUARD", "", [])])
    assert mod.cmd_verify(manifest, "hooks") == mod.EXIT_GUARD


# ── AIR-256：L3 canary 釘 model＋stderr 證據＋ENV-BLOCKED 第三態 ─────────
# 根因（本卡診斷）：canary argv 未釘 --model → 落 ~/.codex/config.toml 預設
# native slug（gpt-6-astra）→ ChatGPT 帳號路徑拒（426 Upgrade Required→rc 1）。
# 對照 --model chatgpt-web/high 同 argv rc=0——webgpt 本身健康。


def _patch_l3_runner(monkeypatch, *, returncode, stderr=""):
    """AIR-256：fake subprocess runner 注入——L3 fixture 單元測試永不真跑 codex。"""
    seen: list[list[str]] = []

    def fake_run(argv, **kwargs):
        seen.append(list(argv))
        return SimpleNamespace(returncode=returncode, stdout="", stderr=stderr)

    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(run=fake_run, TimeoutExpired=subprocess.TimeoutExpired),
    )
    monkeypatch.setattr(
        mod, "shutil", SimpleNamespace(which=lambda n: "/usr/bin/codex")
    )
    return seen


def test_l3_canary_pins_sanctioned_transport_model(tmp_path, monkeypatch):
    """AC-1：canary argv 必釘 --model chatgpt-web/high（AIR-221 sanctioned
    transport）——config 預設 native slug 在 ChatGPT 帳號路徑不可用；canary
    測的是治理鏈實際使用的通道，非 config 預設。"""
    seen = _patch_l3_runner(monkeypatch, returncode=0)
    status, _detail = mod.codex_host_level_fixture(codex_home=tmp_path)
    assert status == "PASS"
    argv = seen[0]
    assert argv[argv.index("--model") + 1] == "chatgpt-web/high"


def test_l3_fail_detail_carries_single_line_stderr_tail(tmp_path, monkeypatch):
    """AC-2：rc≠0 FAIL detail 附 stderr 尾段證據（單行化）；無環境簽名命中
    時仍 FAIL——exit-code-only 訊息無從歸因（本卡診斷痛點）。"""
    stderr = "noise line\n" * 90 + "responses_websocket handshake aborted\n"
    _patch_l3_runner(monkeypatch, returncode=1, stderr=stderr)
    status, detail = mod.codex_host_level_fixture(codex_home=tmp_path)
    assert status == "FAIL"
    assert "responses_websocket handshake aborted" in detail
    assert "\n" not in detail  # 單行化：stderr 證據不得把報告行拆開


def test_l3_env_blocked_on_signature_hit(tmp_path, monkeypatch):
    """AC-3：stderr 命中環境面簽名（本卡實證 426 Upgrade Required）→
    ENV-BLOCKED——訊息明寫環境面歸因（非 installer regression）＋證據尾段。"""
    _patch_l3_runner(
        monkeypatch,
        returncode=1,
        stderr="ERROR: responses_websocket: 426 Upgrade Required\n",
    )
    status, detail = mod.codex_host_level_fixture(codex_home=tmp_path)
    assert status == "ENV-BLOCKED"
    assert "環境面" in detail
    assert "非 installer regression" in detail
    assert "Upgrade Required" in detail


def test_l3_env_blocked_signature_match_is_case_insensitive(tmp_path, monkeypatch):
    """簽名比對大小寫不敏感——實證 stderr 大小寫混雜（Usage Limit/Upgrade Required）。"""
    _patch_l3_runner(monkeypatch, returncode=1, stderr="Usage Limit reached on plan")
    status, _detail = mod.codex_host_level_fixture(codex_home=tmp_path)
    assert status == "ENV-BLOCKED"


def test_probe_codex_env_blocked_propagates_with_l3_line(tmp_path, monkeypatch):
    """AC-3：probe 面保 verdict 字串 ENV-BLOCKED（L3 行可見），非吞成 FAIL。"""
    manifest = _codex_config_manifest(tmp_path)

    def _fake_fixture(*a, **k):
        return "ENV-BLOCKED", "環境面——查 relay/auth/network；證據：426"

    monkeypatch.setattr(mod, "codex_host_level_fixture", _fake_fixture)
    monkeypatch.setattr(
        mod, "shutil", SimpleNamespace(which=lambda n: "/usr/bin/codex")
    )
    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(
            run=lambda *a, **k: SimpleNamespace(
                returncode=0, stdout="codex-cli 0.5", stderr=""
            ),
            TimeoutExpired=subprocess.TimeoutExpired,
        ),
    )
    status, _detail, lines = mod.probe_codex(manifest)
    assert status == "ENV-BLOCKED"
    assert any("[L3] ENV-BLOCKED" in ln for ln in lines)


def test_cmd_verify_env_blocked_still_fail_closed(tmp_path, monkeypatch):
    """AC-3：ENV-BLOCKED 是文案分類不是放行——cmd_verify 映 EXIT_DRIFT
    （verify 整體仍 fail-closed exit 1）。"""
    manifest = {**_manifest_four_probes(), **_codex_config_manifest(tmp_path)}

    def _fake_fixture(*a, **k):
        return "ENV-BLOCKED", "環境面——查 relay/auth/network；證據：426"

    monkeypatch.setattr(mod, "codex_host_level_fixture", _fake_fixture)
    _patch_local_probes_pass(monkeypatch)
    monkeypatch.setattr(
        mod, "shutil", SimpleNamespace(which=lambda n: "/usr/bin/codex")
    )
    monkeypatch.setattr(
        mod,
        "subprocess",
        SimpleNamespace(
            run=lambda *a, **k: SimpleNamespace(
                returncode=0, stdout="codex-cli 0.5", stderr=""
            ),
            TimeoutExpired=subprocess.TimeoutExpired,
        ),
    )
    assert mod.cmd_verify(manifest, "hooks") == mod.EXIT_DRIFT
