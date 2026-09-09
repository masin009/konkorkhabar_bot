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
MAX_OUTPUT_TOKENS = 1200
MAX_RETRIES = 3

CONNECT_TIMEOUT = 15
READ_TIMEOUT = 90

# حداقل طول قابل قبول برای خبر تولیدشده
MIN_OUTPUT_CHARS = 180


# =========================================================
# Main summarizer
# =========================================================

def summarize_news(title, article_text):

    """
    Summarize and rewrite an educational news article
    into a clean Persian Telegram news post.

    Args:
        title: Original news title
        article_text: Full article text

    Returns:
        str  -> formatted news
        None -> if article should be skipped
    """

    # -----------------------------------------------------
    # Check API key
    # -----------------------------------------------------

    if not OPENROUTER_API_KEY:

        print(
            "ERROR: OPENROUTER_API_KEY is not set."
        )

        return None


    if not article_text:

        print(
            "ERROR: article_text is empty."
        )

        return None


    # -----------------------------------------------------
    # Prepare article
    # -----------------------------------------------------

    title = title.strip()

    article_text = article_text.strip()


    if len(article_text) > MAX_ARTICLE_CHARS:

        article_text = article_text[:MAX_ARTICLE_CHARS]


    # =====================================================
    # SYSTEM PROMPT
    # =====================================================

    system_prompt = """
تو یک ویراستار حرفه‌ای اخبار آموزشی و دانشگاهی ایران هستی.

وظیفه تو این است که عنوان و متن کامل خبر را بررسی کنی و از آن
یک خبر کوتاه، دقیق، روان و قابل انتشار در کانال تلگرام بسازی.

مهم‌ترین هدف:
خواننده باید بعد از خواندن خروجی بفهمد دقیقاً چه اتفاقی افتاده،
چه کسی یا چه سازمانی درگیر آن است، چه زمانی اتفاق افتاده یا خواهد افتاد
و اگر مهلت، عدد، نتیجه یا اقدام خاصی وجود دارد، آن را بداند.

قوانین:

1. فقط خبر نهایی را بنویس.
2. هیچ توضیحی درباره کاری که انجام داده‌ای ننویس.
3. هرگز ننویس:
   «تیتر:»
   «عنوان:»
   «پاراگراف اول:»
   «پاراگراف دوم:»
   «پاراگراف سوم:»
   «خلاصه:»
   «متن خبر:»
   «توضیحات:»
   «خبر:»

4. خط اول یک تیتر کوتاه و خبری باشد.
5. قبل از تیتر یک ایموجی خبری مناسب قرار بده.

نمونه:
🔴 تغییرات جدید کنکور ابلاغ شد

یا:
📢 نتایج آزمون کارشناسی ارشد ۱۴۰۵ اعلام شد

6. بعد از تیتر، حداقل 2 پاراگراف کوتاه و مفید بنویس؛
   مگر اینکه متن اصلی واقعاً اطلاعات کافی برای دو پاراگراف نداشته باشد.

7. هر پاراگراف باید حداقل یک نکته واقعی و مهم از خبر را منتقل کند.
8. هیچ پاراگرافی نباید فقط یک یا چند کلمه باشد.
9. خروجی نباید فقط شامل تیتر و یک عبارت کوتاه باشد.
10. از متن اصلی اطلاعات واقعی استخراج کن و آن‌ها را خلاصه و روان کن.

11. در صورت وجود، این اطلاعات را حتماً حفظ کن:
    - تاریخ
    - ساعت
    - مهلت
    - مبلغ
    - تعداد
    - درصد
    - رتبه
    - نتیجه
    - نام آزمون
    - نام دانشگاه
    - نام سازمان
    - شرایط ثبت‌نام
    - نحوه اقدام
    - تصمیم یا تغییر مهم

12. اگر متن درباره یک تصمیم یا تغییر جدید است،
    دقیقاً توضیح بده چه چیزی تغییر کرده است.

13. اگر خبر درباره نتایج است،
    مشخص کن چه نتیجه‌ای اعلام شده و مربوط به چه آزمونی است.

14. اگر خبر درباره ثبت‌نام یا مهلت است،
    مهلت و اقدام موردنیاز داوطلب را حتماً بیاور.

15. اگر خبر درباره دانشگاه یا مدرسه است،
    مشخص کن چه دانشگاه یا مدرسه‌ای و چه اتفاقی درباره آن افتاده است.

16. اطلاعات مهم را حذف نکن فقط برای اینکه خبر کوتاه‌تر شود.

17. در عین حال متن را بیش از حد طولانی نکن.
18. معمولاً 2 تا 4 پاراگراف کوتاه کافی است.
19. هر پاراگراف حدود 1 تا 3 جمله باشد.

20. هیچ اطلاعاتی را اختراع نکن.
21. از حدس زدن خودداری کن.
22. معنی خبر را تغییر نده.

23. متن فارسی طبیعی و حرفه‌ای باشد.
24. از جملات ماشینی و رباتی استفاده نکن.

25. برای مرتب شدن خبر، ابتدای هر پاراگراف یک ایموجی مناسب قرار بده.

برای نمونه:
🔹 اطلاعات اصلی خبر

📌 جزئیات مهم

⏰ تاریخ یا مهلت

📊 نتیجه یا آمار

🎓 اطلاعات مربوط به دانشگاه

📝 اطلاعات مربوط به آزمون یا ثبت‌نام

🏫 اطلاعات مربوط به مدرسه

26. ایموجی‌ها را متناسب با محتوای هر پاراگراف انتخاب کن.
27. در مجموع حدود 3 تا 6 ایموجی کافی است.
28. از ایموجی‌های بی‌ربط استفاده نکن.

29. از Markdown استفاده نکن.
30. هرگز از این موارد استفاده نکن:
    **
    __
    #
    *
    `
    ```

31. لینک، آدرس سایت یا URL در خروجی قرار نده.
32. نام رسانه یا کانال منبع را در خروجی قرار نده.
33. تبلیغات، جملات تبلیغاتی و حاشیه‌ها را حذف کن.

34. اگر متن واقعاً نامرتبط، تبلیغاتی، ناقص یا غیرقابل اعتماد است،
    فقط بنویس:
    SKIP

35. اگر خبر آموزشی و قابل انتشار است،
    حتماً یک خبر کامل و قابل فهم تولید کن.

36. خروجی باید فقط خبر نهایی باشد.
"""


    # =====================================================
    # USER PROMPT
    # =====================================================

    user_prompt = f"""
عنوان اصلی خبر:

{title}


متن کامل خبر:

--------------------------------------------------

{article_text}

--------------------------------------------------

اکنون این خبر را بررسی کن.

ابتدا مهم‌ترین اتفاق یا موضوع خبر را تشخیص بده.

سپس یک خبر کوتاه و کامل برای تلگرام بنویس.

ساختار خروجی:

خط اول:
یک تیتر خبری کوتاه با یک ایموجی مناسب.

بعد:
حداقل دو پاراگراف کوتاه که هرکدام یک بخش مهم از خبر را توضیح دهند.

حتماً مشخص کن:
چه اتفاقی افتاده؟
چه شخص، سازمان، دانشگاه یا آزمونی درگیر است؟
اگر تاریخ، مهلت، عدد، نتیجه یا اقدام خاصی وجود دارد، چیست؟

از اطلاعات خود متن استفاده کن و هیچ چیزی را حدس نزن.

خروجی نباید فقط تیتر باشد.
خروجی نباید شامل توضیحاتی مثل «تیتر»، «پاراگراف اول» و غیره باشد.

اگر خبر ارزش انتشار ندارد، فقط بنویس:

SKIP
"""


    # =====================================================
    # PAYLOAD
    # =====================================================

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

        "temperature": 0.15,

        "max_tokens": MAX_OUTPUT_TOKENS
    }


    # =====================================================
    # HEADERS
    # =====================================================

    headers = {

        "Authorization":
            f"Bearer {OPENROUTER_API_KEY}",

        "Content-Type":
            "application/json",

        "HTTP-Referer":
            "https://github.com/masin009/konkorkhabar_bot",

        "X-Title":
            "Konkorkhabar News Bot"
    }


    # =====================================================
    # RETRY LOOP
    # =====================================================

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            print(
                f"OpenRouter request "
                f"(attempt {attempt}/{MAX_RETRIES})..."
            )


            response = requests.post(

                API_URL,

                headers=headers,

                json=payload,

                timeout=(
                    CONNECT_TIMEOUT,
                    READ_TIMEOUT
                )
            )


            # -------------------------------------------------
            # Temporary errors
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
                        f"Retrying in "
                        f"{wait_time} seconds..."
                    )

                    time.sleep(
                        wait_time
                    )

                    continue


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

                    print(
                        response.text[:1000]
                    )

                except Exception:

                    pass

                return None


            # -------------------------------------------------
            # JSON
            # -------------------------------------------------

            try:

                data = response.json()

            except ValueError:

                print(
                    "ERROR: OpenRouter returned invalid JSON."
                )

                return None


            # -------------------------------------------------
            # Choices
            # -------------------------------------------------

            choices = data.get(
                "choices"
            )


            if not choices:

                print(
                    "ERROR: OpenRouter returned no choices."
                )

                print(data)

                return None


            choice = choices[0]


            message = choice.get(
                "message",
                {}
            )


            content = message.get(
                "content"
            )


            finish_reason = choice.get(
                "finish_reason"
            )


            # -------------------------------------------------
            # Empty response
            # -------------------------------------------------

            if not content:

                print(
                    "ERROR: OpenRouter returned empty content."
                )

                print(
                    f"finish_reason: "
                    f"{finish_reason}"
                )


                if finish_reason == "length":

                    print(
                        "Model reached output token limit."
                    )


                    if attempt < MAX_RETRIES:

                        time.sleep(3)

                        continue


                return None


            # =================================================
            # CLEAN OUTPUT
            # =================================================

            text = content.strip()


            # -------------------------------------------------
            # Remove Markdown
            # -------------------------------------------------

            text = text.replace(
                "**",
                ""
            )

            text = text.replace(
                "__",
                ""
            )

            text = text.replace(
                "```",
                ""
            )

            text = text.replace(
                "`",
                ""
            )


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

                text = text.replace(
                    label,
                    ""
                )


            # =================================================
            # NORMALIZE LINES
            # =================================================

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

                    cleaned_lines.append(
                        line
                    )

                    previous_empty = False


            text = "\n".join(
                cleaned_lines
            ).strip()


            # =================================================
            # CHECK SKIP
            # =================================================

            if text.upper() == "SKIP":

                print(
                    "AI decided to skip this news."
                )

                return None


            # =================================================
            # QUALITY CHECK
            # =================================================

            # اگر خروجی خیلی کوتاه باشد، منتشر نشود
            if len(text) < MIN_OUTPUT_CHARS:

                print(
                    f"⚠️ AI output too short: "
                    f"{len(text)} characters"
                )

                print(
                    "⏭️ Skipping this candidate."
                )

                return None


            # -------------------------------------------------
            # Check whether output contains only a title
            # -------------------------------------------------

            output_lines = [

                line.strip()

                for line in text.splitlines()

                if line.strip()
            ]


            if len(output_lines) < 3:

                print(
                    "⚠️ AI output does not contain enough "
                    "news content."
                )

                print(
                    "⏭️ Skipping this candidate."
                )

                return None


            # -------------------------------------------------
            # Print successful output
            # -------------------------------------------------

            print(
                "News summarized successfully."
            )


            print(
                "\n----- AI OUTPUT -----"
            )


            print(text)


            print(
                "---------------------\n"
            )


            return text


        # =====================================================
        # REQUEST EXCEPTION
        # =====================================================

        except requests.exceptions.RequestException as e:

            print(
                f"OpenRouter request exception: {e}"
            )


            if attempt < MAX_RETRIES:

                wait_time = 5 * attempt

                print(
                    f"Retrying in "
                    f"{wait_time} seconds..."
                )


                time.sleep(
                    wait_time
                )

                continue


            print(
                "OpenRouter request failed "
                "after retries."
            )

            return None


        # =====================================================
        # OTHER ERRORS
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