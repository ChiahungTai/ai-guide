---
name: frontend-ui-engineering
description: "Builds production-quality UIs with Panel/Bokeh. Use when building or modifying interactive dashboards, data visualization apps, or any Panel/Bokeh-based interface. Use when creating Panel components, implementing reactive layouts, managing param state, or optimizing Bokeh rendering performance."
---

# Panel / Bokeh UI Engineering

基於 Panel + Bokeh 的互動式數據視覺化應用開發規範。

## Component Architecture

- 繼承 `pn.viewable.Viewer`（不是 `param.Parameterized`），透過 `__panel__()` 支援 `.servable()` 直接部署
- Widget **不能宣告為 class-level attribute**（所有 instance 共用同一個 widget）
- 用 `pn.Param(self)` 或 `widget.from_param(self.param.x)` 從 param 自動生成 widget，確保雙向綁定

## Reactive Programming

- **綁定 `.param.x`（reference）不是 `.x`（value）**— 後者永遠不會更新
- 偏好 `pn.rx()` reactive expressions 進行鏈式反應
- 用 `pn.rx.when(button)` 控制 transient events（按鈕點擊）
- Side-effect-only callbacks：用 `watch=True` 或 `button.on_click()`
- **更新 `.object` 而非重建 Panel 物件** — 重建會閃爍且低效

## Performance

- `@pn.cache` 自動 memoization
- `pn.state.as_cached('key', loader_func)` 跨 session 資料快取
- `pn.extension(defer_load=True, loading_indicator=True)` 延遲載入
- Slider 用 `value_throttled`（不是 `value`）避免頻繁觸發
- `hv.DynamicMap` 包裹 HoloViews plots，更新時保留 zoom/axis 範圍

## Layout

- `pn.FlexBox` 優於 `Column`/`Row`（響應式自動換行）
- Templates（`FastListTemplate`、`FastGridTemplate`）用於 polished dashboards
- `sizing_mode="stretch_both"` / `"stretch_width"` 響應式尺寸

## State Management (param)

- `obj.param.update()` 批次更新多個 param（atomic change）
- `@param.depends('x', watch=True)` 聲明式依賴

## Common Pitfalls

| 問題 | 症狀 | 修正 |
|------|------|------|
| 綁定 `.x` 非 `.param.x` | 靜默失敗，不更新 | 改用 `.param.x` |
| Widget 當 class attribute | 多 instance 共用狀態 | 在 `__init__` 中建立 |
| 重建 Panel 物件 | 閃爍 + 低效 | 更新 `.object` |
| `col.objects[0] = 'x'` | 不觸發 watcher | 用 `col[0] = 'x'` |
| Tabulator Styler runtime 賦值 | `TypeError: Unsupported dataframe type: Styler`（constructor 會拆、setter 不拆；server state 已改但 widget 不更新） | runtime 分開賦：`tab.value = df; tab.style = styler_df` |
| `RadioButtonGroup` options 用 (label, value) tuple | 按鈕名整串 stringify（tuple 不分離；Select 家族才支援） | 改 **dict options**（key=按鈕名、value=widget value；動態更新 options 後 value 持久——label 帶計數/value 穩定的動態 badge 唯一安全形態） |
| 程式化驅動 slider 等 Constant param | `value_throttled` 不觸發、直接賦值被拒 | 唯一路＝`with param.edit_constant(True):`（用畢自動還原 Constant） |
| `Tabulator.name` 建構後賦值 | `TypeError: Constant parameter 'name' cannot be modified` | 動態表題改外側 Markdown pane，不走 name |
| FlexBox wrap 容器放可變寬文字 | 瞬態內容（如 loading 後綴 +~100px）擠換行、完成後跳回 | transient 回饋走 **overlay**（`Viewable.loading`）不走文字通道 |

## Deployment

```bash
panel serve app.py                          # 單進程
panel serve app.py --num-procs 4            # 多進程
panel serve app.py --auth-provider oauth    # 認證
```

- `pn.state.onload()` 初始化 session
- `pn.state.on_session_destroyed()` 清理資源
