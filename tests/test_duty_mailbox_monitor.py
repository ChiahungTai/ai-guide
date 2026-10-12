"""dutymail 信箱 monitor hook 測試——退役契約面（AIR-312 R1 M1）。

hook 行為面（holderless pending advisory／baseline state／per-address
容錯／eligibility gate／fail-soft／session 隔離／pending-age 帳：
AIR-294 stall＋AIR-297 episode fencing＋doc-rev CAS）已隨 hook 退役
整段移除——obsolete 行為測試不 skip，直接由 retirement tests 取代。

涵蓋：
- **inert no-op（M1 核心）**：任何事件（UserPromptSubmit／SessionStart/
  其他）×任何地址（`<repo>-marshal` 舊址／repo basename 新址）＝零 face
  呼叫（runner 恆不被呼叫——holder status／receive status 唯讀面也不查）
  、零 baseline／pending-age 寫入、零 stdout/stderr、exit 恆 0。
- **stale session snapshot 邊界**：ZCode session 啟動取得 hook 註冊
  快照——`--prune-stale` 升級前啟動的 session 仍持舊註冊、會以絕對路徑
  繼續呼叫本檔直到 session 結束（subprocess 實跑釘：exit 0、零輸出、
  隔離 state 樹零檔）；新 session snapshot 零 duty 條目不再觸發。
- **結構 pin**：內部 hook flow（core 載入／eligibility gate／baseline
  ／age 帳）全數移除——inert 面零 dutymail／payload 相容層依賴。
- governance 退役契約（AIR-312）：zcode 模板零 monitor／duty-receive
  條目（其他 hooks 不動——compact/sweeper 仍在）；cc dormant 模板
  legacy entry enabled=false（不可默默啟動）；manifest hooks surface
  除名；install merge／prune／check 面（AIR-255 家族）照常驗證。
"""

import io
import json
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest
from conftest import REPO_ROOT, load_module

mod = load_module("hooks/duty_mailbox_monitor.py")
gov = load_module("governance/install.py")


def _payload(event="UserPromptSubmit", session_id="sess-1",
             cwd="/fake/ai-guide/repo"):
    return json.dumps(
        {"hook_event_name": event, "session_id": session_id, "cwd": cwd}
    )


# ── 退役 hook inert no-op（AIR-312 R1 M1）─────────────────────────────


class TestHookInertRetirement:
    """monitor 入口 inert：舊 session snapshot 的殘留呼叫必須零效吸收
    ——零查詢零輸出零寫入，exit 恆 0（不擋 prompt）。"""

    @pytest.mark.parametrize("event", ["UserPromptSubmit", "SessionStart",
                                       "Stop"])
    @pytest.mark.parametrize("address", ["ai-guide-marshal", "ai-guide"])
    def test_main_inert_all_events_all_addresses(
        self, event, address, monkeypatch, capsys,
    ):
        calls = []
        monkeypatch.setattr(sys, "stdin", io.StringIO(_payload(event)))
        assert mod.main(["--address", address], runner=calls.append) == 0
        assert calls == []  # runner 恆零呼叫——唯讀 status 也不查
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_subprocess_entry_zero_output_zero_state(
        self, tmp_path, monkeypatch,
    ):
        """真 entrypoint 實跑（subprocess）：舊註冊呼叫形（--address 舊址
        ＋stdin payload）＋隔離 XDG——exit 0、stdout/stderr 空、state 樹
        零檔（session baseline 與跨 session pending-age 帳都不落）。"""
        xdg = tmp_path / "xdg"
        monkeypatch.setenv("XDG_STATE_HOME", str(xdg))
        proc = subprocess.run(
            [sys.executable,
             str(REPO_ROOT / "hooks" / "duty_mailbox_monitor.py"),
             "--address", "ai-guide-marshal"],
            input=_payload(), capture_output=True, text=True, timeout=60,
        )
        assert proc.returncode == 0
        assert proc.stdout == ""
        assert proc.stderr == ""
        assert not xdg.exists() or list(xdg.rglob("*")) == []

    def test_source_zero_internal_flow(self):
        """結構 pin：內部 hook flow 全數移除——inert 面零 dutymail／
        payload 相容層依賴（殘留 import＝退役面半退役，fail-loud）。"""
        source = (
            REPO_ROOT / "hooks" / "duty_mailbox_monitor.py"
        ).read_text(encoding="utf-8")
        for token in ("importlib", "hook_payload_compat", "holder_status",
                      "receive_status", "monitor_once", "pending_age",
                      "is_eligible"):
            assert token not in source, token

    def test_garbage_stdin_still_inert(self, monkeypatch, capsys):
        """壞 JSON／空 stdin——照樣零輸出 exit 0（no-op 不分诊 payload）。"""
        for raw in ("{not json", "", "   \n"):
            monkeypatch.setattr(sys, "stdin", io.StringIO(raw))
            assert mod.main([], runner=None) == 0
        assert capsys.readouterr().out == ""

# ── governance 退役契約（AIR-312）：monitor 註冊退役——zcode 零條目、
#    cc dormant 停用、manifest 除名；其他 hooks 不動 ────────────────────


def _registration(rel):
    return json.loads((gov.MANIFEST_PATH.parent / rel).read_text())


def _groups(doc, event):
    events = doc.get("events", doc)
    groups = events.get(event, [])
    if isinstance(groups, dict):  # grok 形：單 group 物件
        groups = [groups]
    return groups


def _hook_scripts(group):
    return [
        h.get("args", [h.get("command", "")])[0].rsplit("/", 1)[-1]
        if h.get("args")
        else h.get("command", "")
        for h in group.get("hooks", [])
    ]


def _duty_groups(doc, script):
    out = []
    for groups in doc.get("events", doc).values():
        if isinstance(groups, dict):
            groups = [groups]
        if not isinstance(groups, list):
            continue
        for g in groups:
            if isinstance(g, dict) and script in _hook_scripts(g):
                out.append(g)
    return out


class TestRegistrationRetirement:
    """monitor hook 退役契約（AIR-312）：UserPromptSubmit／SessionStart
    自動提醒註冊退役——現役 zcode 模板零條目（其他 hooks 不動）；cc
    dormant 模板 legacy entry 不可默默啟動（enabled=false）；manifest
    hooks surface 除名（腳本留 repo dormant）。"""

    def test_zcode_template_zero_monitor_groups(self):
        doc = _registration("registrations/zcode.json")
        for event in ("UserPromptSubmit", "SessionStart"):
            hits = [
                g
                for g in _groups(doc, event)
                if "duty_mailbox_monitor.py" in _hook_scripts(g)
            ]
            assert hits == [], event

    def test_zcode_zero_duty_receive_groups(self):
        """duty auto-process 同批退役——zcode 模板零 duty_receive 條目
        （AIR-312；本檔為 monitor 側鏡像 pin）。"""
        doc = _registration("registrations/zcode.json")
        for event in ("UserPromptSubmit", "SessionStart"):
            assert _duty_groups(doc, "duty_receive.py") == [], event

    def test_zcode_other_hooks_untouched(self):
        """其他 hooks 不動：compact-restore-inject（UPS）與
        bridge_ledger_sweeper（UPS＋SS）仍在且 enabled。"""
        doc = _registration("registrations/zcode.json")
        ups = _groups(doc, "UserPromptSubmit")
        ss = _groups(doc, "SessionStart")
        assert _hook_scripts(ups[0]) == ["compact-restore-inject.py"]
        assert _hook_scripts(ups[1]) == ["bridge_ledger_sweeper.py"]
        assert _hook_scripts(ss[0]) == ["bridge_ledger_sweeper.py"]
        assert ups[0]["hooks"][0].get("enabled") is True
        assert len(ups) == 2 and len(ss) == 1

    def test_cc_dormant_duty_entries_disabled(self):
        """cc dormant 模板（AIR-215 歷史資產）：duty legacy entry 保留
        形但 enabled=false——回滾套用模板亦不默默啟動退役自動流程。"""
        doc = _registration("registrations/cc.json")
        monitor = _duty_groups(doc, "duty_mailbox_monitor.py")
        receive = _duty_groups(doc, "duty_receive.py")
        assert len(monitor) == 2 and len(receive) == 2  # 歷史形保留
        for g in (*monitor, *receive):
            assert all(h.get("enabled") is False for h in g["hooks"])

    def test_primary_dead_entry_retired_everywhere(self):
        """ai-guide-primary 死門牌條目退役 pin（AC——rg 零命中的測試面
        鏡像）：zcode/cc registrations 零殘留。"""
        for rel in ("registrations/zcode.json", "registrations/cc.json"):
            raw = (gov.MANIFEST_PATH.parent / rel).read_text(encoding="utf-8")
            assert "ai-guide-primary" not in raw

    def test_manifest_inventory_retired(self):
        manifest = gov.load_manifest()
        scripts = manifest["surfaces"]["hooks"]["scripts"]
        assert "hooks/duty_mailbox_monitor.py" not in scripts
        assert "hooks/scbus-address-pending-reminder.py" not in scripts
        assert "hooks/duty_receive.py" not in scripts  # AIR-312 同批
        assert "hooks/duty_holder_release.py" in scripts  # release 保留

    def test_old_script_name_retired_everywhere(self):
        """舊名全面退役 pin：registrations 零 scbus-address-pending-
        reminder 條目（AC——rg 零命中的測試面鏡像）。"""
        for rel in ("registrations/zcode.json", "registrations/cc.json"):
            raw = (gov.MANIFEST_PATH.parent / rel).read_text(encoding="utf-8")
            assert "scbus-address-pending-reminder" not in raw


class TestInstallMergeFace:
    def _template(self):
        raw = (gov.MANIFEST_PATH.parent / "registrations/zcode.json").read_text()
        # render_uninstall：展開 REPO（identity 靠真實 hooks 路徑），HOOK_PYTHON 保留
        return json.loads(gov.render_uninstall(raw))

    def _live(self):
        """模擬 live config root——既有形態取自模板既有 group（byte 等值隔離
        「內容更新」語義）；scbus canonical 條目照 live config 實際形（純
        command 字串、SS 帶 async）。"""
        tmpl = self._template()
        compact_ups = [
            g
            for g in tmpl["events"]["UserPromptSubmit"]
            if "compact-restore-inject.py" in gov._group_scripts(g)
        ]
        return {
            "hooks": {
                "enabled": True,
                "events": {
                    "UserPromptSubmit": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "scbus hook --harness zcode --event user-prompt-submit",
                                }
                            ]
                        },
                        *compact_ups,
                    ],
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "scbus hook --harness zcode --event session-start",
                                    "async": True,
                                }
                            ]
                        }
                    ],
                },
            }
        }

    def test_merge_appends_new_groups_keeps_existing(self):
        live = self._live()
        tmpl = self._template()
        new_root, changed = gov.merge_json_hooks(
            live, tmpl, "hooks", remove=False
        )
        assert changed
        ups = new_root["hooks"]["events"]["UserPromptSubmit"]
        ss = new_root["hooks"]["events"]["SessionStart"]
        live_ups = live["hooks"]["events"]["UserPromptSubmit"]
        live_ss = live["hooks"]["events"]["SessionStart"]
        assert ups[0] == live_ups[0]
        assert ups[1] == live_ups[1]
        # AIR-312 退役後模板貢獻＝compact＋sweeper（UPS）／sweeper（SS）
        assert len(ups) == 3  # scbus＋compact＋sweeper（duty-receive／monitor 已退役）
        assert len(ss) == 2  # scbus＋sweeper
        assert ss[0] == live_ss[0]  # scbus async 條目零動
        assert gov._group_scripts(ups[2]) == frozenset({"bridge_ledger_sweeper.py"})
        assert gov._group_scripts(ss[1]) == frozenset({"bridge_ledger_sweeper.py"})

    def test_merge_idempotent(self):
        live = self._live()
        tmpl = self._template()
        once, _changed = gov.merge_json_hooks(live, tmpl, "hooks", remove=False)
        _again, changed = gov.merge_json_hooks(once, tmpl, "hooks", remove=False)
        assert not changed

    def test_uninstall_removes_only_package_groups(self):
        live = self._live()
        tmpl = self._template()
        merged, _changed = gov.merge_json_hooks(live, tmpl, "hooks", remove=False)
        back, changed = gov.merge_json_hooks(merged, tmpl, "hooks", remove=True)
        assert changed
        events = back["hooks"]["events"]
        assert len(events["UserPromptSubmit"]) == 1
        assert gov._group_scripts(events["UserPromptSubmit"][0]) == frozenset()
        assert events["SessionStart"] == live["hooks"]["events"]["SessionStart"]
        assert gov._group_scripts(events["SessionStart"][0]) == frozenset()

    def test_identity_no_collapse_with_canonical_or_compact(self):
        """退役 pin（AIR-312）：模板雙事件零 monitor group——identity
        no-collapse 檢查的前提（本套件 group 在場）已隨註冊退役消失。"""
        tmpl = self._template()
        for event in ("UserPromptSubmit", "SessionStart"):
            ours = [
                g
                for g in tmpl["events"][event]
                if "duty_mailbox_monitor.py" in gov._group_scripts(g)
            ]
            assert ours == [], event


# ── AIR-255 A：installer prune（ownership-aware）＋removal receipt ────


def _prune_fixture(monkeypatch, tmp_path):
    """zcode render fixture：canonical/REPO_ROOT 錨到 tmp repo（fence 可控）。

    回 (repo, tmpl)——tmpl＝render 後模板 subtree（{enabled, events}，路徑
    全落 tmp repo hooks/）。"""
    repo = tmp_path / "checkout"
    (repo / "hooks").mkdir(parents=True)
    monkeypatch.setattr(gov, "REPO_ROOT", repo)
    monkeypatch.setattr(gov, "_CANONICAL_CACHE", {str(repo): repo})
    monkeypatch.setattr(gov, "_HOOK_PATTERN_CACHE", {})
    monkeypatch.setattr(gov, "_HOOK_PYTHON_CACHE", str(repo / "python3.12"))
    raw = (gov.MANIFEST_PATH.parent / "registrations/zcode.json").read_text()
    return repo, json.loads(gov.render(raw))


def _repo_group(repo, name, on_disk=False, command=None):
    """受管形 group（installer render 形：command＝interpreter、args＝
    repo hooks 絕對路徑）；on_disk=True 同步在 tmp repo 落 script 檔。"""
    if on_disk:
        (repo / "hooks" / name).write_text("# script\n")
    return {
        "hooks": [
            {
                "type": "process",
                "command": command or str(repo / "python3.12"),
                "args": [f"{repo}/hooks/{name}"],
                "timeoutMs": 10000,
            }
        ]
    }


def _foreign_group(tmp_path, name="foreign.py"):
    other = tmp_path / "other-checkout" / "hooks"
    return {
        "hooks": [
            {
                "type": "process",
                "command": "/usr/bin/python3",
                "args": [f"{other}/{name}"],
                "timeoutMs": 10000,
            }
        ]
    }


def _live_with_stale(repo, tmp_path, tmpl, extras):
    """live config root：模板 group 全在場＋extras 插 UserPromptSubmit 前端。"""
    live = json.loads(json.dumps(tmpl))
    live["events"]["UserPromptSubmit"] = [
        *extras,
        *live["events"]["UserPromptSubmit"],
    ]
    return {"hooks": live}


def _script_names(events_doc):
    names = set()
    for groups in events_doc.values():
        for g in groups:
            names |= gov._group_scripts(g)
    return names


class TestReconcilePlan:
    def test_remove_judgement_four_cases(self, tmp_path, monkeypatch):
        """remove 判準四案例：managed+absent→刪／managed+present（rename
        殘留）→刪（無視 script 存在性）／外部路徑→warn 不刪／模板內→留。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live = json.loads(json.dumps(tmpl))
        live["events"]["UserPromptSubmit"] = [
            _repo_group(repo, "scbus-address-pending-reminder.py"),  # 已刪檔
            _repo_group(repo, "old-name-residue.py", on_disk=True),  # rename 殘留
            _foreign_group(tmp_path),  # 外部路徑
            *live["events"]["UserPromptSubmit"],
        ]
        plan = gov._hooks_reconcile_plan(live, tmpl, repo / "hooks")
        removed = {
            p.rsplit("/", 1)[-1] for e in plan["remove"] for p in e["scripts"]
        }
        assert removed == {
            "scbus-address-pending-reminder.py",
            "old-name-residue.py",
        }
        warned = {
            p.rsplit("/", 1)[-1]
            for e in plan["orphan_warn"]
            for p in e["scripts"]
        }
        assert warned == {"foreign.py"}
        assert plan["add"] == []  # 模板 group 全在場
        assert plan["update"] == []

    def test_pure_command_user_group_ignored(self, tmp_path, monkeypatch):
        """純 command 用戶 group（scbus 形，無 script 路徑引用）＝零動作
        零警示——用戶 group 保留。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live = json.loads(json.dumps(tmpl))
        live["events"]["UserPromptSubmit"] = [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "scbus hook --harness zcode"
                        " --event user-prompt-submit",
                    }
                ]
            },
            *live["events"]["UserPromptSubmit"],
        ]
        plan = gov._hooks_reconcile_plan(live, tmpl, repo / "hooks")
        assert plan["remove"] == []
        assert plan["orphan_warn"] == []

    def test_plan_detects_add_and_update(self, tmp_path, monkeypatch):
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live = json.loads(json.dumps(tmpl))
        live["events"]["UserPromptSubmit"].pop()  # 少一條模板 group → add
        live["events"]["SessionStart"][0]["hooks"][0]["timeoutMs"] = 99999
        plan = gov._hooks_reconcile_plan(live, tmpl, repo / "hooks")
        assert {e["event"] for e in plan["add"]} == {"UserPromptSubmit"}
        assert {e["event"] for e in plan["update"]} == {"SessionStart"}
        assert plan["remove"] == []


class TestPruneMergeFace:
    def test_no_flag_zero_removal(self, tmp_path, monkeypatch):
        """不帶 prune flag 的 merge＝零移除（行為完全不變）。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        new_root, _changed = gov.merge_json_hooks(
            live_root, tmpl, "hooks", remove=False
        )
        assert "scbus-address-pending-reminder.py" in _script_names(
            new_root["hooks"]["events"]
        )

    def test_prune_stale_removes_exactly_plan_remove(
        self, tmp_path, monkeypatch
    ):
        """plan 單源：merge（prune_stale）移除集＝plan["remove"]；dry-run
        預覽與 apply 同一份計算。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        extras = [
            _repo_group(repo, "scbus-address-pending-reminder.py"),
            _repo_group(repo, "old-name-residue.py", on_disk=True),
            _foreign_group(tmp_path),
        ]
        live_root = _live_with_stale(repo, tmp_path, tmpl, extras)
        live_sub = live_root["hooks"]
        plan = gov._hooks_reconcile_plan(live_sub, tmpl, repo / "hooks")
        new_root, changed = gov.merge_json_hooks(
            live_root, tmpl, "hooks", remove=False, prune_stale=True,
            repo_hooks_dir=repo / "hooks",
        )
        assert changed
        names = _script_names(new_root["hooks"]["events"])
        for e in plan["remove"]:
            for p in e["scripts"]:
                assert p.rsplit("/", 1)[-1] not in names
        # 外部路徑 group 保留（orphan_warn 只列不刪；_group_scripts 只認本
        # repo 路徑——以 args 原文判定在場）
        assert any(
            "foreign.py" in str(h.get("args", []))
            for groups in new_root["hooks"]["events"].values()
            for g in groups
            for h in g.get("hooks", [])
        )

    def test_prune_stale_idempotent(self, tmp_path, monkeypatch):
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        once, _c1 = gov.merge_json_hooks(
            live_root, tmpl, "hooks", remove=False, prune_stale=True,
            repo_hooks_dir=repo / "hooks",
        )
        _twice, c2 = gov.merge_json_hooks(
            once, tmpl, "hooks", remove=False, prune_stale=True,
            repo_hooks_dir=repo / "hooks",
        )
        assert not c2


class TestPruneApplyFace:
    def _apply_target(self, cfg, prune=True):
        t = {
            "kind": "json-subtree:zcode",
            "target": str(cfg),
            "template": "registrations/zcode.json",
            "merge_root": "hooks",
            "action": "merge",
        }
        if prune:
            t["prune_stale"] = True
        return gov._apply_target({}, t, "install")

    def test_receipt_and_backup_on_removal(
        self, tmp_path, monkeypatch, capsys
    ):
        """apply：先 backup 再移除；逐條 removed 行＋restart receipt 文案
        （禁宣稱 N 個 running session）。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        assert self._apply_target(cfg) == "written"
        out = capsys.readouterr().out
        assert (
            "removed: UserPromptSubmit/{scbus-address-pending-reminder.py}"
            in out
        )
        assert "已移除 1 條 hook 引用" in out
        assert "既有 ZCode sessions 可能仍持 startup snapshot" in out
        assert "重開 session" in out and "每 prompt 可能報錯" in out
        assert "running session" not in out  # 禁程序枚舉宣稱
        assert list(cfg.parent.glob("config.json.bak-*-gov"))  # backup 在場
        doc = json.loads(cfg.read_text())
        assert "scbus-address-pending-reminder.py" not in _script_names(
            doc["hooks"]["events"]
        )

    def test_no_receipt_when_no_stale(self, tmp_path, monkeypatch, capsys):
        _repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps({"hooks": tmpl}, indent=2) + "\n")
        assert self._apply_target(cfg, prune=False) == "noop"
        assert self._apply_target(cfg) == "noop"
        assert "已移除" not in capsys.readouterr().out

    def test_dry_run_preview_lists_plan(self, tmp_path, monkeypatch, capsys):
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [
                _repo_group(repo, "scbus-address-pending-reminder.py"),
                _foreign_group(tmp_path),
            ],
        )
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        manifest = {
            "registrations": {
                "zcode": {
                    "target": str(cfg),
                    "template": "registrations/zcode.json",
                    "merge_root": "hooks",
                }
            }
        }
        gov._print_prune_preview(manifest)
        out = capsys.readouterr().out
        assert "remove" in out
        assert "scbus-address-pending-reminder.py" in out
        assert "foreign.py" in out  # orphan_warn 只列不刪


class TestPrunePlanBuild:
    def test_prune_flag_scopes_to_json_subtree(self):
        manifest = gov.load_manifest()
        plan = gov.build_plan(manifest, "hooks", "install", prune_stale=True)
        zc = [
            t for t in plan["targets"]
            if t["kind"] == "json-subtree:zcode"
        ]
        assert zc and zc[0].get("prune_stale") is True
        assert all(
            not t.get("prune_stale")
            for t in plan["targets"]
            if t["kind"] != "json-subtree:zcode"
        )

    def test_default_build_plan_no_prune(self):
        manifest = gov.load_manifest()
        plan = gov.build_plan(manifest, "hooks", "install")
        assert all(not t.get("prune_stale") for t in plan["targets"])


class TestPruneCliFace:
    def test_prune_stale_check_rejected(self, monkeypatch, capsys):
        monkeypatch.setattr(
            sys, "argv",
            ["install.py", "--surface", "hooks", "--prune-stale", "--check"],
        )
        assert gov.main() == gov.EXIT_GUARD
        assert "prune-stale" in capsys.readouterr().err

    def test_prune_stale_uninstall_rejected(self, monkeypatch, capsys):
        monkeypatch.setattr(
            sys, "argv",
            ["install.py", "--surface", "hooks", "--prune-stale",
             "--uninstall"],
        )
        assert gov.main() == gov.EXIT_GUARD

    def test_prune_stale_dry_run_preview_via_cli(
        self, tmp_path, monkeypatch, capsys
    ):
        """"--prune-stale --dry-run＝只印 plan（預覽與 apply 同源）＋
        --zcode-config 注入面只改讀寫目標。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        cfg = tmp_path / "config-fixture.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        monkeypatch.setattr(
            sys, "argv",
            ["install.py", "--surface", "hooks", "--prune-stale",
             "--dry-run", "--zcode-config", str(cfg)],
        )
        assert gov.main() == gov.EXIT_OK
        out = capsys.readouterr().out
        assert "scbus-address-pending-reminder.py" in out
        assert "remove" in out


# ── AIR-255 修復輪 F-1：--zcode-config 旁路面收斂（僅演練 zcode 面）──


def _drill_manifest(tmp_path, repo, cfg):
    """F-1 演練測試 fake manifest：全部面寫入目標導到 tmp fake target
    （零寫入斷言＝這些路徑最終不存在）。"""
    grok_cfg = tmp_path / "grok-fake-target.json"
    codex_cfg = tmp_path / "codex-fake-target.toml"
    skills_link = tmp_path / "fake-skills-link"
    manifest = {
        "registrations": {
            "grok": {
                "merge": "file",
                "target": str(grok_cfg),
                "template": "registrations/grok.json",
            },
            "zcode": {
                "target": str(cfg),
                "template": "registrations/zcode.json",
                "merge_root": "hooks",
            },
            "codex": {
                "target": str(codex_cfg),
                "template": "registrations/codex.toml",
            },
        },
        "surfaces": {
            "skills": {
                "symlinks": [
                    {"link": str(skills_link), "target": str(repo / "skills")}
                ]
            },
            "rules": {"argv": ["wrap-rules"]},
            "agents": {"argv": ["wrap-agents"]},
            "memory": {"plugin_path": "p", "plugin_id": "x", "pool_setup": "s"},
        },
    }
    return manifest, grok_cfg, codex_cfg, skills_link


class TestZcodeConfigDrillScoping:
    """F-1（修復輪）：--zcode-config 在場（install/dry-run）＝僅演練 zcode 面
    ——其他面 skip＋一行註記＋fake target 零寫入；uninstall 行為不變（旗標
    只覆寫 zcode 面 target，不過濾面）。缺席→全面照跑＝既有測試群
    （test_governance_fail_independence 等）。"""

    @staticmethod
    def _recorders(monkeypatch):
        """wrap／memory 面執行記錄器（演練時不得被呼叫）。"""
        wraps: list[str] = []
        monkeypatch.setattr(
            gov, "run_wrap",
            lambda argv, extra=None: wraps.append(argv[0]) or 0,
        )
        muses: list[int] = []
        monkeypatch.setattr(gov, "_require_muse_cli", lambda: muses.append(1))
        monkeypatch.setattr(
            gov, "subprocess",
            SimpleNamespace(run=lambda *a, **k: SimpleNamespace(
                returncode=0, stdout="", stderr=""
            )),
        )
        return wraps, muses

    @staticmethod
    def _stale_cfg(monkeypatch, tmp_path):
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        cfg = tmp_path / "config-fixture.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        monkeypatch.setattr(gov, "JOURNAL_DIR", tmp_path / "journal")
        # 同檔在前的 CLI dry-run 測試經 main()→set_dry_run() 污染模組全域
        # _DRY_RUN（一次性 latch）——install/uninstall 演練要真寫 fixture，釘回 False。
        monkeypatch.setattr(gov, "_DRY_RUN", False)
        return repo, cfg

    def test_drill_install_only_zcode_face(
        self, tmp_path, monkeypatch, capsys
    ):
        """surface=all＋flag＋install：僅 zcode 面 apply（其他面 fake target
        零寫入、wrap/memory 面零執行）＋skip 一行註記（跳過 6 面）。"""
        repo, cfg = self._stale_cfg(monkeypatch, tmp_path)
        manifest, grok_cfg, codex_cfg, skills_link = _drill_manifest(
            tmp_path, repo, cfg
        )
        wraps, muses = self._recorders(monkeypatch)
        rc = gov.cmd_install_uninstall(
            manifest, "all", "install", prune_stale=True, zcode_override=True,
        )
        assert rc == gov.EXIT_OK
        out = capsys.readouterr().out
        assert "僅演練 zcode 面" in out and "跳過 6 面" in out
        assert "json-subtree:zcode" in out  # zcode 面 apply
        assert "render-file" not in out and "toml-groups" not in out
        assert "手動步驟" not in out  # 演練不印其他面的手動步驟
        assert wraps == [] and muses == []
        # zcode 面真寫入（fixture）：stale 已 prune＋receipt 在場
        assert "已移除 1 條 hook 引用" in out
        doc = json.loads(cfg.read_text())
        assert "scbus-address-pending-reminder.py" not in _script_names(
            doc["hooks"]["events"]
        )
        # 其他面 fake target 零寫入
        assert not grok_cfg.exists()
        assert not codex_cfg.exists()
        assert not skills_link.exists()

    def test_drill_install_non_hooks_surface_zero_apply(
        self, tmp_path, monkeypatch, capsys
    ):
        """surface 非 hooks/all：zcode 面不在 scope——零 apply、cfg 零寫入
        （skills 面 skip：link 不建立）。"""
        repo, cfg = self._stale_cfg(monkeypatch, tmp_path)
        before = cfg.read_text()
        manifest, _grok, _codex, skills_link = _drill_manifest(
            tmp_path, repo, cfg
        )
        wraps, muses = self._recorders(monkeypatch)
        rc = gov.cmd_install_uninstall(
            manifest, "skills", "install", zcode_override=True,
        )
        assert rc == gov.EXIT_OK
        out = capsys.readouterr().out
        assert "僅演練 zcode 面" in out and "跳過 1 面" in out
        assert "json-subtree:zcode" not in out
        assert wraps == [] and muses == []
        assert cfg.read_text() == before
        assert not skills_link.exists()

    def test_drill_dry_run_zcode_only_preview(
        self, tmp_path, monkeypatch, capsys
    ):
        """dry-run＋flag：預覽同過濾（僅 zcode 面 plan；wrap 面零執行）
        ＋prune 預覽在場。"""
        repo, cfg = self._stale_cfg(monkeypatch, tmp_path)
        manifest, _grok, _codex, _link = _drill_manifest(tmp_path, repo, cfg)
        wraps, _muses = self._recorders(monkeypatch)
        rc = gov.cmd_install_uninstall(
            manifest, "all", "dry-run", prune_stale=True,
            zcode_override=True,
        )
        assert rc == gov.EXIT_OK
        out = capsys.readouterr().out
        assert "僅演練 zcode 面" in out and "跳過 6 面" in out
        assert "json-subtree:zcode" in out
        assert "render-file" not in out and "toml-groups" not in out
        assert "symlink" not in out
        assert wraps == []  # wrap --dry-run 不跑
        assert "scbus-address-pending-reminder.py" in out  # prune 預覽
        assert "remove" in out

    def test_uninstall_with_flag_not_filtered(
        self, tmp_path, monkeypatch, capsys
    ):
        """uninstall 行為不變：flag 在場仍全面 uninstall（grok/codex 缺席
        target 走 not-present leave、zcode 面 target＝fixture 照拆模板
        group）——無演練過濾、無 skip 註記。"""
        repo, cfg = self._stale_cfg(monkeypatch, tmp_path)
        manifest, _grok, _codex, _link = _drill_manifest(tmp_path, repo, cfg)
        monkeypatch.setattr(gov, "JOURNAL_DIR", tmp_path / "journal")
        rc = gov.cmd_install_uninstall(
            manifest, "hooks", "uninstall", zcode_override=True,
        )
        assert rc == gov.EXIT_OK
        out = capsys.readouterr().out
        assert "僅演練 zcode 面" not in out
        # 全面 uninstall：grok/codex（缺席）＋zcode（在場）三面都執行
        assert "render-file" in out and "toml-groups" in out
        assert "not-present（leave）" in out and "written" in out
        doc = json.loads(cfg.read_text())
        names = _script_names(doc["hooks"]["events"])
        assert "zcode_agent_background_gate.py" not in names  # 模板 group 已拆
        assert "scbus-address-pending-reminder.py" in names  # uninstall 不 prune


class TestPruneCheckFace:
    def test_check_reports_stale_managed_with_prune_hint(
        self, tmp_path, monkeypatch
    ):
        """--check 對 stale 受管殘留報 drift＋--prune-stale 修法提示。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [_repo_group(repo, "scbus-address-pending-reminder.py")],
        )
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        m = {
            "registrations": {
                "zcode": {
                    "target": str(cfg),
                    "template": "registrations/zcode.json",
                    "merge_root": "hooks",
                    "target_is_symlink": False,
                }
            }
        }
        drifts: list = []
        gov.check_json_face(m, "zcode", drifts)
        hits = [msg for _, msg in drifts if "prune-stale" in msg]
        assert hits
        assert "scbus-address-pending-reminder.py" in hits[0]

    def test_check_pure_command_group_no_new_drift(
        self, tmp_path, monkeypatch
    ):
        """純 command 用戶 group（無套件腳本）→ check 零新增 drift
        （既有行為保留）。"""
        repo, tmpl = _prune_fixture(monkeypatch, tmp_path)
        live_root = _live_with_stale(
            repo, tmp_path, tmpl,
            [{
                "hooks": [{
                    "type": "command",
                    "command": "scbus hook --harness zcode",
                }]
            }],
        )
        cfg = tmp_path / "config.json"
        cfg.write_text(json.dumps(live_root, indent=2) + "\n")
        m = {
            "registrations": {
                "zcode": {
                    "target": str(cfg),
                    "template": "registrations/zcode.json",
                    "merge_root": "hooks",
                    "target_is_symlink": False,
                }
            }
        }
        drifts: list = []
        gov.check_json_face(m, "zcode", drifts)
        assert drifts == []


class TestBackupRetention:
    def test_backup_keep_n_rotation(self, tmp_path):
        """備份保留 pin：自家後綴只留最近 BAK_KEEP 份（1201 教訓——mtime
        排序）。AIR-255 ⑤核對＝已有 keep-N，此測試釘住不退化。

        同秒同 pid 的 backup 檔名相同（互覆）——以預置檔＋distinct mtime
        模擬跨 run 累積，再觸發一次 backup_target 驗證 prune。"""
        f = tmp_path / "cfg.json"
        f.write_text("v0")
        oldest = tmp_path / "cfg.json.bak-20260101-000000-111-gov"
        oldest.write_text("oldest")
        os.utime(oldest, (1_000_000, 1_000_000))
        for i in range(gov.BAK_KEEP - 1):
            bak = tmp_path / f"cfg.json.bak-2026010{i + 2}-000000-111-gov"
            bak.write_text(f"recent{i}")
            os.utime(bak, (2_000_000 + i, 2_000_000 + i))
        f.write_text("v-new")
        gov.backup_target(f)  # 新備份 mtime＝now——最新
        baks = list(tmp_path.glob("cfg.json.bak-*-gov"))
        assert len(baks) == gov.BAK_KEEP
        assert not oldest.exists()  # mtime 最舊者被 prune


