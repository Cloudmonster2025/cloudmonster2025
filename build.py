#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
キャリア羅針盤 — 静的サイトジェネレーター
使い方:
  1. articles/ に Markdown 記事を追加(書式は articles/ 内の既存記事を参照)
  2. python3 build.py を実行
  3. docs/ に完成したサイトが出力される(GitHub Pages / Cloudflare Pages にそのまま公開可)
依存ライブラリなし(Python 3 標準機能のみ)。
"""

import os, re, html, datetime, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "articles")
OUT = os.path.join(BASE, "docs")

# ====== サイト設定(自分の情報に書き換える)======
SITE_NAME = "キャリア羅針盤"
SITE_TAGLINE = "迷わない転職のための実務ノート"
SITE_URL = "https://example.com"  # 公開後に自分のURLへ変更(sitemap用)
AUTHOR_NOTE = "メーカーで事業分析・M&A評価に携わる現役会社員が、実体験と一次情報をもとに転職の実務を整理しています。"
# ================================================

with open(os.path.join(BASE, "static", "style.css"), encoding="utf-8") as f:
    CSS = f.read()


def parse_front_matter(text):
    meta, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    return meta, body


def inline_md(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
    return s


def md_to_html(md):
    """必要十分なミニMarkdownコンバーター(見出し/リスト/引用/CTAボックス対応)"""
    out, para, ul, ol = [], [], False, False

    def flush_para():
        nonlocal para
        if para:
            out.append("<p>" + inline_md(" ".join(para)) + "</p>")
            para = []

    def close_lists():
        nonlocal ul, ol
        if ul:
            out.append("</ul>"); ul = False
        if ol:
            out.append("</ol>"); ol = False

    for line in md.splitlines():
        stripped = line.strip()

        # CTAボックス: @cta 名前 | 説明 | URL | ボタン文言
        if stripped.startswith("@cta "):
            flush_para(); close_lists()
            parts = [p.strip() for p in stripped[5:].split("|")]
            name = parts[0] if len(parts) > 0 else ""
            desc = parts[1] if len(parts) > 1 else ""
            url = parts[2] if len(parts) > 2 else "#"
            btn = parts[3] if len(parts) > 3 else "公式サイトで無料登録"
            out.append(
                f'<aside class="cta"><p class="cta-label">PR</p>'
                f"<p class=\"cta-name\">{html.escape(name)}</p>"
                f"<p class=\"cta-desc\">{html.escape(desc)}</p>"
                f'<a class="cta-btn" href="{html.escape(url)}" rel="nofollow sponsored" target="_blank">{html.escape(btn)}</a></aside>'
            )
            continue

        if not stripped:
            flush_para(); close_lists(); continue
        if stripped.startswith("### "):
            flush_para(); close_lists(); out.append("<h3>" + inline_md(stripped[4:]) + "</h3>"); continue
        if stripped.startswith("## "):
            flush_para(); close_lists(); out.append("<h2>" + inline_md(stripped[3:]) + "</h2>"); continue
        if stripped.startswith("> "):
            flush_para(); close_lists(); out.append("<blockquote>" + inline_md(stripped[2:]) + "</blockquote>"); continue
        if re.match(r"^[-*] ", stripped):
            flush_para()
            if ol: out.append("</ol>"); ol = False
            if not ul: out.append("<ul>"); ul = True
            out.append("<li>" + inline_md(stripped[2:]) + "</li>"); continue
        if re.match(r"^\d+\. ", stripped):
            flush_para()
            if ul: out.append("</ul>"); ul = False
            if not ol: out.append("<ol>"); ol = True
            out.append("<li>" + inline_md(re.sub(r"^\d+\. ", "", stripped)) + "</li>"); continue
        para.append(stripped)

    flush_para(); close_lists()
    return "\n".join(out)


def page(title, description, body, is_home=False):
    home_link = "index.html"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<style>{CSS}</style>
</head>
<body>
<header class="site-head">
  <a class="brand" href="{home_link}">{SITE_NAME}</a>
  <p class="tagline">{SITE_TAGLINE}</p>
</header>
{body}
<footer class="site-foot">
  <p>{AUTHOR_NOTE}</p>
  <p class="fine">当サイトはアフィリエイト広告(PR)を含みます。&copy; {datetime.date.today().year} {SITE_NAME}</p>
</footer>
</body>
</html>"""


def build():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    posts = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".md"):
            continue
        with open(os.path.join(SRC, fn), encoding="utf-8") as f:
            meta, body = parse_front_matter(f.read())
        slug = os.path.splitext(fn)[0]
        posts.append({
            "slug": slug,
            "title": meta.get("title", slug),
            "date": meta.get("date", ""),
            "category": meta.get("category", "その他"),
            "description": meta.get("description", ""),
            "html": md_to_html(body),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)

    # 記事ページ
    for p in posts:
        body = f"""<main class="article">
  <p class="eyebrow">{html.escape(p['category'])} ・ {html.escape(p['date'])}</p>
  <h1>{html.escape(p['title'])}</h1>
  {p['html']}
  <p class="back"><a href="index.html">← 記事一覧へ戻る</a></p>
</main>"""
        with open(os.path.join(OUT, p["slug"] + ".html"), "w", encoding="utf-8") as f:
            f.write(page(f"{p['title']} | {SITE_NAME}", p["description"], body))

    # トップページ
    cards = "\n".join(
        f"""<a class="card" href="{p['slug']}.html">
  <p class="card-cat">{html.escape(p['category'])}</p>
  <p class="card-title">{html.escape(p['title'])}</p>
  <p class="card-desc">{html.escape(p['description'])}</p>
  <p class="card-date">{html.escape(p['date'])}</p>
</a>""" for p in posts)
    hero = f"""<section class="hero">
  <p class="hero-vertical">転職は、準備が九割。</p>
  <div class="hero-main">
    <h1>キャリアの意思決定を、<br>勘ではなく設計で。</h1>
    <p>{AUTHOR_NOTE}</p>
  </div>
</section>
<main class="grid">
{cards}
</main>"""
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(f"{SITE_NAME} | {SITE_TAGLINE}", SITE_TAGLINE, hero, is_home=True))

    # sitemap
    urls = [f"{SITE_URL}/index.html"] + [f"{SITE_URL}/{p['slug']}.html" for p in posts]
    sitemap = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
    sitemap += "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls) + "\n</urlset>\n"
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    print(f"✅ ビルド完了: 記事 {len(posts)} 本 → {OUT}")


if __name__ == "__main__":
    build()
