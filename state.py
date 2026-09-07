import os
import json
from datetime import datetime, timezone


STATE_FILE = "data/state.json"


def load_state():

    os.makedirs(
        "data",
        exist_ok=True
    )

    if not os.path.exists(STATE_FILE):

        return {
            "initialized": False,
            "last_published_at": None
        }

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {
            "initialized": False,
            "last_published_at": None
        }


def save_state(state):

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            state,
            f,
            ensure_ascii=False,
            indent=2
        )


def can_publish(
    state,
    cooldown_minutes=15
):

    last = state.get(
        "last_published_at"
    )

    if not last:
        return True

    try:

        last_time = datetime.fromisoformat(
            last
        )

        now = datetime.now(
            timezone.utc
        )

        elapsed = (
            now - last_time
        ).total_seconds()

        return elapsed >= (
            cooldown_minutes * 60
        )

    except Exception:

        return True


def mark_published(state):

    state["last_published_at"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )