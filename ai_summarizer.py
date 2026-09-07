import os
import requests


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-2.5-flash"

API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def summarize_news(title, article_text):

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY پیدا نشد.")

    prompt = f"""
تو ویراستار یک کانال خبری تخصصی درباره کنکور، مدارس، آموزش و پرورش و دانشگاه‌های ایران هستی.

وظیفه تو این است که متن خبر زیر را به یک خبر کوتاه، دقیق و قابل انتشار در کانال تلگرام تبدیل کنی.

قوانین بسیار مهم:

1. فقط بر اساس اطلاعات موجود در متن خبر بنویس.
2. هیچ اطلاعاتی را حدس نزن یا از خودت اضافه نکن.
3. تاریخ‌ها، اعداد، مهلت‌ها، نام سازمان‌ها و تصمیمات مهم را حفظ کن.
4. خبر را واضح و روان به فارسی بنویس.
5. ابتدا یک تیتر کوتاه و دقیق بنویس.
6. سپس 1 تا 4 پاراگراف کوتاه برای توضیح خبر بنویس.
7. از زیاده‌گویی، مقدمه‌های بی‌اهمیت و تکرار خودداری کن.
8. نام سایت، منبع خبر، لینک سایت یا عبارت «منبع» را ننویس.
9. از عبارت‌هایی مثل «طبق گزارش سایت...» استفاده نکن.
10. تبلیغات، مطالب غیرخبری، اخبار نامرتبط و مطالبی که اطلاعات کافی برای یک خبر قابل انتشار ندارند را منتشر نکن.
11. اگر خبر ارزش انتشار ندارد یا متن برای تشخیص خبر کافی نیست، فقط بنویس:
SKIP
12. از ایموجی استفاده نکن.
13. خروجی باید مستقیماً قابل انتشار در تلگرام باشد.
14. هیچ توضیحی درباره کاری که انجام دادی ننویس.

عنوان خبر:
{title}

متن کامل خبر:
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
            "maxOutputTokens": 700
        }
    }

    response = requests.post(
        API_URL,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        },
        json=payload,
        timeout=60
    )

    if not response.ok:
        raise RuntimeError(
            f"Gemini API Error {response.status_code}: "
            f"{response.text[:1000]}"
        )

    data = response.json()

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(
            f"پاسخ غیرمنتظره از Gemini: {data}"
        )

    text = text.strip()

    if text.upper() == "SKIP":
        return None

    return text