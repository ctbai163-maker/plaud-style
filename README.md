<h1 align="center">plaud-style</h1>

<p align="center">
  <strong>Plaud 内部分析的统一视觉规范：图表与 HTML 页面</strong><br>
  <sub>Claude Code skill · 也可以单独使用 chart_theme.py 和 base.css</sub>
</p>

<p align="center">
  <a href="docs/README_en.md">English</a> · <strong>中文</strong>
</p>

---

## 效果预览

<p align="center">
  <img src="docs/preview-light.png" alt="浅色" width="720">
</p>

<details>
<summary>深色模式</summary>

<p align="center">
  <img src="docs/preview-dark.png" alt="深色" width="720">
</p>

</details>

样例页由 `demo.py` 生成，数据是虚构的。

---

## 这套规范从哪里来

色板是 Plaud 的品牌色：Victory Purple、Clarity Blue、Amplify Green。图表主题和页面样式原本散在两个调研项目里，各自一份。

本 skill 做了三件事：**把它们从项目里拎出来，变成所有分析共用的一份；补上品牌色板缺的东西（负向色、系列规则）；把每个颜色用 dataviz 的校验脚本验过一遍。**

---

## 为什么需要它

靠复制文件传递色板，会漂。有一个项目里审出过四套互不一致的"样式"，只有一套真正用过。每开一个新分析，都要重新找文件、重新问一遍"我们的配色是什么"。

另一个问题在色板本身：三个品牌色相里，蓝和绿太浅（白底上只有 1.8:1 和 1.5:1），拿去画细线或当文字会看不清；而且没有负向色，分析里一出现"下降"，每个人都会自己发明一个红。

这套规范解决的不是美观问题，而是**一致性和可读性**：同一个颜色在所有分析里意思相同，每个颜色都验过对比度和色觉障碍下的区分度，规则写下来而不是靠记忆。

---

## 工作方式

AI 收到做图或做页面的请求时，本 skill 提供色板和规则，并附带可直接调用的代码：

| 文件 | 用途 |
|---|---|
| `SKILL.md` | 色板表、12 条规则、校验记录（色值的唯一权威） |
| `chart_theme.py` | matplotlib 主题；三个现成图型 `ranking_bar` / `lift_bars` / `trend_lines`；有序、顺序、发散色阶 |
| `base.css` | 页面样式：深浅色、核心结论块、卡片、表、徽章、`.chart-frame` |
| `page.py` | 把正文套上样式，输出自包含的 HTML 或 Artifact 片段 |
| `demo.py` | 回归样例 |

与 `dataviz`（做图的方法）、`artifact-design`（做页面的契约）配合使用：方法按它们，颜色以本 skill 为准。

---

## 色板

| 角色 | 色值 | 用在哪 |
|---|---|---|
| 强调 · 系列 1 | Victory Purple `#8F53ED` | 焦点品牌、核心发现 |
| 默认对比 · 系列 2 · 极性正向 | Clarity Blue `#00D0FF`（线和点用 `#099EC3`） | 常规序列、上升 |
| 已确认 · 系列 3 | Amplify Green `#21EF6A`（线和点用 `#03A745`） | 通过、已确认，带 ✓ 或文字 |
| 负向 | `#C03A2B` | 下降、低于基线 |
| 弱化 | Deep Black `#000000` | 不重要的项 |
| Other / 参考 | `#8C8883` | 并入 Other 的系列、附录分布图 |
| 文字、坐标轴 | `#413D3B` | |
| 边线 | `#E0DDD9` | |
| 页面背景 | `#FAFAF7` | |

品牌原色里的蓝和绿只做大面积填充（宽柱、色块、徽章底），并且要带数值标签；线、点、细柱一律用压暗后的标记色。完整色值（含深色模式、文字色）见 `SKILL.md`。

---

## 关键规则

| # | 规则 |
|---|---|
| 1 | 一张图一个结论，标题写成结论句（"A 领先 11 个点"），不写"A 的分布" |
| 2 | 名义分类：所有柱同一个默认色，只有被点名的那一根用紫 |
| 3 | 最多 3 个系列（紫、蓝、绿，固定顺序）；多了并成灰色 Other 或拆成小图，不自己生成第 4 个色 |
| 4 | 有顺序用有序色阶，量级用顺序色阶，极性用蓝 ↔ 红；顺序和极性不能只靠颜色，要有位置或带符号的数值 |
| 5 | 文字永远不用系列色 |
| 6 | 绿只表示"已确认"，不当极性；红绿不单独区分（色觉障碍下只差 ΔE 8） |
| 7 | 不做双轴；≥ 2 个系列时图例和线尾直接标注同时有 |
| 8 | 图按浅底设计，放进 HTML 用 `.chart-frame`，深色页面里也看得见 |
| 9 | 虚构或占位数据必须写"示例数据" |

完整的 12 条见 `SKILL.md`。

---

## 现成图型

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/skills/plaud-style"))
from chart_theme import *

apply_theme("zh")            # 含中日文字必须 zh；纯英文图用 "en"
set_output_dir("charts")
fig, ax = ranking_bar(["A", "B", "C"], [42, 31, 24], highlight="A", fmt="{:.0f}%",
                      headline="A 领先 11 个点", caption="n = 1,200")
save_chart(fig, "ranking")   # -> charts/ranking.svg
```

页面：`page.py` 的 `render_page()` / `write_page()` 把正文套上 `base.css`；发布成 Artifact 用 `render_page(..., for_artifact=True)`。

---

## 校验

颜色用 dataviz 的 `validate_palette.js` 验过（2026-10-12）：

| 检查 | 结果 |
|---|---|
| 标记色 `#8F53ED,#099EC3,#03A745`，浅色，全部两两比较 | 通过；色觉障碍最差 ΔE 12.9，常视力最差 18.8 |
| 同上，深色 | 通过 |
| 发散对 `#C03A2B` ↔ `#099EC3` | 通过；色觉障碍 ΔE 20.4 |
| 有序色阶，3 / 5 / 7 阶，三个色相 | 通过 |
| 品牌原色蓝、绿直接当线 | 不通过（对比度 1.8 / 1.5:1），所以用标记色 |

---

## 安装方法

把以下链接发送给 Agent，它会帮你完成安装配置：

👉 https://github.com/ctbai163-maker/plaud-style

这是私有仓库，需要先被邀请为协作者，并已登录 GitHub（`gh auth login` 或配置好 git 凭据）。

**Claude Code**
```bash
git clone https://github.com/ctbai163-maker/plaud-style.git ~/.claude/skills/plaud-style
```
装完重开一个会话，skill 才会出现在列表里。之后用 `git -C ~/.claude/skills/plaud-style pull` 更新。

**其他 AI / 不用 skill 的场景**

把 `chart_theme.py`、`base.css`、`page.py` 拷进项目，再把 `SKILL.md` 里的「规则」一节加入你的项目规范文件（`CLAUDE.md` / `AGENTS.md` / system prompt）即可。

### 依赖

- 带 matplotlib 的 Python（`pip install matplotlib`），出图用
- `dataviz` skill（Claude 自带），改色值后重跑校验用，日常出图不需要

试一下：`python3 ~/.claude/skills/plaud-style/demo.py /tmp/plaud-demo`，然后打开 `/tmp/plaud-demo/demo.html`。

---

## 改色值

`SKILL.md` 的色板表是唯一权威。改色时同步改 `chart_theme.py` 和 `base.css` 里的同一组十六进制，按 `SKILL.md` 末尾的校验命令重跑，最后跑一遍 `demo.py` 看浅色和深色。

---

## 致谢

色板：Plaud 品牌色。图表主题与页面样式：由内部两个调研项目的版本泛化而来。颜色校验方法：Claude 自带的 `dataviz` skill。  
整理与维护：[@ctbai163-maker](https://github.com/ctbai163-maker)。
