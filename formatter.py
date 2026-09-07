def format_news(news):

    title = news["title"].strip()

    summary = news["summary"].strip()

    source = news["source"]

    link = news["link"]

    # اگر خلاصه خیلی طولانی باشد
    if len(summary) > 700:

        summary = summary[:700].rsplit(
            " ",
            1
        )[0] + "..."

    text = f"""🔴 {title}

{summary}

🔗 منبع: {source}
{link}

📒 @konkorkhabar"""

    return text