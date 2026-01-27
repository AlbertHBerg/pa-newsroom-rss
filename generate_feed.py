import time
import html
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import format_datetime

BASE_URL = "https://www.paconsulting.com"
NEWSROOM_URL = "https://www.paconsulting.com/newsroom?filterContentType=InTheMedia"
MAX_ITEMS = 10
TIMEOUT = 30

HEADOUT)HEADERS = {
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_exc = e
            time.sleep(1.5 * (i + 1))
    raise last_exc

def get_meta(soup, prop):
    tag = soup.find("meta", property=prop)
    return tag["content"].strip() if tag and tag.get("content") else ""

def cdata(text):
    if text is None:
        return "<![CDATA[]]>"
    text = text.replace("&amp;", "&")
    text = text.replace("&", "&amp;")
    text = text.replace("]]>", "]]&gt;")
    return f"<![CDATA[{text}]]>"

# ----------------------------------------
# NEW: extract article links + publication dates
# ----------------------------------------

def extract_article_links(list_html):
    soup = BeautifulSoup(list_html, "html.parser")
    items = []

    for card in soup.select("a.search-result"):
        label_el = card.select_one(".search-result__label")
        if not label_el:
            continue
        if "In The Media" not in label_el.get_text(strip=True):
            continue

        href = card.get("href")
        if not href.startswith("https://www.paconsulting.com/newsroom/"):
            continue

        # extract PA's date text
        date_el = card.select_one(".search-result__date")
        date_text = date_el.get_text(strip=True) if date_el else None

        items.append((href, date_text))

    uniq = []
    for href, d in items:
        if href not in [x[0] for x in uniq]:
            uniq.append((href, d))

    return uniq[:MAX_ITEMS]

# ----------------------------------------
# MAIN RSS BUILDER
# ----------------------------------------

def parse_pa_date(date_text):
    """
    Convert '14 January 2026' → RFC822 pubDate.
    Fallback to now() if parsing fails.
    """
    if not date_text:
        return format_datetime(datetime.utcnow())

    try:
        dt = datetime.strptime(date_text, "%d %B %Y")
        return format_datetime(dt)
    except Exception:
        return format_datetime(datetime.utcnow())

def build_items_html(article_tuples):
    items = ""
    for url, raw_date in article_tuples:

        try:
            html_content = fetch(url)
        except Exception:
            continue

        soup = BeautifulSoup(html_content, "html.parser")

        title = get_meta(soup, "og:title") or (soup.title.get_text(strip=True) if soup.title else "")
        description = get_meta(soup, "og:description") or ""
        image = get_meta(soup, "og:image") or ""

        # NEW: real publication date
        pub_date = parse_pa_date(raw_date)

        enclosure = ""
        if image:
            enclosure = f'<enclosure url="{html.escape(image)}" type="image/jpeg" />'

        items += f"""
    <item>
      <title>{cdata(title)}</title>
      <link>{html.escape(url)}</link>
      <guid>{html.escape(url)}</guid>
      <description>{cdata(description)}</description>
      <pubDate>{pub_date}</pubDate>
      {enclosure}
    </item>"""

    return items

# ----------------------------------------
# MAIN
# ----------------------------------------

def main():
    list_html = fetch(NEWSROOM_URL)
    article_tuples = extract_article_links(list_html)

    # fallback if PA changes their filter
    if len(article_tuples) < MAX_ITEMS:
        try:
            alt_html = fetch("https://www.paconsulting.com/newsroom")
            extra = extract_article_links(alt_html)
            for tup in extra:
                if tup[0] not in [x[0] for x in article_tuples] and len(article_tuples) < MAX_ITEMS:
                    article_tuples.append(tup)
        except:
            pass

    items_xml = build_items_html(article_tuples)

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>PA Consulting – In the Media</title>
  <link>{NEWSROOM_URL}</link>
  <description>Automatically generated feed (In the Media)</description>
  {items_xml}
</channel>
</rss>
"""

    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss)

if __name__ == "__main__":
    main()
``
    "User-Agent": "Mozilla/5.0 (compatible; PA-Newsroom-RSS/1.0)"
}

# ----------------------------------------
# HELPERS
# ----------------------------------------

def fetch(url, retries=3):
    last_exc = None
    for i in range(retries):
        try:
