import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

def test_google_news():
    q = "Technology"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=8).read()
    root = ET.fromstring(html)
    items = root.findall(".//item")
    print(f"Found {len(items)} articles.")
    for item in items[:2]:
        print(item.findtext("title"))
        print(item.findtext("link"))
        print(item.findtext("pubDate"))

test_google_news()
