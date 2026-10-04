# -*- coding: utf-8 -*-
"""第三本书：把 src3/*.md 编译为 HTML 在线阅读版（仅 HTML，不含 EPUB / Markdown）。
   复用 build2.py 的渲染管线，只替换素材目录、元信息与分部页。"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build2 as B

ROOT = os.path.dirname(os.path.abspath(__file__))
B.SRC = os.path.join(ROOT, "src3")
B.OUT = os.path.join(ROOT, "output")

B.META.update({
    "title": "把话说清楚",
    "subtitle": "关系场景对话与回应手册",
    "tagline": "118 个具体场景：别这样说、可以这样说，以及为什么",
    "author": "Delmi 编著",
    "date": "2026年10月",
    "title_safe": "把话说清楚_关系场景对话与回应手册",
})

B.PARTS = [
    ("第一章", "第一部分", "开场",
     "第一次开口、社交软件、线下搭话与被搭话。"),
    ("第四章", "第二部分", "聊天",
     "话题怎么开、怎么聊深、怎么收场、对方不回怎么办。"),
    ("第八章", "第三部分", "邀约与约会",
     "怎么开口约、约会现场说什么、约会之后怎么接。"),
    ("第十一章", "第四部分", "好感与边界",
     "表达好感、确认同意、拒绝别人，以及被拒绝。"),
    ("第十四章", "第五部分", "冲突与长期",
     "吵架、道歉、提需求与设边界、分手。"),
    ("第十八章", "第六部分", "特殊场景",
     "异地、危险与不适、家人朋友与社交圈。"),
]

FOOTER_OLD = ("原素材中带有明显价值倾向、缺乏依据或涉及同意红线的内容，"
              "已在正文中逐条删除、改写并说明（见附录 B）。")
FOOTER_NEW = ("原素材中用于绕开对方同意、制造情绪控制的表述已全部删除；"
              "涉及拒绝、边界与不适场景的回应方式，为编者补充。")


if __name__ == "__main__":
    sections = B.parse_sections()
    items = B.make_items(sections)
    B.WORDS = sum(len(re.sub(r"[\s#|>\-*]", "", "".join(s["lines"]))) + len(s["title"])
                  for s in sections)
    h = B.build_html(items)
    # 替换页脚说明（第三本的附录结构与第二本不同）
    txt = open(h, encoding="utf-8").read()
    if FOOTER_OLD in txt:
        open(h, "w", encoding="utf-8").write(txt.replace(FOOTER_OLD, FOOTER_NEW))

    scen = sum(len([l for l in s["lines"] if l.startswith("## 场景")]) for s in sections)
    rep = ["节数: %d" % len(sections), "含分部页的渲染项: %d" % len(items),
           "正文字数(约): %d" % B.WORDS,
           "章节(h1): %d" % len([s for s in sections if not s["title"].startswith("附录")]),
           "场景条目(## 场景): %d" % scen,
           "小节(##): %d" % sum(len([l for l in s["lines"] if l.startswith("## ")]) for s in sections),
           "表格: %d" % sum(len([l for l in s["lines"] if l.strip().startswith("| ---")])
                           for s in sections),
           "输出: 仅 HTML 在线阅读版（不含 EPUB / Markdown）"]
    rep.append("%s %d bytes" % (os.path.basename(h), os.path.getsize(h)))
    with open(os.path.join(B.OUT, "_build3.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(rep))
