import requests
import feedparser

from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}


def clean_html(text):

    if not text:
        return ""

    soup = BeautifulSoup(text, "html.parser")

    return soup.get_text(
        " ",
        strip=True
    )


def extract_article_text(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        # حذف بخش‌های غیرخبری
        for tag in soup([
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
            "form",
            "noscript",
            "iframe"
        ]):
            tag.decompose()

        # اولویت با article
        containers = []

        article = soup.find("article")

        if article:
            containers.append(article)

        # سپس main
        main = soup.find("main")

        if main:
            containers.append(main)

        # کلاس‌هایی که معمولاً محتوای مقاله هستند
        for element in soup.find_all(
            ["div", "section"],
            class_=True
        ):

            class_name = " ".join(
                element.get("class", [])
            ).lower()

            if any(
                keyword in class_name
                for keyword in [
                    "article",
                    "content",
                    "body",
                    "post",
                    "news"
                ]
            ):
                containers.append(element)

        best_text = ""

        for container in containers:

            paragraphs = []

            for p in container.find_all("p"):

                text = p.get_text(
                    " ",
                    strip=True
                )

                if len(text) >= 40:
                    paragraphs.append(text)

            text = "\n".join(paragraphs)

            if len(text) > len(best_text):
                best_text = text

        # اگر روش بالا جواب نداد
        if len(best_text) < 200:

            paragraphs = []

            for p in soup.find_all("p"):

                text = p.get_text(
                    " ",
                    strip=True
                )

                if len(text) >= 40:
                    paragraphs.append(text)

            best_text = "\n".join(paragraphs)

        # محدود کردن حجم برای AI
        best_text = best_text.strip()

        if len(best_text) > 15000:
            best_text = best_text[:15000]

        return best_text

    except Exception as e:

        print(
            f"⚠️ خطا در خواندن مقاله: {e}"
        )

        return ""


def get_feed(source):

    try:

        response = requests.get(
            source["url"],
            timeout=20,
            headers=HEADERS
        )

        response.raise_for_status()

        feed = feedparser.parse(
            response.content
        )

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

                "published": published,

            })

        return results

    except Exception as e:

        print(
            f"❌ خطا در دریافت "
            f"{source['name']}: {e}"
        )

        return []