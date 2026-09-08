import os

from dotenv import load_dotenv

from sources import SOURCES
from collector import (
    get_feed,
    extract_article_text
)
from filters import is_relevant
from dedup import (
    load_seen,
    save_seen,
    make_id,
    is_duplicate
)
from formatter import format_news
from telegram_sender import send_message
from state import (
    load_state,
    save_state,
    can_publish,
    mark_published
)
from ai_summarizer import summarize_news


load_dotenv()


BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)

CHANNEL_USERNAME = os.getenv(
    "CHANNEL_USERNAME",
    "@konkorkhabar"
)


MAX_NEWS_PER_SOURCE = 10


if not BOT_TOKEN:

    raise ValueError(
        "BOT_TOKEN پیدا نشد."
    )


if not os.getenv(
    "GEMINI_API_KEY"
):

    raise ValueError(
        "GEMINI_API_KEY پیدا نشد."
    )


def main():

    print("=" * 60)

    print(
        "🤖 Konkorkhabar News Bot"
    )

    print(
        "🔎 Starting collection cycle..."
    )

    print(
        f"📤 Destination: "
        f"{CHANNEL_USERNAME}"
    )

    print("=" * 60)


    seen = load_seen()

    state = load_state()


    # -------------------------------------------------
    # FIRST RUN
    # -------------------------------------------------

    if not state.get(
        "initialized",
        False
    ):

        print(
            "🆕 First run detected."
        )

        print(
            "📚 Existing RSS news will "
            "be marked as known."
        )

        print(
            "🚫 No old news will be published."
        )

        for source in SOURCES:

            news_list = get_feed(
                source
            )

            for news in news_list:

                news_id = make_id(
                    news["title"],
                    news["link"]
                )

                seen.add(
                    news_id
                )

        state["initialized"] = True

        save_seen(seen)
        save_state(state)

        print(
            "✅ Initial database created."
        )

        print(
            "➡️ From the next cycle, "
            "only new news will be considered."
        )

        return


    # -------------------------------------------------
    # 15 MINUTE COOLDOWN
    # -------------------------------------------------

    if not can_publish(
        state,
        cooldown_minutes=15
    ):

        print(
            "⏳ 15-minute cooldown is active."
        )

        print(
            "🚫 Nothing will be published."
        )

        return


    candidates = []


    # -------------------------------------------------
    # COLLECT NEW NEWS
    # -------------------------------------------------

    for source in SOURCES:

        print(
            f"\n🔎 Checking: "
            f"{source['name']}"
        )

        try:

            news_list = get_feed(
                source
            )
            print(
    f"📌 دریافت شد: {len(news_list)} خبر"
)

            news_list = news_list[
                :MAX_NEWS_PER_SOURCE
            ]

            for news in news_list:

                title = news["title"]

                summary = news["summary"]

                news_id = make_id(
                    title,
                    news["link"]
                )


                if is_duplicate(
                    news_id,
                    seen
                ):

                    continue


                if not is_relevant(
                    title,
                    summary
                ):

                    print(
                        f"⏭️ Irrelevant: "
                        f"{title}"
                    )

                    seen.add(
                        news_id
                    )

                    continue


                candidates.append(
                    (
                        news_id,
                        news
                    )
                )

        except Exception as e:

            print(
                f"❌ Error processing "
                f"{source['name']}: {e}"
            )


    if not candidates:

        print(
            "\n📭 No new relevant news."
        )

        save_seen(seen)

        return


    # -------------------------------------------------
    # NEWEST FIRST
    # -------------------------------------------------

    candidates.reverse()


    print(
        f"\n📰 New candidates: "
        f"{len(candidates)}"
    )


    # -------------------------------------------------
    # TRY CANDIDATES UNTIL ONE IS PUBLISHED
    # -------------------------------------------------

    for news_id, news in candidates:

        title = news["title"]

        link = news["link"]


        print(
            f"\n📰 Candidate:"
            f"\n{title}"
        )


        # ---------------------------------------------
        # READ FULL ARTICLE
        # ---------------------------------------------

        article_text = extract_article_text(
            link
        )


        if len(article_text) < 200:

            print(
                "⚠️ Article text is too short."
            )

            continue


        print(
            f"📄 Article text: "
            f"{len(article_text)} characters"
        )


        # ---------------------------------------------
        # AI SUMMARY
        # ---------------------------------------------

        try:

            ai_text = summarize_news(
                title,
                article_text
            )

        except Exception as e:

            print(
                f"❌ Gemini error: {e}"
            )

            continue


        # ---------------------------------------------
        # AI DECIDES SKIP
        # ---------------------------------------------

        if not ai_text:

            print(
                "⏭️ AI decided to skip."
            )

            seen.add(
                news_id
            )

            continue


        # ---------------------------------------------
        # FINAL TELEGRAM MESSAGE
        # ---------------------------------------------

        message = format_news(
            ai_text
        )


        # ---------------------------------------------
        # SEND
        # ---------------------------------------------

        try:

            success = send_message(
                BOT_TOKEN,
                CHANNEL_USERNAME,
                message
            )

            if success:

                print(
                    "✅ NEWS PUBLISHED"
                )

                seen.add(
                    news_id
                )

                mark_published(
                    state
                )

                save_seen(
                    seen
                )

                save_state(
                    state
                )

                return

            else:

                print(
                    "❌ Telegram rejected message."
                )

                return

        except Exception as e:

            print(
                f"❌ Telegram error: {e}"
            )

            return


    # -------------------------------------------------
    # NOTHING PUBLISHED
    # -------------------------------------------------

    save_seen(
        seen
    )

    print(
        "\n📭 No suitable news "
        "was published this cycle."
    )


if __name__ == "__main__":

    main()