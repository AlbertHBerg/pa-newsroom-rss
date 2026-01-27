import time
import html
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import format_datetime

# ----------------------------------------
# KONFIGURATION
# ----------------------------------------
BASE_URL = "https://www.paconsulting.com"
NEWSROOM_URL = "https://www.paconsulting.com/newsroom?filterContentType=InTheMedia"
MAX_ITEMS = 10
TIMEOUT = 30

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PA-Newsroom-RSS/1.0)"
}

# ----------------------------------------
# HJÄLPFUNKTIONER
# ----------------------------------------

def fetch(url, retries=3):
    """Fetch HTML with retry/backoff."""
    last_exc = None
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last_exc = e
            time.sleep(1.5 * (i + 1))
    raise last_exc


def get_meta(soup, prop):
    """Extract OpenGraph meta tag content."""
    tag = soup.find("meta", property=prop)
    return tag["content"].strip() if tag and tag.get("content") else ""


def cdata(text):
    """Wrap text safely in CDATA and escape harmful sequences."""
    if text is None:
        return "<![CDATA[]]>"
    # Fix double-encoded ampersands first
    text = text.replace("&amp;", "&")
    # Escape standalone &
    text = text.replace("&", "&amp;")
    # Prevent CDATA termination inside content
    text = text.replace("]]>", "]]&gt;")
    return f"<![CDATA[{text}]]>"


def extract_article_links(list_html):
    """
    Extract only 'In The Media' article URLs from PA's newsroom list.
    Looks specifically for <a class="search-result"> blocks
    with an inner label containing 'In The Media'.
    """
    soup = BeautifulSoup(list_html, "html.parser")
    urls = []

    for card in soup.select("a.search-result"):
        label_el = card.select_one(".search-result__label")
        if not label_el:
            continue

        label = label_el.get_text(strip=True)
        if "In The Media" not in label:
            continue  # skip Press releases or anything else

        href = card.get("href")
        if href and href.startswith("https://www.paconsulting.com/newsroom/"):
            urls.append(href)

    # dedupe + cap items
    uniq = []
    for u in urls:
        if u not in uniq:
            uniq.append(u)
    return uniq[:MAX_ITEMS]


# ----------------------------------------
# RSS-GENERERING
# ----------------------------------------

def build_items_html(urls):
    items = ""
    for url in urls:
        try:
            html_content = fetch(url)
        except Exception:
            continue

        soup = BeautifulSoup(html_content, "html.parser")

        title = get_meta(soup, "og:title")
        description = get_meta(soup, "og:description")
        image = get_meta(soup, "og:image")

        # fallback för titel
        if not title and soup.title:
            title = soup.title.get_text(strip=True)

        # fallback för beskrivning
        if not description:
            p = soup.find("p")
            description = p.get_text(strip=True) if p else ""

        pub_date = format_datetime(datetime.utcnow())

        enclosure = ""
        if image:
            # escape image URL
            img = html.escape(image)
            enclosure = f'<enclosure url="{img}" type="image/jpeg" />'

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
    urls = extract_article_links(list_html)

    # fallback om filtret laddade för lite eller zero
    if len(urls) < MAX_ITEMS:
        try:
            alt_html = fetch("https://www.paconsulting.com/newsroom")
            alt_urls = extract_article_links(alt_html)
            for u in alt_urls:
                if u not in urls and len(urls) < MAX_ITEMS:
                    urls.append(u)
        except Exception:
            pass

    items_xml = build_items_html(urls)

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
