# stale-running corpus 快照（AIR-149 S1——TC-2 H 級 oracle）

- 快照時點：2026-09-20T10:10:03+00:00
- 來源：`~/.zcode/cli/agents/` 唯讀掃描——`status=="running"` 且 `createdAt` 距快照 >7 天，取最舊 10 份
- 去敏：保留結構欄位；`prompt`/`description` 截斷至 160 字元；`profileSnapshot` 僅留 `name`
- 計數：10 份（TC-2 引快照時點計數 `manifest.json`，不綁 EP 歷史數字）

| agentId | createdAt | parentSessionId | 檔 |
|---|---|---|---|
| agent_c77bd007-0205-45ed-a430-1eb7ba224828 | 2026-08-26T05:11:33.716Z | sess_fc27ccc1-1668-4d98-8e34-9b84b60fa4b0 | `agent_c77bd007-0205-45ed-a430-1eb7ba224828.json` |
| agent_d83a8b24-df42-4112-8682-486292825601 | 2026-08-29T04:14:05.446Z | sess_d9956c75-f28a-44cc-993e-a04e16984689 | `agent_d83a8b24-df42-4112-8682-486292825601.json` |
| agent_2e48f8ca-44f3-4c41-a99b-65cf837d3c65 | 2026-08-29T04:15:37.333Z | sess_d9956c75-f28a-44cc-993e-a04e16984689 | `agent_2e48f8ca-44f3-4c41-a99b-65cf837d3c65.json` |
| agent_241d043b-20f5-4219-87fe-056589d54baf | 2026-08-29T04:22:59.347Z | sess_d9956c75-f28a-44cc-993e-a04e16984689 | `agent_241d043b-20f5-4219-87fe-056589d54baf.json` |
| agent_8dd948d5-2e19-44dc-812f-364c68fecf2d | 2026-08-29T04:22:59.347Z | sess_d9956c75-f28a-44cc-993e-a04e16984689 | `agent_8dd948d5-2e19-44dc-812f-364c68fecf2d.json` |
| agent_fd17888f-29d0-4ef7-9fbf-d591a23540a5 | 2026-08-29T04:22:59.671Z | sess_d9956c75-f28a-44cc-993e-a04e16984689 | `agent_fd17888f-29d0-4ef7-9fbf-d591a23540a5.json` |
| agent_bcfd23da-9b9c-478d-8f30-195c3563bce4 | 2026-08-29T04:23:49.330Z | sess_d9956c75-f28a-44cc-993e-a04e16984689 | `agent_bcfd23da-9b9c-478d-8f30-195c3563bce4.json` |
| agent_29ee168b-dadc-4da5-965c-c86d6ec1ad06 | 2026-08-29T14:47:59.618Z | sess_2fe1ad7c-047a-4a54-9cd4-131cb363507c | `agent_29ee168b-dadc-4da5-965c-c86d6ec1ad06.json` |
| agent_729b3469-0ac1-4834-a546-2cd049fc7edf | 2026-08-29T14:47:59.618Z | sess_2fe1ad7c-047a-4a54-9cd4-131cb363507c | `agent_729b3469-0ac1-4834-a546-2cd049fc7edf.json` |
| agent_5bd38f30-42d5-4ccf-8b39-1d6e11f14d87 | 2026-09-04T05:28:36.056Z | sess_8d13ef19-d566-4c52-b074-ff2a41982440 | `agent_5bd38f30-42d5-4ccf-8b39-1d6e11f14d87.json` |
