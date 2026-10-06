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

            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except (
        json.JSONDecodeError,
        OSError
    ):

        return []


def save_chat_history(
    messages
):

    CHAT_HISTORY_FILE.parent.mkdir(
        parents=True,
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
            ensure_ascii=False,
            indent=2
        )


def clear_chat_history():

    if CHAT_HISTORY_FILE.exists():

        try:

            CHAT_HISTORY_FILE.unlink()

        except OSError:

            with open(
                CHAT_HISTORY_FILE,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    [],
                    file
                )