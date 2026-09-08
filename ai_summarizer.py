import os
import time
import requests

from dotenv import load_dotenv


load_dotenv()


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = "gemini-2.0-flash"

API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def summarize_news(title, article_text):

    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY پیدا نشد."
        )


    prompt = f"""
تو ویراستار یک کانال خبری تخصصی درباره کنکور، مدارس، آموزش و پرورش و دانشگاه‌های ایران هستی.

متن خبر زیر را به یک خبر کوتاه و دقیق برای تلگرام تبدیل کن.

قوانین:
- فقط از اطلاعات متن استفاده کن.
- چیزی حدس نزن.
- تاریخ، عدد، نام سازمان و مهلت‌ها را حفظ کن.
- ابتدا تیتر کوتاه بده.
- سپس ۱ تا ۳ پاراگراف کوتاه.
- لینک و نام منبع را ننویس.
- تبلیغ یا خبر بی‌ارزش را منتشر نکن.
- اگر ارزش انتشار ندارد فقط بنویس SKIP.
- ایموجی استفاده نکن.

عنوان:
{title}

متن:
{article_text}
"""


    payload = {

        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],

        "generationConfig": {

            "temperature": 0.2,

            "maxOutputTokens": 400

        }

    }


    for attempt in range(3):

        try:

            response = requests.post(

                API_URL,

                headers={

                    "Content-Type": "application/json",

                    "x-goog-api-key": GEMINI_API_KEY

                },

                json=payload,

                timeout=90

            )


            if not response.ok:

                raise RuntimeError(
                    f"Gemini Error {response.status_code}: "
                    f"{response.text[:500]}"
                )


            data = response.json()


            text = (
                data["candidates"][0]
                ["content"]
                ["parts"][0]
                ["text"]
            )


            text = text.strip()


            if text.upper() == "SKIP":

                return None


            return text


        except Exception as e:

            print(
                f"⚠️ Gemini attempt {attempt+1}/3 failed: {e}"
            )

            if attempt < 2:

                time.sleep(5)


    raise RuntimeError(
        "Gemini بعد از ۳ تلاش پاسخ نداد."
    )