import os
import time
import requests

from dotenv import load_dotenv


# ============================================================
# Load environment variables
# ============================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_MODEL = "openrouter/free"

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# ============================================================
# Settings
# ============================================================

MAX_ARTICLE_CHARS = 10000
MAX_OUTPUT_TOKENS = 1000
MAX_RETRIES = 3

CONNECT_TIMEOUT = 15
READ_TIMEOUT = 90


# ============================================================
# Summarizer
# ============================================================

def summarize_news(title, article_text):

    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY پیدا نشد. "
            "مقدار OPENROUTER_API_KEY را در فایل .env بررسی کن."
        )

    # --------------------------------------------------------
    # Limit article size
    # --------------------------------------------------------

    if not article_text:
        return None

    article_text = article_text.strip()

    if len(article_text) > MAX_ARTICLE_CHARS:
        article_text = article_text[:MAX_ARTICLE_CHARS]

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = f"""
تو ویراستار یک کانال خبری تخصصی درباره کنکور، مدارس،
آموزش و پرورش و دانشگاه‌های ایران هستی.

متن خبر زیر را به یک خبر کوتاه، دقیق و قابل انتشار در تلگرام
تبدیل کن.

قوانین بسیار مهم:

- فقط از اطلاعات موجود در متن استفاده کن.
- هیچ اطلاعاتی را حدس نزن یا اضافه نکن.
- تاریخ‌ها، اعداد، نام سازمان‌ها، مهلت‌ها و جزئیات مهم را دقیق حفظ کن.
- ابتدا یک تیتر کوتاه و خبری بنویس.
- سپس ۱ تا ۳ پاراگراف کوتاه و روان بنویس.
- لینک ننویس.
- نام منبع یا نام خبرگزاری را ننویس.
- عبارت «منبع» را ننویس.
- تبلیغات و مطالب غیرخبری را حذف کن.
- اگر خبر ارزش انتشار برای کانال کنکور، مدارس،
  آموزش و پرورش یا دانشگاه‌ها ندارد، فقط بنویس SKIP.
- اگر متن ناقص یا غیرقابل اعتماد است، SKIP بنویس.
- ایموجی استفاده نکن.
- متن نهایی باید به زبان فارسی باشد.
- پاسخ را کوتاه نگه دار.
- قبل از پاسخ نهایی، فقط به اندازه لازم متن را تحلیل کن.
- پاسخ نهایی را مستقیماً ارائه کن.

عنوان:
{title}

متن کامل خبر:
{article_text}
"""

    # --------------------------------------------------------
    # Request payload
    # --------------------------------------------------------

    payload = {
        "model": OPENROUTER_MODEL,

        "messages": [
            {
                "role": "system",
                "content": (
                    "تو یک ویراستار حرفه‌ای اخبار آموزشی ایران هستی. "
                    "دقیق، کوتاه و بدون اضافه کردن اطلاعات عمل کن. "
                    "از پاسخ‌های طولانی و تحلیل اضافی خودداری کن."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        "temperature": 0.2,

        # قبلاً 400 بود و مدل‌های reasoning-heavy
        # قبل از تولید content به سقف می‌رسیدند.
        "max_tokens": MAX_OUTPUT_TOKENS
    }

    # --------------------------------------------------------
    # Headers
    # --------------------------------------------------------

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",

        "HTTP-Referer": (
            "https://github.com/masin009/konkorkhabar_bot"
        ),

        "X-Title": "Konkorkhabar Bot"
    }

    # --------------------------------------------------------
    # Retry loop
    # --------------------------------------------------------

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            print(
                f"🤖 ارسال درخواست به OpenRouter "
                f"(تلاش {attempt}/{MAX_RETRIES})..."
            )

            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
            )

            # ------------------------------------------------
            # HTTP errors
            # ------------------------------------------------

            if not response.ok:

                status_code = response.status_code

                error_text = response.text[:1500]

                # خطاهای موقتی → retry
                if status_code in (408, 429, 500, 502, 503, 504):

                    raise RuntimeError(
                        f"OpenRouter HTTP {status_code}: "
                        f"{error_text}"
                    )

                # خطاهای دائمی → retry نکن
                raise ValueError(
                    f"OpenRouter HTTP {status_code}: "
                    f"{error_text}"
                )

            # ------------------------------------------------
            # Parse JSON
            # ------------------------------------------------

            try:
                data = response.json()

            except ValueError:
                raise RuntimeError(
                    "OpenRouter پاسخ JSON معتبر برنگرداند: "
                    f"{response.text[:1000]}"
                )

            # ------------------------------------------------
            # Choices
            # ------------------------------------------------

            choices = data.get("choices", [])

            if not choices:
                raise RuntimeError(
                    f"OpenRouter هیچ choices برنگرداند: {data}"
                )

            choice = choices[0]

            message = choice.get("message", {})

            text = message.get("content")

            finish_reason = choice.get("finish_reason")

            # ------------------------------------------------
            # Important:
            # Some OpenRouter models return reasoning but
            # content=None when they hit the token limit.
            # ------------------------------------------------

            if text is None:

                reasoning = message.get("reasoning", "")

                print(
                    "⚠️ OpenRouter content خالی است."
                )

                print(
                    f"   finish_reason: {finish_reason}"
                )

                if reasoning:
                    print(
                        f"   reasoning length: "
                        f"{len(reasoning)} characters"
                    )

                # If model hit token limit, retry.
                if finish_reason == "length":

                    raise RuntimeError(
                        "مدل قبل از تولید پاسخ نهایی "
                        "به سقف توکن رسید."
                    )

                raise RuntimeError(
                    f"متن پاسخ OpenRouter خالی است: {data}"
                )

            # ------------------------------------------------
            # Clean response
            # ------------------------------------------------

            text = str(text).strip()

            if not text:

                raise RuntimeError(
                    "OpenRouter متن خالی برگرداند."
                )

            # ------------------------------------------------
            # SKIP
            # ------------------------------------------------

            if text.upper() == "SKIP":
                print("⏭️ Gemini/OpenRouter تصمیم گرفت خبر SKIP شود.")
                return None

            # ------------------------------------------------
            # Successful response
            # ------------------------------------------------

            print(
                "✅ پاسخ OpenRouter با موفقیت دریافت شد."
            )

            return text

        # ====================================================
        # Retryable errors
        # ====================================================

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.RequestException,
        ) as e:

            print(
                f"⚠️ OpenRouter attempt "
                f"{attempt}/{MAX_RETRIES} failed: {e}"
            )

            if attempt < MAX_RETRIES:

                wait_time = 3 * attempt

                print(
                    f"⏳ {wait_time} ثانیه تا تلاش بعدی..."
                )

                time.sleep(wait_time)

        # ====================================================
        # Runtime errors that may be temporary
        # ====================================================

        except RuntimeError as e:

            print(
                f"⚠️ OpenRouter attempt "
                f"{attempt}/{MAX_RETRIES} failed: {e}"
            )

            if attempt < MAX_RETRIES:

                wait_time = 3 * attempt

                print(
                    f"⏳ {wait_time} ثانیه تا تلاش بعدی..."
                )

                time.sleep(wait_time)

        # ====================================================
        # Permanent errors
        # ====================================================

        except ValueError as e:

            print(
                f"❌ OpenRouter error: {e}"
            )

            raise

    # ========================================================
    # All retries failed
    # ========================================================

    raise RuntimeError(
        f"OpenRouter بعد از {MAX_RETRIES} تلاش "
        "پاسخ قابل استفاده نداد."
    )