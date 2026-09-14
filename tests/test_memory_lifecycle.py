"""Memory 生命周期工具鏈測試（generator 投影 / MEMORY.md 手寫 gate / Stop 重生成推導）。

三件套行為錨點：索引生成 gate 分級（22,500 字元/190 行 fail-loud——09-05 S1（AIR-25）
CC 式：超限**索引照寫出**＋exit 1＋行動訊息（官方 memory.md:401-403「write still
succeeds + error telling Claude to rewrite」——拒寫會停滯索引＝新條目不可見＝召回斷裂；
`--check` 仍不寫）與 frontmatter 解析、手寫攔截
＋條目寫入治理（desc>100/body 膨脹>12,000 硬擋、收斂放行）的 self-gating 條件、
跨 harness memory 目錄推導——Claude 端底線也轉 dash 的專案名
編碼陷阱與 ZCode 端 basename-sha256 命名皆以本機真實目錄名為錨（hash 是路徑字串的
純函數，跨機器成立）。
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from conftest import REPO_ROOT, load_module

ASSET_REL = "skills/memory-audit/scripts/generate_index.py"
generator = load_module(ASSET_REL)
block_memory = load_module("hooks/block-memory-index-write.py")
regen = load_module("hooks/memory-index-regen.py")

ASSET = REPO_ROOT / ASSET_REL


def make_pool(tmp_path: Path, n: int = 1, desc: str | None = None) -> Path:
    """建 fixture memory 池：裝 generator + n 個合規條目檔（desc 覆寫供 CJK gate 測試）。"""
    gen = tmp_path / "_generate_index.py"
    shutil.copy(ASSET, gen)
    for i in range(n):
        description = desc if desc is not None else f"條目 {i:03d} 描述"
        (tmp_path / f"proj-{i:03d}.md").write_text(
            "---\n"
            f"name: proj-{i:03d}\n"
            f"description: {description}\n"
            "metadata:\n"
            "  type: project\n"
            "---\n"
            "body\n",
            encoding="utf-8",
        )
    return tmp_path


# ---------------------------------------------------------------------------
# generate_index：frontmatter 解析（頂層 type / metadata.type / 引號剝除）
# ---------------------------------------------------------------------------


def test_parse_frontmatter_top_level_type():
    fm = generator.parse_frontmatter(
        "---\ntype: user\nname: a\ndescription: d\n---\nbody"
    )
    assert fm["type"] == "user" and fm["name"] == "a" and fm["description"] == "d"


def test_parse_frontmatter_metadata_type():
    fm = generator.parse_frontmatter(
        "---\nname: a\ndescription: d\nmetadata:\n  type: project\n---\n"
    )
    assert fm["metadata.type"] == "project"


def test_parse_frontmatter_quotes_stripped():
    fm = generator.parse_frontmatter('---\ndescription: "quoted desc"\n---\n')
    assert fm["description"] == "quoted desc"


def test_parse_frontmatter_absent():
    assert generator.parse_frontmatter("no frontmatter here") == {}


# ---------------------------------------------------------------------------
# generate_index：E2E（subprocess 跑部署形態的 script 檔）
# ---------------------------------------------------------------------------


def test_generator_e2e_writes_index(tmp_path):
    pool = make_pool(tmp_path, n=2)
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    idx = (pool / "MEMORY.md").read_text(encoding="utf-8")
    assert "proj-000" in idx and "proj-001" in idx
    assert "禁手寫" in idx  # 投影聲明 header
    assert "## Project" in idx


def test_generator_e2e_check_does_not_write(tmp_path):
    pool = make_pool(tmp_path, n=1)
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0
    assert not (pool / "MEMORY.md").exists()


def test_generator_e2e_gate_fail_loud(tmp_path):
    """SM-1：超限（n=200 > 190 行 gate）→ 索引**照寫出**＋exit 1＋行動訊息。

    09-05 S1（AIR-25）gate 失敗模式改 CC 式：拒寫會讓索引停滯、新條目對未來
    session 不可見（召回斷裂，flash-forensic 條目實證）——寫出（投影新鮮）＋
    fail-loud 行動訊息（命令當下 session 縮池）才是正確失敗模式。
    """
    pool = make_pool(tmp_path, n=200)
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 1
    assert "[FAIL]" in r.stdout
    assert "merge or drop" in r.stdout  # 行動訊息（官方 error telling to rewrite）
    idx_path = pool / "MEMORY.md"
    assert idx_path.exists()  # 照寫出——不停滯
    assert "proj-199" in idx_path.read_text(encoding="utf-8")  # 完整索引（尾條目在場）


def test_generator_e2e_over_limit_check_does_not_write(tmp_path):
    """SM-2：超限時 --check 仍不寫入——寫出動作須 `if not check_only` guard。

    超限 gate 分支在 check_only 分支之前（共用 return 1 路徑），無 guard 照字面
    實作會讓 --check 也寫入＝違反其零副作用語義（既有 check_does_not_write
    是未超限 case，此處釘超限邊界）。
    """
    pool = make_pool(tmp_path, n=200)
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 1
    assert "[FAIL]" in r.stdout
    assert not (pool / "MEMORY.md").exists()


def test_generator_e2e_byte_gate(tmp_path):
    """SM-3：CJK 重池——chars/lines gate 內、bytes 破 24,000 → info 縱深預警不擋寫入。

    80 條 × 130 CJK 字 description：chars ≈ 10,418（<22,500）、bytes ≈ 26,464（>24,000）
    ——bytes 非任何端實際截斷線（兩端皆 25,000 chars、量 UTF-16 length）；info 為
    縱深預警（CJK 一字 3B 提前折射），ZCode 主力場景照常寫入（2026-09-03 裁決「zcode 優先」）。
    """
    pool = make_pool(tmp_path, n=80, desc="深" * 130)
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0
    assert "[INFO]" in r.stdout
    assert "25,000 chars" in r.stdout
    assert (pool / "MEMORY.md").exists()


def test_generator_e2e_chars_gate(tmp_path):
    """SM-9：chars gate 邊界——chars 破 22,500 而 lines 未超 → fail-loud（chars 路徑錨）。

    178 條 × desc 130 CJK（截 100）：chars ≈ 23,060（>22,500）、lines = 184（<190）
    ——gate_fail_loud（n=200）兩 gate 皆破，chars-only 邊界由本測試釘住：gate 值 typo 或
    再調整（09-03 18,500→22,500）時有紅燈保護。
    """
    pool = make_pool(tmp_path, n=178, desc="深" * 130)
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 1
    assert "[FAIL]" in r.stdout
    assert "chars" in r.stdout
    assert (pool / "MEMORY.md").exists()  # S1：chars-only 超限同樣照寫出（不停滯）


def test_generator_stale_tmp_aged_removed(tmp_path):
    """SM-8：aged 殘檔（mtime>60s）在寫入模式被清除。"""
    pool = make_pool(tmp_path, n=1)
    stale = pool / "MEMORY.md.999.tmp"
    stale.write_text("debris", encoding="utf-8")
    old = time.time() - 120
    os.utime(stale, (old, old))
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0
    assert not stale.exists()


def test_generator_fresh_tmp_not_deleted(tmp_path):
    """R1 回歸鎖：新鮮 tmp（in-flight 模擬）不被 cleanup 誤殺——並行安全。"""
    pool = make_pool(tmp_path, n=1)
    fresh = pool / "MEMORY.md.12345.tmp"
    fresh.write_text("in-flight", encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0
    assert fresh.exists()


def test_generator_check_mode_no_fs_side_effects(tmp_path):
    """I1：--check 只驗證——連 aged 殘檔都不清、不寫索引。"""
    pool = make_pool(tmp_path, n=1)
    stale = pool / "MEMORY.md.999.tmp"
    stale.write_text("debris", encoding="utf-8")
    old = time.time() - 120
    os.utime(stale, (old, old))
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0
    assert stale.exists()
    assert not (pool / "MEMORY.md").exists()


def test_generator_concurrent_smoke(tmp_path):
    """SM-2：兩 process 並行同池——unique tmp 使交錯無害，兩者皆 exit 0。

    行為鎖（修復後確定性通過；修復前固定檔名下為機率性交錯失敗——本測試
    與 fresh-tmp 鎖共同釘住併發語義）。
    """
    pool = make_pool(tmp_path, n=5)
    procs = [
        subprocess.Popen(
            [sys.executable, str(pool / "_generate_index.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(2)
    ]
    outs = [p.communicate() for p in procs]
    assert all(p.returncode == 0 for p in procs), outs
    idx = (pool / "MEMORY.md").read_text(encoding="utf-8")
    assert "proj-004" in idx
    assert not list(pool.glob("MEMORY.md.*.tmp"))


# ---------------------------------------------------------------------------
# block-memory-index-write：手寫攔截 self-gating
# ---------------------------------------------------------------------------


def test_block_memory_violation_with_generator():
    assert block_memory.is_index_violation("/x/memory/MEMORY.md", True)


def test_block_memory_ok_no_generator():
    """self-gating：同目錄沒裝 generator 的專案不攔（opt-in）。"""
    assert not block_memory.is_index_violation("/x/memory/MEMORY.md", False)


def test_block_memory_ok_other_file():
    assert not block_memory.is_index_violation("/x/memory/some-entry.md", True)


def test_block_memory_violation_relative_path():
    assert block_memory.is_index_violation("MEMORY.md", True)


# ---------------------------------------------------------------------------
# block-memory-index-write：條目寫入治理（subprocess 餵 stdin JSON——hook 真實形態）
# ---------------------------------------------------------------------------

HOOK = REPO_ROOT / "hooks" / "block-memory-index-write.py"


def run_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )


def hook_payload(tool: str, file_path: Path, **kw) -> dict:
    ti = {"file_path": str(file_path)}
    ti.update(kw)
    return {"tool_name": tool, "tool_input": ti}


def test_entry_write_desc_overlong_blocked(tmp_path):
    """desc 130 chars（>100）→ exit 2；語義：索引行原料超額在寫入端擋。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "fat-desc.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content="---\nname: fat-desc\ndescription: "
            + "長" * 130
            + "\nmetadata:\n  type: project\n---\nbody\n",
        )
    )
    assert r.returncode == 2
    assert "description" in r.stderr


def test_entry_write_body_overlimit_blocked(tmp_path):
    """既有條目 Write 覆寫 13,000 chars（>12,000，desc 合規）→ exit 2——膨脹治理管既有檔；
    新建檔的等價場景由新建閘（3,000）先攔，見 test_entry_write_new_entry_overlimit_blocked。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "fat-body.md"
    target.write_text(
        "---\nname: fat-body\ndescription: 合規短述\nmetadata:\n  type: project\n---\n"
        + "x" * 11_000,
        encoding="utf-8",
    )
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content="---\nname: fat-body\ndescription: 合規短述\nmetadata:\n  type: project\n---\n"
            + "x" * 13_000,
        )
    )
    assert r.returncode == 2
    assert "12,000" in r.stderr


def test_entry_write_within_limits_allowed(tmp_path):
    """合規 Write（desc 短、body <12,000）→ exit 0。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "ok-entry.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content="---\nname: ok-entry\ndescription: 合規短述\nmetadata:\n  type: project\n---\nbody\n",
        )
    )
    assert r.returncode == 0


def test_entry_write_new_entry_overlimit_blocked(tmp_path):
    """新建條目（target 不存在）content >3,000 → exit 2——寫入當下即蒸後形。

    09-06 user 拍板「不要寫一堆廢話後來再 audit」：新條目直寫敘事流水
    （timeline/過程/commit 清單）是池膨脹主入口——12K 膨脹治理對 cur=0 的
    新建檔案無約束力，此閘補真空。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "new-fat-entry.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content="---\nname: new-fat-entry\ndescription: 合規短述\nmetadata:\n  type: project\n---\n"
            + "y" * 3_500,
        )
    )
    assert r.returncode == 2
    assert "3,000" in r.stderr


def test_entry_rewrite_existing_not_new_entry_gate(tmp_path):
    """既有條目 Write 覆寫（cluster merge 收斂/維護場景，cur>0）不走新建閘——仍走 12K 膨脹治理。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "existing-entry.md"
    target.write_text(
        "---\nname: existing-entry\ndescription: 合規短述\nmetadata:\n  type: project\n---\n"
        + "z" * 4_500,
        encoding="utf-8",
    )
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content="---\nname: existing-entry\ndescription: 合規短述\nmetadata:\n  type: project\n---\n"
            + "z" * 5_000,
        )
    )
    assert r.returncode == 0


def test_entry_write_desc_commit_hash_blocked(tmp_path):
    """SM-3/SM-4（09-05 S2/AIR-25）：desc 含 commit hash（≤100 chars）→ exit 2
    ——內容契約獨立於長度契約；hash 屬 git log 可推導（官方 skip-derivable）。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "hash-desc.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content=(
                "---\nname: hash-desc\ndescription: 全弧完結含 commit 47aa89d 收案\n"
                "metadata:\n  type: project\n---\nbody\n"
            ),
        )
    )
    assert r.returncode == 2
    assert "hash" in r.stderr


def test_entry_write_body_hash_allowed(tmp_path):
    """反向：desc 合規、body 引 hash（歷史合法引用）→ exit 0——契約只約束 desc。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "body-hash.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content=(
                "---\nname: body-hash\ndescription: 合規短述\nmetadata:\n  type: project\n"
                "---\n落地於 commit 47aa89d，細節見 EP。\n"
            ),
        )
    )
    assert r.returncode == 0


def test_entry_edit_desc_commit_hash_blocked(tmp_path):
    """Edit 分支 desc hash 檢查（review F2）——new_string 含 description: 行帶
    commit hash → exit 2（與 Write 分支同契約；釘住 `desc and` guard 不被誤刪）。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "edit-hash.md"
    target.write_text(
        "---\nname: edit-hash\ndescription: 原始合規\nmetadata:\n  type: project\n---\nbody\n",
        encoding="utf-8",
    )
    r = run_hook(
        hook_payload(
            "Edit",
            target,
            old_string="description: 原始合規",
            new_string="description: 全弧完結含 commit 47aa89d 收案",
        )
    )
    assert r.returncode == 2
    assert "hash" in r.stderr


def test_entry_write_desc_commit_word_false_positive_allowed(tmp_path):
    """digit-lookahead 補強（mosaic 實戰案例）：desc 含「commit feedback」——
    "feedbac" 恰 7 個純字母 hex 字元，但無數字 → 放行（真 hash 7+ 碼全字母
    機率≈0.01%，誤擋合法 desc 的代價更高）。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "commit-word.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content=(
                "---\nname: commit-word\ndescription: git commit feedback 群——staging 陷阱與 mixed-tree 紀律\n"
                "metadata:\n  type: feedback\n---\nbody\n"
            ),
        )
    )
    assert r.returncode == 0


def test_entry_write_folded_desc_hash_passthrough(tmp_path):
    """F7 反例（EP review）：folded（>-）desc 含 hash → 放行——釘住「與長度檢查
    同界」承諾（folded 量到摺疊符號本身、desc 值抽取不到——既有品質洞邊界不擴大）。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "folded.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content=(
                "---\nname: folded\ndescription: >-\n"
                "  commit 47aa89d hidden in folded\nmetadata:\n  type: project\n---\nbody\n"
            ),
        )
    )
    assert r.returncode == 0


def test_entry_write_desc_bare_hash_blocked(tmp_path):
    """09-10 bare-hash 擴（mosaic 收案群「收案 93715b60a」繞過實證）：desc 含無前綴
    hash（7+ hex 且含數字與 a-f 字母）→ exit 2——與 commit-前綴分支同契約。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "bare-hash.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content=(
                "---\nname: bare-hash\ndescription: 控制台收案 93715b60a 卡 Done\n"
                "metadata:\n  type: project\n---\nbody\n"
            ),
        )
    )
    assert r.returncode == 2
    assert "hash" in r.stderr


def test_entry_edit_desc_bare_hash_blocked(tmp_path):
    """Edit 分支同契約：new_string 的 description 行帶 bare hash → exit 2。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "edit-bare-hash.md"
    target.write_text(
        "---\nname: edit-bare-hash\ndescription: 原始合規\nmetadata:\n  type: project\n---\nbody\n",
        encoding="utf-8",
    )
    r = run_hook(
        hook_payload(
            "Edit",
            target,
            old_string="description: 原始合規",
            new_string="description: 收案 d4f9e3ca4 整理",
        )
    )
    assert r.returncode == 2
    assert "hash" in r.stderr


def test_entry_write_desc_pure_digit_run_allowed(tmp_path):
    """邊界（文檔化殘餘）：純數字 7+ 串（緊湊日期 20260909）放行——bare 分支要求
    a-f 字母，漏全數字真 hash（~2-4%）歸夜間掃尾。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "digit-run.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content=(
                "---\nname: digit-run\ndescription: 版本 20260909 快照整理\n"
                "metadata:\n  type: project\n---\nbody\n"
            ),
        )
    )
    assert r.returncode == 0


def test_entry_write_desc_date_blocked(tmp_path):
    """09-10 M2（收案群「09-09」流入實證）：desc 含 MM-DD → exit 2——日期住 body／卡。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "date-desc.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content=(
                "---\nname: date-desc\ndescription: 09-09 控制台收案進度\n"
                "metadata:\n  type: project\n---\nbody\n"
            ),
        )
    )
    assert r.returncode == 2
    assert "日期" in r.stderr


def test_entry_write_desc_session_id_blocked(tmp_path):
    """09-10 M2：desc 含 sess_ → exit 2（sess_ 屬 DB 可推導，接續錨點留 body）。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "sess-desc.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content=(
                "---\nname: sess-desc\ndescription: 接續 sess_zzzz99 未完事項\n"
                "metadata:\n  type: project\n---\nbody\n"
            ),
        )
    )
    assert r.returncode == 2
    assert "session" in r.stderr


def test_entry_write_desc_version_dots_allowed(tmp_path):
    """反向：點號版號（v2.1——點斷 hex run）→ exit 0——日期閘不誤傷版號語彙。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "version-desc.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content=(
                "---\nname: version-desc\ndescription: 升級 v2.1 整理要點\n"
                "metadata:\n  type: project\n---\nbody\n"
            ),
        )
    )
    assert r.returncode == 0


def test_desc_gate_regex_boundaries():
    """三 pattern 邊界單元錨：全日期經 MM-DD 子串命中；字母前綴數字（S1-S4）
    因 \\b 不中；bare hash 同時要求數字與 a-f 字母。"""
    assert block_memory.DATE_RE.search("2026-09-10 全量重跑")
    assert not block_memory.DATE_RE.search("S1-S4 全鏈完成")
    assert block_memory.HASH_RE.search("收案 93715b60a")
    assert not block_memory.HASH_RE.search("版本 20260909 快照")
    assert block_memory.SESS_RE.search("接續 sess_740807c3")


def test_entry_edit_grow_overlimit_blocked(tmp_path):
    """既有 11,800 chars 檔 Edit +500（變大且超 12,000）→ exit 2——膨脹方向擋。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "growing.md"
    base = (
        "---\nname: growing\ndescription: 合規\nmetadata:\n  type: project\n---\n"
        + "y" * 11_700
    )
    target.write_text(base, encoding="utf-8")
    r = run_hook(
        hook_payload(
            "Edit",
            target,
            old_string="y" * 10,
            new_string="y" * 10 + "z" * 500,
        )
    )
    assert r.returncode == 2
    assert "膨脹" in r.stderr


def test_entry_edit_shrink_overlimit_file_allowed(tmp_path):
    """既有超大檔（13,000）收斂型 Edit（delta<0）→ exit 0——不卡 audit 收縮。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "shrinking.md"
    base = (
        "---\nname: shrinking\ndescription: 合規\nmetadata:\n  type: project\n---\n"
        + "y" * 12_900
    )
    target.write_text(base, encoding="utf-8")
    r = run_hook(
        hook_payload(
            "Edit",
            target,
            old_string="y" * 5_000,
            new_string="y" * 10,
        )
    )
    assert r.returncode == 0


def test_entry_edit_desc_overlong_blocked(tmp_path):
    """Edit 的 new_string 含 description: 行且值 >100 → exit 2。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "desc-edit.md"
    target.write_text(
        "---\nname: desc-edit\ndescription: 短\n---\nbody\n", encoding="utf-8"
    )
    r = run_hook(
        hook_payload(
            "Edit",
            target,
            old_string="description: 短",
            new_string="description: " + "長" * 130,
        )
    )
    assert r.returncode == 2


def test_entry_governance_self_gated(tmp_path):
    """同目錄無 generator → 條目寫入不攔（裝 script 即 opt-in，沿襲索引 gate 語義）。"""
    target = tmp_path / "plain-entry.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content="---\nname: plain\ndescription: " + "長" * 130 + "\n---\nbody\n",
        )
    )
    assert r.returncode == 0


def test_entry_write_desc_boundary_100_pass_101_blocked(tmp_path):
    """F6：desc 邊界值——恰 100 放行、101 擋（＝寫入紀律值；09-03 P1 對齊）。"""
    pool = make_pool(tmp_path, n=1)
    for n, expect in ((100, 0), (101, 2)):
        r = run_hook(
            hook_payload(
                "Write",
                pool / f"desc-{n}.md",
                content="---\nname: desc-{n}\ndescription: "
                + "長" * n
                + "\nmetadata:\n  type: project\n---\nbody\n".replace("{n}", str(n)),
            )
        )
        assert r.returncode == expect, f"desc={n}"


def test_entry_write_shrink_overlimit_file_allowed(tmp_path):
    """F2 行為錨：既有 13K 檔 Write 收斂到 12.5K（仍 >12,000 但變短）→ 放行。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "shrink.md"
    target.write_text(
        "---\nname: shrink\ndescription: 合規\nmetadata:\n  type: project\n---\n"
        + "y" * 12_900,
        encoding="utf-8",
    )
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content="---\nname: shrink\ndescription: 合規\nmetadata:\n  type: project\n---\n"
            + "y" * 12_500,
        )
    )
    assert r.returncode == 0


def test_entry_edit_replace_all_bloat_blocked(tmp_path):
    """F3 行為錨：replace_all 膨脹 = delta × occurrences——多處置換越線要擋。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "rep.md"
    body = ("y" * 10 + "\n") * 1_050
    target.write_text(
        "---\nname: rep\ndescription: 合規\nmetadata:\n  type: project\n---\n" + body,
        encoding="utf-8",
    )
    r = run_hook(
        hook_payload(
            "Edit",
            target,
            old_string="y" * 10,
            new_string="y" * 10 + "z" * 20,
            replace_all=True,
        )
    )
    assert r.returncode == 2


def test_truncate_threshold_cross_layer_alignment():
    """F4：generator 截斷線 == hook DESC_LIMIT（跨層單一源機械錨）。"""
    assert generator.TRUNCATE_DESC == block_memory.DESC_LIMIT


# ---------------------------------------------------------------------------
# memory-index-regen：跨 harness 目錄推導（本機真實目錄名為錨）
# ---------------------------------------------------------------------------


def test_sha16_anchor_ai_rules():
    # 錨：本機真實目錄 ~/.zcode/cli/memories/projects/ai-guide-91ff86777c287082（2026-09-14 改名 ai-guide；sha256(絕對路徑)前 16 碼）
    assert regen.sha16("/Users/ctai/Github/ai-guide") == "91ff86777c287082"


def test_claude_dir_underscore_trap():
    # 錨：Claude 專案名編碼把底線也轉 dash（mosaic_alpha → mosaic-alpha）
    d = regen.claude_memory_dir("/Users/ctai/Github/mosaic_alpha", Path("/H"))
    assert str(d) == "/H/.claude/projects/-Users-ctai-Github-mosaic-alpha/memory"


def test_zcode_dir_underscore_preserved():
    # 錨：ZCode basename 原樣保留底線＋dash＋sha16（對照真實目錄命名）
    d = regen.zcode_memory_dir("/Users/ctai/Github/mosaic_alpha", Path("/H"))
    assert (
        str(d) == "/H/.zcode/cli/memories/projects/mosaic_alpha-91db1aef2f9baec8/memory"
    )


def test_regen_runs_generator_once_with_symlink_dedupe(tmp_path):
    """ZCode 目錄 symlink → Claude 同一實體 pool：resolve() 去重只跑一次。"""
    zdir = regen.zcode_memory_dir("/Users/ctai/Github/ai-guide", tmp_path)
    zdir.mkdir(parents=True)
    make_pool(zdir, n=1)
    cdir = regen.claude_memory_dir("/Users/ctai/Github/ai-guide", tmp_path)
    cdir.parent.mkdir(parents=True)
    cdir.symlink_to(zdir)
    notes = regen.run_for_cwd("/Users/ctai/Github/ai-guide", tmp_path)
    assert len(notes) == 1
    assert (zdir / "MEMORY.md").exists()


def test_regen_skips_pool_without_generator(tmp_path):
    regen.zcode_memory_dir("/x/p", tmp_path).parent.mkdir(parents=True)
    assert regen.run_for_cwd("/x/p", tmp_path) == []


def test_regen_stale_copy_writes_skip_marker(tmp_path):
    """副本與資產源不符 → 跳過執行＋寫 _regen-skipped-stale。

    09-06 pending-decisions ③查證產出：byte 比對跳過是 by-design（信任邊界），
    但跳過路徑 stdout 不進 context＝靜默停滯——marker 讓停滯 fail-visible。"""
    zdir = regen.zcode_memory_dir("/Users/ctai/Github/ai-guide", tmp_path)
    zdir.mkdir(parents=True)
    make_pool(zdir, n=1)
    g = zdir / "_generate_index.py"
    g.write_text(g.read_text(encoding="utf-8") + "# stale\n", encoding="utf-8")
    notes = regen.run_for_cwd("/Users/ctai/Github/ai-guide", tmp_path)
    assert any("不符" in n for n in notes)
    assert not (zdir / "MEMORY.md").exists()  # 未執行 generator
    assert (zdir / "_regen-skipped-stale").exists()  # 停滯可見


def test_regen_fresh_run_clears_skip_marker(tmp_path):
    """副本相符成功執行 → 清 _regen-skipped-stale（殘留標記隨修復消失）。"""
    zdir = regen.zcode_memory_dir("/Users/ctai/Github/ai-guide", tmp_path)
    zdir.mkdir(parents=True)
    make_pool(zdir, n=1)
    (zdir / "_regen-skipped-stale").write_text("殘留\n", encoding="utf-8")
    regen.run_for_cwd("/Users/ctai/Github/ai-guide", tmp_path)
    assert (zdir / "MEMORY.md").exists()  # generator 有跑
    assert not (zdir / "_regen-skipped-stale").exists()


def test_generator_frontmatter_violation_fail_loud(tmp_path):
    """F-1②／AIR-27 CC 式：frontmatter 違規（缺 type）→ exit 1＋[FAIL] 含檔名
    ＋**壞條目跳過、合法條目照常寫出**——一個壞檔不再擋全部條目的投影
    （原拒寫＝停滯面比 size gate 更大，與「拒寫＝召回斷裂」原則自相矛盾）。
    """
    pool = make_pool(tmp_path, n=1)
    (tmp_path / "bad-entry.md").write_text(
        "---\nname: bad-entry\ndescription: 缺 type\n---\nbody\n", encoding="utf-8"
    )
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 1
    assert "bad-entry.md" in r.stdout
    idx_path = pool / "MEMORY.md"
    assert idx_path.exists()  # CC 式：合法條目照常投影
    idx = idx_path.read_text(encoding="utf-8")
    assert "proj-000" in idx  # 合法條目在場
    assert "bad-entry" not in idx  # 壞條目被跳過


def test_generator_frontmatter_violation_check_does_not_write(tmp_path):
    """AIR-27 對稱邊界：errs＋--check → 不寫入（--check 零副作用對兩種 gate 一致）。"""
    pool = make_pool(tmp_path, n=1)
    (tmp_path / "bad-entry.md").write_text(
        "---\nname: bad-entry\ndescription: 缺 type\n---\nbody\n", encoding="utf-8"
    )
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 1
    assert "bad-entry.md" in r.stdout
    assert not (pool / "MEMORY.md").exists()


def test_regen_skips_tampered_generator(tmp_path):
    """F2①：池內 generator 與資產源不符 → 跳過執行（防植入持久化執行鏈）。"""
    zdir = regen.zcode_memory_dir("/Users/ctai/Github/ai-guide", tmp_path)
    zdir.mkdir(parents=True)
    make_pool(zdir, n=1)
    (zdir / "_generate_index.py").write_text("# tampered\n", encoding="utf-8")
    notes = regen.run_for_cwd("/Users/ctai/Github/ai-guide", tmp_path)
    assert any("不符" in n for n in notes)
    assert not (zdir / "MEMORY.md").exists()


def test_regen_failure_marker_written_and_cleared(tmp_path):
    """F4①：generator 失敗→`_regen-failed` 標記；下次成功→清除。

    失敗場景用真實形態：generator 與資產 identical，但池內含 frontmatter
    違規條目 → generator 自身 fail-loud exit 1（偽造 failing generator 會被
    F2 的資產比對防護跳過、走不到 marker 路徑）。
    """
    zdir = regen.zcode_memory_dir("/x/proj", tmp_path)
    zdir.mkdir(parents=True)
    make_pool(zdir, n=1)
    bad = zdir / "bad-entry.md"
    bad.write_text("---\nname: bad\ndescription: 缺 type\n---\n", encoding="utf-8")
    regen.run_for_cwd("/x/proj", tmp_path)
    assert (zdir / "_regen-failed").exists()
    bad.unlink()
    regen.run_for_cwd("/x/proj", tmp_path)
    assert not (zdir / "_regen-failed").exists()
    assert (zdir / "MEMORY.md").exists()


def test_regen_skips_when_asset_source_missing(tmp_path, monkeypatch):
    """資產源缺席 → fail-closed：不執行池內 generator＋寫停滯 marker。

    信任邊界不該在無從驗證時蒸發（codex 09-06 審查 I-3：原設計資產缺場
    照舊執行＝把不可驗證狀態當可信訊號）。"""
    zdir = regen.zcode_memory_dir("/Users/ctai/Github/ai-guide", tmp_path)
    zdir.mkdir(parents=True)
    make_pool(zdir, n=1)
    monkeypatch.setattr(regen, "ASSET_SOURCE", tmp_path / "no-such-asset.py")
    notes = regen.run_for_cwd("/Users/ctai/Github/ai-guide", tmp_path)
    assert any("資產源缺席" in n for n in notes)
    assert not (zdir / "MEMORY.md").exists()  # 未執行 generator
    assert (zdir / "_regen-skipped-stale").exists()  # 停滯可見


# ---------------------------------------------------------------------------
# generate_index rank 排序（AIR-39 S1——type 四組 × rank 三層 × mtime 尾序）
# ---------------------------------------------------------------------------


def write_rank_entry(
    pool: Path, name: str, typ: str, rank_line=None, nested_rank=None
) -> Path:
    """寫一條 rank fixture：rank_line 為頂層 rank 行（如 "rank: hot"）；
    nested_rank 為 metadata 內 rank 值原文（如 '"hot"' 含引號——解析器巢狀不剝引號）。"""
    lines = ["---", f"name: {name}", f"description: {name} 描述"]
    if rank_line is not None:
        lines.append(rank_line)
    lines.append("metadata:")
    lines.append(f"  type: {typ}")
    if nested_rank is not None:
        lines.append(f"  rank: {nested_rank}")
    lines.append("---")
    lines.append("body")
    p = pool / f"{name}.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def test_parse_rank_defaults_and_quote_stripping():
    """parse_rank：缺省/invalid→core（永不進 errs）；巢狀帶引號值剝除；雙落點皆解析。"""
    assert generator.parse_rank({}) == generator.RANK_ORDER["core"]
    assert generator.parse_rank({"rank": "urgent"}) == generator.RANK_ORDER["core"]
    assert generator.parse_rank({"rank": "hot"}) == generator.RANK_ORDER["hot"]
    assert generator.parse_rank({"rank": "cold"}) == generator.RANK_ORDER["cold"]
    assert (
        generator.parse_rank({"metadata.rank": '"hot"'}) == generator.RANK_ORDER["hot"]
    )
    assert (
        generator.parse_rank({"metadata.rank": "core"}) == generator.RANK_ORDER["core"]
    )


def test_generator_rank_sorting_e2e(tmp_path):
    """S1 語義 E2E：type 四組序 × rank 三層 × 組內 mtime 新在前。

    fixture 以 os.utime 顯式設 mtime 差（防 flaky）；檔名字母序 ≠ 期望投影序
    （如 a-user-cold 字母首位但 rank cold 須沉 user 組尾）——排序未實作即紅燈。
    """
    pool = make_pool(tmp_path, n=0)
    write_rank_entry(pool, "a-user-cold", "user", "rank: cold")
    write_rank_entry(pool, "b-user-hot-old", "user", "rank: hot")
    write_rank_entry(pool, "c-user-hot-new", "user", "rank: hot")
    write_rank_entry(pool, "d-feedback-default", "feedback", None)
    write_rank_entry(pool, "e-feedback-core", "feedback", "rank: core")
    write_rank_entry(pool, "f-feedback-invalid", "feedback", "rank: urgent")
    write_rank_entry(pool, "g-project-nested-hot", "project", None, '"hot"')
    write_rank_entry(pool, "h-project-toplevel-cold", "project", "rank: cold")
    write_rank_entry(pool, "i-reference-cold", "reference", "rank: cold")
    base = time.time() - 1000
    mtimes = {
        "b-user-hot-old": base + 10,  # user/hot 舊 → hot 層尾
        "c-user-hot-new": base + 20,  # user/hot 新 → hot 層首
        "e-feedback-core": base + 30,  # feedback/core 最舊
        "d-feedback-default": base + 40,  # 缺省 core 與顯式 core 同層、按 mtime 居中
        "f-feedback-invalid": base + 50,  # invalid→core 最新 → core 層首
        "g-project-nested-hot": base + 60,  # 巢狀引號 hot
        "h-project-toplevel-cold": base + 70,  # 更新但 cold → 仍沉 hot 之後
        "i-reference-cold": base + 80,
        "a-user-cold": base + 900,  # 全池最新但 cold → 仍沉 user 組尾（rank 勝 mtime）
    }
    for stem, ts in mtimes.items():
        os.utime(pool / f"{stem}.md", (ts, ts))
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stdout
    idx = (pool / "MEMORY.md").read_text(encoding="utf-8")
    expected = [
        "c-user-hot-new",
        "b-user-hot-old",
        "a-user-cold",
        "f-feedback-invalid",
        "d-feedback-default",
        "e-feedback-core",
        "g-project-nested-hot",
        "h-project-toplevel-cold",
        "i-reference-cold",
    ]
    pos = [idx.index(stem) for stem in expected]
    assert pos == sorted(pos), expected
    sec = [idx.index(f"## {t}") for t in ("User", "Feedback", "Project", "Reference")]
    assert sec == sorted(sec)


def test_generator_rank_counts_line(tmp_path):
    """--check 輸出 rank 分層計數行；hot 超 1/3 附 WARN（AIR-39 SM-6 可觀測）。"""
    pool = make_pool(tmp_path, n=0)
    write_rank_entry(pool, "a-hot", "feedback", "rank: hot")
    write_rank_entry(pool, "b-core", "feedback", None)
    write_rank_entry(pool, "c-cold", "feedback", "rank: cold")
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stdout
    assert "rank 分層：hot=1 core=1 cold=1" in r.stdout
    assert "hot 佔比" not in r.stdout  # 1/3 未超＝無警示


def test_generator_rank_counts_warn(tmp_path):
    """hot 佔比超 1/3 時計數行附 WARN（rank 通膨可觀測）。"""
    pool = make_pool(tmp_path, n=0)
    for i in range(3):
        write_rank_entry(pool, f"hot-{i}", "feedback", "rank: hot")
    write_rank_entry(pool, "cold-0", "feedback", "rank: cold")
    r = subprocess.run(
        [sys.executable, str(pool / "_generate_index.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stdout
    assert "rank 分層：hot=3 core=0 cold=1" in r.stdout
    assert "hot 佔比超 1/3" in r.stdout


# ---------------------------------------------------------------------------
# generate_index B 形態（AIR-48 P3——_resident-set.md 清單檔 opt-in）
# ---------------------------------------------------------------------------


def make_resident_set(pool: Path, ids) -> Path:
    lines = ["# 常駐集合（顯式清單——rank 只排集合內順序）"]
    for i in ids:
        lines.append(f"- {i}")
    p = pool / "_resident-set.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def run_gen(pool: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(pool / "_generate_index.py"), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_parse_resident_set_line_forms():
    """清單解析：backtick（necessity-set 直拷）／list marker／裸 id 三形態＋註解跳過。"""
    text = (
        "# header comment\n"
        "\n"
        "`commit-consent`——commit 確認門。\n"
        "1. `feedback_verify-wt`——並行樹防護\n"
        "- feedback_evidence-over-claims\n"
        "project_session-topology\n"
    )
    assert generator.parse_resident_set(text) == [
        "commit-consent",
        "feedback_verify-wt",
        "feedback_evidence-over-claims",
        "project_session-topology",
    ]


def test_gate_chars_b_cross_layer():
    """B 形態 gate 常數錨：6,000（SKILL 層 1 prose 同值——AIR-48 P3 單一源）。"""
    assert generator.GATE_CHARS_B == 6_000


def test_b_form_renders_resident_and_inventory(tmp_path):
    """清單在場 → MEMORY.md＝常駐段＋Routing；_inventory.md＝全量投影。"""
    pool = make_pool(tmp_path, n=3)
    make_resident_set(pool, ["proj-000", "proj-002"])
    r = run_gen(pool)
    assert r.returncode == 0, r.stdout
    mem = (pool / "MEMORY.md").read_text(encoding="utf-8")
    assert "resident" in mem and "## Routing" in mem
    assert "proj-000" in mem and "proj-002" in mem
    assert "proj-001" not in mem  # 非常駐不進常駐面
    inv = (pool / "_inventory.md").read_text(encoding="utf-8")
    assert all(f"proj-00{i}" in inv for i in range(3))  # inventory 全量
    assert "流入率口徑（B）＝inventory chars" in r.stdout


def test_b_form_sm4_new_entry_grows_inventory_not_memory(tmp_path):
    """SM-4：新增非 resident 條目 → 常駐面不變、inventory 增長。"""
    pool = make_pool(tmp_path, n=2)
    make_resident_set(pool, ["proj-000"])
    assert run_gen(pool).returncode == 0
    mem_before = (pool / "MEMORY.md").read_text(encoding="utf-8")
    (pool / "proj-new.md").write_text(
        "---\nname: proj-new\ndescription: 新條目\nmetadata:\n  type: project\n---\nbody\n",
        encoding="utf-8",
    )
    r = run_gen(pool)
    assert r.returncode == 0, r.stdout
    assert (pool / "MEMORY.md").read_text(encoding="utf-8") == mem_before
    assert "proj-new" in (pool / "_inventory.md").read_text(encoding="utf-8")


def test_b_form_missing_entry_fail_loud(tmp_path):
    """R2 缺檔：清單 id 不存在 → exit 1＋MEMORY.md 保留上一份常駐面＋inventory 照寫。"""
    pool = make_pool(tmp_path, n=3)
    make_resident_set(pool, ["proj-000"])
    assert run_gen(pool).returncode == 0
    mem_before = (pool / "MEMORY.md").read_text(encoding="utf-8")
    make_resident_set(pool, ["proj-000", "ghost-entry"])
    r = run_gen(pool)
    assert r.returncode == 1
    assert "ghost-entry" in r.stdout
    assert (pool / "MEMORY.md").read_text(encoding="utf-8") == mem_before  # 保留舊面
    assert "proj-002" in (pool / "_inventory.md").read_text(encoding="utf-8")


def test_b_form_bad_frontmatter_fail_loud(tmp_path):
    """R2 壞 frontmatter：清單 id 對到壞 fm 條目（進 errs 不在 entries）→ exit 1＋保留舊面。"""
    pool = make_pool(tmp_path, n=2)
    (pool / "broken.md").write_text(
        "---\nname: broken\ndescription: 缺 type\n---\nbody\n", encoding="utf-8"
    )
    make_resident_set(pool, ["proj-000", "broken"])
    r = run_gen(pool)
    assert r.returncode == 1
    assert "broken" in r.stdout
    assert not (pool / "MEMORY.md").exists()  # 首跑即失敗——不發布常駐面


def test_b_form_rename_fail_loud(tmp_path):
    """R2 rename：條目 rename（檔名＋frontmatter name 同步改——夜間 merge/rename 真實形態）
    後清單未同步（舊 id 命中 0）→ exit 1＋保留舊面＋提示同步清單。"""
    pool = make_pool(tmp_path, n=2)
    make_resident_set(pool, ["proj-000", "proj-001"])
    assert run_gen(pool).returncode == 0
    mem_before = (pool / "MEMORY.md").read_text(encoding="utf-8")
    (pool / "proj-001.md").rename(pool / "proj-renamed.md")
    (pool / "proj-renamed.md").write_text(
        "---\nname: proj-renamed\ndescription: 條目 001 描述\nmetadata:\n"
        "  type: project\n---\nbody\n",
        encoding="utf-8",
    )
    r = run_gen(pool)
    assert r.returncode == 1
    assert "proj-001" in r.stdout
    assert (pool / "MEMORY.md").read_text(encoding="utf-8") == mem_before


def test_b_form_gate_6k_fail_loud(tmp_path):
    """B gate：常駐面 >6,000 chars → exit 1＋常駐面照寫出（CC 式不停滯——成員都在只是胖）。"""
    pool = make_pool(tmp_path, n=55, desc="深" * 100)
    make_resident_set(pool, [f"proj-{i:03d}" for i in range(55)])
    r = run_gen(pool)
    assert r.returncode == 1
    assert "[FAIL]" in r.stdout and "B gate" in r.stdout
    mem = (pool / "MEMORY.md").read_text(encoding="utf-8")
    assert "proj-054" in mem  # 照寫出（新鮮投影，不停滯）


def test_b_form_inventory_write_fail_keeps_memory(tmp_path):
    """R3 發布順序：inventory 寫入失敗（路徑被目錄佔用）→ 不切換常駐面＋marker＋exit 1。"""
    pool = make_pool(tmp_path, n=2)
    make_resident_set(pool, ["proj-000"])
    assert run_gen(pool).returncode == 0
    mem_before = (pool / "MEMORY.md").read_text(encoding="utf-8")
    (pool / "_inventory.md").unlink()
    (pool / "_inventory.md").mkdir()  # 佔住路徑——write tmp+replace 失敗
    r = run_gen(pool)
    assert r.returncode == 1
    assert "_inventory.md 寫入失敗" in r.stdout
    assert (pool / "MEMORY.md").read_text(encoding="utf-8") == mem_before
    assert (pool / "_inventory-write-failed").exists()


def test_b_form_inventory_write_fail_rerun_recovers(tmp_path):
    """R3 重跑恢復：障礙移除 → regen 成功 → marker 清除＋B 形態在場。"""
    pool = make_pool(tmp_path, n=2)
    make_resident_set(pool, ["proj-000"])
    assert run_gen(pool).returncode == 0
    (pool / "_inventory.md").unlink()
    (pool / "_inventory.md").mkdir()
    assert run_gen(pool).returncode == 1
    (pool / "_inventory.md").rmdir()  # 移除障礙
    r = run_gen(pool)
    assert r.returncode == 0, r.stdout
    assert not (pool / "_inventory-write-failed").exists()
    assert "resident" in (pool / "MEMORY.md").read_text(encoding="utf-8")
    assert "proj-001" in (pool / "_inventory.md").read_text(encoding="utf-8")


def test_b_form_check_zero_side_effects(tmp_path):
    """--check 零副作用（B 形態）：MEMORY.md 與 _inventory.md 皆不寫、連殘檔都不清。"""
    pool = make_pool(tmp_path, n=2)
    make_resident_set(pool, ["proj-000"])
    stale = pool / "_inventory.md.999.tmp"
    stale.write_text("debris", encoding="utf-8")
    old = time.time() - 120
    os.utime(stale, (old, old))
    r = run_gen(pool, "--check")
    assert r.returncode == 0, r.stdout
    assert not (pool / "MEMORY.md").exists()
    assert not (pool / "_inventory.md").exists()
    assert stale.exists()


def test_a_form_no_inventory_without_set(tmp_path):
    """A 形態回歸：無清單檔 → 不產 _inventory.md（形式選擇＝清單檔在場與否）。"""
    pool = make_pool(tmp_path, n=2)
    r = run_gen(pool)
    assert r.returncode == 0, r.stdout
    assert (pool / "MEMORY.md").exists()
    assert not (pool / "_inventory.md").exists()
    assert "resident" not in (pool / "MEMORY.md").read_text(encoding="utf-8")


def test_block_memory_inventory_write_blocked():
    """AIR-48 P3⑤：_inventory.md 手寫防護——B 形態全量投影同禁手寫。"""
    assert block_memory.is_index_violation("/x/memory/_inventory.md", True)
    assert block_memory.is_index_violation("_inventory.md", True)
    assert not block_memory.is_index_violation("/x/memory/_inventory.md", False)


# ---------------------------------------------------------------------------
# block-memory-index-write：③放置閘（新建條目非阻斷提醒——弧收案慣性實證）
# ---------------------------------------------------------------------------


def test_placement_gate_new_entry_reminded_but_allowed(tmp_path):
    """新建條目（檔不存在）→ stderr 注入六問指針＋exit 0（提醒不判斷、寫入照常）。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "brand-new.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content=(
                "---\nname: brand-new\ndescription: 合規短述一行鉤子\n"
                "metadata:\n  type: project\n---\n一句話事實。\n"
            ),
        )
    )
    assert r.returncode == 0
    assert "放置閘" in r.stderr
    assert "Hook Blocked" not in r.stderr


def test_placement_gate_existing_entry_no_reminder(tmp_path):
    """既有條目加段（多數寫入形態）→ 不觸發提醒（噪音可控）。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "proj-000.md"
    r = run_hook(hook_payload("Edit", target, old_string="body", new_string="body2"))
    assert r.returncode == 0
    assert "放置閘" not in r.stderr


def test_placement_gate_fires_before_hard_block(tmp_path):
    """新建＋desc 超限：提醒先印、硬閘後擋（exit 2）——兩訊息並存。"""
    pool = make_pool(tmp_path, n=1)
    target = pool / "fat-desc.md"
    r = run_hook(
        hook_payload(
            "Write",
            target,
            content="---\nname: fat-desc\ndescription: " + "長" * 130 + "\n---\nx\n",
        )
    )
    assert r.returncode == 2
    assert "放置閘" in r.stderr
    assert "description" in r.stderr


def test_placement_gate_no_generator_silent(tmp_path):
    """self-gating：無 generator 目錄 → 靜默放行（不提醒）。"""
    nogen = tmp_path / "nogen"
    nogen.mkdir()
    r = run_hook(hook_payload("Write", nogen / "new.md", content="x"))
    assert r.returncode == 0
    assert "放置閘" not in r.stderr
