"""Builds the generated parts of the FRONTS 1944 site. Pure Python, no packages needed.

  python -I tools/build.py

What it does, every run:
  1. the roadmap: takes the page the game repo keeps (RTS-merge\\Docs\\roadmap\\fronts-roadmap.html and its img\\),
     wraps it with the site's top bar and foot, and writes roadmap/index.html + roadmap/img/
  2. the devlog: turns content/devlog/*.md into devlog/<slug>/index.html and the list devlog/index.html
  3. the landing page: refills the marked blocks in index.html (top bar, foot, roadmap tally, latest devlog posts)

Edit the roadmap in the game repo, write devlog posts in content/devlog, then run this and commit the result.
"""
import html
import re
import shutil
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
ROADMAP_SRC = Path(r"C:\Playground\UP\RTS-merge\Docs\roadmap")
ITCH = "https://comeandgetsome.itch.io/fronts-1944"
DISCORD = "https://discord.gg/7SDqVMBS3U"  # permanent invite, lands on #welcome
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@400;500;600;700'
         '&family=Saira+Stencil+One&family=Special+Elite&display=swap">')


# ---------------------------------------------------------------------------------------------- the shared chrome
def top(root, here):
    def link(href, label, key, ext=False, cls=""):
        cur = ' aria-current="page"' if key == here else ""
        c = ' class="%s"' % cls if cls else ""
        return '<a href="%s"%s%s>%s</a>' % (href if ext else root + href, c, cur, label)
    return ('<a class="skip" href="#main">Skip to the content</a>\n<header class="site-top">\n  <div class="site-wrap">\n'
            '    <a class="brand" href="%s">FRONTS <span>1944</span></a>\n    <nav class="nav" aria-label="Site">\n      %s\n'
            '    </nav>\n  </div>\n</header>' % (root or "./", "\n      ".join([
                link("#game", "The game", "game", cls="wide"),
                link("roadmap/", "Roadmap", "roadmap"),
                link("devlog/", "Devlog", "devlog"),
                link(DISCORD, "Discord", "discord", ext=True),
                link(ITCH, "Play", "play", ext=True, cls="play")])))


def foot(root):
    return ('<footer class="site-foot">\n  <div class="site-wrap">\n    <div class="cols">\n'
            '      <a class="brand" href="%s">FRONTS <span>1944</span></a>\n'
            '      <ul>\n        <li><a href="%s">Play the free demo on itch.io</a></li>\n        <li><a href="%s">Join the testers on Discord</a></li>\n        <li>Steam page: coming soon</li>\n      </ul>\n'
            '      <ul>\n        <li><a href="%sroadmap/">Roadmap</a></li>\n        <li><a href="%sdevlog/">Devlog</a></li>\n      </ul>\n'
            '    </div>\n'
            '    <p class="fine">FRONTS 1944 is made by one developer in Hungary. Pictures marked <i>Concept</i> are generated targets '
            'for the look and are not the game; every other picture is the game\'s own frame.</p>\n'
            '    <p class="fine">&copy; 2026 FRONTS 1944</p>\n  </div>\n</footer>' % (root or "./", ITCH, DISCORD, root, root))


def fill(text, name, content):
    pat = re.compile(r"<!--%s-->.*?<!--/%s-->" % (name, name), re.S)
    if not pat.search(text):
        sys.exit("marker <!--%s--> missing" % name)
    return pat.sub(lambda m: "<!--%s-->\n%s\n<!--/%s-->" % (name, content, name), text)


def head(title, desc, root, url, extra=""):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n<link rel="canonical" href="https://fronts1944.com/%s">\n'
            '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n'
            '<meta property="og:image" content="https://fronts1944.com/assets/img/social-card.jpg">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
            '<link rel="icon" href="%sassets/icon-32.png" sizes="32x32">\n<link rel="apple-touch-icon" href="%sassets/icon-180.png">\n'
            '%s\n<link rel="stylesheet" href="%sassets/chrome.css">\n%s</head>\n'
            % (html.escape(title), html.escape(desc), url, html.escape(title), html.escape(desc), root, root, FONTS, root, extra))


# ---------------------------------------------------------------------------------------------- 1. the roadmap
STEP = re.compile(r'\{ s: "(done|now|ahead)", when: "([^"]*)", title: "([^"]*)"')


def roadmap():
    page = (ROADMAP_SRC / "fronts-roadmap.html").read_text(encoding="utf-8")
    page = re.sub(r"<title>.*?</title>\n?", "", page, count=1)
    page = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>\n?', "", page, count=1)
    out = SITE / "roadmap"
    out.mkdir(exist_ok=True)
    doc = (head("Roadmap – FRONTS 1944", "The FRONTS 1944 roadmap: every step of the game's development, taken or planned, on one operations map.",
                "../", "roadmap/", '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n')
           + "<body>\n" + top("../", "roadmap") + '\n<main id="main">\n' + page.strip() + "\n</main>\n" + foot("../") + "\n</body>\n</html>\n")
    (out / "index.html").write_text(doc, encoding="utf-8", newline="\n")
    if (out / "img").exists():
        shutil.rmtree(out / "img")
    shutil.copytree(ROADMAP_SRC / "img", out / "img")
    steps = STEP.findall(page)
    print("roadmap: %d objectives, %d pictures" % (len(steps), len(list((out / "img").glob("*.jpg")))))
    return steps


def tally(steps):
    n = {k: sum(1 for s in steps if s[0] == k) for k in ("done", "now", "ahead")}
    total = len(steps)
    nxt = [s for s in steps if s[0] == "now"] + [s for s in steps if s[0] == "ahead"][:2]
    return ('      <div class="tally"><div class="t-done"><b>%d</b><span>objectives taken</span></div>'
            '<div class="t-now"><b>%d</b><span>under attack</span></div><div class="t-ahead"><b>%d</b><span>ahead</span></div></div>\n'
            '      <div class="bar" role="img" aria-label="%d of %d objectives taken"><i class="b-done" style="width:%.2f%%"></i>'
            '<i class="b-now" style="width:%.2f%%"></i><i class="b-ahead" style="width:%.2f%%"></i></div>\n'
            '      <ul class="next">%s</ul>\n      <p></p>'
            % (n["done"], n["now"], n["ahead"], n["done"], total, 100 * n["done"] / total, 100 * n["now"] / total, 100 * n["ahead"] / total,
               "".join('<li class="%s"><span><b>%s</b> &middot; %s</span></li>' % (s[0], html.escape(s[2]), html.escape(s[1].lower()))
                       for s in nxt)))


# ---------------------------------------------------------------------------------------------- 2. the devlog
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*", r"<i>\1</i>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return s


def markdown(text, root):
    """A small Markdown: ## and ### headings, paragraphs, - lists, ![alt](picture) on its own line, **bold**, *italic*, links."""
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().splitlines()
        first = lines[0]
        img = re.fullmatch(r"!\[([^\]]*)\]\(([^)\s]+)\)", block.strip())
        if img:
            src = img.group(2) if "://" in img.group(2) else root + img.group(2)
            out.append('<figure><img src="%s" alt="%s" loading="lazy"><figcaption>%s</figcaption></figure>'
                       % (src, html.escape(img.group(1)), inline(img.group(1))))
        elif first.startswith("### "):
            out.append("<h3>%s</h3>" % inline(first[4:]))
        elif first.startswith("## "):
            out.append("<h2>%s</h2>" % inline(first[3:]))
        elif all(l.startswith("- ") for l in lines):
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % inline(l[2:]) for l in lines))
        else:
            out.append("<p>%s</p>" % inline(" ".join(l.strip() for l in lines)))
    return "\n".join(out)


def posts():
    found = []
    for f in sorted((SITE / "content" / "devlog").glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
        if not m:
            sys.exit("%s: no front matter" % f.name)
        meta = dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M))
        for k in ("title", "date", "summary", "image"):
            if k not in meta:
                sys.exit("%s: front matter needs %s" % (f.name, k))
        meta["slug"] = f.stem
        meta["body"] = m.group(2)
        found.append(meta)
    return sorted(found, key=lambda p: p["date"], reverse=True)


POST_CSS = """<link rel="stylesheet" href="{r}assets/site.css">
<style>
.post {{ max-width: 760px; margin: 0 auto; padding: 48px 0 72px; }}
.post h1 {{ font-size: clamp(40px, 7vw, 68px); line-height: .98; margin: 8px 0 18px; }}
.post .hero {{ margin: 0 0 28px; }}
.post h2 {{ font-size: clamp(28px, 4.5vw, 38px); margin: 34px 0 10px; }}
.post h3 {{ margin: 26px 0 6px; }}
.post p, .post li {{ font-size: 19px; }}
.post ul {{ padding-left: 22px; display: grid; gap: 6px; }}
.post li::marker {{ color: var(--olive); }}
.post figure {{ margin: 26px 0; }}
.post figure img {{ border: 2px solid var(--ink); box-shadow: 5px 6px 0 var(--shade); width: 100%; height: auto; }}
.post figcaption {{ font: 400 13px/1.4 var(--type); color: var(--ink-soft); margin-top: 10px; letter-spacing: .03em; }}
.post a {{ color: var(--own); }}
.back {{ font: 600 15px/1 var(--body); letter-spacing: .08em; text-transform: uppercase; }}
.posts {{ display: grid; gap: 22px; grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr)); margin-top: 26px; }}
.posts a.card {{ text-decoration: none; color: inherit; display: block; }}
.posts .when {{ font: 400 13px/1 var(--type); letter-spacing: .08em; color: var(--ink-soft); }}
</style>
"""


def nice(date):
    y, mo, d = date.split("-")
    return "%d %s %s" % (int(d), ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                                  "October", "November", "December"][int(mo) - 1], y)


def cards(items, root):
    return '<div class="posts">%s</div>' % "".join(
        '<a class="card" href="%sdevlog/%s/"><div class="shot"><img src="%s%s" width="800" height="450" loading="lazy" alt=""></div>'
        '<div class="txt"><span class="when">%s</span><h3>%s</h3><p>%s</p></div></a>'
        % (root, p["slug"], root, p["image"], nice(p["date"]), html.escape(p["title"]), html.escape(p["summary"])) for p in items)


def devlog(items):
    base = SITE / "devlog"
    for d in base.iterdir():
        if d.is_dir():
            shutil.rmtree(d)
    for p in items:
        r = "../../"
        body = ('<article class="post wrap">\n<a class="back" href="../">&larr; All posts</a>\n<div class="eyebrow" style="margin-top:22px">Devlog &middot; %s</div>\n'
                '<h1>%s</h1>\n<figure class="hero"><img src="%s%s" alt=""></figure>\n%s\n</article>'
                % (nice(p["date"]), html.escape(p["title"]), r, p["image"].replace("-md.", "-lg."), markdown(p["body"], r)))
        doc = (head(p["title"] + " – FRONTS 1944 devlog", p["summary"], r, "devlog/%s/" % p["slug"], POST_CSS.format(r=r))
               + "<body>\n" + top(r, "devlog") + '\n<main id="main">\n' + body + "\n</main>\n" + foot(r) + "\n</body>\n</html>\n")
        (base / p["slug"]).mkdir()
        (base / p["slug"] / "index.html").write_text(doc, encoding="utf-8", newline="\n")
    r = "../"
    body = ('<section class="wrap" style="padding-block:48px 72px">\n<div class="eyebrow">Dispatches from the workshop</div>\n'
            '<h1 style="font-size:clamp(48px,9vw,92px);line-height:.95;margin:6px 0 10px">Devlog</h1>\n'
            '<p class="lede">What was built, what broke and what comes next.</p>\n%s\n</section>' % cards(items, r))
    doc = (head("Devlog – FRONTS 1944", "The FRONTS 1944 devlog: what was built, what broke and what comes next.", r, "devlog/", POST_CSS.format(r=r))
           + "<body>\n" + top(r, "devlog") + '\n<main id="main">\n' + body + "\n</main>\n" + foot(r) + "\n</body>\n</html>\n")
    (base / "index.html").write_text(doc, encoding="utf-8", newline="\n")
    print("devlog: %d posts" % len(items))


# ---------------------------------------------------------------------------------------------- 3. the landing page
def landing(steps, items):
    p = SITE / "index.html"
    t = p.read_text(encoding="utf-8")
    t = fill(t, "TOP", top("", "home"))
    t = fill(t, "FOOT", foot(""))
    t = fill(t, "ROADMAP-TALLY", tally(steps))
    t = fill(t, "DEVLOG-LATEST", cards(items[:3], "") if items else "<p>The first dispatch is on its way.</p>")
    p.write_text(t, encoding="utf-8", newline="\n")
    print("landing: refilled")


if __name__ == "__main__":
    steps = roadmap()
    items = posts()
    devlog(items)
    landing(steps, items)
