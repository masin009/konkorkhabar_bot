import requests


def send_message(
    bot_token,
    channel,
    text
):

    url = (
        f"https://api.telegram.org/"
        f"bot{bot_token}/sendMessage"
    )

    data = {

        "chat_id": channel,

        "text": text,

        "disable_web_page_preview": False

    }

    response = requests.post(
        url,
        data=data,
        timeout=20
    )

    result = response.json()

    if not result.get("ok"):

        print(
            "❌ Telegram Error:",
            result
        )

        return False

    return True