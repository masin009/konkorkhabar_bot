import os
import json
import hashlib


DATABASE_FILE = "data/seen_news.json"


def load_seen():

    os.makedirs("data", exist_ok=True)

    if not os.path.exists(DATABASE_FILE):

        return set()

    try:

        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        return set(data)

    except Exception:

        return set()


def save_seen(seen):

    os.makedirs("data", exist_ok=True)

    with open(
        DATABASE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            list(seen),
            f,
            ensure_ascii=False,
            indent=2
        )


def make_id(title, link):

    raw = f"{title}|{link}"

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def is_duplicate(news_id, seen):

    return news_id in seen