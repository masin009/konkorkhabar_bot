import os
import time

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


# =========================================
# Environment
# =========================================

load_dotenv()


BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)

CHANNEL_USERNAME = os.getenv(
    "CHANNEL_USERNAME"
)


# =========================================
# Settings
# =========================================

CHECK_INTERVAL = 300

MAX_NEWS_PER_SOURCE = 10


# =========================================
# Validation
# =========================================

if not BOT_TOKEN:

    raise ValueError(
        "BOT_TOKEN در فایل .env پیدا نشد."
    )


if not CHANNEL_USERNAME:

    raise ValueError(
        "CHANNEL_USERNAME در فایل .env پیدا نشد."
    )


# =========================================
# Load database
# =========================================

seen = load_seen()


print("=" * 50)

print(
    "🤖 Konkorkhabar News Bot Started"
)

print(
    f"📤 Destination: {CHANNEL_USERNAME}"
)

print(
    f"📰 Sources: {len(SOURCES)}"
)

print("=" * 50)


# =========================================
# Main Loop
# =========================================

while True:

    try:

        for source in SOURCES:

            print(
                f"\n🔎 Checking: {source['name']}"
            )

            news_list = get_feed(
                source
            )

            # فقط جدیدترین موارد
            news_list = news_list[
                :MAX_NEWS_PER_SOURCE
            ]

            for news in reversed(news_list):

                title = news["title"]

                summary = news["summary"]

                link = news["link"]


                # =================================
                # Relevance filter
                # =================================

                if not is_relevant(
                    title,
                    summary
                ):

                    print(
                        f"⏭️ Not relevant: {title}"
                    )

                    continue


                # =================================
                # Duplicate detection
                # =================================

                news_id = make_id(
                    title,
                    link
                )

                if is_duplicate(
                    news_id,
                    seen
                ):

                    continue


                # =================================
                # Format
                # =================================

                message = format_news(
                    news
                )


                # =================================
                # Send Telegram
                # =================================

                success = send_message(
                    BOT_TOKEN,
                    CHANNEL_USERNAME,
                    message
                )


                if success:

                    print(
                        f"✅ Published: {title}"
                    )

                    seen.add(
                        news_id
                    )

                    save_seen(
                        seen
                    )

                else:

                    print(
                        f"❌ Failed: {title}"
                    )


        print(
            f"\n💤 Sleeping {CHECK_INTERVAL} seconds..."
        )

        time.sleep(
            CHECK_INTERVAL
        )


    except KeyboardInterrupt:

        print(
            "\n🛑 Bot stopped."
        )

        break


    except Exception as e:

        print(
            f"\n❌ Main error: {e}"
        )

        print(
            "🔄 Restarting after 30 seconds..."
        )

        time.sleep(30)