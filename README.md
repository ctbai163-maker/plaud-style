# plaud-style

Plaud 内部分析的统一视觉规范，Claude Code 的一个 skill：图表（matplotlib / SVG）、HTML 报告页、Artifact 页面，一律用同一套品牌配色和版式规格。

做什么：
- 色板：品牌紫 `#8F53ED`、蓝 `#00D0FF`、绿 `#21EF6A`，加负向红 `#C03A2B`。线和点用校验过的压暗版本，色值见 `SKILL.md`。
- 三个现成图型：排名柱图、涨跌柱图、折线图，标题、脚注、数值标签、深浅色都按规格做好。
- 页面样式：核心结论块、卡片、表、徽章，深色模式，手机宽度可读。

## 安装

```bash
git clone https://github.com/ctbai163-maker/plaud-style.git ~/.claude/skills/plaud-style
```

这是私有仓库，需要先被邀请为协作者，并已登录 GitHub（`gh auth login` 或配置好 git 凭据）。装完重开一个 Claude Code 会话，skill 才会出现在列表里。

出图需要装了 matplotlib 的 Python：`pip install matplotlib`。

## 试一下

```bash
python3 ~/.claude/skills/plaud-style/demo.py /tmp/plaud-demo
open /tmp/plaud-demo/demo.html
```

之后直接对 Claude 说「用 Plaud 配色做一张图」或「做一个 HTML 报告」就会调用它。

## 更新

```bash
git -C ~/.claude/skills/plaud-style pull
```

## 改色值

`SKILL.md` 的色板表是唯一权威。改色时同步改 `chart_theme.py` 和 `base.css` 里的同一组十六进制，再按 `SKILL.md` 末尾的「校验记录」重跑 dataviz 校验脚本，最后跑一遍 `demo.py` 看浅色和深色。
