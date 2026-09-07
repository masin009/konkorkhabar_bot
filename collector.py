import feedparser
import requests
from bs4 import BeautifulSoup


def clean_html(text):

    if not text:
        return ""

    soup = BeautifulSoup(text, "html.parser")

    return soup.get_text(" ", strip=True)


def get_feed(source):

    try:

        response = requests.get(
            source["url"],
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        feed = feedparser.parse(response.content)

        results = []

        for item in feed.entries:

            title = clean_html(
                item.get("title", "")
            )

            summary = clean_html(
                item.get("summary", "")
            )

            link = item.get(
                "link",
                ""
            )

            published = item.get(
                "published",
                ""
            )

            if not title or not link:
                continue

            results.append({

                "source": source["name"],

                "title": title,

                "summary": summary,

                "link": link,

                "published": published

            })

        return results

    except Exception as e:

        print(
            f"❌ خطا در دریافت {source['name']}: {e}"
        )

        return []