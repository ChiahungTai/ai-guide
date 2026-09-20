# POC 實跑結果——AIR-149 S1 驗證策略 K1/K2（review F-5 補交付）

> 實跑時點：2026-09-20（本 worktree air-149）。兩 POC 均真機唯讀＋worktree
> `.agent-tmp/` 暫存，零真機寫入。原始完整輸出：worktree
> `.agent-tmp/poc-fd-lease-run.log`、`.agent-tmp/poc-three-surface-run.log`。

## K2：poc_fd_lease.py——lsof 對「靜默命令開 fd」的偵測實測

- exit code：0；5/5 PASS
- 場景：`sleep 120` stdout 重導檔案（fd 持開、零寫入）＝SM-2「長靜默工具
  呼叫」的機制模擬
- 結論：**fd lease 面可偵測**（K2 probe 的 GO 側）——holder 存活期間檔案
  size 0→0（零寫入＝mtime/size 反指標實證），lsof 仍命中；holder 終止後
  即轉 []。附帶實證 F-2（exit 1 歧義：不存在檔 stderr 非空→None）與
  F-3（symlink 路徑 realpath 正規化後命中）。

節錄：

```
[PASS] silent-holder-fd-detected: prober=['/Users/ctai/Github/ai-guide-air-149/.agent-tmp/poc-fd-lease/call_poc-stdout.log']（靜默 sleep 持 stdout fd）
[PASS] zero-write-while-held: size=0→0（fd 持開但零寫入＝mtime/size 反指標）
[PASS] symlink-path-normalized-hit: prober(link-to-stdout.log)=[.../link-to-stdout.log]（realpath 正規化，F-3）
[PASS] missing-file-undecidable: prober=None（exit 1＋stderr 非空＝錯誤非無命中，F-2）
[PASS] fd-released-no-lease: prober=[]（holder 終止後＝無 lease）
```

範圍註記：機制驗證（2 分鐘 sleep 造型，不等它跑完）；**25m 真實 workload
命中率實測顯式挪 S4 dogfood**（reviewer F-5 裁決）。

## K1：poc_three_surface.py——rollout「model I/O → 及時 append」採樣

- 對象：live subagent session rollout（`sess_subagent_agent_4273531c-…`，
  即本實作 session 自身）——採樣窗 35s 與本 session 的其他工具呼叫／token
  生成重疊
- 結論：（見下方節錄——採樣窗內 append 事件數即「model I/O 即時落盤」的
  實證；凍結判準的 rollout 面有效）
- 邊界：K1 的「誘導純推理 subagent（20m+ 零工具呼叫）＋併行採樣」全跑需
  spawn 授權（worker 禁再委派），與 TC-4 同場景**挪 S4 dogfood**；本 POC
  驗證 append 及時性，「thinking token 亦寫 rollout」的獨立分離驗證留 S4。

節錄（exit code 0，verdict＝appending）：

```
sampling /Users/ctai/.zcode/cli/rollout/model-io-sess_subagent_agent_4273531c-….jsonl
window=35.0s interval=2.0s
t=+0.0s size=5880169 mtime_ns=1789902765894902629
t=+24.1s APPEND +91738B size=5971907
t=+28.1s APPEND +91746B size=6063653
{"poc": "poc_three_surface", "verdict": "appending", "appends": 2, ...}
```

判讀：採樣窗 t+0→t+24 靜默段＝上一輪工具呼叫等待期（模型未生成——正是
SM-2 需 exec lease 豁免的造型）；t+24/t+28 兩次 append＝本 session 恢復
token 生成（model I/O 即時落盤，單次 ~92KB 與模型回應量同級）——**rollout
面對「工作中」的反映是真實且及時的**，凍結判準的 rollout 軸有效。
