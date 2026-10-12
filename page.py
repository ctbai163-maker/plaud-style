"""
page.py -- 把正文 HTML 套上 Plaud 样式，输出一份自包含的页面 (skill: plaud-style)

    import sys, os
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/plaud-style"))
    from page import render_page, write_page, inline_svg

    body = '<div class="page"><h1>...</h1> ... </div>'
    write_page("report.html", "页面名称", body)                # 本地 HTML，完整文档
    open("fragment.html", "w").write(render_page("页面名称", body, for_artifact=True))
                                                              # 发布 Artifact：不带 <html>/<head>/<body>

图用 inline_svg("charts/x.svg") 内联进去（页面就一个文件，不依赖旁边的图），
放在 <div class="chart-frame"> 里。
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))


def base_css():
    with open(os.path.join(_HERE, "base.css"), encoding="utf-8") as f:
        return f.read()


def inline_svg(path):
    """读一个 SVG 文件，去掉 XML 声明和 DOCTYPE，返回可以直接嵌进 HTML 的字符串。"""
    with open(path, encoding="utf-8") as f:
        s = f.read()
    s = re.sub(r"<\?xml[^>]*\?>\s*", "", s)
    s = re.sub(r"<!DOCTYPE[^>]*>\s*", "", s)
    return s.strip()


def render_page(title, body_html, lang="zh-CN", extra_css="", for_artifact=False):
    """返回 HTML 字符串。

    for_artifact=True：只返回 <title> + <style> + 正文，不含 <!doctype>/<html>/<head>/<body>
    （Artifact 发布时平台会自己包一层骨架）。"""
    style = f"<style>\n{base_css()}\n{extra_css}\n</style>"
    if for_artifact:
        return f"<title>{title}</title>\n{style}\n{body_html}\n"
    return (
        f'<!doctype html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n{style}\n</head>\n<body>\n{body_html}\n</body>\n</html>\n"
    )


def write_page(path, title, body_html, **kw):
    html = render_page(title, body_html, **kw)
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved: {os.path.abspath(path)}")
    return os.path.abspath(path)
