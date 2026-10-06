#!/usr/bin/env python3
"""mail-watch daemon 核心（AIR-265 S1——模組＋subcommand CLI）。

職責：machine-level dutymail 信件 watcher——跨 session 常駐 daemon，
每 interval 秒對 per-address mailbox 執行唯讀 `receive status` 輪詢，
pendingCount 出現 rising edge 時以 say 音訊通知。收信處理面（
duty_receive 處理器）只在 prompt 邊界觸發——閒置時段的 rising edge
由本 watcher 補位；活躍 session 處理窗口 <interval 者 rising edge
自然不觸發（自然去抖）。

核心不變量（EP invariant 對應）：
- 唯讀單 face：dutymail 呼叫面只消費 `receive status --address
  <alias>`——本檔絕不觸達其他 dutymail 面。binary 解析（DUTYMAIL_BIN
  →PATH→plugin cache 版本最新）與 state 慣例（0600 atomic 寫）經
  同源 import scripts/duty_receive.py 複用，不複製邏輯。
- 人類音訊面不搶職責：say 是 advisory 非保證——不代理 transport
  cursor、不代理 SC human seen/done、不代理 monitor hook 的 session
  advisory；baseline 跨 session 機器級（不歸任一 session），與
  roundtrip 三線表的 session-local advisory baseline 並存互不代理。
- 寧重不漏：state 損壞視同冷啟（baseline 0 起算、pending>0 通知一次
  ——最多一次重複 advisory）；say 失敗 fail-soft（log 續跑、baseline
  已更新不回滾、下輪不重試本輪）；face typed-failure（storage/
  transient 類）跳過該輪＋心跳標記，不崩潰；usage/admission 類＝
  壞配置 fail-loud exit 2（不硬跑）。
- singleton by flock：跨進程互斥靠 fcntl.flock 狀態鎖（watch.lock）
  ——crash 自動釋放＝stale 偵測免費；stop 驗鎖不盲殺（鎖可取＝無
  daemon、清殘留回報 clean-stale；鎖被持才讀 state.json pid 發
  SIGTERM，bounded grace 5s 內未退＝回報失敗、不升級 SIGKILL 留
  human）；stop 不刪 state.json——restart 後 edge 邏輯自然接手
  （stop→新信→start＝pending>baseline＝rising edge 通知）。
- say 慣例：`say -v Meijia -r 180`＋中性句 ≤20 字（無稱謂——不製造
  稱謂清單第三份同步副本；對齊 voice skill 開始通知先例）。
- macOS sleep/resume：loop 凍結、resume 後下一輪補上（rising edge
  照觸發）；睡眠中被系統丟棄的 say＝已知一次性邊角（advisory 非保證
  ，行為記 skills/mail-watch/SKILL.md）。
- 不做 launchd（YAGNI）：skill 級 start/stop 控制；常駐排程承諾非
  本檔範圍。

決策表（per address；每輪）：
1. pendingCount > baseline → say 一次（文案見 notify_text）＋
   baseline=count。
2. pendingCount <= baseline → 靜默＋baseline=count（落下同步更新
   ——下次上升可再通知）。
3. state 缺席/損壞（冷啟）＝該 address baseline 0 起算＋pending>0
   通知一次。
4. face typed-failure：storage/fencing/wait-timeout/unknown＝該
   address 跳輪＋心跳失敗標記（baseline 不動）；usage/admission＝
   raise（daemon exit 2 fail-loud——壞配置不硬跑）。

CLI 面：start／stop／status（＋內部 daemon 子命令＝start 的 detach
目標，help 隱藏）。state＝`${XDG_STATE_HOME:-~/.local/state}/
ai-guide/duty-watch/`（watch.lock＋state.json＋daemon.log；0600
atomic 寫、路徑可注入——測試 tmp state dir，不碰真 store）。

測試形態：核心函式吃 injectable runner（fake dutymail 回固定 JSON）
與 injectable say（捕獲 argv；禁測試實播語音）——見
tests/test_duty_mail_watch.py（TC-W1..W9）。
"""

import argparse
import fcntl
import importlib.util
import os
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 唯讀 face 包裝／binary 解析／state 慣例（0600 atomic 寫）單一源＝
# scripts/duty_receive.py——以檔案路徑載入（自建模組名，不進
# sys.modules["duty_receive"]；與 hooks/duty_mailbox_monitor.py 同式）。
_CORE_SPEC = importlib.util.spec_from_file_location(
    "_duty_mail_watch_core", os.path.join(_REPO, "scripts", "duty_receive.py")
)
core = importlib.util.module_from_spec(_CORE_SPEC)
_CORE_SPEC.loader.exec_module(core)

TAG = "mail-watch"
DEFAULT_ADDRESS = "ai-guide-marshal"
DEFAULT_INTERVAL_SECONDS = 30
MIN_INTERVAL_SECONDS = 5
STATE_DIRNAME = "duty-watch"
LOCK_FILENAME = "watch.lock"
STATE_FILENAME = "state.json"
DAEMON_LOG_FILENAME = "daemon.log"
READY_WAIT_SECONDS = 3.0
STOP_GRACE_SECONDS = 5.0
SLEEP_SLICE_SECONDS = 0.5
START_POLL_SECONDS = 0.1
STOP_POLL_SECONDS = 0.2
SAY_TIMEOUT_SECONDS = 15
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_BAD_CONFIG = 2
EXIT_ALREADY_RUNNING = 3
SAY_VOICE = "Meijia"
SAY_RATE = "180"
# typed failure 分類：usage/admission＝配置面（壞配置不硬跑——fail-loud
# exit 2）；其餘（storage/fencing/wait-timeout/unknown）＝transient
# （跳輪＋心跳標記，不崩潰）。
FAIL_LOUD_CLASSES = frozenset({"usage", "admission"})

# 本進程 spawn 的 daemon 持握（防 Popen GC ResourceWarning；cmd_stop
# 確認退出後 best-effort 回收）。
_spawned_daemons: list[subprocess.Popen] = []


# ── state 路徑（XDG state／ai-guide/duty-watch；可注入）───────────────


def state_base_dir(base_dir=None):
    """state 目錄（base_dir 可注入——測試 tmp state dir，不碰真 store）。"""
    if base_dir is not None:
        return base_dir
    root = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    return os.path.join(root, "ai-guide", STATE_DIRNAME)


def lock_path(base_dir=None):
    return os.path.join(state_base_dir(base_dir), LOCK_FILENAME)


def state_file_path(base_dir=None):
    return os.path.join(state_base_dir(base_dir), STATE_FILENAME)


# ── singleton 狀態鎖（flock；crash 自動釋放＝stale 偵測免費）───────────


def try_lock(path):
    """非阻塞 flock → fd | None（None＝鎖被持——singleton 訊號）。

    開檔失敗（權限等）OSError 原樣傳出——無鎖即無 single-instance 保證，
    fail-loud 寧崩不靜默。
    """
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return None
    return fd


def _pid_from_state(path):
    """state.json 的 daemon pid → int | None（缺席/形漂移＝None）。"""
    doc = core.load_state(path)
    pid = doc.get("pid") if isinstance(doc, dict) else None
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return None
    return pid


def _reap_registered(pid):
    """best-effort 回收本進程 spawn 的 daemon（僅在確認退出後呼叫）。"""
    for proc in _spawned_daemons[:]:
        if proc.pid == pid:
            try:
                proc.wait(timeout=1.0)
            except Exception:  # best-effort 回收——不擋 stop 回報
                pass
            _spawned_daemons.remove(proc)
            return


# ── 通知面（say 慣例：Meijia 180＋中性句 ≤20 字＋無稱謂）──────────────


def notify_text(address, count):
    """say 文案——中性句模板「<label> 信箱有 N 封新信待判讀」（label＝
    address 去 -marshal 尾；無稱謂——不製造稱謂清單第三份同步副本）。"""
    label = address.removesuffix("-marshal")
    return f"{label} 信箱有 {count} 封新信待判讀"


def say_argv(text):
    """say 慣例 argv（EP invariant 6）：`say -v Meijia -r 180`。"""
    return ["say", "-v", SAY_VOICE, "-r", SAY_RATE, text]


def _default_say(argv):
    """真實 say 呼叫（無 shell）；失敗 raise（fail-soft 由 poll_round
    吸收——log 續跑）。"""
    proc = subprocess.run(
        argv, capture_output=True, text=True,
        timeout=SAY_TIMEOUT_SECONDS, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"say exit {proc.returncode}：{(proc.stderr or '').strip()[:120]}"
        )


# ── 唯讀查詢（單 face：receive status → pendingCount）─────────────────


def _pending_count(runner, address):
    """`receive status --address <a>` → pendingCount（非負整數）。

    pendingCount 形漂移 raise（shape-drift——交 fail-soft 跳輪路徑，
    禁靜默歸零）。
    """
    result = core.receive_status(runner, address)
    count = result.get("pendingCount")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise core.DutymailFaceError(
            "shape-drift", "unknown",
            f"receive status pendingCount 非非負整數：{result!r}", False, 0,
        )
    return count


def _entry_baseline(entries, address):
    """該 address baseline → int | None（無紀錄/形漂移＝None＝冷啟）。"""
    entry = entries.get(address)
    if not isinstance(entry, dict):
        return None
    value = entry.get("baseline")
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return None
    return value


# ── daemon loop 核心：一輪輪詢（edge 判定＋心跳 atomic 寫）─────────────


def poll_round(state, addresses, runner, say, state_file, now=None):
    """一輪輪詢（決策表見 module docstring）→ notified list[(address,
    count)]。

    每輪：逐 address 唯讀 `receive status` → edge 判定 → say（fail-soft
    ：baseline 已更新不回滾、不重試本輪）→ 心跳 atomic 0600 寫
    （last_poll_at／per-address last_seen／失敗輪標記）。fail-loud
    typed failure（usage/admission）raise——由 daemon loop 轉 exit 2
    （壞配置不硬跑）。
    """
    moment = now if now is not None else time.time()
    entries = state.get("addresses")
    if not isinstance(entries, dict):
        entries = {}
        state["addresses"] = entries
    notified = []
    failed = False
    for address in addresses:
        try:
            count = _pending_count(runner, address)
        except core.DutymailFaceError as exc:
            if exc.error_class in FAIL_LOUD_CLASSES:
                raise  # usage/admission——壞配置 fail-loud
            failed = True
            print(
                f"[{TAG}] {address} fail-soft 跳輪：{exc}", file=sys.stderr
            )
            continue
        baseline = _entry_baseline(entries, address)
        if baseline is None:
            baseline = 0  # 冷啟（state 缺席/損壞）——baseline 0 起算
        if count > baseline:
            try:
                say(say_argv(notify_text(address, count)))
            except Exception as exc:  # say 失敗 fail-soft——log 續跑
                print(
                    f"[{TAG}] say 失敗（fail-soft 續跑，不重試本輪——殘缺"
                    f"通知由冷啟/stale 週期補）：{exc!r}",
                    file=sys.stderr,
                )
            notified.append((address, count))
        entries[address] = {"baseline": count, "last_seen": count}
    state["last_poll_at"] = moment
    state["last_round_failed"] = failed
    core.save_state(state_file, state)
    return notified


class _StopFlag:
    """SIGTERM 旗標——handler 只翻旗（loop 於中斷點乾淨退出）。"""

    def __init__(self):
        self.stop = False


def _interruptible_sleep(seconds, flag):
    """分片睡（≤0.5s/片）——SIGTERM 後 ≤一片內醒來退出。"""
    deadline = time.monotonic() + seconds
    while not flag.stop:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(SLEEP_SLICE_SECONDS, remaining))


def run_daemon(addresses, interval, base_dir=None, runner=None, say=None):
    """daemon 主迴圈：取 flock → 寫 ready state → loop（poll→sleep）→
    SIGTERM 乾淨退。

    鎖被持＝single-instance 拒絕（exit 3 帶現 PID）；成功＝寫 state.json
    （pid＋started_at）後進 loop（starter 以 state.json pid 就位為 ready
    信號）。退出時 fd 關＝鎖自動釋放、state.json 保留（stop 不刪——
    restart 後 edge 邏輯自然接手）。
    """
    runner = runner if runner is not None else core._default_runner
    say = say if say is not None else _default_say
    spath = state_file_path(base_dir)
    fd = try_lock(lock_path(base_dir))
    if fd is None:
        pid = _pid_from_state(spath)
        print(
            f"[{TAG}] single-instance 拒絕：already running"
            f"（pid {pid if pid is not None else 'unknown'}）",
            file=sys.stderr,
        )
        return EXIT_ALREADY_RUNNING
    state = core.load_state(spath)
    if not isinstance(state, dict):
        state = {}  # 冷啟（state 缺席/損壞）
    if not isinstance(state.get("addresses"), dict):
        state["addresses"] = {}
    state["pid"] = os.getpid()
    state["started_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    state["interval"] = interval
    core.save_state(spath, state)  # ready 信號（state.json pid 就位）
    flag = _StopFlag()

    def _on_sigterm(_signum, _frame):
        flag.stop = True

    signal.signal(signal.SIGTERM, _on_sigterm)
    try:
        while not flag.stop:
            try:
                poll_round(state, addresses, runner, say, spath)
            except core.DutymailFaceError as exc:
                print(
                    f"[{TAG}] fail-loud（壞配置不硬跑）：{exc}",
                    file=sys.stderr,
                )
                return EXIT_BAD_CONFIG
            _interruptible_sleep(interval, flag)
    finally:
        try:
            os.close(fd)  # fd 關＝flock 自動釋放；state.json 保留
        except OSError:
            pass
    return EXIT_OK


# ── start／stop／status（subcommand 實作）─────────────────────────────


def daemon_argv(addresses, interval, base_dir=None):
    """start 的 detach 目標 argv（內部 daemon 子命令）。"""
    argv = [sys.executable, os.path.abspath(__file__), "daemon"]
    for address in addresses:
        argv += ["--address", address]
    argv += ["--interval", str(interval), "--state-dir", state_base_dir(base_dir)]
    return argv


def cmd_start(addresses, interval, base_dir=None):
    """啟動 daemon：Popen detach（start_new_session）＋等 ready 信號
    （state.json pid 就位，bounded 3s）再回報。

    快速預檢鎖（被持＝already running 拒絕、exit 3 帶現 PID）；最終
    互斥仍由 daemon 自取 flock 仲裁（預檢後 race 由 daemon 擋）。
    daemon stdout/stderr 落 state 目錄 daemon.log（靜默死亡 postmortem
    面——status 證活是正道，log 是驗屍）。
    """
    lpath = lock_path(base_dir)
    spath = state_file_path(base_dir)
    probe = try_lock(lpath)
    if probe is None:
        pid = _pid_from_state(spath)
        print(
            f"[{TAG}] start 拒絕：already running"
            f"（pid {pid if pid is not None else 'unknown'}）",
            file=sys.stderr,
        )
        return EXIT_ALREADY_RUNNING
    os.close(probe)  # 立即釋放——真正互斥由 daemon 自取
    log_path = os.path.join(state_base_dir(base_dir), DAEMON_LOG_FILENAME)
    with open(log_path, "ab") as log:
        proc = subprocess.Popen(
            daemon_argv(addresses, interval, base_dir),
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
        )
    _spawned_daemons.append(proc)
    deadline = time.monotonic() + READY_WAIT_SECONDS
    while time.monotonic() < deadline:
        state = core.load_state(spath)
        if state and state.get("pid") == proc.pid:
            print(
                f"[{TAG}] started（pid {proc.pid}；addresses "
                f"{','.join(addresses)}；interval {interval}s；"
                f"state {spath}）"
            )
            return EXIT_OK
        if proc.poll() is not None:
            break  # daemon 早死（race 輸鎖／壞配置 fail-loud）
        time.sleep(START_POLL_SECONDS)
    print(
        f"[{TAG}] start 失敗：daemon 未就緒（exit {proc.poll()}；"
        f"log {log_path}）",
        file=sys.stderr,
    )
    return EXIT_FAIL


def cmd_stop(base_dir=None):
    """停止 daemon——驗鎖不盲殺。

    鎖可取＝無 daemon：清 stale runtime 殘留（pid/started_at；baseline
    保留）回報 clean-stale。鎖被持＝讀 state.json pid → SIGTERM →
    bounded grace（5s）內鎖釋放＝成功；未退＝回報失敗（不升級
    SIGKILL——留 human）。
    """
    lpath = lock_path(base_dir)
    spath = state_file_path(base_dir)
    probe = try_lock(lpath)
    if probe is not None:
        os.close(probe)
        state = core.load_state(spath)
        if isinstance(state, dict) and state.get("pid") is not None:
            state.pop("pid", None)
            state.pop("started_at", None)
            core.save_state(spath, state)  # 清 stale 殘留；baseline 保留
            print(
                f"[{TAG}] 無 daemon——清 stale 殘留（clean-stale；"
                f"baseline 保留：{spath}）"
            )
        else:
            print(f"[{TAG}] 無 daemon（clean；state {spath}）")
        return EXIT_OK
    pid = _pid_from_state(spath)
    if pid is None:
        print(
            f"[{TAG}] stop 失敗：鎖被持但 state 無有效 pid——留 human 處置",
            file=sys.stderr,
        )
        return EXIT_FAIL
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass  # 剛好退出——仍以鎖釋放確認
    except PermissionError as exc:
        print(
            f"[{TAG}] stop 失敗：無權限對 pid {pid} 發訊號（{exc!r}）",
            file=sys.stderr,
        )
        return EXIT_FAIL
    deadline = time.monotonic() + STOP_GRACE_SECONDS
    released = False
    while time.monotonic() < deadline:
        probe = try_lock(lpath)
        if probe is not None:
            os.close(probe)
            released = True
            break
        time.sleep(STOP_POLL_SECONDS)
    if not released:
        print(
            f"[{TAG}] stop 失敗：pid {pid} 於 {STOP_GRACE_SECONDS:.0f}s 內"
            f"未退出（不升級 SIGKILL——留 human）",
            file=sys.stderr,
        )
        return EXIT_FAIL
    _reap_registered(pid)
    print(f"[{TAG}] stopped（pid {pid} 退出；state.json 保留：{spath}）")
    return EXIT_OK


def pid_alive(pid):
    """kill(pid, 0) 探測——ProcessLookupError＝死；PermissionError＝存在
    但非本 user（仍視為 alive）。"""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def cmd_status(base_dir=None, addresses=None, runner=None):
    """唯讀證活報告（可隨時跑）：lock 持有態＋PID 活性（kill(pid,0)）＋
    last_poll_at 新鮮度（> interval×3＝stale-heartbeat 警告）＋
    per-address baseline＋現值 pendingCount（一發 live probe）。"""
    runner = runner if runner is not None else core._default_runner
    spath = state_file_path(base_dir)
    state = core.load_state(spath)
    state = state if isinstance(state, dict) else {}
    probe = try_lock(lock_path(base_dir))
    lock_held = probe is None
    if probe is not None:
        os.close(probe)
    pid = state.get("pid")
    if lock_held:
        alive = pid_alive(pid)
        print(
            f"[{TAG}] daemon：running（pid {pid}；process "
            f"{'alive' if alive else 'dead——鎖在但進程不在（邊角）'}）"
        )
    else:
        print(f"[{TAG}] daemon：not running（lock free；state {spath}）")
    interval = state.get("interval")
    if (
        not isinstance(interval, int) or isinstance(interval, bool)
        or interval < MIN_INTERVAL_SECONDS
    ):
        interval = DEFAULT_INTERVAL_SECONDS
    last_poll = state.get("last_poll_at")
    if isinstance(last_poll, (int, float)) and not isinstance(last_poll, bool):
        age = max(0.0, time.time() - last_poll)
        threshold = interval * 3
        mark = (
            "stale-heartbeat（>interval×3 未心跳——daemon 可能凍結/sleep）"
            if age > threshold
            else "fresh"
        )
        print(
            f"[{TAG}] heartbeat：last_poll {age:.0f}s 前（{mark}；"
            f"threshold {threshold}s）"
        )
    entries = state.get("addresses")
    entries = entries if isinstance(entries, dict) else {}
    if addresses is None:
        addresses = list(entries) or [DEFAULT_ADDRESS]
    for address in addresses:
        entry = entries.get(address)
        baseline = entry.get("baseline") if isinstance(entry, dict) else None
        try:
            pending = _pending_count(runner, address)
        except core.DutymailFaceError as exc:
            print(
                f"[{TAG}] {address}：baseline={baseline} "
                f"pending=？（live probe 失敗：{exc}）"
            )
        else:
            print(
                f"[{TAG}] {address}：baseline={baseline} "
                f"pending={pending}（live probe）"
            )
    return EXIT_OK


# ── CLI 面（模組＋subcommand CLI；start／stop／status＋內部 daemon）────


def _interval_arg(raw):
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"非整數秒：{raw!r}") from exc
    if value < MIN_INTERVAL_SECONDS:
        raise argparse.ArgumentTypeError(
            f"下限 {MIN_INTERVAL_SECONDS}s（得 {value}s）"
        )
    return value


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "mail-watch：machine-level dutymail 信件 watcher（AIR-265——"
            "唯讀 receive status 輪詢＋rising edge say advisory；flock "
            "singleton）"
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser(
        "start", help="啟動 daemon（detach＋等 ready；singleton by flock）"
    )
    start.add_argument(
        "--address", action="append", metavar="ALIAS",
        help=f"監看門牌（可重複；預設 {DEFAULT_ADDRESS}）",
    )
    start.add_argument(
        "--interval", type=_interval_arg, default=DEFAULT_INTERVAL_SECONDS,
        metavar="S",
        help=f"輪詢間隔秒（預設 {DEFAULT_INTERVAL_SECONDS}、下限 "
             f"{MIN_INTERVAL_SECONDS}）",
    )
    start.add_argument(
        "--state-dir", default=None, metavar="DIR",
        help="state 目錄覆寫（預設 XDG state／~/.local/state；測試注入）",
    )
    stop = sub.add_parser(
        "stop", help="停止 daemon（驗鎖不盲殺；state.json 保留）"
    )
    stop.add_argument(
        "--state-dir", default=None, metavar="DIR", help="state 目錄覆寫"
    )
    status = sub.add_parser(
        "status", help="證活＋新鮮＋baseline＋現值（唯讀、可隨時跑）"
    )
    status.add_argument(
        "--address", action="append", metavar="ALIAS",
        help="live probe 門牌（可重複；預設 state 內清單→預設門牌）",
    )
    status.add_argument(
        "--state-dir", default=None, metavar="DIR", help="state 目錄覆寫"
    )
    daemon = sub.add_parser(
        "daemon", help=argparse.SUPPRESS  # start 的內部 detach 目標
    )
    daemon.add_argument("--address", action="append", metavar="ALIAS")
    daemon.add_argument(
        "--interval", type=_interval_arg, default=DEFAULT_INTERVAL_SECONDS,
        metavar="S",
    )
    daemon.add_argument(
        "--state-dir", default=None, metavar="DIR"
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.command == "start":
        return cmd_start(
            args.address or [DEFAULT_ADDRESS], args.interval, args.state_dir
        )
    if args.command == "stop":
        return cmd_stop(args.state_dir)
    if args.command == "status":
        return cmd_status(args.state_dir, args.address)
    return run_daemon(
        args.address or [DEFAULT_ADDRESS], args.interval, args.state_dir
    )


if __name__ == "__main__":
    raise SystemExit(main())
