"""duty receive adapter 測試（AIR-254.3 S1+S2）。

涵蓋（工單 AC1 全項）：
- ensure_holder 三分流：fresh bind（status→bind CAS）/ renew / rebind-on-fencing
  （renew class-5 → status→rebind）；rebind CAS 失敗（epoch-conflict）→
  HolderConflict（surface、單次嘗試不轟炸）。
- triage default-deny：未知 class／solicit intent／壞 body（非 JSON、非
  object、缺 class 鍵）→ surface；auto 需 class+intent+機械驗證全過；
  receipt 需 in_reply_to 或 body idempotency 鍵（task/card）。
- flush-ack 防護（EP invariant 4）：triage 中途 raise → ack 不被呼叫；
  ack 只在全批處置後（advance-after-emit——commit 由呼叫端在輸出後執行）。
- invalidate 路徑：遺留未 ack 批次（state 記錄）——已處置→先試 ack；
  未處置→prepare --invalidate 重 prepare（寧重不漏）。
- digest 輸出形（N/M/K＋最舊 X 分鐘＋class 計數）；surface 全文前 3 筆、
  超出者一行摘要；無新信零輸出。
- hook 面：stdin payload 驅動 run()——eligibility gate（cwd repo 外＝
  零查詢零輸出）、store 缺席（class 4 storage）fail-soft＝零 stdout
  exit 0＋stderr 註記、stdin 壞 JSON/未知事件靜默、config 壞形 fail-loud
  exit 3、args 誤用 exit 2。
- policy 載入 governance/dutymail-processor.toml（default-deny 表；未知
  鍵／壞形 fail-loud）；代碼層底線：solicit 恆 surface、未列 class 恆
  surface（config 無法放寪）。
- governance 接線：zcode/cc 註冊雙事件各一條＋manifest scripts 登記。

測試全走 injectable runner（fake dutymail 回固定 JSON）＋fake state 路徑
（tmp_path）——不碰真 store（真 store 往返＝S3，marshal 職責）。
"""

import io
import json
import os
import stat
import sys

import pytest
from conftest import REPO_ROOT, load_module

mod = load_module("scripts/duty_receive.py")
hook = load_module("hooks/duty_receive.py")

ADDR = "ai-guide-marshal"
REPO = "/fake/ai-guide/repo"
REAL_CONFIG = str(REPO_ROOT / "governance" / "dutymail-processor.toml")


def _stdin(event="UserPromptSubmit", cwd=REPO, session_id="sess-1"):
    return json.dumps(
        {"hook_event_name": event, "session_id": session_id, "cwd": cwd}
    )


UPS_STDIN = _stdin()
SS_STDIN = _stdin(event="SessionStart")

NOW_US = 10_000_000_000  # 固定 now——age 斷言用


# ── fake dutymail（typed contract：成功 stdout 一個 JSON；失敗 raise）──


def _ok(result):
    return json.dumps({"schemaVersion": 1, "ok": True, "result": result})


def _err(code, error_class, exit_code=3, message="typed failure"):
    return mod.DutymailFaceError(
        code=code, error_class=error_class, message=message,
        retryable=False, exit_code=exit_code,
    )


def _hook_err(code, error_class, exit_code=3, message="typed failure"):
    """hook 面錯誤——用 hook.core 的類別實例（conftest 載入的 mod 與
    hook import 的 core 是同檔案不同 instance，except 面看後者）。"""
    return hook.core.DutymailFaceError(
        code=code, error_class=error_class, message=message,
        retryable=False, exit_code=exit_code,
    )


def _seq_runner(steps):
    """injectable runner：steps 依呼叫序（str stdout 或 Exception）。

    超出步數＝AssertionError（釘「單次嘗試、不重試轟炸」）。
    """
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


def _status_doc(epoch=4, live=False):
    return _ok({
        "addressId": "a1", "alias": ADDR, "bindingEpoch": epoch,
        "leaseExpiresAtUs": 0, "live": live,
    })


def _bind_doc(epoch=5, token="tok-fresh"):
    return _ok({
        "addressId": "a1", "alias": ADDR, "bindingEpoch": epoch,
        "holderToken": token, "leaseExpiresAtUs": 99,
    })


def _renew_doc(epoch=5):
    return _ok({
        "addressId": "a1", "alias": ADDR, "bindingEpoch": epoch,
        "leaseExpiresAtUs": 199,
    })


def _prepare_doc(envs, batch_token="bt-1"):
    if not envs:
        return _ok({
            "addressId": "a1", "batchToken": None, "fromSeq": None,
            "throughSeq": None, "envelopes": [], "expiresAtUs": None,
        })
    return _ok({
        "addressId": "a1", "batchToken": batch_token,
        "fromSeq": 1, "throughSeq": len(envs),
        "envelopes": envs, "expiresAtUs": NOW_US + 60_000_000,
    })


def _ack_doc(replayed=False):
    return _ok({
        "addressId": "a1", "receiptId": "r-1", "fromSeq": 1,
        "throughSeq": 2, "ackedAtUs": NOW_US, "replayed": replayed,
    })


def _env_item(
    eid, klass="usage-liveness", intent="inform", body=None,
    in_reply_to=None, created_us=None, canonical=None,
):
    """合成 prepare envelopes 元素（canonicalEnvelope＝canonical JSON 字串）。

    body=None 以 class 生成預設 machine-headers；canonical 直供壞信案例。
    """
    if created_us is None:
        created_us = NOW_US - 60_000_000  # 1 分鐘前
    if body is None and canonical is None:
        body = {"class": klass, "task": "T-1", "reply_address": "x-marshal"}
    env = {
        "schema_version": 2,
        "message_id": "m-" + eid,
        "envelope_id": eid,
        "from": {"session_id": "s-" + eid, "name": None, "harness": "zcode"},
        "to": {"address": ADDR},
        "delivery": {
            "mode": "queue", "fallback": "queue", "intent": intent,
            "wake": "none", "fallback_used": False,
        },
        "created_at_us": created_us,
        "body": json.dumps(body, ensure_ascii=False) if body is not None else "not-json{",
    }
    if in_reply_to is not None:
        env["in_reply_to"] = in_reply_to
    text = canonical if canonical is not None else json.dumps(env, ensure_ascii=False)
    return {"envelopeId": eid, "acceptanceSeq": 1, "canonicalEnvelope": text}


def _seed_state(path, token="tok-old", epoch=4, batch_token=None,
                disposed=False, address=ADDR):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc = {
        "address": address, "epoch": epoch, "token": token,
        "bound_at_iso": "2026-10-05T00:00:00+00:00",
    }
    if batch_token is not None:
        doc["batch_token"] = batch_token
        doc["batch_disposed"] = disposed
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)


def _read_state(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _policy():
    return mod.load_policy(REAL_CONFIG)


def _hook_run(raw, runner, state_dir, config_path=REAL_CONFIG, **kw):
    return hook.run(
        raw, ADDR, runner=runner, state_dir=str(state_dir),
        config_path=config_path, **kw
    )


@pytest.fixture
def state_file(tmp_path):
    return str(tmp_path / "state" / "sess-1.json")


# ── binary 解析順序（DUTYMAIL_BIN → PATH → plugin cache 最新版）────────


class TestBinaryResolution:
    def test_env_var_wins(self, monkeypatch):
        monkeypatch.setenv("DUTYMAIL_BIN", "/opt/dutymail")
        assert mod._resolve_binary() == "/opt/dutymail"

    def test_path_lookup_second(self, monkeypatch):
        monkeypatch.delenv("DUTYMAIL_BIN", raising=False)
        monkeypatch.setattr(mod.shutil, "which", lambda name: "/usr/bin/dutymail")
        assert mod._resolve_binary() == "/usr/bin/dutymail"

    def test_plugin_cache_picks_newest_version(self, monkeypatch):
        monkeypatch.delenv("DUTYMAIL_BIN", raising=False)
        monkeypatch.setattr(mod.shutil, "which", lambda name: None)
        base = "/fake/plugins/delegate-market/delegate"
        monkeypatch.setattr(mod.glob, "glob", lambda pattern: [
            base + "/2.12.0/bin/aarch64-apple-darwin/dutymail",
            base + "/3.1.0/bin/aarch64-apple-darwin/dutymail",
            base + "/10.0.0/bin/aarch64-apple-darwin/dutymail",
            base + "/3.0.9/bin/aarch64-apple-darwin/dutymail",
        ])
        monkeypatch.setattr(mod.os.path, "expanduser", lambda p: "/fake")
        got = mod._resolve_binary()
        assert got.endswith("/10.0.0/bin/aarch64-apple-darwin/dutymail")
        assert "/3.1.0/" not in got  # 禁手 pin 版化路徑——數值版本排序

    def test_none_found_raises(self, monkeypatch):
        monkeypatch.delenv("DUTYMAIL_BIN", raising=False)
        monkeypatch.setattr(mod.shutil, "which", lambda name: None)
        monkeypatch.setattr(mod.glob, "glob", lambda pattern: [])
        with pytest.raises(RuntimeError, match="dutymail binary not found"):
            mod._resolve_binary()


# ── policy：config 表載入＋default-deny 底線───────────────────────────


class TestPolicy:
    def test_real_config_initial_table(self):
        policy = _policy()
        assert policy.allows("usage-liveness", "inform")
        assert policy.allows("terminal-completion", "inform")
        assert policy.allows("receipt", "receipt")
        assert not policy.allows("handoff", "inform")
        assert not policy.allows("patrol", "inform")
        assert not policy.allows("work-order", "inform")

    def test_unlisted_class_always_surface(self):
        """代碼層底線：未列 class 恆 surface——config 加列也擋不住 solicit。"""
        policy = _policy()
        assert not policy.allows("unknown-class-x", "inform")
        assert not policy.allows("usage-liveness", "solicit")  # solicit 恆 surface

    def test_missing_config_fail_loud(self, tmp_path):
        with pytest.raises(mod.ConfigError):
            mod.load_policy(str(tmp_path / "nope.toml"))

    def test_bad_toml_fail_loud(self, tmp_path):
        p = tmp_path / "bad.toml"
        p.write_text("[class_rule\n", encoding="utf-8")
        with pytest.raises(mod.ConfigError):
            mod.load_policy(str(p))

    def test_unknown_row_key_fail_loud(self, tmp_path):
        p = tmp_path / "c.toml"
        p.write_text(
            '[[class_rule]]\nclass = "usage-liveness"\n'
            'auto_intent = ["inform"]\naction = "auto"\nzzz = 1\n',
            encoding="utf-8",
        )
        with pytest.raises(mod.ConfigError):
            mod.load_policy(str(p))

    def test_unknown_top_key_fail_loud(self, tmp_path):
        p = tmp_path / "c.toml"
        p.write_text(
            '[[class_rule]]\nclass = "usage-liveness"\n'
            'auto_intent = ["inform"]\naction = "auto"\n[extra]\nx = 1\n',
            encoding="utf-8",
        )
        with pytest.raises(mod.ConfigError):
            mod.load_policy(str(p))

    def test_bad_action_fail_loud(self, tmp_path):
        p = tmp_path / "c.toml"
        p.write_text(
            '[[class_rule]]\nclass = "usage-liveness"\n'
            'auto_intent = ["inform"]\naction = "auto-all"\n',
            encoding="utf-8",
        )
        with pytest.raises(mod.ConfigError):
            mod.load_policy(str(p))

    def test_row_missing_key_fail_loud(self, tmp_path):
        p = tmp_path / "c.toml"
        p.write_text('[[class_rule]]\nclass = "usage-liveness"\n', encoding="utf-8")
        with pytest.raises(mod.ConfigError):
            mod.load_policy(str(p))

    def test_duplicate_class_fail_loud(self, tmp_path):
        p = tmp_path / "c.toml"
        p.write_text(
            '[[class_rule]]\nclass = "usage-liveness"\n'
            'auto_intent = ["inform"]\naction = "auto"\n'
            '[[class_rule]]\nclass = "usage-liveness"\n'
            'auto_intent = ["inform"]\naction = "auto"\n',
            encoding="utf-8",
        )
        with pytest.raises(mod.ConfigError):
            mod.load_policy(str(p))

    def test_solicit_in_auto_intent_fail_loud(self, tmp_path):
        """config 不可放寪 solicit 底線——列了即配置錯誤（fail-loud）。"""
        p = tmp_path / "c.toml"
        p.write_text(
            '[[class_rule]]\nclass = "usage-liveness"\n'
            'auto_intent = ["solicit"]\naction = "auto"\n',
            encoding="utf-8",
        )
        with pytest.raises(mod.ConfigError):
            mod.load_policy(str(p))


# ── triage：default-deny 判定＋機械驗證────────────────────────────────


class TestTriage:
    def test_auto_happy_inform(self):
        d = mod.triage(_env_item("e-1"), _policy())
        assert d.action == "auto"
        assert d.klass == "usage-liveness"
        assert d.intent == "inform"

    def test_unknown_class_surface(self):
        d = mod.triage(_env_item("e-1", klass="mystery"), _policy())
        assert d.action == "surface"

    def test_solicit_surface_even_registered(self):
        d = mod.triage(_env_item("e-1", intent="solicit"), _policy())
        assert d.action == "surface"

    def test_bad_body_json_surface(self):
        item = _env_item("e-1", body=None, canonical=None)
        # body 生成為 "not-json{" 的路徑：直接構造 canonical 壞 body
        env = json.loads(item["canonicalEnvelope"])
        env["body"] = "not-json{"
        item["canonicalEnvelope"] = json.dumps(env, ensure_ascii=False)
        d = mod.triage(item, _policy())
        assert d.action == "surface"
        assert d.reason == "bad-body"

    def test_body_non_object_surface(self):
        item = _env_item("e-1")
        env = json.loads(item["canonicalEnvelope"])
        env["body"] = "[1,2]"
        item["canonicalEnvelope"] = json.dumps(env, ensure_ascii=False)
        d = mod.triage(item, _policy())
        assert d.action == "surface"
        assert d.reason == "bad-body"

    def test_body_missing_class_key_surface(self):
        item = _env_item("e-1", body={"task": "T-1"})
        d = mod.triage(item, _policy())
        assert d.action == "surface"
        assert d.reason == "bad-body"

    def test_receipt_without_correlation_surface(self):
        item = _env_item(
            "e-1", klass="receipt", intent="receipt",
            body={"class": "receipt"},  # 無 in_reply_to、無 task/card
        )
        d = mod.triage(item, _policy())
        assert d.action == "surface"
        assert d.reason == "receipt-no-idempotency"

    def test_receipt_with_in_reply_to_auto(self):
        item = _env_item(
            "e-1", klass="receipt", intent="receipt",
            body={"class": "receipt"}, in_reply_to="env-orig",
        )
        d = mod.triage(item, _policy())
        assert d.action == "auto"

    def test_receipt_with_body_task_auto(self):
        item = _env_item(
            "e-1", klass="receipt", intent="receipt",
            body={"class": "receipt", "task": "T-9"},
        )
        d = mod.triage(item, _policy())
        assert d.action == "auto"

    def test_receipt_with_body_card_auto(self):
        item = _env_item(
            "e-1", klass="receipt", intent="receipt",
            body={"class": "receipt", "card": "AIR-1"},
        )
        d = mod.triage(item, _policy())
        assert d.action == "auto"

    def test_handoff_always_surface(self):
        d = mod.triage(_env_item("e-1", klass="handoff"), _policy())
        assert d.action == "surface"

    def test_bad_canonical_envelope_surface(self):
        item = _env_item("e-1", canonical="not-even-json")
        d = mod.triage(item, _policy())
        assert d.action == "surface"
        assert d.reason == "bad-envelope"

    def test_unknown_intent_value_surface(self):
        item = _env_item("e-1", intent="please")
        d = mod.triage(item, _policy())
        assert d.action == "surface"


# ── ensure_holder：fresh bind／renew／rebind-on-fencing─────────────────


class TestEnsureHolder:
    def test_fresh_bind_status_then_bind_cas(self, state_file):
        runner = _seq_runner([_status_doc(epoch=4), _bind_doc(epoch=5)])
        st = mod.ensure_holder(ADDR, runner, state_file)
        assert st["token"] == "tok-fresh"
        assert st["epoch"] == 5
        assert runner.calls == [
            ["holder", "status", "--address", ADDR],
            ["holder", "bind", "--address", ADDR, "--expected-epoch", "4"],
        ]
        saved = _read_state(state_file)
        assert saved == {
            "address": ADDR, "epoch": 5, "token": "tok-fresh",
            "bound_at_iso": st["bound_at_iso"],
        }

    def test_fresh_address_epoch_zero_binds_with_expected_zero(
        self, state_file,
    ):
        """fresh address（從未 bind）：status 合法回 bindingEpoch=0＋
        live=False＋leaseExpiresAtUs=None——首次 bind 的 consent CAS 觀察值
        正是 `--expected-epoch 0`（S3 真實 store 實測形狀）。"""
        fresh_status = _ok({
            "addressId": "a1", "alias": ADDR, "bindingEpoch": 0,
            "leaseExpiresAtUs": None, "live": False,
        })
        runner = _seq_runner([fresh_status, _bind_doc(epoch=1)])
        st = mod.ensure_holder(ADDR, runner, state_file)
        assert st["epoch"] == 1
        assert st["token"] == "tok-fresh"
        assert runner.calls == [
            ["holder", "status", "--address", ADDR],
            ["holder", "bind", "--address", ADDR, "--expected-epoch", "0"],
        ]

    def test_live_holder_not_preempted_zero_bind(self, state_file):
        """holder 搶奪防護（S3 finding #2）：live holder 在場（另一
        session 持有消費權威）→ 零 bind 呼叫、HolderConflict surface
        （不搶、待 lease 到期）、單次嘗試。"""
        runner = _seq_runner([_ok({
            "addressId": "a1", "alias": ADDR, "bindingEpoch": 1,
            "leaseExpiresAtUs": NOW_US + 300_000_000, "live": True,
        })])
        with pytest.raises(mod.HolderConflict) as exc:
            mod.ensure_holder(ADDR, runner, state_file)
        msg = str(exc.value)
        assert "另一 session holding（epoch 1）" in msg
        assert "本 session 不搶" in msg
        assert "現 holder 承擔" in msg
        assert len(runner.calls) == 1  # 只 status——零 bind 零重試

    def test_lease_expired_epoch_one_takeover(self, state_file):
        """lease 到期換代（live=False）＝正當 rebind：bind 以 observed
        epoch 為 consent 觀察值（epoch=1 → --expected-epoch 1）。"""
        runner = _seq_runner([
            _ok({
                "addressId": "a1", "alias": ADDR, "bindingEpoch": 1,
                "leaseExpiresAtUs": 0, "live": False,
            }),
            _bind_doc(epoch=2, token="tok-takeover"),
        ])
        st = mod.ensure_holder(ADDR, runner, state_file)
        assert st["epoch"] == 2 and st["token"] == "tok-takeover"
        assert runner.calls[1] == [
            "holder", "bind", "--address", ADDR, "--expected-epoch", "1",
        ]

    def test_renew_fencing_with_live_foreign_holder_also_no_preempt(
        self, state_file,
    ):
        """renew 撞 fencing 後觀察到他方 live holder——同樣不搶（統一
        live 閘，非僅 fresh 路徑）。"""
        _seed_state(state_file)
        runner = _seq_runner([
            _err("stale-epoch", "fencing", exit_code=5),
            _ok({
                "addressId": "a1", "alias": ADDR, "bindingEpoch": 5,
                "leaseExpiresAtUs": NOW_US + 300_000_000, "live": True,
            }),
        ])
        with pytest.raises(mod.HolderConflict, match="另一 session holding"):
            mod.ensure_holder(ADDR, runner, state_file)
        assert len(runner.calls) == 2  # renew＋status——零 bind

    def test_holder_status_zero_face_passthrough(self, state_file):
        """status face 的零值／空值合法面（epoch 0／lease null／live
        False）原樣通過 holder_status 包裝——除 observed epoch（非負
        整數）外零欄位被驗證拒絕。"""
        doc = _ok({
            "addressId": "a1", "alias": ADDR, "bindingEpoch": 0,
            "leaseExpiresAtUs": None, "live": False,
        })
        runner = _seq_runner([doc])
        got = mod.holder_status(runner, ADDR)
        assert got["bindingEpoch"] == 0
        assert got["live"] is False
        assert got["leaseExpiresAtUs"] is None

    def test_state_file_0600_atomic(self, state_file):
        runner = _seq_runner([_status_doc(), _bind_doc()])
        mod.ensure_holder(ADDR, runner, state_file)
        mode = stat.S_IMODE(os.stat(state_file).st_mode)
        assert mode == 0o600
        leftovers = [f for f in os.listdir(os.path.dirname(state_file))
                     if f.endswith(".tmp")]
        assert leftovers == []  # atomic 寫不留 tmp 殘屍

    def test_renew_when_token_present(self, state_file):
        _seed_state(state_file)
        runner = _seq_runner([_renew_doc(epoch=4)])
        st = mod.ensure_holder(ADDR, runner, state_file)
        assert st["token"] == "tok-old"
        assert runner.calls == [
            ["holder", "renew", "--address", ADDR, "--token", "tok-old"],
        ]

    def test_rebind_on_fencing_renew_failure(self, state_file):
        """renew class-5（lease-expired）→ status → rebind → 存新 token。"""
        _seed_state(state_file)
        runner = _seq_runner([
            _err("lease-expired", "fencing", exit_code=5),
            _status_doc(epoch=4),
            _bind_doc(epoch=5, token="tok-gen2"),
        ])
        st = mod.ensure_holder(ADDR, runner, state_file)
        assert st["token"] == "tok-gen2"
        assert st["epoch"] == 5
        assert _read_state(state_file)["token"] == "tok-gen2"
        assert runner.calls[2] == [
            "holder", "bind", "--address", ADDR, "--expected-epoch", "4",
        ]

    def test_rebind_cas_conflict_single_attempt(self, state_file, capsys):
        """rebind CAS 失敗（epoch-conflict）＝回衝突、不重試轟炸（單次）。"""
        _seed_state(state_file)
        runner = _seq_runner([
            _err("stale-epoch", "fencing", exit_code=5),
            _status_doc(epoch=4),
            _err("epoch-conflict", "fencing", exit_code=5),
        ])
        with pytest.raises(mod.HolderConflict):
            mod.ensure_holder(ADDR, runner, state_file)
        assert len(runner.calls) == 3  # 無第四發

    def test_storage_error_propagates(self, state_file):
        _seed_state(state_file)
        runner = _seq_runner([
            _err("store-incompatible", "storage", exit_code=4),
        ])
        with pytest.raises(mod.DutymailFaceError):
            mod.ensure_holder(ADDR, runner, state_file)


# ── process_batch：flush-ack 防護＋ack-only-after-disposition＋invalidate


class TestProcessBatch:
    def test_ack_only_after_all_dispositions_commit_separated(self, state_file):
        """3 封（1 auto＋2 surface）：prepare→state 記 batch→全 triage→
        回傳 lines＋commit；ack 只在 commit()（輸出寫出後）執行。"""
        envs = [
            _env_item("e-1", klass="usage-liveness"),
            _env_item("e-2", klass="handoff"),
            _env_item("e-3", klass="handoff"),
        ]
        runner = _seq_runner([
            _status_doc(), _bind_doc(), _prepare_doc(envs), _ack_doc(),
        ])
        _lines, commit = mod.process_once(
            ADDR, runner, _policy(), state_file, now_us=NOW_US,
        )
        # run 返回當下：prepare 已呼、ack 未呼（advance-after-emit）
        joined = list(runner.calls)
        assert joined[-1][0:2] == ["receive", "prepare"]
        assert not any(c[0:2] == ["receive", "ack"] for c in runner.calls)
        # state 已記 batch_token（undisposed——crash window 防線）
        mid = _read_state(state_file)
        assert mid["batch_token"] == "bt-1"
        assert mid["batch_disposed"] is False
        commit()
        ack_calls = [c for c in runner.calls if c[0:2] == ["receive", "ack"]]
        assert len(ack_calls) == 1
        assert ack_calls[0] == [
            "receive", "ack", "--address", ADDR,
            "--token", "tok-fresh", "--batch", "bt-1",
        ]
        final = _read_state(state_file)
        assert "batch_token" not in final and "batch_disposed" not in final

    def test_prepare_bounded_max_count_8(self, state_file):
        runner = _seq_runner([
            _status_doc(), _bind_doc(),
            _prepare_doc([_env_item("e-1")]), _ack_doc(),
        ])
        _lines, commit = mod.process_once(
            ADDR, runner, _policy(), state_file, now_us=NOW_US,
        )
        commit()
        prep = next(
            c for c in runner.calls if c[0:2] == ["receive", "prepare"]
        )
        assert prep[prep.index("--max-count") + 1] == "8"

    def test_flush_ack_protection_triage_raise(self, state_file, monkeypatch):
        """EP invariant 4：triage 中途例外 → ack 不被呼叫（絕不 flush-ack）。"""
        envs = [_env_item("e-1"), _env_item("e-2"), _env_item("e-3")]
        runner = _seq_runner([
            _status_doc(), _bind_doc(), _prepare_doc(envs),
        ])
        real_triage = mod.triage
        boom = [False]

        def poisoned(item, policy):
            if item["envelopeId"] == "e-2":
                boom[0] = True
                raise RuntimeError("triage exploded mid-batch")
            return real_triage(item, policy)

        monkeypatch.setattr(mod, "triage", poisoned)
        with pytest.raises(RuntimeError, match="triage exploded"):
            mod.process_once(
                ADDR, runner, _policy(), state_file, now_us=NOW_US,
            )
        assert boom[0]
        assert not any(
            c[0:2] == ["receive", "ack"] for c in runner.calls
        )  # ack 未被呼叫
        st = _read_state(state_file)
        assert st["batch_token"] == "bt-1" and st["batch_disposed"] is False

    def test_empty_batch_quiet_no_state_batch(self, state_file):
        runner = _seq_runner([_status_doc(), _bind_doc(), _prepare_doc([])])
        lines, commit = mod.process_once(
            ADDR, runner, _policy(), state_file, now_us=NOW_US,
        )
        assert lines == []
        assert commit is None
        assert "batch_token" not in _read_state(state_file)

    def test_legacy_undisposed_invalidates(self, state_file):
        """遺留批次未處置 → prepare --invalidate 重 prepare（寧重不漏）。"""
        _seed_state(state_file, batch_token="bt-stale", disposed=False)
        envs = [_env_item("e-1", klass="handoff")]
        runner = _seq_runner([
            _renew_doc(), _prepare_doc(envs, batch_token="bt-2"), _ack_doc(),
        ])
        _lines, commit = mod.process_once(
            ADDR, runner, _policy(), state_file, now_us=NOW_US,
        )
        prep = next(
            c for c in runner.calls if c[0:2] == ["receive", "prepare"]
        )
        assert "--invalidate" in prep  # flag 形（凍結語義無值）
        assert not any(  # 未處置絕不代 ack 舊批
            "bt-stale" in c for c in runner.calls
        )
        commit()
        assert _read_state(state_file).get("batch_token") is None

    def test_legacy_disposed_acks_first(self, state_file):
        """遺留批次已處置（state 記錄）→ 先試 ack（冪等重試），再 fresh prepare。"""
        _seed_state(state_file, batch_token="bt-stale", disposed=True)
        envs = [_env_item("e-1", klass="handoff")]
        runner = _seq_runner([
            _renew_doc(),
            _ack_doc(replayed=True),  # 遺留 ack——replayed 分支
            _prepare_doc(envs, batch_token="bt-2"),
            _ack_doc(),
        ])
        _lines, commit = mod.process_once(
            ADDR, runner, _policy(), state_file, now_us=NOW_US,
        )
        assert runner.calls[1] == [
            "receive", "ack", "--address", ADDR,
            "--token", "tok-old", "--batch", "bt-stale",
        ]
        commit()
        assert _read_state(state_file).get("batch_token") is None

    def test_legacy_disposed_ack_expired_falls_through(self, state_file):
        """遺留 ack 失敗（batch-expired class 3）→ 清記錄、落 fresh prepare。"""
        _seed_state(state_file, batch_token="bt-stale", disposed=True)
        envs = [_env_item("e-1", klass="handoff")]
        runner = _seq_runner([
            _renew_doc(),
            _err("batch-expired", "admission", exit_code=3),
            _prepare_doc(envs, batch_token="bt-2"),
            _ack_doc(),
        ])
        _lines, commit = mod.process_once(
            ADDR, runner, _policy(), state_file, now_us=NOW_US,
        )
        assert runner.calls[2][0:2] == ["receive", "prepare"]
        commit()

    def test_prepare_batch_conflict_retry_invalidate(self, state_file):
        """prepare 撞 live batch（crash-before-state-write 孤兒）→ --invalidate 重試一次。"""
        envs = [_env_item("e-1", klass="handoff")]
        runner = _seq_runner([
            _status_doc(), _bind_doc(),
            _err("batch-conflict", "admission", exit_code=3),
            _prepare_doc(envs),
            _ack_doc(),
        ])
        _lines, commit = mod.process_once(
            ADDR, runner, _policy(), state_file, now_us=NOW_US,
        )
        preps = [c for c in runner.calls if c[0:2] == ["receive", "prepare"]]
        assert len(preps) == 2
        assert "--invalidate" not in preps[0]
        assert "--invalidate" in preps[1]
        commit()

    def test_prepare_fencing_rebinds_once(self, state_file):
        """prepare 撞 class-5（stale-epoch）→ status→rebind→重 prepare 一次。"""
        envs = [_env_item("e-1", klass="handoff")]
        runner = _seq_runner([
            _status_doc(), _bind_doc(token="tok-a"),
            _err("stale-epoch", "fencing", exit_code=5),
            _status_doc(epoch=6), _bind_doc(epoch=7, token="tok-b"),
            _prepare_doc(envs),
            _ack_doc(),
        ])
        _lines, commit = mod.process_once(
            ADDR, runner, _policy(), state_file, now_us=NOW_US,
        )
        assert _read_state(state_file)["token"] == "tok-b"
        commit()
        ack = next(c for c in runner.calls if c[0:2] == ["receive", "ack"])
        assert ack[ack.index("--token") + 1] == "tok-b"

    def test_holder_conflict_no_prepare(self, state_file):
        """bind CAS 衝突 → surface 衝突訊息、零 prepare 零 ack（不轟炸）。"""
        runner = _seq_runner([
            _status_doc(epoch=4),
            _err("epoch-conflict", "fencing", exit_code=5),
        ])
        with pytest.raises(mod.HolderConflict):
            mod.process_once(
                ADDR, runner, _policy(), state_file, now_us=NOW_US,
            )
        assert not any(
            c[0] == "receive" for c in runner.calls
        )


# ── digest／surface 渲染──────────────────────────────────────────────


class TestDigestRendering:
    def _run_lines(self, state_file, envs):
        runner = _seq_runner([
            _status_doc(), _bind_doc(), _prepare_doc(envs), _ack_doc(),
        ])
        lines, commit = mod.process_once(
            ADDR, runner, _policy(), state_file, now_us=NOW_US,
        )
        return lines, commit

    def test_digest_line_shape(self, state_file):
        envs = [
            _env_item("e-1", klass="usage-liveness"),
            _env_item("e-2", klass="handoff",
                      created_us=NOW_US - 5 * 60_000_000),
            _env_item("e-3", klass="handoff",
                      created_us=NOW_US - 2 * 60_000_000),
        ]
        lines, _commit = self._run_lines(state_file, envs)
        digest = lines[0]
        assert digest.startswith("[duty-receive] " + ADDR + "：")
        assert "新到 3、1 件例行已處理、2 件等你（最舊 5 分鐘）" in digest
        assert "class：usage-liveness×1、handoff×2" in digest

    def test_digest_k_zero_no_age_paren(self, state_file):
        envs = [_env_item("e-1"), _env_item("e-2", klass="terminal-completion")]
        lines, _commit = self._run_lines(state_file, envs)
        digest = lines[0]
        assert "新到 2、2 件例行已處理、0 件等你" in digest
        assert "最舊" not in digest

    def test_surface_full_text_first_three_then_summary(self, state_file):
        envs = [_env_item(f"e-{i}", klass="handoff") for i in range(1, 6)]
        lines, _commit = self._run_lines(state_file, envs)
        surf = [ln for ln in lines if "待你處置" in ln]
        assert len(surf) == 5
        full = [ln for ln in surf if "摘要" not in ln]
        summary = [ln for ln in surf if "摘要" in ln]
        assert len(full) == 3 and len(summary) == 2
        # 全文＝canonical envelope 逐字（verbatim——非摘要非重排）
        assert full[0] == (
            "[duty-receive] 待你處置（1/5）：" + envs[0]["canonicalEnvelope"]
        )
        for i, ln in enumerate(summary, 4):
            assert (
                f"from=s-e-{i} class=handoff intent=inform "
                f"envelope_id=e-{i}" in ln
            )

    def test_auto_items_no_full_text(self, state_file):
        envs = [_env_item("e-1"), _env_item("e-2")]
        lines, _commit = self._run_lines(state_file, envs)
        assert len(lines) == 1  # 只剩 digest 行——auto 由 digest 吸收
        assert "例行已處理" in lines[0]

    def test_auto_wording_not_work_accepted(self, state_file):
        """輸出語義：例行信「已處理」——不得宣稱 work accepted（已承接）。"""
        envs = [_env_item("e-1")]
        lines, _commit = self._run_lines(state_file, envs)
        assert "承接" not in lines[0]

    def test_future_created_at_clamps_to_zero_minutes(self, state_file):
        """created_at_us 在未來（時鐘偏移）→ age clamp 0——不得顯示
        「最舊 -2 分鐘」（S3 finding #3）。"""
        envs = [
            _env_item(
                "e-1", klass="handoff",
                created_us=NOW_US + 2 * 60_000_000,  # 未來 2 分鐘
            ),
        ]
        lines, _commit = self._run_lines(state_file, envs)
        digest = lines[0]
        assert "最舊 0 分鐘" in digest
        assert "最舊 -" not in digest


# ── hook 面：stdin 驅動／eligibility／fail-soft／fail-loud────────────


@pytest.fixture(autouse=True)
def _gate(monkeypatch):
    monkeypatch.setattr(hook, "script_repo_root", lambda: REPO)


class TestHookRun:
    def test_happy_path_additional_context(self, tmp_path):
        envs = [_env_item("e-1", klass="handoff")]
        runner = _seq_runner([
            _status_doc(), _bind_doc(), _prepare_doc(envs), _ack_doc(),
        ])
        code, out, commit = _hook_run(UPS_STDIN, runner, tmp_path, now_us=NOW_US)
        assert code == 0
        doc = json.loads(out)
        assert doc["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        ctx = doc["hookSpecificOutput"]["additionalContext"]
        assert "新到 1、0 件例行已處理、1 件等你" in ctx
        assert "待你處置（1/1）" in ctx
        commit()
        state = tmp_path / "sess-1.json"
        assert "batch_token" not in _read_state(str(state))

    def test_sessionstart_event(self, tmp_path):
        runner = _seq_runner([_status_doc(), _bind_doc(), _prepare_doc([])])
        code, out, _commit = _hook_run(SS_STDIN, runner, tmp_path)
        assert (code, out) == (0, "")  # 無新信零 stdout

    def test_no_new_mail_zero_stdout(self, tmp_path):
        runner = _seq_runner([_status_doc(), _bind_doc(), _prepare_doc([])])
        code, out, commit = _hook_run(UPS_STDIN, runner, tmp_path)
        assert (code, out, commit) == (0, "", None)

    def test_eligibility_gate_outside_repo_zero_queries(self, tmp_path):
        runner = _seq_runner([])
        raw = _stdin(cwd="/tmp/other-project")
        code, out, commit = _hook_run(raw, runner, tmp_path)
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []  # 零查詢

    def test_cwd_missing_fail_closed(self, tmp_path):
        runner = _seq_runner([])
        raw = json.dumps({"hook_event_name": "UserPromptSubmit",
                          "session_id": "s1"})
        code, out, commit = _hook_run(raw, runner, tmp_path)
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_missing_session_id_zero_queries(self, tmp_path):
        runner = _seq_runner([])
        raw = json.dumps({"hook_event_name": "UserPromptSubmit", "cwd": REPO})
        code, out, commit = _hook_run(raw, runner, tmp_path)
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_bad_stdin_json_silent(self, tmp_path):
        runner = _seq_runner([])
        code, out, commit = _hook_run("{not json", runner, tmp_path)
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_unknown_event_silent(self, tmp_path):
        runner = _seq_runner([])
        raw = _stdin(event="Stop")
        code, out, commit = _hook_run(raw, runner, tmp_path)
        assert (code, out, commit) == (0, "", None)
        assert runner.calls == []

    def test_store_absent_fail_soft_stderr_note(self, tmp_path, capsys):
        """store 缺席（class 4 storage）＝stderr 一行註記＋零 stdout exit 0。"""
        runner = _seq_runner([
            _hook_err("store-incompatible", "storage", exit_code=4),
        ])
        code, out, commit = _hook_run(UPS_STDIN, runner, tmp_path)
        assert (code, out, commit) == (0, "", None)
        err = capsys.readouterr().err
        assert "store" in err
        assert "duty-receive" in err

    def test_other_face_failure_fail_soft(self, tmp_path, capsys):
        runner = _seq_runner([
            _hook_err("unknown-address", "admission", exit_code=3),
        ])
        code, out, commit = _hook_run(UPS_STDIN, runner, tmp_path)
        assert (code, out, commit) == (0, "", None)
        err = capsys.readouterr().err
        assert "unknown-address" in err  # 實際錯誤摘要隨行

    def test_config_bad_fail_loud_exit3(self, tmp_path, capsys):
        runner = _seq_runner([])
        code, out, commit = _hook_run(
            UPS_STDIN, runner, tmp_path, config_path=str(tmp_path / "nope.toml"),
        )
        assert (code, out, commit) == (3, "", None)
        assert runner.calls == []
        assert "config" in capsys.readouterr().err

    def test_holder_conflict_surfaced_as_line(self, tmp_path):
        runner = _seq_runner([
            _status_doc(epoch=4),
            _hook_err("epoch-conflict", "fencing", exit_code=5),
        ])
        code, out, commit = _hook_run(UPS_STDIN, runner, tmp_path)
        assert code == 0 and commit is None
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        assert "衝突" in ctx
        assert not any(c[0] == "receive" for c in runner.calls)

    def test_main_missing_address_exit2(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "stdin", io.StringIO(UPS_STDIN))
        with pytest.raises(SystemExit) as exc:
            hook.main([])
        assert exc.value.code == 2

    def test_main_happy_commit_after_stdout(self, tmp_path, capsys,
                                            monkeypatch):
        envs = [_env_item("e-1", klass="handoff")]
        runner = _seq_runner([
            _status_doc(), _bind_doc(), _prepare_doc(envs), _ack_doc(),
        ])
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
        monkeypatch.setattr(sys, "stdin", io.StringIO(UPS_STDIN))
        rc = hook.main(
            ["--address", ADDR, "--config", REAL_CONFIG], runner=runner
        )
        assert rc == 0
        captured = capsys.readouterr()
        assert "新到 1" in captured.out
        state = tmp_path / "ai-guide" / "duty-receive" / "sess-1.json"
        assert "batch_token" not in _read_state(str(state))


# ── governance 接線：registrations 雙事件＋manifest scripts 登記───────


class TestRegistrationWiring:
    def _doc(self, rel):
        return json.loads(
            (REPO_ROOT / "governance" / rel).read_text(encoding="utf-8")
        )

    def _groups(self, doc, event):
        events = doc.get("events", doc)
        return events.get(event, [])

    def _scripts(self, group):
        return [
            h.get("args", [h.get("command", "")])[0].rsplit("/", 1)[-1]
            if h.get("args") else h.get("command", "")
            for h in group.get("hooks", [])
        ]

    def test_zcode_both_events_one_group_each(self):
        doc = self._doc("registrations/zcode.json")
        for event in ("UserPromptSubmit", "SessionStart"):
            hits = [g for g in self._groups(doc, event)
                    if "duty_receive.py" in self._scripts(g)]
            assert len(hits) == 1, event
            entry = hits[0]["hooks"][0]
            assert entry["type"] == "process"
            assert "async" not in entry  # sync——additionalContext 通道
            assert entry.get("timeoutMs")
            assert entry["args"][1:] == ["--address", "ai-guide-marshal"]

    def test_cc_dormant_same_shape(self):
        doc = self._doc("registrations/cc.json")
        for event in ("UserPromptSubmit", "SessionStart"):
            hits = [g for g in self._groups(doc, event)
                    if "duty_receive.py" in self._scripts(g)]
            assert len(hits) == 1, event

    def test_manifest_inventory_lists_hook(self):
        import tomllib
        raw = (REPO_ROOT / "governance" / "manifest.toml").read_bytes()
        manifest = tomllib.loads(raw.decode("utf-8"))
        assert "hooks/duty_receive.py" in manifest["surfaces"]["hooks"]["scripts"]

    def test_scbus_entries_untouched(self):
        """原 scbus-address-pending-reminder 條目數不減（zcode=4、cc=2）。"""
        zc = self._doc("registrations/zcode.json")
        cc = self._doc("registrations/cc.json")

        def count(doc):
            n = 0
            for groups in doc.get("events", doc).values():
                for g in groups:
                    for h in g.get("hooks", []):
                        args = h.get("args", [])
                        if any("scbus-address-pending-reminder.py" in a
                               for a in args):
                            n += 1
            return n

        assert count(zc) == 4
        assert count(cc) == 2
