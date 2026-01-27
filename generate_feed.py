import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import format_datetime

BASE_URL = "https://www.paconsulting.com"
NEWSROOM_URL = "https://www.paconsulting.com/newsroom?filterContentType=InTheMedia"
MAX_ITEMS = 10
TIMEOUT = 30

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; PA-Newsroom-RSS/1.0)"
}

def get_meta(soup, prop):
    tag = soup.find("meta", property=prop)
    return tag["content"].strip() if tag and tag.get("content") else ""

def fetch(url):
    return requests.get(url, headers=headers, timeout=TIMEOUT).text

def main():
    html = fetch(NEWSROOM_URL)
    soup = BeautifulSoup(html, "html.parser")

    # Hämta länkar till artiklar (begränsa till MAX_ITEMS)
    links = []
    for a in soup.select("a[href^='/newsroom/']"):
        href = a.get("href")
        if not href:
            continue
        if href.startswith("/newsroom/") and href not in links:
            links.append(href)
        if len(links) >= MAX_ITEMS:
            break

    items_xml = ""

    for href in links:
        url = BASE_URL + href
        article_html = fetch(url)
        article_soup = BeautifulSoup(article_html, "html.parser")

        title = get_meta(article_soup, "og:title") or article_soup.title.get_text(strip=True)
        description = get_meta(article_soup, "og:description")
        image = get_meta(article_soup, "og:image")

        # Fallbacks om något saknas
        if not description:
            # Försök hitta ingress i body om og:description saknas
            p = article_soup.find("p")
            description = p.get_text(strip=True) if p else ""

        pub_date = format_datetime(datetime.utcnow())

        # enclosure används ofta för bilder i RSS
        enclosure = f'<enclosure url="{image}" type="image/jpeg" />' if image else ""

        items_xml += f"""
    <item>
      <title><![CDATA[{title}]]></title>
      <link>{url}</link>
      <guid>{url}</guid>
      <description><![CDATA[{description}]]></description>
      <pubDate>{pub_date}</pubDate>
      {enclosure}
    </item>"""

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>PA Consulting – In the Media</title>
  <link>{NEWSROOM_URL}</link>
  <description>Automatically generated feed from PA Consulting newsroom (In the Media)</description>
  {items_xml}
</channel>
</rss>
"""

    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss)

if __name__ == "__main__":
    main()
