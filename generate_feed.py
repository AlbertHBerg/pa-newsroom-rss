import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import format_datetime

BASE_URL = "https://www.paconsulting.com"
NEWSROOM_URL = "https://www.paconsulting.com/newsroom?filterContentType=InTheMedia"
MAX_ITEMS = 10
TIMEOUT = 30

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PA-Newsroom-RSS/1.0)"
}

def fetch(url, retries=3):
    """Fetch HTML with retry + backoff."""
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last = e
            time.sleep(1.5 * (i+1))
    raise last

def get_meta(soup, prop):
    tag = soup.find("meta", property=prop)
    return tag["content"].strip() if tag and tag.get("content") else ""

def extract_article_links(html):
    """
    PA Newsroom uses full URLs for articles:
      https://www.paconsulting.com/newsroom/...
    We select ONLY <a.search-result> inside the listing block.
    """
    soup = BeautifulSoup(html, "html.parser")

    links = []
    for a in soup.select("a.search-result"):
        href = a.get("href")
        if not href:
            continue
        if href.startswith("https://www.paconsulting.com/newsroom/"):
            links.append(href)

    # Remove duplicates and cap at MAX_ITEMS
    uniq = []
    for x in links:
        if x not in uniq:
            uniq.append(x)
    return uniq[:MAX_ITEMS]

def build_items_html(urls):
    items = ""
    for url in urls:
        try:
            article_html = fetch(url)
        except Exception:
            continue

        soup = BeautifulSoup(article_html, "html.parser")

        title = get_meta(soup, "og:title")
        description = get_meta(soup, "og:description")
        image = get_meta(soup, "og:image")

        # Fallbacks
        if not title and soup.title:
            title = soup.title.get_text(strip=True)
        if not description:
            p = soup.find("p")
            description = p.get_text(strip=True) if p else ""

        pub_date = format_datetime(datetime.utcnow())

        enclosure = f'<enclosure url="{image}" type="image/jpeg" />' if image else ""

        items += f"""
    <item>
      <title><![CDATA[{title}]]></title>
      <link>{url}</link>
      <guid>{url}</guid>
      <description><![CDATA[{description}]]></description>
      <pubDate>{pub_date}</pubDate>
      {enclosure}
    </item>"""

    return items

def main():
    list_html = fetch(NEWSROOM_URL)
    urls = extract_article_links(list_html)

    # fallback: om listan är tom, testa utan filter
    if len(urls) == 0:
        alt_html = fetch("https://www.paconsulting.com/newsroom")
        urls = extract_article_links(alt_html)

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
