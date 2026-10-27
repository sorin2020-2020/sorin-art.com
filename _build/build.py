#!/usr/bin/env python3
"""Builds sorin-art.com from _build/content.py.

Usage (from the repository root):
    python3 _build/build.py [RAW_CARGO_IMAGE_DIR]

Images
- Every processed image is recorded in _build/images.json, so rebuilding never
  needs the original files again.
- To add new photos, drop them in _build/media/<project-slug>/ (git-ignored) and
  reference them in content.py as "media/<project-slug>/<file>". The first build
  resizes them into assets/img/ and records them in images.json.
"""
import datetime, html, json, os, shutil, sys
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)  # repository root = published site
sys.path.insert(0, HERE)
from content import ARTIST, GROUPS, PROJECTS, ABOUT  # noqa: E402

RAW = sys.argv[1] if len(sys.argv) > 1 else None
MANIFEST = os.path.join(HERE, "images.json")
Image.MAX_IMAGE_PIXELS = None
e = html.escape
DOMAIN = "sorin-art.com"
BASE = f"https://{DOMAIN}/"

# ---------------------------------------------------------------- images
manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
raw_files = {f.split(".")[0][:8]: f for f in os.listdir(RAW)} if RAW and os.path.isdir(RAW) else {}
os.makedirs(os.path.join(OUT, "assets/img"), exist_ok=True)


def _next_name(slug):
    n = 1
    while os.path.exists(os.path.join(OUT, f"assets/img/{slug}-{n:02d}-l.jpg")):
        n += 1
    return f"{slug}-{n:02d}"


def img(key, slug, idx=None):
    """Return {l, m, lw, lh, mw, mh} for an image key, processing it if needed."""
    m = manifest.get(key)
    if m and os.path.exists(os.path.join(OUT, m["l"])):
        return m
    if key.startswith("media/"):
        src = os.path.join(HERE, key)
    elif key in raw_files:
        src = os.path.join(RAW, raw_files[key])
    else:
        raise SystemExit(f"Image '{key}' is not in images.json and no source file was found.")
    im = ImageOps.exif_transpose(Image.open(src))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (236, 237, 239))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    im = im.convert("RGB")
    name = f"{slug}-{idx:02d}" if idx else _next_name(slug)
    out = {}
    for k, edge, q in (("l", 1800, 80), ("m", 900, 76)):
        c = im.copy()
        c.thumbnail((edge, edge), Image.LANCZOS)
        p = f"assets/img/{name}-{k}.jpg"
        c.save(os.path.join(OUT, p), "JPEG", quality=q, optimize=True, progressive=True)
        out[k] = p
        out[k + "w"], out[k + "h"] = c.size
    manifest[key] = out
    return out


def nice_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


# ---------------------------------------------------------------- html helpers
def page(title, body, depth=0, desc=None, cls="", path="", image=None, extra_head=""):
    r = "../" * depth
    desc = desc or f"{ARTIST['name']}, {ARTIST['tagline'][0].lower()}{ARTIST['tagline'][1:]}"
    full = title if title == ARTIST["name"] else f"{title} | {ARTIST['name']}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(full)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{BASE}{path}">
<meta property="og:image" content="{BASE}{image or OG_DEFAULT}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{BASE}{path}">
<link rel="icon" href="{r}assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{r}assets/fonts/archivo-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}assets/css/style.css">
{extra_head}</head>
<body class="{cls}">
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <a class="site-name" href="{r}index.html">{e(ARTIST['name'])}</a>
  <nav aria-label="Main">
    <a href="{r}index.html#work">Work</a>
    <a href="{r}about.html">About</a>
    <a href="#contact">Contact</a>
  </nav>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer" id="contact">
  <p class="footer-lead">Commissions, exhibitions and collaborations</p>
  <p class="footer-mail"><a href="mailto:{e(ARTIST['email'])}">{e(ARTIST['email'])}</a></p>
  <ul class="footer-links">
    <li><a href="{e(ARTIST['instagram'])}" rel="noopener" target="_blank">Instagram</a></li>
    <li>{e(ARTIST['location'])}</li>
    <li>&copy; <span data-year>2026</span> {e(ARTIST['name'])}</li>
  </ul>
</footer>
<script src="{r}assets/js/main.js" defer></script>
</body>
</html>
"""


def yt_thumb(vid):
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"


def last_update(p):
    return max((u["date"] for u in p.get("log", [])), default=None)


def cover_html(p, depth, sizes="(min-width: 1100px) 30vw, (min-width: 640px) 45vw, 92vw"):
    r = "../" * depth
    if p.get("template") == "thesis":
        return f'<img src="{r}assets/thesis/f001.jpg" alt="" loading="lazy" decoding="async" class="is-sketch">'
    if p.get("cover"):
        m = img_meta[p["cover"]]
        return (f'<img src="{r}{m["m"]}" srcset="{r}{m["m"]} {m["mw"]}w, {r}{m["l"]} {m["lw"]}w" '
                f'sizes="{sizes}" width="{m["mw"]}" height="{m["mh"]}" alt="" loading="lazy" decoding="async">')
    return f'<img src="{yt_thumb(p["video"][0])}" alt="" loading="lazy" decoding="async" data-remote>'


def meta_line(p):
    upd = last_update(p)
    if upd:
        return f"{p['medium']}, updated {nice_date(upd)}"
    return ", ".join(x for x in (p["medium"], p["year"]) if x)


def card(p, depth=0):
    r = "../" * depth
    cls = "card"
    if not p.get("cover") and p.get("video"):
        cls += " card--film"
    if p.get("template") == "thesis":
        cls += " card--sketch"
    return f"""<li class="{cls}">
  <a href="{r}work/{p['slug']}.html">
    <span class="card-media">{cover_html(p, depth)}</span>
    <span class="card-title">{e(p['title'])}</span>
    <span class="card-meta">{e(meta_line(p))}</span>
  </a>
</li>"""


def body_html(blocks):
    out = []
    for kind, val in blocks:
        if kind == "p":
            out.append(f"<p>{e(val)}</p>")
        elif kind == "h":
            out.append(f"<h2>{e(val)}</h2>")
        elif kind == "ol":
            out.append("<ol>" + "".join(f"<li>{e(x)}</li>" for x in val) + "</ol>")
        elif kind == "ul":
            out.append("<ul>" + "".join(f"<li>{e(x)}</li>" for x in val) + "</ul>")
        elif kind == "quote":
            text, who = val
            out.append(f"<blockquote><p>{e(text)}</p><footer>{e(who)}</footer></blockquote>")
    return "\n".join(out)


def video_html(p, depth):
    vid, start = p["video"]
    r = "../" * depth
    poster = img_meta[p["cover"]]["l"] if p.get("cover") else None
    poster_img = (f'<img src="{r}{poster}" alt="" loading="lazy">' if poster
                  else f'<img src="{yt_thumb(vid).replace("hqdefault", "maxresdefault")}" alt="" data-remote>')
    watch = f"https://www.youtube.com/watch?v={vid}" + (f"&t={start}s" if start else "")
    return f"""<figure class="video">
  <button class="video-play" type="button" data-video="{vid}" data-start="{start}" aria-label="Play video: {e(p['title'])}">
    {poster_img}
    <span class="video-icon" aria-hidden="true"></span>
  </button>
  <figcaption><a href="{watch}" target="_blank" rel="noopener">Watch on YouTube</a></figcaption>
</figure>"""


def facts_html(p):
    facts = []
    if p.get("year"):
        facts.append(("Year", e(p["year"])))
    facts.append(("Medium", e(p["medium"])))
    facts += [(k, e(v)) for k, v in p.get("meta", [])]
    if p.get("links"):
        facts.append(("Links", "<br>".join(
            f'<a href="{e(u)}"{"" if u.startswith("../") else " target=\"_blank\" rel=\"noopener\""}>{e(t)}</a>'
            for t, u in p["links"])))
    return "\n".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in facts)


def gallery_html(p, keys, title="Images"):
    items = []
    for n, h in enumerate(keys, 1):
        m = img_meta[h]
        items.append(f'<li><a href="../{m["l"]}" data-lightbox data-w="{m["lw"]}" data-h="{m["lh"]}">'
                     f'<img src="../{m["m"]}" width="{m["mw"]}" height="{m["mh"]}" alt="{e(p["title"])}, image {n} of {len(keys)}" loading="lazy" decoding="async"></a></li>')
    return f"""<section class="gallery" aria-label="{e(title)}">
  <h2 class="gallery-title">{e(title)} <span>{len(keys)}</span></h2>
  <ul class="gallery-grid">
{chr(10).join(items)}
  </ul>
</section>"""


def log_html(p):
    entries = sorted(p.get("log", []), key=lambda u: u["date"], reverse=True)
    if not entries:
        return ""
    rows = []
    for u in entries:
        pics = ""
        if u.get("images"):
            pics = '<ul class="log-images">' + "".join(
                f'<li><a href="../{img_meta[k]["l"]}" data-lightbox><img src="../{img_meta[k]["m"]}" width="{img_meta[k]["mw"]}" height="{img_meta[k]["mh"]}" alt="{e(p["title"])}, {e(nice_date(u["date"]))}" loading="lazy" decoding="async"></a></li>'
                for k in u["images"]) + "</ul>"
        title = f'<h3>{e(u["title"])}</h3>' if u.get("title") else ""
        text = "".join(f"<p>{e(t)}</p>" for t in ([u["text"]] if isinstance(u.get("text"), str) else u.get("text", [])))
        rows.append(f"""<li class="log-entry">
  <time datetime="{u['date']}">{e(nice_date(u['date']))}</time>
  <div class="log-body">{title}{text}{pics}</div>
</li>""")
    return f"""<section class="log" aria-labelledby="log-title">
  <h2 id="log-title" class="gallery-title">Progress log <span>{len(entries)}</span></h2>
  <ol class="log-list">
{chr(10).join(rows)}
  </ol>
</section>"""


# ---------------------------------------------------------------- collect images
img_meta = {}
for p in PROJECTS:
    keys = list(dict.fromkeys(p.get("gallery", "").split()))
    for extra in (p.get("cover"), p.get("lead")):
        if extra and extra not in keys:
            keys.append(extra)
    for i, k in enumerate(keys, 1):
        img_meta[k] = img(k, p["slug"], i if len(k) == 8 else None)
    for u in p.get("log", []):
        for k in u.get("images", []):
            img_meta[k] = img(k, p["slug"])
    p["_gallery"] = list(dict.fromkeys(p.get("gallery", "").split()))
portrait = img(ABOUT["portrait"], "portrait", 1)
feat = PROJECTS[0]
OG_DEFAULT = img_meta[feat["lead"]]["l"]

# ---------------------------------------------------------------- clean generated files
for f in ("index.html", "about.html", "404.html"):
    if os.path.exists(os.path.join(OUT, f)):
        os.remove(os.path.join(OUT, f))
shutil.rmtree(os.path.join(OUT, "work"), ignore_errors=True)
os.makedirs(os.path.join(OUT, "work"))
for sub in ("css", "js", "fonts"):
    shutil.rmtree(os.path.join(OUT, "assets", sub), ignore_errors=True)
    shutil.copytree(os.path.join(HERE, "static", sub), os.path.join(OUT, "assets", sub))
shutil.copy(os.path.join(HERE, "static", "favicon.svg"), os.path.join(OUT, "assets", "favicon.svg"))

group_names = dict(GROUPS)
order = [p for g, _ in GROUPS for p in PROJECTS if p["group"] == g]


# ---------------------------------------------------------------- thesis page
def thesis_page(p, prev_p, next_p):
    t = p["thesis"]
    n = t["frames"]
    contents = "\n".join(f"<li><span>{e(c)}</span><span class=\"pg\">{pg}</span></li>" for c, pg in t["contents"])
    changed = "\n".join(f"<li><h3>{e(h)}</h3><p>{e(b)}</p></li>" for h, b in t["changed"])
    return f"""<article class="project thesis">
<div class="project-head">
  <p class="crumb"><a href="../index.html#{p['group']}">{e(group_names[p['group']])}</a></p>
  <h1>{e(p['title'])}</h1>
  <p class="thesis-version">{e(t['version_label'])}</p>
  <p class="standfirst">{e(p['summary'])}</p>
</div>
<div class="thesis-grid">
  <figure class="flipbook" data-flipbook data-frames="{n}" data-src="../assets/thesis/f{{n}}.jpg" data-scroll-scrub>
    <div class="flipbook-stage" tabindex="0" role="img" aria-label="Flipbook: a young man walking through the Amsterdam rain slowly turns into a machine. Use the left and right arrow keys to turn the pages.">
      <img src="../assets/thesis/f001.jpg" width="520" height="803" alt="" draggable="false">
      <span class="flipbook-corner" aria-hidden="true"></span>
    </div>
    <figcaption>
      <div class="flipbook-controls">
        <button type="button" class="flip-play" aria-pressed="false">Flip the pages</button>
        <input type="range" class="flip-range" min="1" max="{n}" value="1" aria-label="Page of the flipbook">
        <output class="flip-count">1 / {n}</output>
      </div>
      <p>{e(t['flip_caption'])}</p>
    </figcaption>
  </figure>
  <div class="prose thesis-text">
{body_html(p['body'])}
    <h2>Where I changed my mind</h2>
    <ul class="changed">
{changed}
    </ul>
    <blockquote class="pull"><p>{e(t['pull_quote'])}</p></blockquote>
    <p class="thesis-download"><a class="button" href="../assets/thesis/{t['pdf']}" download>Download the thesis (PDF, {t['pdf_size']})</a></p>
  </div>
</div>
<div class="project-body thesis-after">
  <section class="contents" aria-labelledby="toc">
    <h2 id="toc">Contents</h2>
    <ol class="toc">
{contents}
    </ol>
  </section>
  <dl class="facts">
{facts_html(p)}
  </dl>
</div>
<nav class="pager" aria-label="More work">
  <a class="pager-prev" href="{prev_p['slug']}.html"><span>Previous</span>{e(prev_p['title'])}</a>
  <a class="pager-next" href="{next_p['slug']}.html"><span>Next</span>{e(next_p['title'])}</a>
</nav>
</article>"""


# ---------------------------------------------------------------- project pages
for i, p in enumerate(order):
    prev_p, next_p = order[i - 1], order[(i + 1) % len(order)]
    if p.get("template") == "thesis":
        html_out = thesis_page(p, prev_p, next_p)
        ogimg = "assets/thesis/f001.jpg"
    else:
        parts = [f"""<article class="project">
<div class="project-head">
  <p class="crumb"><a href="../index.html#{p['group']}">{e(group_names[p['group']])}</a></p>
  <h1>{e(p['title'])}</h1>
  <p class="standfirst">{e(p['summary'])}</p>
</div>"""]
        if p.get("video"):
            parts.append(video_html(p, 1))
        else:
            lead = p.get("lead") or p.get("cover")
            m = img_meta[lead]
            parts.append(f'<figure class="lead"><img src="../{m["l"]}" width="{m["lw"]}" height="{m["lh"]}" alt="{e(p["title"])}" fetchpriority="high"></figure>')
        parts.append(f"""<div class="project-body">
  <div class="prose">
{body_html(p['body'])}
  </div>
  <dl class="facts">
{facts_html(p)}
  </dl>
</div>""")
        parts.append(log_html(p))
        gal = p["_gallery"] if not (p.get("video") and p.get("cover") is None) else []
        if gal:
            parts.append(gallery_html(p, gal))
        parts.append(f"""<nav class="pager" aria-label="More work">
  <a class="pager-prev" href="{prev_p['slug']}.html"><span>Previous</span>{e(prev_p['title'])}</a>
  <a class="pager-next" href="{next_p['slug']}.html"><span>Next</span>{e(next_p['title'])}</a>
</nav>
</article>""")
        html_out = "\n".join(x for x in parts if x)
        ogimg = img_meta[p.get("cover") or feat["lead"]]["l"]
    with open(os.path.join(OUT, "work", p["slug"] + ".html"), "w") as f:
        f.write(page(p["title"], html_out, depth=1, desc=f"{p['title']}: {p['summary']}",
                     cls="is-project" + (" is-thesis" if p.get("template") == "thesis" else ""),
                     path=f"work/{p['slug']}.html", image=ogimg))

# ---------------------------------------------------------------- index
fm = img_meta[feat["lead"]]
thesis = next((p for p in PROJECTS if p.get("template") == "thesis"), None)
groups_html = []
for g, label in GROUPS:
    items = [p for p in PROJECTS if p["group"] == g]
    if g == "in-progress":
        items.sort(key=lambda p: last_update(p) or "", reverse=True)
    if not items:
        continue
    groups_html.append(f"""<section class="group" id="{g}" aria-labelledby="h-{g}">
  <h2 id="h-{g}">{e(label)} <span class="count">{len(items)}</span></h2>
  <ul class="cards">
{chr(10).join(card(p) for p in items)}
  </ul>
</section>""")
jump = "\n".join(f'<li><a href="#{g}">{e(l)}</a></li>' for g, l in GROUPS if any(p["group"] == g for p in PROJECTS))
thesis_band = ""
if thesis:
    thesis_band = f"""<a class="thesis-band" href="work/{thesis['slug']}.html">
  <span class="thesis-band-flip" data-flipbook data-frames="{thesis['thesis']['frames']}" data-src="assets/thesis/f{{n}}.jpg" data-autoplay>
    <img src="assets/thesis/f001.jpg" width="520" height="803" alt="" loading="lazy">
  </span>
  <span class="thesis-band-text">
    <span class="feature-kicker">{e(thesis['thesis']['version_label'])}</span>
    <span class="thesis-band-title">{e(thesis['title'])}</span>
    <span class="feature-sum">{e(thesis['thesis']['band_text'])}</span>
    <span class="thesis-band-link">Read the introduction</span>
  </span>
</a>"""
index_body = f"""<section class="hero">
  <h1 class="wordmark"><span>Sorin</span> <span>Angeleanu</span></h1>
  <div class="hero-foot">
    <p class="tagline">{e(ARTIST['tagline'])}</p>
    <p class="hero-aside">Based in {e(ARTIST['location'])}.<br>Graduated from the Royal Academy of Art, The Hague, 2024.</p>
  </div>
</section>
<a class="feature" href="work/{feat['slug']}.html">
  <span class="feature-media"><img src="{fm['l']}" width="{fm['lw']}" height="{fm['lh']}" alt="{e(feat['title'])}: a visitor's hand on the glowing membrane of the installation" fetchpriority="high"></span>
  <span class="feature-text">
    <span class="feature-kicker">Graduation work</span>
    <span class="feature-title">{e(feat['title'])}</span>
    <span class="feature-sum">{e(feat['summary'])}</span>
  </span>
</a>
{thesis_band}
<div class="work" id="work">
  <nav class="jump" aria-label="Work categories"><ul>{jump}</ul></nav>
{chr(10).join(groups_html)}
</div>"""
with open(os.path.join(OUT, "index.html"), "w") as f:
    f.write(page(ARTIST["name"], index_body, cls="is-home", path=""))

# ---------------------------------------------------------------- about
rows = lambda lst: "\n".join(f"<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>" for a, b in lst)
about_body = f"""<article class="about">
  <h1>About</h1>
  <div class="about-grid">
    <figure class="portrait"><img src="{portrait['l']}" width="{portrait['lw']}" height="{portrait['lh']}" alt="Portrait of {e(ARTIST['name'])}"></figure>
    <div class="prose about-statement">
      {''.join(f'<p>{e(s)}</p>' for s in ABOUT['statement'])}
    </div>
  </div>
  <section class="cv">
    <h2>Selected work and experience</h2>
    <dl class="cv-list">{rows(ABOUT['selected'])}</dl>
    <h2>Education</h2>
    <dl class="cv-list">{rows(ABOUT['education'])}</dl>
    <h2>Skills and tools</h2>
    <dl class="cv-list cv-list--wide">{rows(ABOUT['skills'])}</dl>
  </section>
</article>"""
with open(os.path.join(OUT, "about.html"), "w") as f:
    f.write(page("About", about_body, desc=f"About {ARTIST['name']}, interactive media artist based in {ARTIST['location']}.",
                 cls="is-about", path="about.html", image=portrait["l"]))

# ---------------------------------------------------------------- 404
nf = """<section class="notfound"><h1>Page not found</h1><p>The page may have moved when the site was rebuilt.</p><p><a href="/index.html">Go to all work</a></p></section>"""
with open(os.path.join(OUT, "404.html"), "w") as f:
    f.write(page("Page not found", nf, path="404.html").replace('href="assets/', 'href="/assets/').replace('src="assets/', 'src="/assets/')
            .replace('href="index.html', 'href="/index.html').replace('href="about.html', 'href="/about.html'))

# ---------------------------------------------------------------- domain, seo, housekeeping
open(os.path.join(OUT, "CNAME"), "w").write(DOMAIN + "\n")
open(os.path.join(OUT, ".nojekyll"), "w").close()
shutil.copy(os.path.join(HERE, "static", "README.md"), os.path.join(OUT, "README.md"))
urls = ["", "about.html"] + [f"work/{p['slug']}.html" for p in order]
open(os.path.join(OUT, "sitemap.xml"), "w").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{BASE}{u}</loc></url>\n" for u in urls) + "</urlset>\n")
open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
json.dump(manifest, open(MANIFEST, "w"), indent=1, sort_keys=True)
print("built", len(order), "pages,", len(manifest), "images in manifest")
