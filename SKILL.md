---
name: plaud-style
description: "Plaud 内部分析的统一视觉规范。凡是要做图表（matplotlib / SVG / HTML 图）、HTML 报告页、Artifact 页面，或任何要求「用 Plaud 配色 / 主题色 / 品牌色」的可视化时使用。提供经校验的色板（品牌紫 #8F53ED / 蓝 #00D0FF / 绿 #21EF6A + 负向 #C03A2B）、chart_theme.py（现成图型）、base.css（页面样式）。与 dataviz、artifact-design 同时使用时，颜色以本 skill 为准。Use for any Plaud chart, HTML report, brand palette, chart theme, internal analysis visuals."
---

# plaud-style

Plaud 的图表和 HTML 页面用这一套。目录里的文件：

| 文件 | 用途 |
|---|---|
| `chart_theme.py` | matplotlib 主题 + 三个现成图型（`ranking_bar` / `lift_bars` / `trend_lines`）+ 色阶工具 |
| `base.css` | 页面样式：色彩 token、深浅色、结论块、卡片、表、徽章、`.chart-frame` |
| `page.py` | `render_page()` 把正文套上样式；`inline_svg()` 把图内联进页面 |
| `demo.py` | 回归样例。改了上面任何一个文件，跑一遍并打开 `demo.html` 看浅色和深色 |

## 和其他 skill 的关系

- **`dataviz`**（做图的方法）和 **`artifact-design`**（做页面的契约）照常用。它们自带中性色板，**颜色以本 skill 为准**；方法、图型选择、标记规格、可访问性仍按它们。
- **CausalImpact 实验图**（Geo-experiment 项目）不用本 skill，它有自己的图规范，橙/绿/红是语义色。
- **Google Sheets / 飞书表格**的格式走 `sheet-format`（摩根格式，另一个 skill，装了才有）。

## 色板

| 角色 | 品牌原色（大面积填充、徽章底） | 图表标记色（线、点、细柱） | 文字色（浅 / 深） |
|---|---|---|---|
| 强调（焦点品牌、核心发现）· 系列 1 | Victory Purple `#8F53ED` | `#8F53ED` | `#814BD5` / `#A575F1` |
| 默认对比 · 系列 2 · 极性正向 | Clarity Blue `#00D0FF` | `#099EC3` | `#007D99` / `#00D0FF` |
| 已确认 / 通过 · 系列 3 | Amplify Green `#21EF6A` | `#03A745` | `#12833A` / `#21EF6A` |
| 负向 / 下降 / 低于基线 | — | `#C03A2B`（深色 `#C64030`） | `#C03A2B` / `#E8604D` |
| Other / 参考 / 附录分布 | — | `#8C8883` | — |
| 正文、坐标轴 | `#413D3B`（深色页面 `#EDEBE8`） | | |
| 页面背景 / 卡片 / 边线 | `#FAFAF7` / `#FFFFFF` / `#E0DDD9`（深色 `#1C1B19` / `#26241F` / `#3A3733`） | | |

Deep Black `#000000` 只用于弱化项。**这张表是色值的唯一权威**，`chart_theme.py` 和 `base.css` 里各有一份同样的十六进制，改色时三处同步，再跑校验。

## 规则

1. **颜色最后选。** 先定图型，一张图一个结论，标题写成结论句（"A 领先 11 个点"），不写"A 的分布"。
2. **名义分类**（品牌、地区、渠道）：所有柱同一个默认色，只有被点名的那一根用紫。不按数值大小给柱子上不同的色。
3. **最多 3 个系列**：紫、蓝、绿，固定顺序，颜色跟着实体走、不跟着排名走。多了就 `fold_top_n()` 并成灰色的 Other，或拆成小图。**不要自己生成第 4 个色，也不要用同色浅阶凑**，它们在色觉障碍下分不开。可加的量（sessions、金额）用 `agg="sum"`，指数和比率用 `agg="mean"`。
4. **有顺序**（漏斗阶段、分档）用 `ordinal_ramp(n, hue)`；**量级**用 `seq_cmap()`；**极性**（升/降、高于/低于基线）用蓝 ↔ 红，`div_cmap()` 或 `lift_bars()`。顺序和极性都不能只靠颜色，要有位置或带符号的数值标签。
5. **品牌原色蓝和绿太浅**（白底 1.8:1 和 1.5:1）。它们只做大面积填充（宽柱、色块、徽章底），并且必须带数值标签；**线、点、细柱、描边一律用标记色**。
6. **文字永远不用系列色**，用 ink 或 `*-text`。高亮柱子的标签加粗，不上色。
7. **绿只表示"已确认/通过"**，必须带 ✓ 或文字；不当极性，也不当第 4 个系列。**红绿不单独区分**，红和绿标记色在色觉障碍模拟下只差 ΔE 8.0。
8. **不做双轴。** 两个量级不同的指标拆成两张图，或统一成指数。≥2 个系列时图例和线尾直接标注同时有；线宽 2；末点加白环。
9. **附录里的纯分布图用中性灰**，不上品牌色（品牌色的意思是"这个重要"）。
10. **图按浅底设计**：透明背景 SVG，放进 HTML 时套 `.chart-frame`（框内永远是浅底），深色页面里才不会看不见。
11. **脚注写 n 和数据来源。虚构或占位数据必须写"示例数据"**，不能当成真实结果。
12. **画完要渲染出来看一眼**：标签有没有叠、有没有被裁、深色下能不能读。校验脚本只管颜色，不管版面。

## 用法

**图表**（需要装了 matplotlib 的 Python：`pip install matplotlib`）：

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills/plaud-style"))
from chart_theme import *

apply_theme("zh")            # 含中日文字必须 zh；纯英文图用 "en"
set_output_dir("charts")     # 默认 ./charts，也可设环境变量 PLAUD_CHARTS_DIR
fig, ax = ranking_bar(["A", "B", "C"], [42, 31, 24], highlight="A", fmt="{:.0f}%",
                      headline="A 领先 11 个点", caption="n = 1,200")
save_chart(fig, "ranking")   # -> charts/ranking.svg；also_png=True 再出一份 PNG
```

自己画别的图型时：`apply_theme()` 之后用 `new_figure()` 拿带标题/脚注版位的 `fig, ax`，颜色取 `SERIES` / `C_NEGATIVE` / `C_NEUTRAL`，防重叠用 `add_vref_label` 等。

**HTML 页面**：

```python
from page import render_page, write_page, inline_svg
body = f'<div class="page"><h1>…</h1><section class="finding"><span class="label">核心结论</span><p>…</p></section>'
body += f'<div class="chart-frame">{inline_svg("charts/ranking.svg")}</div></div>'
write_page("report.html", "页面名称", body)
```

页面结构：结论块放最前面，再展开；组件类名见 `base.css`（`.finding` `.card` `.kpi-row` `.chart-frame` `.data-table` `.badge` `.up` `.down` `.ok` `.emphasis`）。行内数字强调用 `.up`（正向，蓝）/ `.down`（负向，红）/ `.ok`（已确认，绿）。

**发布成 Artifact**：`render_page(..., for_artifact=True)` 返回不带 `<html>/<head>/<body>` 的片段（平台会自己包骨架），然后按 `artifact-design` 的契约发布（标题、响应式、深浅色已经在 `base.css` 里满足）。

## 校验记录（2026-10-12，dataviz 的 `validate_palette.js`）

脚本在 `dataviz` skill 的 `scripts/` 下（调用 `dataviz` 后会给出 base directory）。

| 检查 | 结果 |
|---|---|
| 品牌原色 `#8F53ED,#00D0FF,#21EF6A` | 蓝、绿亮度超出范围，对比度警告（1.78 / 1.50:1）→ 所以线和点不用原色 |
| 标记色 `#8F53ED,#099EC3,#03A745`，浅色，`--pairs all` | 全部通过；CVD 最差 ΔE 12.9（deutan），常视力最差 18.8 |
| 同上，深色（`#1C1B19`）| 全部通过 |
| 发散对 `#C03A2B` ↔ `#099EC3` | 通过；CVD ΔE 20.4。红 ↔ 绿标记色只有 8.0，红 ↔ 紫 29.2 |
| `ordinal_ramp` n = 3 / 5 / 7，三个色相，`--ordinal` | 全部通过 |

改了色值后重跑：

```bash
node <dataviz base>/scripts/validate_palette.js "#8F53ED,#099EC3,#03A745" --mode light --surface "#FFFFFF" --pairs all
node <dataviz base>/scripts/validate_palette.js "#8F53ED,#099EC3,#03A745" --mode dark  --surface "#1C1B19" --pairs all
```

## 已知限制

- `ranking_bar` / `lift_bars` 的柱子是直角，不是 dataviz 规格里的 4px 圆角数据端。
- 图是静态 SVG/PNG，没有悬停提示。需要交互的图用 HTML 原生画（颜色取 `base.css` 的 `--m-*` token），并按 `dataviz` 的 interaction 规范做。
- `chart_theme.py` 的中文字体链首选 STHeiti（macOS 常见），后面有几个备选。如果标签变成方块，调整 `FONT_FAMILY` 的顺序，CJK 字体必须排在最前。
- 来源：由 Japan Brand Tracking 和 APAC Brand Tracking 两个项目的图表主题泛化而来。
