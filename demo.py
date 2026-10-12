"""
demo.py -- plaud-style 的回归样例：一张图型各一，加一个完整页面。数据是虚构的。

    python3 ~/.claude/skills/plaud-style/demo.py [输出目录]

改了 chart_theme.py / base.css 之后跑一遍，打开 demo.html 看浅色和深色（给 <html> 加
data-theme="dark" 即可预览深色）。需要装了 matplotlib 的 Python。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chart_theme import (apply_theme, fold_top_n, lift_bars, ordinal_ramp, ranking_bar,  # noqa: E402
                         save_chart, set_output_dir, trend_lines)
from page import inline_svg, write_page  # noqa: E402

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "plaud-style-demo")
apply_theme("zh")
set_output_dir(os.path.join(OUT, "charts"))

EXAMPLE = "示例数据，非真实结果"

fig, _ = ranking_bar(
    ["Plaud Note", "品牌 B", "品牌 C", "品牌 D", "品牌 E"], [42, 31, 24, 18, 9], highlight="Plaud Note",
    fmt="{:.0f}%", headline="Plaud Note 的提示后知晓率领先 11 个百分点",
    subtitle="提示后品牌知晓率，占受访者 %", caption=f"{EXAMPLE}。n = 1,200")
save_chart(fig, "ranking")

fig, _ = lift_bars(
    ["地区 A", "地区 B", "地区 C", "地区 D", "地区 E"], [24.4, 9.1, 3.2, -2.8, -6.5],
    headline="五个地区里三个上升、两个下降", subtitle="投放期 sessions 相对反事实的变化",
    caption=f"{EXAMPLE}。未显示置信区间")
save_chart(fig, "lift")

weeks = list(range(1, 13))
raw = {
    "实验区": [100 + 5.5 * i + (0 if i < 6 else 4 * (i - 5)) for i in range(12)],
    "对照 A": [98 + 1.3 * i for i in range(12)],
    "对照 B": [95 + 1.1 * i + (-1) ** i for i in range(12)],
    "对照 C": [90 + 0.9 * i for i in range(12)],
    "对照 D": [88 + 0.8 * i for i in range(12)],
}
fig, _ = trend_lines(
    weeks, fold_top_n(raw, 3, "其他", agg="mean"), other="其他",   # 指数不能求和，用 mean
    headline="第 6 周之后，实验区与对照区拉开差距",
    subtitle="每周 sessions 指数（第 1 周 = 100）", caption=f"{EXAMPLE}。对照 C、D 取均值合并为「其他」")
save_chart(fig, "trend")

steps = ordinal_ramp(4, "purple")
swatches = "".join(f'<span class="swatch" style="background:{c}"></span>' for c in steps)


def chart(name):
    return f'<div class="chart-frame">{inline_svg(os.path.join(OUT, "charts", name + ".svg"))}</div>'


body = f"""
<div class="page">
  <header>
    <h1>示例分析：Plaud 配色的图表与页面</h1>
    <p class="meta">plaud-style 回归样例 · {EXAMPLE}</p>
  </header>

  <section class="finding">
    <span class="label">核心结论</span>
    <p><strong>实验区在第 6 周之后拉开差距</strong>，累计比反事实高 <span class="up">+24.4%</span>；
    两个地区下降（<span class="down">−2.8%</span>、<span class="down">−6.5%</span>），不能算进整体效果。
    结论 <span class="ok">✓ 已通过安慰剂检验</span>。</p>
  </section>

  <section>
    <h2>三个数字</h2>
    <div class="kpi-row">
      <div class="kpi"><div class="value">42%</div><div class="label">提示后知晓率</div></div>
      <div class="kpi"><div class="value up">+24.4%</div><div class="label">地区 A 提升</div></div>
      <div class="kpi"><div class="value down">−6.5%</div><div class="label">地区 E 下降</div></div>
    </div>
  </section>

  <section>
    <h2>图</h2>
    <div class="chart-grid">{chart("ranking")}{chart("lift")}</div>
  </section>

  <section>
    <h2>时间趋势</h2>
    {chart("trend")}
    <p class="caption">图例和线尾标注同时存在：最多 3 个系列，多出来的并成「其他」（灰）。</p>
  </section>

  <section>
    <h2>表</h2>
    <div class="scroll-x card">
    <table class="data-table">
      <thead><tr><th>地区</th><th>基线</th><th>投放期</th><th>变化</th><th>状态</th></tr></thead>
      <tbody>
        <tr class="hl"><td>地区 A</td><td>1,240</td><td>1,543</td><td class="up">+24.4%</td><td><span class="badge purple">焦点</span></td></tr>
        <tr><td>地区 B</td><td>980</td><td>1,069</td><td class="up">+9.1%</td><td><span class="badge blue">稳定</span></td></tr>
        <tr><td>地区 C</td><td>1,105</td><td>1,140</td><td class="up">+3.2%</td><td><span class="badge green">✓ 通过</span></td></tr>
        <tr><td>地区 D</td><td>870</td><td>846</td><td class="down">−2.8%</td><td><span class="badge neg">下降</span></td></tr>
        <tr><td>地区 E</td><td>760</td><td>711</td><td class="down">−6.5%</td><td><span class="badge neutral">观察</span></td></tr>
      </tbody>
    </table>
    </div>
  </section>

  <section>
    <h2>有序色阶</h2>
    <p>顺序本身有意义（漏斗阶段、分档）才用同色相的有序色阶：{swatches}，亮度单调、相邻差 ≥ 0.07。
    没有顺序的分类用上面的系列色，不用色阶。</p>
  </section>

  <footer class="caption">{EXAMPLE}。由 ~/.claude/skills/plaud-style/demo.py 生成。</footer>
</div>
"""
write_page(os.path.join(OUT, "demo.html"), "Plaud 样式示例", body)
