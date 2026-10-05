import json

from config import CHAT_HISTORY_FILE


def load_chat_history():
    if not CHAT_HISTORY_FILE.exists():
        return []

    try:
        with open(
            CHAT_HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    except Exception:
        return []


def save_chat_history(messages):
    CHAT_HISTORY_FILE.parent.mkdir(
        exist_ok=True
    )

    with open(
        CHAT_HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            messages,
            file,
            indent=2,
            ensure_ascii=False
        )


def clear_chat_history():
    save_chat_history([])