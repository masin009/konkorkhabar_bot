import os

from dotenv import load_dotenv

from sources import SOURCES
from collector import get_feed
from filters import is_relevant
from dedup import (
    load_seen,
    save_seen,
    make_id,
    is_duplicate
)
from formatter import format_news
from telegram_sender import send_message


# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@konkorkhabar")

MAX_NEWS_PER_SOURCE = 10


if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN پیدا نشد.")

if not CHANNEL_USERNAME:
    raise ValueError("CHANNEL_USERNAME پیدا نشد.")


def main():
    print("=" * 60)
    print("🤖 Konkorkhabar News Bot")
    print("🔎 Starting one news collection cycle...")
    print(f"📤 Destination: {CHANNEL_USERNAME}")
    print(f"📰 Sources: {len(SOURCES)}")
    print("=" * 60)

    seen = load_seen()

    total_checked = 0
    total_relevant = 0
    total_published = 0
    total_duplicate = 0

    for source in SOURCES:

        print(f"\n🔎 Checking: {source['name']}")

        try:
            news_list = get_feed(source)

            if not news_list:
                print("⚠️ No news received.")
                continue

            # Limit the number of items processed from each source
            news_list = news_list[:MAX_NEWS_PER_SOURCE]

            print(f"📥 Received: {len(news_list)} news")

            # Oldest first → newest last
            for news in reversed(news_list):

                total_checked += 1

                title = news["title"]
                summary = news["summary"]

                # -----------------------------
                # Relevance filter
                # -----------------------------
                if not is_relevant(title, summary):
                    print(f"⏭️ Irrelevant: {title}")
                    continue

                total_relevant += 1

                # -----------------------------
                # Duplicate detection
                # -----------------------------
                news_id = make_id(
                    title,
                    news["link"]
                )

                if is_duplicate(news_id, seen):
                    total_duplicate += 1
                    print(f"♻️ Duplicate: {title}")
                    continue

                # -----------------------------
                # Format message
                # -----------------------------
                message = format_news(news)

                # -----------------------------
                # Send to Telegram
                # -----------------------------
                try:

                    success = send_message(
                        BOT_TOKEN,
                        CHANNEL_USERNAME,
                        message
                    )

                    if success:

                        print(f"✅ Published: {title}")

                        seen.add(news_id)
                        total_published += 1

                    else:

                        print(f"❌ Telegram rejected: {title}")

                except Exception as e:

                    print(
                        f"❌ Telegram error for "
                        f"'{title}': {e}"
                    )

                    # Do not mark as seen
                    # so it can be retried later.

        except Exception as e:

            print(
                f"❌ Error while processing "
                f"{source['name']}: {e}"
            )

            # Continue with the next source
            continue

    # Save database after the whole cycle
    save_seen(seen)

    print("\n" + "=" * 60)
    print("📊 Cycle finished")
    print(f"🔎 Checked: {total_checked}")
    print(f"🎯 Relevant: {total_relevant}")
    print(f"♻️ Duplicates: {total_duplicate}")
    print(f"📤 Published: {total_published}")
    print("=" * 60)


if __name__ == "__main__":
    main()