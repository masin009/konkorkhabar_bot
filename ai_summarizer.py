import os
import time

import requests
from dotenv import load_dotenv


# =========================================================
# Load environment variables
# =========================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_MODEL = "openrouter/free"

API_URL = "https://openrouter.ai/api/v1/chat/completions"


# =========================================================
# Settings
# =========================================================

MAX_ARTICLE_CHARS = 10000
MAX_OUTPUT_TOKENS = 1000
MAX_RETRIES = 3

CONNECT_TIMEOUT = 15
READ_TIMEOUT = 90


# =========================================================
# Main summarizer
# =========================================================

def summarize_news(article_text):
    """
    Summarize and rewrite a news article into a clean,
    natural Persian Telegram news post.

    Returns:
        str  -> formatted news
        None -> if article should be skipped
    """

    # -----------------------------------------------------
    # Check API key
    # -----------------------------------------------------

    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY is not set.")
        return None

    if not article_text:
        print("ERROR: article_text is empty.")
        return None

    # -----------------------------------------------------
    # Limit article size
    # -----------------------------------------------------

    article_text = article_text.strip()

    if len(article_text) > MAX_ARTICLE_CHARS:
        article_text = article_text[:MAX_ARTICLE_CHARS]

    # -----------------------------------------------------
    # Prompt
    # -----------------------------------------------------

    system_prompt = """
تو یک ویراستار حرفه‌ای اخبار آموزشی و دانشگاهی ایران هستی.

وظیفه تو این است که متن خام خبر را بررسی کنی و فقط اطلاعات مهم و قابل انتشار
آن را به یک خبر کوتاه، روان، طبیعی و حرفه‌ای برای کانال تلگرام تبدیل کنی.

قوانین بسیار مهم:

1. مستقیماً متن نهایی خبر را بنویس.
2. هرگز درباره نحوه نوشتن خبر توضیح نده.
3. هرگز از عبارت‌هایی مثل این‌ها استفاده نکن:
   «تیتر:»
   «عنوان:»
   «پاراگراف اول:»
   «پاراگراف دوم:»
   «متن خبر:»
   «خلاصه:»
   «توضیحات:»
4. خط اول می‌تواند یک تیتر کوتاه و خبری باشد، اما نباید قبل از آن کلمه «تیتر» یا «عنوان» نوشته شود.
5. بعد از تیتر، متن خبر را به صورت طبیعی و یکپارچه بنویس.
6. فقط مهم‌ترین اطلاعات خبر را نگه دار.
7. از توضیحات اضافه، حاشیه، تبلیغات و جملات تکراری صرف‌نظر کن.
8. تاریخ‌ها، ساعت‌ها، مهلت‌ها، اعداد، نتایج، نام دانشگاه‌ها، سازمان‌ها،
   آزمون‌ها و سایر اطلاعات مهم را دقیق حفظ کن.
9. هیچ اطلاعاتی را که در متن اصلی وجود ندارد اختراع نکن.
10. معنی خبر را تغییر نده.
11. متن باید فارسی روان و طبیعی باشد و حالت رباتی نداشته باشد.
12. از جمله‌های کوتاه و قابل خواندن در تلگرام استفاده کن.
13. در صورت مرتبط بودن، از ایموجی مناسب استفاده کن.
14. در کل خبر بیشتر از 2 تا 4 ایموجی استفاده نکن.
15. ایموجی باید متناسب با موضوع باشد، مانند:
    🎓 برای دانشگاه و آموزش
    📝 برای آزمون و ثبت‌نام
    📚 برای آموزش و امتحان
    ⏰ برای مهلت و زمان
    📊 برای نتایج و آمار
    📢 برای اطلاعیه مهم
16. از Markdown استفاده نکن.
17. هرگز از این موارد استفاده نکن:
    **
    __
    #
    *
    `
    ```
18. هیچ لینک، آدرس سایت یا منبع خبر را در خروجی قرار نده.
19. نام رسانه یا کانال منتشرکننده خبر را نیز در خروجی نیاور.
20. عبارت‌های رباتی و توضیحات متا مانند
    «در این خبر آمده است»،
    «خبر فوق بیان می‌کند»،
    «خلاصه خبر به شرح زیر است»
    و موارد مشابه را استفاده نکن.
21. خروجی معمولاً شامل یک تیتر کوتاه و 1 تا 4 پاراگراف کوتاه باشد.
22. اگر خبر طولانی است، فقط اطلاعات مهم آن را انتخاب و خلاصه کن.
23. اگر متن تبلیغاتی، نامرتبط، ناقص یا غیرقابل اعتماد است، فقط بنویس:
    SKIP
24. اگر خبر درباره موضوعات آموزشی، کنکور، آزمون، دانشگاه، مدرسه،
    آموزش و پرورش، سوابق تحصیلی، معدل، انتخاب رشته یا موضوعات مرتبط است،
    آن را به شکل یک خبر تمیز و قابل انتشار بازنویسی کن.
25. خروجی باید فقط خود خبر نهایی باشد و هیچ توضیح دیگری خارج از خبر نداشته باشد.

نمونه سبک خروجی:

🎓 نتایج اولیه آزمون کارشناسی ارشد ۱۴۰۵ اعلام شد

نتایج اولیه آزمون کارشناسی ارشد سال ۱۴۰۵ منتشر شد. داوطلبان می‌توانند
با مراجعه به سامانه مربوطه، نتیجه آزمون خود را مشاهده کنند.

مهلت و جزئیات انتخاب رشته نیز در اطلاعیه سازمان سنجش اعلام شده است.

دقت کن که این فقط نمونه سبک است و نباید اطلاعات آن را به خبرهای دیگر اضافه کنی.
"""


    user_prompt = f"""
متن خبر خام:

--------------------

{article_text}

--------------------

اکنون خبر را بررسی کن و فقط نسخه نهایی و تمیز آن را بنویس.

اگر خبر ارزش انتشار ندارد یا اطلاعات آن برای تهیه یک خبر قابل اعتماد کافی نیست،
فقط بنویس:

SKIP
"""

    # -----------------------------------------------------
    # Request payload
    # -----------------------------------------------------

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": MAX_OUTPUT_TOKENS
    }

    # -----------------------------------------------------
    # Headers
    # -----------------------------------------------------

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/masin009/konkorkhabar_bot",
        "X-Title": "Konkorkhabar News Bot"
    }

    # =====================================================
    # Retry loop
    # =====================================================

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            print(
                f"OpenRouter request "
                f"(attempt {attempt}/{MAX_RETRIES})..."
            )

            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
            )

            # -------------------------------------------------
            # HTTP errors
            # -------------------------------------------------

            if response.status_code in {
                408,
                429,
                500,
                502,
                503,
                504
            }:

                print(
                    f"OpenRouter temporary error: "
                    f"HTTP {response.status_code}"
                )

                if attempt < MAX_RETRIES:

                    wait_time = 5 * attempt

                    print(
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)

                    continue

                print("OpenRouter failed after retries.")
                return None

            # -------------------------------------------------
            # Other HTTP errors
            # -------------------------------------------------

            if response.status_code != 200:

                print(
                    f"OpenRouter error: "
                    f"HTTP {response.status_code}"
                )

                try:
                    print(response.text[:1000])
                except Exception:
                    pass

                return None

            # -------------------------------------------------
            # Parse JSON
            # -------------------------------------------------

            try:
                data = response.json()

            except ValueError:

                print("ERROR: OpenRouter returned invalid JSON.")
                return None

            # -------------------------------------------------
            # Validate response
            # -------------------------------------------------

            choices = data.get("choices")

            if not choices:

                print("ERROR: OpenRouter returned no choices.")
                print(data)

                return None

            choice = choices[0]

            message = choice.get("message", {})

            content = message.get("content")

            finish_reason = choice.get("finish_reason")

            # -------------------------------------------------
            # Empty content
            # -------------------------------------------------

            if not content:

                print(
                    "ERROR: OpenRouter returned empty content."
                )

                print(
                    f"finish_reason: {finish_reason}"
                )

                if finish_reason == "length":

                    print(
                        "The model reached the output token limit."
                    )

                    if attempt < MAX_RETRIES:

                        time.sleep(3)

                        continue

                return None

            # -------------------------------------------------
            # Clean output
            # -------------------------------------------------

            text = content.strip()

            # Remove Markdown accidentally generated by model
            text = text.replace("**", "")
            text = text.replace("__", "")
            text = text.replace("```", "")
            text = text.replace("`", "")

            # -------------------------------------------------
            # Remove unwanted labels
            # -------------------------------------------------

            forbidden_labels = [
                "تیتر:",
                "عنوان:",
                "پاراگراف:",
                "پاراگراف اول:",
                "پاراگراف دوم:",
                "پاراگراف سوم:",
                "پاراگراف چهارم:",
                "پاراگراف پنجم:",
                "خلاصه:",
                "متن خبر:",
                "توضیحات:",
                "خبر:",
            ]

            for label in forbidden_labels:
                text = text.replace(label, "")

            # -------------------------------------------------
            # Normalize excessive blank lines
            # -------------------------------------------------

            lines = text.splitlines()

            cleaned_lines = []

            previous_empty = False

            for line in lines:

                line = line.strip()

                if not line:

                    if not previous_empty:
                        cleaned_lines.append("")

                    previous_empty = True

                else:

                    cleaned_lines.append(line)

                    previous_empty = False

            text = "\n".join(cleaned_lines).strip()

            # -------------------------------------------------
            # Check SKIP
            # -------------------------------------------------

            if text.upper() == "SKIP":

                print("AI decided to skip this news.")
                return None

            # -------------------------------------------------
            # Remove accidental SKIP around text
            # -------------------------------------------------

            if text.startswith("SKIP"):

                remaining = text[4:].strip()

                if not remaining:

                    print("AI decided to skip this news.")
                    return None

            # -------------------------------------------------
            # Final validation
            # -------------------------------------------------

            if len(text) < 20:

                print(
                    "ERROR: Generated news is too short."
                )

                return None

            # -------------------------------------------------
            # Success
            # -------------------------------------------------

            print("News summarized successfully.")

            return text

        # =====================================================
        # Request exception
        # =====================================================

        except requests.exceptions.RequestException as e:

            print(
                f"OpenRouter request exception: {e}"
            )

            if attempt < MAX_RETRIES:

                wait_time = 5 * attempt

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

                continue

            print(
                "OpenRouter request failed after retries."
            )

            return None

        # =====================================================
        # Unexpected errors
        # =====================================================

        except RuntimeError as e:

            print(
                f"Runtime error in OpenRouter: {e}"
            )

            return None

        except ValueError as e:

            print(
                f"Value error in OpenRouter: {e}"
            )

            return None

        except Exception as e:

            print(
                f"Unexpected error in AI summarizer: {e}"
            )

            return None

    return None