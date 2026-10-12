"""
chart_theme.py -- Plaud 统一图表主题 (skill: plaud-style)
────────────────────────────────────────────────────────────────────────────
用法（任何项目里）::

    import sys, os
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/plaud-style"))
    from chart_theme import *

    apply_theme("en")                 # 或 "zh"（含中日文字时必须用 zh，见下）
    set_output_dir("charts")          # 默认 ./charts，也可用环境变量 PLAUD_CHARTS_DIR
    fig, ax = ranking_bar(["A", "B", "C"], [42, 30, 18], highlight="A",
                          headline="A leads the ranking", caption="Source: ...  n = 1,200")
    save_chart(fig, "ranking")        # -> charts/ranking.svg

出处：由 Japan Brand Tracking 的 chart_theme.py 泛化而来（它又移植自 APAC 的
chart_templates/chart_theme.py）。相比那两份：
  * 不再写死项目路径，输出目录是参数；
  * 新增负向色 C_NEGATIVE、经校验的"图表标记色" M_*、中性色 C_NEUTRAL；
  * 序列规则改为"最多 3 个系列，其余并成 Other / 拆小图"（见 fold_top_n），
    不再用同色浅阶凑第 4–8 个系列（那样在 CVD 下分不开）；
  * 有序色阶(ordinal_ramp)按亮度步长≥0.06 生成，旧的 stage_colors 在 n≥4 时不过校验；
  * 去掉调查问卷专用的函数（QID 标题、segment 配色）。

色板的规则和校验记录见 SKILL.md。所有颜色常量的唯一权威表在 SKILL.md；
base.css 里有同一组十六进制，改色时两处同步。
────────────────────────────────────────────────────────────────────────────
"""

import math
import os
import re

import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ── 输出目录 ──────────────────────────────────────────────────────────────
_OUT_DIR = os.environ.get("PLAUD_CHARTS_DIR") or os.path.join(os.getcwd(), "charts")


def set_output_dir(path):
    """指定图的输出目录（相对路径按当前工作目录解析）。目录在第一次保存时才创建。"""
    global _OUT_DIR
    _OUT_DIR = os.path.abspath(path)
    return _OUT_DIR


def out(filename):
    """把文件名解析到输出目录里。没写扩展名时默认 .svg。"""
    if not os.path.splitext(filename)[1]:
        filename += ".svg"
    os.makedirs(_OUT_DIR, exist_ok=True)
    return os.path.join(_OUT_DIR, filename)


# ── 品牌色（原色，用于大面积填充 / 品牌识别，必须配数值标签）─────────────────
C_EMPHASIS = "#8F53ED"   # Victory Purple  焦点品牌 / 核心发现
C_DEFAULT = "#00D0FF"    # Clarity Blue    常规对比序列
C_GREEN = "#21EF6A"      # Amplify Green   已确认 / 通过（状态，不是系列色）
C_MUTED = "#000000"      # Deep Black      弱化

# ── 图表标记色（线、点、细柱、描边用；已用 dataviz 校验脚本验证）──────────────
M_EMPHASIS = "#8F53ED"   # = 品牌紫，本身就过线
M_DEFAULT = "#099EC3"    # Clarity Blue 压暗到白底 ≥3:1，同色相
M_GREEN = "#03A745"      # Amplify Green 压暗到白底 ≥3:1，同色相
C_NEGATIVE = "#C03A2B"   # 负向 / 下降 / 低于基线（2026-10 新增，已与 M_DEFAULT 组成发散对）
C_NEUTRAL = "#8C8883"    # Other / 参考 / 附录分布（白底 3.52:1）

SERIES = [M_EMPHASIS, M_DEFAULT, M_GREEN]   # 固定顺序，不循环
SERIES_MAX = len(SERIES)

# ── 文字与框线 ────────────────────────────────────────────────────────────
C_AXIS = "#413D3B"       # 坐标轴文字、参考线
C_TITLE = "#413D3B"
C_NOTE = "#6B6661"       # 脚注、n=（浅底上 5.4:1）
C_SPINE = "#E0DDD9"
C_SURFACE = "#FFFFFF"    # 图的底。图一律按浅底设计，放进 HTML 时套 .chart-frame

# 兼容旧名
C_HIGHLIGHT = C_EMPHASIS
C_PRIMARY = C_DEFAULT


# ── 颜色工具：OKLCH（用来生成有序色阶）─────────────────────────────────────
def _s2l(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _l2s(c):
    c = max(0.0, min(1.0, c))
    return 255 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)


def _lch_to_hex(L, C, H):
    """OKLCH -> (hex, 是否在 sRGB 色域内)。"""
    a, b = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    ok = all(-1e-4 <= x <= 1 + 1e-4 for x in rgb)
    return "#{:02X}{:02X}{:02X}".format(*[round(_l2s(x)) for x in rgb]), ok


def _rel_lum(hex_color):
    r, g, b = [_s2l(int(hex_color[i:i + 2], 16)) for i in (1, 3, 5)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    """WCAG 对比度。"""
    hi, lo = sorted([_rel_lum(a), _rel_lum(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _tint(hex_color, factor):
    """向白色混合。factor=1.0 原色，0.0 纯白。"""
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return "#{:02X}{:02X}{:02X}".format(*[round(v * factor + 255 * (1 - factor)) for v in (r, g, b)])


# 三个品牌色相在 OKLCH 里的色相角与最大彩度（取自品牌原色）
_HUE = {"purple": (297.0, 0.220), "blue": (221.9, 0.147), "green": (148.5, 0.231)}
_RAMP_STEP = 0.07        # 相邻两阶亮度差，校验线是 0.06
_RAMP_DARK_LIMIT = 0.28  # 再深就接近黑了


def _max_chroma_hex(L, H, C_cap):
    C = C_cap
    while C > 0.02 and not _lch_to_hex(L, C, H)[1]:
        C -= 0.002
    return _lch_to_hex(L, C, H)[0]


def _ramp_light_end(hue):
    """该色相里"在白底上仍有 ≥2:1 对比"的最亮一阶（有序色阶的浅端规则）。"""
    H, C_cap = _HUE[hue]
    for i in range(400):
        L = 0.90 - i * 0.001
        hx = _max_chroma_hex(L, H, C_cap)
        if contrast(hx, "#FFFFFF") >= 2.05:
            return L
    raise RuntimeError("no light end found")


def ordinal_ramp(n, hue="purple"):
    """n 阶同色相有序色阶，浅 -> 深。用于"顺序本身有意义"的东西：漏斗阶段、分档、队列。

    亮度单调、相邻差 0.07（过 dataviz --ordinal 校验）、浅端在白底 ≥2:1。
    最多 7 阶；超过说明该分组了。名义分类（没有顺序）不要用它，用 SERIES。
    """
    if hue not in _HUE:
        raise ValueError(f"hue must be one of {sorted(_HUE)}")
    if not 1 <= n <= 7:
        raise ValueError("ordinal_ramp supports 1-7 steps (the range checked with dataviz --ordinal)")
    H, C_cap = _HUE[hue]
    top = _ramp_light_end(hue)
    if top - _RAMP_STEP * (n - 1) < _RAMP_DARK_LIMIT:
        raise ValueError(f"ordinal_ramp supports at most {int((top - _RAMP_DARK_LIMIT) / _RAMP_STEP) + 1} steps for {hue}")
    return [_max_chroma_hex(top - _RAMP_STEP * i, H, C_cap) for i in range(n)]


def seq_cmap(hue="purple", n=7):
    """顺序（量级）色阶，给热力图 / 色块：浅 = 小，深 = 大。"""
    return LinearSegmentedColormap.from_list(f"plaud_seq_{hue}", ordinal_ramp(n, hue))


def div_cmap():
    """发散色阶：负向 C_NEGATIVE <- 中性灰 -> 正向 M_DEFAULT。两端是 dataviz 校验过的一对。"""
    return LinearSegmentedColormap.from_list("plaud_div", [C_NEGATIVE, "#EDEAE6", M_DEFAULT])


# 保留品牌原色的 10 阶浅化（旧项目里的 GRAD_*）。新图请优先用 ordinal_ramp。
GRAD_PURPLE = [_tint(C_EMPHASIS, 1.0 - i * 0.09) for i in range(10)]
GRAD_BLUE = [_tint(C_DEFAULT, 1.0 - i * 0.09) for i in range(10)]
GRAD_GREEN = [_tint(C_GREEN, 1.0 - i * 0.09) for i in range(10)]


# ── 系列规则：最多 3 个，其余并成 Other ───────────────────────────────────
def fold_top_n(series, n=SERIES_MAX, other="Other", agg="sum"):
    """series: {名称: 数值序列或标量}。保留合计最大的 n 项，其余并成 other。

    agg="sum"：可加的量（sessions、订单、金额）。agg="mean"：不可加的量（指数、比率、
    均值）——对指数求和会得出一条比任何单项都高的"其他"线，是错的，别用 sum。

    品牌色板只有三个色相，第 4 个系列无论怎么生成都会和前三个混淆。规则是并成 Other
    （灰），或者拆成小图。"""
    if agg not in ("sum", "mean"):
        raise ValueError("agg must be 'sum' or 'mean'")

    def total(v):
        try:
            return sum(v)
        except TypeError:
            return v

    def combine(vals):
        return sum(vals) / (len(vals) if agg == "mean" else 1)

    ranked = sorted(series, key=lambda k: total(series[k]), reverse=True)
    keep, rest = ranked[:n], ranked[n:]
    out_ = {k: series[k] for k in keep}
    if rest:
        try:
            out_[other] = [combine(vals) for vals in zip(*[series[k] for k in rest])]
        except TypeError:
            out_[other] = combine([series[k] for k in rest])
    return out_


def series_colors(names, other="Other"):
    """按固定顺序给系列上色；名为 other 的永远是中性灰。颜色跟着实体走，不跟着排名走。"""
    named = [k for k in names if k != other]
    if len(named) > SERIES_MAX:
        raise ValueError(f"{len(named)} 个系列超过 {SERIES_MAX}：用 fold_top_n() 并成 Other，或拆成小图。")
    colors = dict(zip(named, SERIES))
    if other in names:
        colors[other] = C_NEUTRAL
    return colors


# ── 字体 ──────────────────────────────────────────────────────────────────
# matplotlib 的 font.sans-serif 是"第一个可用字体"，不是逐字回退：含中日文字的图
# 必须让 CJK 字体排在最前，否则整图变豆腐块。英文图用 Arial。
FONT_FAMILY = ["STHeiti", "Hiragino Sans GB", "PingFang SC", "Noto Sans CJK SC",
               "Microsoft YaHei", "Arial Unicode MS", "Arial", "sans-serif"]
FONT_FAMILY_EN = ["Arial", "Helvetica", "sans-serif"]
FONT_TITLE = 12
FONT_TICK = 10
FONT_LABEL = 10
FONT_NOTE = 8

# ── 版式常量 ──────────────────────────────────────────────────────────────
LEGEND_LOC = "lower left"
LEGEND_ANCHOR = (0, 1.01)
FIGSIZE_STD = (6.0, 4.2)      # ≤6 项
FIGSIZE_LONG = (7.0, 5.0)     # 7–12 项
FIGSIZE_XLARGE = (7.0, 8.5)   # 13–20 项
BAR_HEIGHT_DEFAULT = 0.6
LINE_WIDTH = 2.0              # 线宽 2px 是硬规格，别加粗
MARKER_SIZE = 6

BASE_RCPARAMS = {
    "font.family": "sans-serif",
    "font.sans-serif": FONT_FAMILY,
    "text.color": C_AXIS,
    "axes.labelcolor": C_AXIS,
    "axes.edgecolor": C_SPINE,
    "xtick.color": C_AXIS,
    "ytick.color": C_AXIS,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "axes.prop_cycle": matplotlib.cycler(color=SERIES),
    "lines.linewidth": LINE_WIDTH,
    "figure.facecolor": "none",
    "axes.facecolor": "none",
    "savefig.transparent": True,
    # SVG 文字转曲线：别人电脑没有这个字体时标签也不会错位。代价：文字不可选、文件更大。
    "svg.fonttype": "path",
}


def apply_theme(lang="zh"):
    """每个出图脚本开头调用一次。

    lang="zh"：CJK 字体链（默认）。lang="en"：Arial 链，只能用于纯拉丁字符的图。"""
    plt.rcParams.update(BASE_RCPARAMS)
    if lang == "en":
        plt.rcParams["font.sans-serif"] = FONT_FAMILY_EN
    elif lang != "zh":
        raise ValueError(f"lang must be 'zh' or 'en', got {lang!r}")


def configure_spines(ax, left=True, bottom=True):
    ax.spines["left"].set_visible(left)
    ax.spines["bottom"].set_visible(bottom)
    if left:
        ax.spines["left"].set_color(C_SPINE)
    if bottom:
        ax.spines["bottom"].set_color(C_SPINE)


# ── 防重叠小工具 ──────────────────────────────────────────────────────────
def add_vref_label(ax, x_data, label, y_frac=0.97, ha="left", x_nudge=None):
    """竖直参考线的标签：x 用数据坐标、y 用轴比例坐标，永远不会压到 x 轴。"""
    if x_nudge is None:
        xlim = ax.get_xlim()
        x_nudge = (xlim[1] - xlim[0]) * 0.01
    ax.text(x_data + x_nudge, y_frac, label, transform=ax.get_xaxis_transform(),
            fontsize=FONT_NOTE, color=C_AXIS, style="italic", va="top", ha=ha)


def add_href_label(ax, y_data, label, x_frac=0.97, va="bottom", y_nudge=None):
    if y_nudge is None:
        ylim = ax.get_ylim()
        y_nudge = (ylim[1] - ylim[0]) * 0.01
    ax.text(x_frac, y_data + y_nudge, label, transform=ax.get_yaxis_transform(),
            fontsize=FONT_NOTE, color=C_AXIS, style="italic", va=va, ha="right")


# ── 文本测量与换行（量真实渲染宽度，不猜字符数；CJK 逐字断行）───────────────
_CJK = r"　-〿぀-ヿ㐀-䶿一-鿿＀-￯"
_TOKEN = re.compile(rf"(\s*)([{_CJK}]|[^\s{_CJK}]+)")
_cjk_re = re.compile(rf"[{_CJK}]")
_measure = {}


def _renderer():
    fig = Figure()
    FigureCanvasAgg(fig)
    return fig, fig.canvas.get_renderer()


def text_width_in(s, fontsize, fontweight="normal"):
    """文字在当前字体设置下的渲染宽度（英寸）。"""
    key = (plt.rcParams["font.sans-serif"][0], s, fontsize, fontweight)
    if key not in _measure:
        fig, r = _renderer()
        t = fig.text(0, 0, s, fontsize=fontsize, fontweight=fontweight)
        _measure[key] = t.get_window_extent(renderer=r).width / fig.dpi
    return _measure[key]


def _measured_wrap(text, fontsize, max_width_in, fontweight="normal"):
    lines = []
    for para in str(text).split("\n"):
        cur = ""
        for ws, tok in _TOKEN.findall(para):
            if not cur:
                cand = tok
            elif ws:                       # 作者写了空格就保留（"第 6 周"）
                cand = f"{cur} {tok}"
            elif _cjk_re.match(tok[0]) or _cjk_re.match(cur[-1]):
                cand = cur + tok           # 中文之间不加空格
            else:
                cand = f"{cur} {tok}"      # 两个拉丁词之间必须有空格
            if cur and text_width_in(cand, fontsize, fontweight) > max_width_in:
                lines.append(cur)
                cur = tok
            else:
                cur = cand
        lines.append(cur)
    return lines


TITLE_LINE_H = 0.24
SUBTITLE_H = 0.22
TITLE_TOP_PAD = 0.16
CAPTION_LINE_H = 0.16


def headline_block(text, max_width_in, fontsize=None):
    """图的标题 = 一句结论（不是"X 的分布"这种名词）。返回 (行, 所需高度英寸)。"""
    lines = _measured_wrap(text, fontsize or FONT_TITLE, max_width_in, "bold")
    return lines, TITLE_LINE_H * len(lines) + TITLE_TOP_PAD


def caption_block(text, max_width_in, fontsize=None):
    lines = _measured_wrap(text, fontsize or FONT_NOTE, max_width_in)
    return lines, CAPTION_LINE_H * len(lines) + 0.10


def add_fig_caption(fig, lines, y=0.01, fontsize=None, x=0.0):
    """画脚注。放在 figure 层而不是 axes 层，tight_layout 不会把它裁掉。"""
    fig.text(x, y, "\n".join(lines), ha="left", va="bottom",
             fontsize=fontsize or FONT_NOTE, color=C_NOTE, style="italic")


def new_figure(figsize=FIGSIZE_STD, headline=None, subtitle=None, caption=None,
               left=0.6, right=0.25, top_pad=0.45, bottom_pad=0.5):
    """建一张带"标题 / 副标题 / 脚注"版位的图，返回 (fig, ax)。

    绘图区按英寸定位，标题和脚注占的高度另外加在 figsize 上，所以文字再长也不会压到图。
    left/right/top_pad/bottom_pad 单位英寸；top_pad 给图例留位置。"""
    w, h = figsize
    inner_w = w - 0.3
    hl_lines, hl_h = headline_block(headline, inner_w) if headline else ([], 0.0)
    sub_h = SUBTITLE_H if subtitle else 0.0
    cp_lines, cp_h = caption_block(caption, inner_w) if caption else ([], 0.0)
    total_h = h + hl_h + sub_h + cp_h
    fig = plt.figure(figsize=(w, total_h))
    x0, x1 = left / w, 1 - right / w
    y0 = (cp_h + bottom_pad) / total_h
    y1 = 1 - (hl_h + sub_h + top_pad) / total_h
    ax = fig.add_axes([x0, y0, x1 - x0, y1 - y0])
    y = 1 - TITLE_TOP_PAD / total_h
    if hl_lines:
        fig.text(0, y, "\n".join(hl_lines), ha="left", va="top", fontsize=FONT_TITLE,
                 color=C_TITLE, fontweight="bold")
        y -= TITLE_LINE_H * len(hl_lines) / total_h
    if subtitle:
        fig.text(0, y - 0.02, subtitle, ha="left", va="top", fontsize=FONT_NOTE, color=C_NOTE)
    if cp_lines:
        add_fig_caption(fig, cp_lines, y=0.01)
    return fig, ax


# ── 标签 / 数值格式 ───────────────────────────────────────────────────────
def bar_color(name, highlight=None):
    """名义分类的柱子：全部同一个默认色，只有被点名的那一根用强调色。
    不要按数值大小给柱子上不同的色（长度已经表达了数值）。"""
    return C_EMPHASIS if (highlight is not None and name == highlight) else C_DEFAULT


def highlight_ytick(ax, labels, highlight_label):
    """高亮项的标签加粗。文字不穿系列色（规则：文字永远用文字色）。"""
    for tick_label, val in zip(ax.get_yticklabels(), labels):
        if val == highlight_label:
            tick_label.set_fontweight("bold")


def highlight_xtick(ax, categories, highlight_cat):
    for label, cat in zip(ax.get_xticklabels(), categories):
        if cat == highlight_cat:
            label.set_fontweight("bold")


def save_chart(fig, filename, also_png=False):
    """保存。默认 SVG；also_png=True 额外存 180dpi PNG（Notion 等不渲染 SVG 的场合）。
    返回写出的路径列表。"""
    base, ext = os.path.splitext(out(filename))
    ext = ext or ".svg"
    if ext == ".png":
        also_png, ext = True, ".svg"
    written = []
    fig.savefig(base + ext, format=ext.lstrip("."), bbox_inches="tight", transparent=True)
    written.append(base + ext)
    if also_png:
        fig.savefig(base + ".png", format="png", dpi=180, bbox_inches="tight", transparent=True)
        written.append(base + ".png")
    plt.close(fig)
    for p in written:
        print(f"Saved: {p}")
    return written


# ── 现成图型（按规格做好：细标记、直接标注、无双轴、数值标签）───────────────
def _size_for(n):
    return FIGSIZE_STD if n <= 6 else FIGSIZE_LONG if n <= 12 else FIGSIZE_XLARGE


def ranking_bar(labels, values, highlight=None, fmt="{:,.0f}", headline=None, subtitle=None,
                caption=None, sort=True, figsize=None):
    """横向排名柱图（名义分类）。所有柱同色，highlight 那一根用强调色；每根柱带数值。
    值必须 ≥0；有正有负用 lift_bars。"""
    items = list(zip(labels, values))
    if any(v < 0 for _, v in items):
        raise ValueError("ranking_bar 不支持负值，用 lift_bars。")
    if sort:
        items.sort(key=lambda t: t[1], reverse=True)
    labels = [k for k, _ in items]
    vals = [v for _, v in items]
    n = len(items)
    label_w = max(text_width_in(str(k), FONT_TICK, "bold") for k in labels)
    fig, ax = new_figure(figsize or _size_for(n), headline, subtitle, caption,
                         left=min(3.6, label_w + 0.35), right=0.7, top_pad=0.15, bottom_pad=0.1)
    ys = list(range(n))[::-1]
    ax.barh(ys, vals, height=BAR_HEIGHT_DEFAULT, color=[bar_color(k, highlight) for k in labels])
    vmax = max(vals) if vals else 1
    for y, v in zip(ys, vals):
        ax.text(v + vmax * 0.015, y, fmt.format(v), va="center", ha="left",
                fontsize=FONT_TICK, color=C_AXIS)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=FONT_TICK)
    ax.set_xlim(0, vmax * 1.12)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0)
    configure_spines(ax, left=False, bottom=False)
    if highlight is not None:
        highlight_ytick(ax, labels, highlight)
    return fig, ax


def lift_bars(labels, values, fmt="{:+.1f}%", headline=None, subtitle=None, caption=None,
              sort=True, figsize=None):
    """横向发散柱图：基线是 0，正向 M_DEFAULT（蓝），负向 C_NEGATIVE（红）。
    正负靠"柱子在 0 的哪一侧 + 带符号的数值标签"表达，不只靠颜色。"""
    items = list(zip(labels, values))
    if sort:
        items.sort(key=lambda t: t[1], reverse=True)
    labels = [k for k, _ in items]
    vals = [v for _, v in items]
    n = len(items)
    label_w = max(text_width_in(str(k), FONT_TICK) for k in labels)
    fig, ax = new_figure(figsize or _size_for(n), headline, subtitle, caption,
                         left=min(3.6, label_w + 0.35), right=0.7, top_pad=0.15, bottom_pad=0.1)
    ys = list(range(n))[::-1]
    ax.barh(ys, vals, height=BAR_HEIGHT_DEFAULT,
            color=[M_DEFAULT if v >= 0 else C_NEGATIVE for v in vals])
    span = (max(vals + [0]) - min(vals + [0])) or 1
    for y, v in zip(ys, vals):
        ax.text(v + (0.015 if v >= 0 else -0.015) * span, y, fmt.format(v).replace("-", "\u2212"), va="center",
                ha="left" if v >= 0 else "right", fontsize=FONT_TICK, color=C_AXIS)
    ax.axvline(0, color=C_AXIS, lw=1.0)
    lo, hi = min(vals + [0]), max(vals + [0])
    ax.set_xlim(lo - (0.16 * span if lo < 0 else 0), hi + 0.16 * span)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=FONT_TICK)
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0)
    configure_spines(ax, left=False, bottom=False)
    return fig, ax


def trend_lines(x, series, fmt="{:,.0f}", headline=None, subtitle=None, caption=None,
                ylabel=None, figsize=None, other="Other"):
    """折线图，最多 3 个系列（+ Other 灰线）。线宽 2、末点加环、线尾直接标注名称和末值，
    ≥2 个系列时同时有图例。多于 3 个系列先用 fold_top_n() 并成 Other。"""
    names = list(series)
    colors = series_colors(names, other)
    fig, ax = new_figure(figsize or FIGSIZE_STD, headline, subtitle, caption,
                         left=0.75, right=1.7, top_pad=0.5 if len(names) > 1 else 0.2)
    for name in names:
        ax.plot(x, series[name], color=colors[name], lw=LINE_WIDTH, solid_capstyle="round", label=name)
        ax.plot([x[-1]], [series[name][-1]], "o", color=colors[name], ms=MARKER_SIZE + 1,
                mec=C_SURFACE, mew=2, zorder=3)
    ymin, ymax = ax.get_ylim()
    gap = (ymax - ymin) * 0.07
    ends = sorted(((series[n][-1], n) for n in names))
    ypos, prev = {}, None
    for val, name in ends:                       # 线尾标签错开，避免叠在一起
        y = val if prev is None or val - prev >= gap else prev + gap
        ypos[name], prev = y, y
    for name in names:
        ax.annotate(f"{name}  {fmt.format(series[name][-1])}", xy=(x[-1], series[name][-1]),
                    xytext=(8, 0), textcoords="offset points", va="center", ha="left",
                    fontsize=FONT_TICK, color=C_AXIS, annotation_clip=False)
        if abs(ypos[name] - series[name][-1]) > 1e-9:
            ax.texts[-1].xy = (x[-1], ypos[name])
    ax.yaxis.grid(True, color=C_SPINE, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    configure_spines(ax, left=False, bottom=True)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=FONT_LABEL)
    if len(names) > 1:
        ax.legend(loc=LEGEND_LOC, bbox_to_anchor=LEGEND_ANCHOR, ncol=len(names), frameon=False,
                  fontsize=FONT_NOTE + 1, handlelength=1.6)
    return fig, ax
