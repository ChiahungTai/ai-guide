#!/usr/bin/env python3
"""dutymail 值星收信 hook 前導（AIR-254.3 S2）。

薄前導：stdin payload（SessionStart／UserPromptSubmit——值星在場的
interaction boundary）→ eligibility gate（cwd 在 repo 內，AIR-233 模式
——不過＝零查詢零輸出）→ session_id 取自 payload（per-session holder
state key）→ 載入 scripts/duty_receive 核心（檔案路徑顯式載入——
hooks/ 與 scripts/ 同 repo，核心單一源不複製）→
hookSpecificOutput.additionalContext 輸出（sync；
與 AIR-233 hook 同形）。核心邏輯（holder／prepare／triage／ack、
default-deny 分診表、絕不 flush-ack）單一源＝scripts/duty_receive.py。

決策表（hook 運作面；stdout 皆協議 JSON 或空）：

| 情境 | stdout | exit |
|---|---|---|
| 新到信件（digest＋surface 一行摘要——B′ AIR-258：全文面＝SC INBOX） | hookSpecificOutput | 0 |
| 無新信（空批次）／無 session_id | 空（安靜） | 0 |
| eligibility gate 不過（cwd 在 repo 外） | 空（零查詢零輸出） | 0 |
| store 缺席（face class 4 storage） | 空＋stderr 一行註記 | 0 |
| binary 缺席（resolver 全 miss＝BinaryMissing——環境壞，非 store 軟 path） | 空；consecutive miss <3 靜默、≥3 stderr advisory 一行（sidecar 計數；binary 在場呼叫歸零——resolve 已過，含 face 失敗；唯 BinaryMissing 不歸零——AIR-274 M1） | 0（advisory 不擋 prompt） |
| 其他 face 失敗（含 shape 漂移） | 空＋stderr 註記帶錯誤摘要 | 0 |
| holder 衝突（live holder 在場／rebind CAS 失敗——皆不搶不重試） | 衝突訊息行（surface） | 0 |
| 併發鎖逾時（fallback——照跑，可能重複呈報 bounded） | 照常輸出＋stderr 一行 lock timeout＋sidecar 計數 | 0 |
| stdin 壞 JSON／缺或未知事件 | 空（fail-soft） | 0 |
| config 缺席／壞形 | 空＋stderr 註記 | 3（fail-loud——配置錯誤要大聲） |
| 註冊 args 誤用（argparse 拒絕） | 空（stderr 用法） | 2（大聲、刻意——misconfig 歸註冊單一源修復） |

ack（唯一 cursor 前進邊）由 commit closure 在 stdout 寫出成功後執行
（advance-after-emit：先呈報後 ack）；ack 失敗不擋 turn——state 保留
處置紀錄，下輪先試 ack（冪等）或重 prepare（寧重不漏）。

本 hook 不觸達 send／replies 面（v1 絕不主動送信）；只掛值星在場的
兩事件，無 session＝零查詢零輸出（閒置完全安靜）。部署 runtime＝
governance-resolved Python 3.12（hooks/AGENTS.md 部署紀律——本 hook
非 sc-router canonical 條目，獨立 group 註冊；部署＝marshal 職責）。
"""

import argparse
import importlib.util
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)  # hook_payload_compat（hooks/ 同目錄）
import hook_payload_compat as compat

# 核心單一源＝scripts/duty_receive.py——以檔案路徑顯式載入（自建模組名
# _duty_receive_core，不進 sys.modules["duty_receive"]）：sys.path dance 下
# `import duty_receive` 在 scripts/ 已在 path 時會解析回 hooks/ 自己
# （同名 circular import），對 scripts/ 的 path 依賴整段退役。
_core_spec = importlib.util.spec_from_file_location(
    "_duty_receive_core", os.path.join(_REPO, "scripts", "duty_receive.py")
)
core = importlib.util.module_from_spec(_core_spec)
_core_spec.loader.exec_module(core)

# disposition ledger 核心（AIR-287 消費端份——received 記帳面單一源；
# 同 importlib 檔案路徑載入模式，零 sys.path 依賴）。
_dd_spec = importlib.util.spec_from_file_location(
    "_duty_disposition_core",
    os.path.join(_REPO, "scripts", "duty_disposition.py"),
)
dd = importlib.util.module_from_spec(_dd_spec)
_dd_spec.loader.exec_module(dd)

HOOK_TAG = core.HOOK_TAG
SUPPORTED_EVENTS = ("SessionStart", "UserPromptSubmit")


def _default_sink_factory(session_id):
    """生產面 sink 工廠（AIR-287 接線）：session 綁定 safe received
    sink——duty_disposition.make_received_sink 內建 failure containment
    （記帳失敗只 stderr，絕不擋收信）。factory 本身 raise＝run() 內
    fail-soft 吸收（sink=None 照跑）。"""
    return dd.make_received_sink(session_id)


def _default_resolution_factory(session_id):
    """生產面 resolution sink 工廠（AIR-287 bi 修復必修 1——codex
    F1）：session 綁定 safe resolution sink——digest 呈現完成邊界推進
    （auto→handled／surface→needs-human；單一源＝duty_disposition.
    record_resolution，推進點裁定＝該模組 docstring）。factory 本身
    raise＝run() 內 fail-soft 吸收（sink=None 照跑）。"""
    return dd.make_resolution_sink(session_id)


# ── monitor eligibility gate（AIR-233 模式：cwd/workspace 鎖）────────


def script_repo_root():
    """hook script 所在 repo 根（registrations 以絕對路徑引用本目錄
    腳本；repo 根＝hooks/ 上一層。測試 monkeypatch 此函式換鎖）。"""
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def is_eligible(cwd):
    """合法 invocation 判定：session cwd（payload `cwd`）必須在 script
    所在 repo 內。fail-closed——cwd 缺席／非字串／repo 外皆 False（
    gate 不過＝零查詢零輸出，防錯誤 session 消費信件）。"""
    if not isinstance(cwd, str) or not cwd:
        return False
    root = script_repo_root()
    real = os.path.realpath(cwd)
    return real == root or real.startswith(root + os.sep)


def _default_config_path():
    return os.path.join(
        script_repo_root(), "governance", "dutymail-processor.toml"
    )


def run(raw, address, runner=None, state_dir=None, config_path=None,
        now_us=None, lock_factory=None, disposition_sink_factory=None,
        resolution_sink_factory=None):
    """stdin 原文 → (exit_code, stdout, commit | None)。

    永不 raise、exit 恆 0（唯二例外：config 壞形＝3 fail-loud；args
    誤用由 argparse exit 2）。runner／state_dir／config_path／now_us／
    lock_factory／disposition_sink_factory／resolution_sink_factory 可
    注入（測試 fake face＋fake state＋fake lock＋fake sink，不碰真
    store）。commit＝resolution 推進＋ack closure——呼叫端在 stdout
    寫出成功後才執行（advance-after-emit）。

    disposition_sink_factory（AIR-287 接線；可選）：session_id 抽取後
    呼叫一次得 sink（生產面＝_default_sink_factory——disposition
    ledger received 記帳），注入 process_once；建構失敗＝stderr 一行
    ＋sink=None 照跑（記帳面故障不擋收信）。None（預設）＝零記帳，
    既有行為不變。

    resolution_sink_factory（AIR-287 bi 修復必修 1；可選）：session_id
    抽取後呼叫一次得 resolution sink（生產面＝
    _default_resolution_factory——digest 呈現完成邊界推進 auto→
    handled／surface→needs-human），注入 process_once commit；建構
    失敗＝stderr 一行＋None 照跑。None（預設）＝不推進。

    併發鎖（AIR-255 B）：process_once 前取 per-session advisory lock，
    critical section 涵蓋 load→decide→save＋ack commit 全序列（取鎖後
    process_once 內部 load state＝重新判定——double-present 防護）；
    commit 由回傳的 wrapped closure 於執行後釋鎖。撞鎖逾時＝fallback
    照跑（stderr 一行＋dedicated sidecar 計數 <safe_sid>.fallbacks——
    不碰 state 主檔）——絕不擋 prompt。
    """
    runner = runner if runner is not None else core._default_runner
    lock_acquire = (
        lock_factory if lock_factory is not None
        else core.acquire_session_lock
    )
    try:
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return 0, "", None
        event_name = compat.hook_event_name(payload)
        if event_name not in SUPPORTED_EVENTS:
            return 0, "", None
        if not is_eligible(payload.get("cwd")):
            return 0, "", None
        session_id = compat.session_id(payload)
        if not session_id:
            return 0, "", None
        try:
            policy = core.load_policy(
                config_path if config_path is not None
                else _default_config_path()
            )
        except core.ConfigError as exc:
            print(
                f"[{HOOK_TAG}] config fail-loud（{exc}）", file=sys.stderr
            )
            return 3, "", None
        state_file = core.state_path(session_id, state_dir)
        sink = None
        if disposition_sink_factory is not None:
            try:
                sink = disposition_sink_factory(session_id)
            except Exception as exc:
                print(
                    f"[{dd.TAG}] disposition sink 建構失敗——本批不記帳"
                    f"（{exc!r}）",
                    file=sys.stderr,
                )
        resolution_sink = None
        if resolution_sink_factory is not None:
            try:
                resolution_sink = resolution_sink_factory(session_id)
            except Exception as exc:
                print(
                    f"[{dd.TAG}] resolution sink 建構失敗——本批不推進"
                    f"（{exc!r}）",
                    file=sys.stderr,
                )
        lock = lock_acquire(session_id, state_dir)
        released = False

        def _release():
            # 每路徑恰一次：fallback 計數在週期末落 dedicated sidecar
            # （F-2 修復輪起不碰 state 主檔），再釋鎖。
            nonlocal released
            if released:
                return
            released = True
            try:
                if not lock.held:
                    core.bump_lock_fallback(session_id, state_dir)
            except Exception as exc:
                # F-4（修復輪）：計數丟失可容忍——bump 失敗只 stderr 一行
                # 註記；例外不得從此處外洩（_commit_with_release 的 finally
                # 鏈中，本例外會取代 original_commit 的原例外——遮蔽 ack
                # 真原委）。
                print(
                    f"[{HOOK_TAG}] fallback 計數失敗——計數丟失（可容忍）"
                    f"：{exc!r}",
                    file=sys.stderr,
                )
            finally:
                lock.release()

        if not lock.held:
            detail = f"（{lock.error}）" if lock.error else ""
            print(
                f"[{HOOK_TAG}] lock timeout——可能重複呈報（bounded）"
                f"{detail}",
                file=sys.stderr,
            )

        def _runner_resets_miss(argv):
            # AIR-274 M1：binary 在場證據＝resolver 已過（成功 return
            # 或 face 失敗——DutymailFaceError 必在 binary 已執行後）
            # ——consecutive-miss 計數歸零；唯 BinaryMissing 不歸零。
            # reset 內部容錯不 raise，原例外照傳。
            try:
                out = runner(argv)
            except core.BinaryMissing:
                raise  # resolver miss——計數留給 except 分支 bump
            except Exception:
                core.reset_binary_miss(session_id, state_dir)
                raise
            core.reset_binary_miss(session_id, state_dir)
            return out

        try:
            lines, commit = core.process_once(
                address, _runner_resets_miss, policy, state_file,
                now_us=now_us, disposition_sink=sink,
                resolution_sink=resolution_sink,
            )
        except core.HolderConflict as exc:
            lines, commit = [f"[{HOOK_TAG}] {exc}"], None
        except core.DutymailFaceError as exc:
            _release()
            kind = (
                "store 缺席（pre-migration）" if exc.is_storage
                else "dutymail face 失敗"
            )
            print(
                f"[{HOOK_TAG}] fail-soft：{kind}——{exc}", file=sys.stderr
            )
            return 0, "", None
        except core.BinaryMissing:
            # AIR-274 M1：與 store-absent 分流——consecutive-miss 計數，
            # 達門檻 stderr advisory（surface 可見）；未達靜默。exit 恆 0
            # （hook 非零會擋 prompt）。
            _release()
            count = core.bump_binary_miss(session_id, state_dir)
            if count >= core.MISS_ADVISORY_THRESHOLD:
                print(
                    f"[{HOOK_TAG}] dutymail binary missing x {count}"
                    f"——請檢查 plugin 安裝",
                    file=sys.stderr,
                )
            return 0, "", None
        except Exception:
            _release()
            raise  # 交外層 fail-soft
        out = ""
        if lines:
            out = json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": event_name,
                        "additionalContext": "\n".join(lines),
                    }
                },
                ensure_ascii=False,
            )
        if commit is None:
            _release()
            return 0, out, None
        original_commit = commit

        def _commit_with_release():
            try:
                return original_commit()
            finally:
                _release()

        return 0, out, _commit_with_release
    except Exception as exc:  # fail-soft by design——絕不擋 turn
        print(f"[{HOOK_TAG}] fail-soft（{exc!r}）", file=sys.stderr)
        return 0, "", None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "dutymail 值星收信 hook 前導（AIR-254.3；SessionStart／"
            "UserPromptSubmit sync 兩事件）"
        )
    )
    parser.add_argument(
        "--address", required=True, metavar="ALIAS",
        help="門牌 alias（exact match；由註冊條目顯式宣告）",
    )
    parser.add_argument(
        "--config", default=None, metavar="PATH",
        help="分診表路徑覆寫（預設 repo 根 governance/"
        "dutymail-processor.toml）",
    )
    parser.add_argument(
        "--state-dir", default=None, metavar="DIR",
        help="holder state 目錄覆寫（預設 XDG state——診斷用）",
    )
    return parser.parse_args(argv)


def main(argv=None, runner=None) -> int:
    args = parse_args(argv)
    code, out, commit = run(
        sys.stdin.read(), args.address,
        runner=runner, state_dir=args.state_dir,
        config_path=args.config,
        disposition_sink_factory=_default_sink_factory,  # AIR-287 記帳
        resolution_sink_factory=_default_resolution_factory,  # AIR-287 bi 處理推進
    )
    if out:
        sys.stdout.write(out)
        sys.stdout.flush()
    if code != 0:
        return code
    if commit is not None:
        try:
            commit()  # advance-after-emit：stdout 寫出成功後才 ack
        except Exception as exc:  # 寧重不漏——不擋 turn
            print(
                f"[{HOOK_TAG}] ack 失敗——state 保留處置紀錄，下輪先試"
                f" ack（{exc!r}）",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
