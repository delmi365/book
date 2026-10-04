# -*- coding: utf-8 -*-
"""把 src/*.md 手稿编译为 HTML 在线阅读版（仅 HTML，不含 EPUB / Markdown）。"""
import os, re, html, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

META = {
    "title": "价值交换",
    "subtitle": "亲密关系中的生存价值与繁殖价值",
    "tagline": "一本关于自我建设、吸引力与长期关系的完整手册",
    "author": "Delmi 编著",
    "date": "2026年9月",
    "title_safe": "价值交换_生存价值与繁殖价值",
}

PARTS = [
    ("第一章", "第一部分", "价值：被误解的底层逻辑",
     "先承认关系里有交换，再把交换的对象看清楚——是体验，不是清单。"),
    ("第四章", "第二部分", "硬价值：可见的部分",
     "把“先天无法选择”和“后天可以改造”严格分开，把力气全部投在后者。"),
    ("第八章", "第三部分", "软价值：决定上限的部分",
     "硬件决定你能被多少人考虑，软件决定你能不能被留下。"),
    ("第十三章", "第四部分", "从吸引到关系",
     "相遇、筛选、维护、底线——关系真正的难点全部在“找到之后”。"),
    ("附录 A", "第五部分", "行动手册",
     "读到这里，剩下的事只有一件：明天早上开始做什么。"),
]


# ---------- markdown -> html ----------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\s][^*]*?)\*(?!\*)", r"<em>\1</em>", s)
    return s


def render_table(rows):
    def cells(r):
        return [c.strip() for c in r.strip().strip("|").split("|")]
    if len(rows) < 2:
        return ""
    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    out = ["<div class=\"tw\"><table><thead><tr>",
           "".join("<th>%s</th>" % inline(c) for c in head),
           "</tr></thead>"]
    if body:
        out.append("<tbody>")
        for r in body:
            out.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
        out.append("</tbody>")
    out.append("</table></div>")
    return "".join(out)


def blocks_to_html(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i].rstrip()
        s = line.strip()
        if not s:
            i += 1
            continue
        if s in ("---", "***", "___"):
            out.append("<hr>")
            i += 1
            continue
        if s.startswith("### "):
            out.append("<h4>%s</h4>" % inline(s[4:].strip()))
            i += 1
            continue
        if s.startswith("## "):
            out.append("<h3>%s</h3>" % inline(s[3:].strip()))
            i += 1
            continue
        if s.startswith("# "):
            out.append("<h2>%s</h2>" % inline(s[2:].strip()))
            i += 1
            continue
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % "<br>".join(inline(x) for x in buf))
            continue
        if s.startswith("|"):
            tbl = []
            while i < n and lines[i].strip().startswith("|"):
                tbl.append(lines[i].strip())
                i += 1
            out.append(render_table(tbl))
            continue
        if re.match(r"^\d+\.\s", s):
            items = []
            start = int(re.match(r"^(\d+)\.", s).group(1))
            while i < n and re.match(r"^\d+\.\s", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s", "", lines[i].strip()))
                i += 1
            attr = ' start="%d"' % start if start != 1 else ""
            out.append("<ol%s>" % attr + "".join("<li>%s</li>" % inline(x) for x in items) + "</ol>")
            continue
        if s.startswith("- "):
            items = []
            while i < n and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:].strip())
                i += 1
            out.append("<ul>" + "".join("<li>%s</li>" % inline(x) for x in items) + "</ul>")
            continue
        buf = [s]
        i += 1
        while i < n:
            t = lines[i].strip()
            if not t or t in ("---",) or re.match(r"^(#|>|\||\d+\.\s|-\s)", t):
                break
            buf.append(t)
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))
    return "\n".join(out)


def parse_sections():
    files = sorted(f for f in os.listdir(SRC) if f.endswith(".md"))
    text = ""
    for f in files:
        with open(os.path.join(SRC, f), encoding="utf-8") as fh:
            text += fh.read().rstrip() + "\n\n"
    lines = text.split("\n")
    sections, cur = [], None
    for ln in lines:
        if ln.startswith("# ") and not ln.startswith("## "):
            cur = {"title": ln[2:].strip(), "lines": []}
            sections.append(cur)
        else:
            if cur is None:
                cur = {"title": "卷首", "lines": []}
                sections.append(cur)
            cur["lines"].append(ln)
    for s in sections:
        while s["lines"] and (not s["lines"][0].strip() or s["lines"][0].strip() == "---"):
            s["lines"].pop(0)
        while s["lines"] and (not s["lines"][-1].strip() or s["lines"][-1].strip() == "---"):
            s["lines"].pop()
    return sections


def make_items(sections):
    """把章节列表与分部页合并成渲染序列。"""
    items, used = [], set()
    for sec in sections:
        for key, pnum, pname, pdesc in PARTS:
            if sec["title"].startswith(key) and key not in used:
                used.add(key)
                items.append({"kind": "part", "num": pnum, "name": pname, "desc": pdesc})
        items.append({"kind": "doc", "sec": sec})
    return items


def slug(idx):
    return "sec-%d" % idx


# ---------- HTML 电子书 ----------
CSS = """
:root{
 --paper:#f7f4ee; --paper2:#fffdf9; --ink:#23262b; --ink2:#4a4f57; --ink3:#7b8189;
 --line:#e3dcd0; --accent:#9a5b3f; --accent2:#b98150; --gold:#c9a227;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);
 font-family:"Source Han Serif SC","Noto Serif SC","Songti SC","SimSun",Georgia,serif;
 font-size:17px;line-height:1.95;-webkit-font-smoothing:antialiased}
#bar{position:fixed;top:0;left:0;height:3px;width:0;background:linear-gradient(90deg,var(--accent),var(--gold));z-index:99}
header.top{position:fixed;top:3px;left:0;right:0;height:52px;background:rgba(247,244,238,.92);
 backdrop-filter:blur(8px);border-bottom:1px solid var(--line);z-index:98;display:flex;align-items:center;
 padding:0 20px;gap:14px}
header.top .bt{font-size:14px;color:var(--ink2);letter-spacing:.06em}
header.top .sep{flex:1}
header.top button{font-family:inherit;font-size:13px;color:var(--ink2);background:var(--paper2);
 border:1px solid var(--line);border-radius:999px;padding:5px 13px;cursor:pointer}
header.top button:hover{color:var(--accent);border-color:var(--accent2)}
#tocbtn{display:none}
.wrap{display:flex;max-width:1180px;margin:0 auto;padding:0 24px}
nav.side{width:252px;flex:0 0 252px;position:sticky;top:55px;align-self:flex-start;
 max-height:calc(100vh - 80px);overflow-y:auto;padding:26px 18px 60px 0;font-family:"Microsoft YaHei",system-ui,sans-serif}
nav.side h4{margin:0 0 14px;font-size:12px;letter-spacing:.22em;color:var(--ink3);font-weight:600}
nav.side a{display:block;color:var(--ink2);text-decoration:none;font-size:13.5px;line-height:1.5;
 padding:6px 10px;border-left:2px solid transparent;border-radius:0 6px 6px 0}
nav.side a:hover{background:var(--paper2);color:var(--accent)}
nav.side a.active{border-left-color:var(--accent);color:var(--accent);background:var(--paper2);font-weight:600}
nav.side a.sub{font-size:12.5px;color:var(--ink3);padding-left:22px}
main{flex:1;min-width:0;padding:70px 0 90px}
.cover{min-height:88vh;display:flex;flex-direction:column;justify-content:center;
 border-bottom:3px double var(--line);margin-bottom:60px;padding:40px 0}
.cover .kicker{font-size:12.5px;letter-spacing:.42em;color:var(--accent);margin-bottom:26px;
 font-family:"Microsoft YaHei",sans-serif}
.cover h1{font-size:66px;line-height:1.12;margin:0 0 20px;letter-spacing:.06em;font-weight:700}
.cover h2{font-size:21px;font-weight:400;color:var(--ink2);margin:0 0 30px;line-height:1.7;letter-spacing:.03em}
.cover .rule{width:74px;height:3px;background:var(--accent);margin:0 0 30px}
.cover .tag{font-size:16px;color:var(--ink2);line-height:2;max-width:29em}
.cover .meta{margin-top:56px;font-size:13.5px;color:var(--ink3);line-height:2.1;
 font-family:"Microsoft YaHei",sans-serif}
section.doc{padding-top:34px;border-top:1px solid var(--line);margin-bottom:26px}
section.doc:first-of-type{border-top:none}
.partpage{margin:78px 0 34px;padding:58px 0 48px;text-align:center;
 border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.partpage .pn{font-size:12.5px;letter-spacing:.42em;color:var(--accent);margin-bottom:18px;
 font-family:"Microsoft YaHei",sans-serif}
.partpage h2{font-size:30px;margin:0 0 16px;letter-spacing:.06em}
.partpage p{color:var(--ink2);font-size:15.5px;max-width:26em;margin:0 auto;text-align:center}
nav.side a.partlink{margin-top:12px;font-size:11.5px;letter-spacing:.12em;color:var(--accent);
 font-weight:600}
nav.side a.partlink:hover{background:none;color:var(--accent2)}
h2.ch{font-size:34px;line-height:1.4;letter-spacing:.03em;margin:34px 0 26px;font-weight:700;position:relative}
h2.ch::before{content:"";position:absolute;left:0;bottom:-12px;width:46px;height:3px;background:var(--accent)}
h3{font-size:21.5px;margin:46px 0 16px;letter-spacing:.02em;font-weight:700;color:var(--ink)}
h3::after{content:"";display:block;width:22px;height:2px;background:var(--accent2);margin-top:10px;opacity:.75}
h4{font-size:18px;margin:32px 0 12px;font-weight:700;color:var(--ink)}
p{margin:0 0 18px;text-align:justify}
strong{color:#111;font-weight:700;
 background:linear-gradient(transparent 62%,rgba(201,162,39,.28) 62%)}
em{font-style:normal;color:var(--ink2)}
blockquote{margin:26px 0;padding:18px 24px;background:var(--paper2);border-left:4px solid var(--accent);
 border-radius:0 8px 8px 0;color:var(--ink2)}
blockquote p{margin:0}
ul,ol{margin:0 0 20px;padding-left:1.35em}
li{margin:0 0 9px}
hr{border:none;height:1px;background:var(--line);margin:40px 0}
.tw{overflow-x:auto;margin:26px 0}
table{border-collapse:collapse;width:100%;font-size:15px;
 font-family:"Microsoft YaHei",system-ui,sans-serif;background:var(--paper2)}
th,td{border:1px solid var(--line);padding:10px 13px;text-align:left;vertical-align:top;line-height:1.7}
th{background:#f0eae0;font-weight:700;color:#3a3f46;white-space:nowrap}
tr:nth-child(even) td{background:#fbf8f2}
#top{position:fixed;right:26px;bottom:26px;width:44px;height:44px;border-radius:50%;
 background:var(--paper2);border:1px solid var(--line);color:var(--accent);font-size:17px;cursor:pointer;
 box-shadow:0 6px 18px rgba(60,45,30,.12);opacity:0;pointer-events:none;transition:opacity .25s}
#top.on{opacity:1;pointer-events:auto}
footer{border-top:1px solid var(--line);margin-top:70px;padding:30px 0 0;color:var(--ink3);
 font-size:13px;font-family:"Microsoft YaHei",sans-serif;line-height:2}
@media(max-width:900px){
 nav.side{position:fixed;left:0;top:55px;bottom:0;width:270px;background:var(--paper);z-index:97;
  padding:22px 18px;transform:translateX(-100%);transition:transform .25s;box-shadow:8px 0 24px rgba(0,0,0,.08)}
 nav.side.open{transform:none}
 #tocbtn{display:inline-block}
 .wrap{padding:0 18px}
 .cover h1{font-size:42px}
 main{padding-top:60px}
 h2.ch{font-size:27px}
 body{font-size:16.5px}
}
@media print{
 #bar,header.top,nav.side,#top{display:none!important}
 body{background:#fff;font-size:11.5pt}
 main{padding:0}
 section.doc{break-before:page;page-break-before:always}
 .cover{min-height:auto;page-break-after:always}
 .tw{overflow:visible}
}
"""

JS = """
(function(){
 var bar=document.getElementById('bar'),top=document.getElementById('top');
 var secs=[].slice.call(document.querySelectorAll('section.doc'));
 var links={};
 [].slice.call(document.querySelectorAll('nav.side a')).forEach(function(a){links[a.getAttribute('href')]=a;});
 function onScroll(){
  var h=document.documentElement.scrollHeight-window.innerHeight;
  var y=window.scrollY||document.documentElement.scrollTop;
  bar.style.width=(h>0?(y/h*100):0)+'%';
  top.classList.toggle('on',y>600);
  var cur=secs[0];
  secs.forEach(function(s){if(s.offsetTop-140<=y)cur=s;});
  [].slice.call(document.querySelectorAll('nav.side a')).forEach(function(a){a.classList.remove('active');});
  if(cur&&links['#'+cur.id])links['#'+cur.id].classList.add('active');
 }
 document.addEventListener('scroll',onScroll,{passive:true});
 window.addEventListener('resize',onScroll);
 onScroll();
 top.onclick=function(){window.scrollTo({top:0,behavior:'smooth'});};
 var tb=document.getElementById('tocbtn'),nav=document.querySelector('nav.side');
 tb.onclick=function(){nav.classList.toggle('open');};
 nav.addEventListener('click',function(e){if(e.target.tagName==='A')nav.classList.remove('open');});
})();
"""


def build_html(items):
    nav_items = ['<h4>目 录</h4>']
    docs = []
    i = -1
    for it in items:
        if it["kind"] == "part":
            nav_items.append('<a class="partlink" href="#part-%s">%s</a>'
                             % (it["num"], html.escape(it["num"] + " " + it["name"])))
            docs.append('<section class="partpage" id="part-%s">'
                        '<div class="pn">%s</div><h2>%s</h2><p>%s</p></section>'
                        % (it["num"], html.escape(it["num"]), html.escape(it["name"]),
                           inline(it["desc"])))
            continue
        sec = it["sec"]
        i += 1
        sid = slug(i)
        subs = [l for l in sec["lines"] if l.startswith("## ")]
        nav_items.append('<a href="#%s">%s</a>' % (sid, html.escape(sec["title"])))
        for j, sub in enumerate(subs):
            nav_items.append('<a class="sub" href="#%s-%d">%s</a>' %
                             (sid, j, html.escape(sub[3:].strip())))
        body = blocks_to_html(list(sec["lines"]))
        # 给每个 ## 小节标题直接加上锚点 id（不注入裸 <span>，否则会被转义成乱码）
        cnt = [0]
        def _h3(m):
            i = cnt[0]; cnt[0] += 1
            return '<h3 id="%s-%d">' % (sid, i) + m.group(1) + "</h3>"
        body = re.sub(r"<h3>(.*?)</h3>", _h3, body, flags=re.S)
        docs.append('<section class="doc" id="%s">\n<h2 class="ch">%s</h2>\n%s\n</section>'
                    % (sid, inline(sec["title"]), body))
    cover = """
<div class="cover">
 <div class="kicker">SURVIVAL VALUE &amp; REPRODUCTIVE VALUE</div>
 <h1>%(title)s</h1>
 <div class="rule"></div>
 <h2>%(subtitle)s</h2>
 <p class="tag">%(tagline)s</p>
 <div class="meta">%(author)s<br>%(date)s · 全 %(count)d 节 · 约 %(words)s 字</div>
</div>""" % {"title": META["title"], "subtitle": META["subtitle"], "tagline": META["tagline"],
             "author": META["author"], "date": META["date"], "count": len(items), "words": WORDS}
    page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s · %(subtitle)s</title>
<style>%(css)s</style>
</head>
<body>
<div id="bar"></div>
<header class="top">
 <span class="bt">%(title)s</span>
 <span class="sep"></span>
 <button id="tocbtn">目录</button>
 <button onclick="window.print()">打印 / 存 PDF</button>
</header>
<div class="wrap">
<nav class="side">%(nav)s</nav>
<main>
%(cover)s
%(docs)s
<footer>%(title)s · %(subtitle)s<br>%(author)s · %(date)s<br>本书以读者提供的一段关于“生存价值与繁殖价值”的笔记为原始素材，经概念溯源、结构重建与内容扩充而成。</footer>
</main>
</div>
<button id="top">↑</button>
<script>%(js)s</script>
</body>
</html>""" % {"title": META["title"], "subtitle": META["subtitle"], "css": CSS,
              "nav": "\n".join(nav_items), "cover": cover,
              "docs": "\n\n".join(docs), "js": JS, "author": META["author"], "date": META["date"]}
    path = os.path.join(OUT, META["title_safe"] + "_电子书.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return path


# ---------- EPUB ----------
EPUB_CSS = """body{font-family:serif;line-height:1.8;margin:5%}
h1{font-size:1.5em;border-bottom:2px solid #9a5b3f;padding-bottom:.3em;margin:1.4em 0 .8em}
h2{font-size:1.2em;margin:1.3em 0 .6em;color:#9a5b3f}
h3{font-size:1.05em;margin:1.1em 0 .5em}
p{margin:.6em 0;text-indent:0}
blockquote{margin:1em 0;padding:.6em 1em;border-left:3px solid #9a5b3f;background:#faf7f2}
table{border-collapse:collapse;width:100%;font-size:.85em;margin:1em 0}
th,td{border:1px solid #ddd;padding:.4em .5em;text-align:left}
th{background:#f0eae0}
.cover{text-align:center;margin-top:22%}
.cover .t{font-size:2.4em;font-weight:bold;letter-spacing:.1em;margin-bottom:.4em}
.cover .s{font-size:1.1em;color:#555;margin-bottom:2em}
.cover .a{font-size:.95em;color:#777}
"""


def xhtml_page(title, inner, css_href="style.css"):
    return """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">
<head><meta charset="utf-8"/><title>%s</title>
<link rel="stylesheet" type="text/css" href="%s"/></head>
<body>
%s
</body></html>""" % (html.escape(title), css_href, inner)


def build_epub(items):
    bookid = "urn:uuid:wb-value-book-2026"
    files = []
    # cover
    files.append(("OEBPS/cover.xhtml", xhtml_page(
        META["title"],
        '<div class="cover"><div class="t">%s</div><div class="s">%s</div>'
        '<p>%s</p><div class="a">%s<br/>%s</div></div>'
        % (META["title"], META["subtitle"], META["tagline"], META["author"], META["date"]))))
    # chapters
    manifest, spine, navlis = [], [], []
    idx = 0
    for it in items:
        idx += 1
        fn = "chap%02d.xhtml" % idx
        if it["kind"] == "part":
            inner = ('<div class="cover"><div class="s">%s</div><div class="t">%s</div>'
                     '<p>%s</p></div>' % (it["num"], it["name"], it["desc"]))
            label = "%s %s" % (it["num"], it["name"])
        else:
            sec = it["sec"]
            inner = "<h1>%s</h1>\n%s" % (inline(sec["title"]), blocks_to_html(sec["lines"]))
            label = sec["title"]
        files.append(("OEBPS/" + fn, xhtml_page(label, inner)))
        manifest.append('<item id="c%d" href="%s" media-type="application/xhtml+xml"/>' % (idx, fn))
        spine.append('<itemref idref="c%d"/>' % idx)
        navlis.append('<li><a href="%s">%s</a></li>' % (fn, html.escape(label)))
    nav = xhtml_page("目录", '<nav xmlns:epub="http://www.idpf.org/2007/ops" epub:type="toc" id="toc">'
                     '<h1>目录</h1><ol>%s</ol></nav>' % "".join(navlis))
    files.append(("OEBPS/nav.xhtml", nav))
    navpoints = "".join(
        '<navPoint id="n%d" playOrder="%d"><navLabel><text>%s</text></navLabel>'
        '<content src="chap%02d.xhtml"/></navPoint>'
        % (k + 1, k + 1, html.escape(re.findall(r'>([^<]+)</a>', navlis[k])[0]), k + 1)
        for k in range(len(navlis)))
    files.append(("OEBPS/toc.ncx", """<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head><meta name="dtb:uid" content="%s"/></head>
<docTitle><text>%s</text></docTitle>
<navMap>%s</navMap></ncx>""" % (bookid, html.escape(META["title"]), navpoints)))
    files.append(("OEBPS/style.css", EPUB_CSS))
    opf = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">%s</dc:identifier>
<dc:title>%s</dc:title>
<dc:creator>%s</dc:creator>
<dc:language>zh-CN</dc:language>
<dc:description>%s</dc:description>
<meta property="dcterms:modified">%s</meta>
</metadata>
<manifest>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
<item id="css" href="style.css" media-type="text/css"/>
<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>
%s
</manifest>
<spine toc="ncx">
<itemref idref="cover"/>
<itemref idref="nav"/>
%s
</spine>
</package>""" % (bookid, html.escape(META["title"]), META["author"], META["tagline"],
                  datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "\n".join(manifest), "\n".join(spine))
    files.append(("OEBPS/content.opf", opf))
    files.append(("META-INF/container.xml", """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""))
    path = os.path.join(OUT, META["title_safe"] + ".epub")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", zipfile.ZIP_STORED)
        for name, data in files:
            z.writestr(name, data.encode("utf-8"), zipfile.ZIP_DEFLATED)
    return path


# ---------- 合并手稿 ----------
def build_manuscript(items):
    lines = ["# %s" % META["title"], "", "> %s" % META["subtitle"], "",
             "> %s ｜ %s ｜ %s" % (META["tagline"], META["author"], META["date"]), "",
             "---", "", "# 目录", ""]
    n = 0
    for it in items:
        if it["kind"] == "part":
            lines.append("**%s %s**" % (it["num"], it["name"]))
        else:
            n += 1
            lines.append("%d. %s" % (n, it["sec"]["title"]))
    lines += ["", "---", ""]
    for it in items:
        if it["kind"] == "part":
            lines += ["", "> **%s · %s** —— %s" % (it["num"], it["name"], it["desc"]), "", "---", ""]
            continue
        sec = it["sec"]
        lines.append("# " + sec["title"])
        lines += sec["lines"]
        lines += ["", "---", ""]
    path = os.path.join(OUT, META["title_safe"] + "_全书手稿.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


if __name__ == "__main__":
    sections = parse_sections()
    items = make_items(sections)
    WORDS = sum(len(re.sub(r"[\s#|>\-*]", "", "".join(s["lines"]))) + len(s["title"]) for s in sections)
    globals()["WORDS"] = WORDS
    h = build_html(items)
    rep = ["节数: %d" % len(sections), "含分部页的渲染项: %d" % len(items),
           "正文字数(约): %d" % WORDS,
           "输出: 仅 HTML 在线阅读版（不含 EPUB / Markdown）"]
    rep.append("%s %d bytes" % (os.path.basename(h), os.path.getsize(h)))
    with open(os.path.join(OUT, "_build.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(rep))
