import datetime as dt
import json
import logging
import re
from typing import Any

import pytz
from get_menu import BotBase
from redis_conn import get_cached_menu, set_menu_on_cache

REGEX_DATE = r"/dia\s*([0-9]{0,2})(-|\/)([0-9]{0,2})"

logger = logging.getLogger(__name__)
timezone = pytz.timezone("America/Sao_Paulo")

def transform_date (match: str) -> tuple[bool, str]:
    """
        Transform a date from "dd-mm" or "dd/mm" to "yyyy-mm-dd",
        returning a tuple with True and the transformed date if success,

    :param match: message regex
    :return: tuple with a True if success and the transformed date
    """
    match = re.search(REGEX_DATE, match)
    if not match:
        return False, "Invalid format"

    try:
        day = int(match.group(1))
        month = int(match.group(3))

        date = dt.datetime(dt.datetime.now(tz=timezone).year, month, day)

        return True, date.strftime('%Y-%m-%d')

    except Exception as exc:
        return False, str(exc)

def format_menu (menu: dict[str, Any]) -> str:
    message = ""

    for title, value in menu.items():
        emoji = "🥗" if "vegano" in title.lower() else "🥩"
        message += f"🍽️ *{title}*\n"
        message += f"{emoji} *{value['protein']}*\n"

        # Enrich the description
        description = value['description'].split("\n\n", maxsplit=1)[0].split("\n")
        description = [line.capitalize() for line in description]
        description[-2] = f"*{description[-2].capitalize()}*"
        description = "\n".join(description)

        message += f"{description}\n\n\n"

    return message

async def get_or_insert_menu_in_cache (date: str) -> dict[str, Any]:
    menu = get_cached_menu(date)

    if menu is not None:
        menu = json.loads(menu)

    else:
        for _ in range(3):
            try:
                bot = BotBase(extra_date=date)
                menu = await bot.get_menu()

                # Can't find the menu
                if menu is None:
                    return False, "Menu not found"

                set_menu_on_cache(menu)
                break

            except Exception as exc:
                logger.error(f"Error: {exc}")

    return menu

async def get_menu_from_command (date: str) -> tuple[bool, str]:
    if date == "today":
        date = dt.datetime.now(tz=timezone).strftime("%Y-%m-%d")

    elif date == "tomorrow":
        date = (dt.datetime.now(tz=timezone) + dt.timedelta(days=1)).strftime("%Y-%m-%d")

    else:
        success, date = transform_date(date)

        if not success:
            return False, date

    menu = await get_or_insert_menu_in_cache(date)

    return True, format_menu(menu)

def get_dates_until_next_sunday(start_date: dt.datetime | None = None):
    # Added bcuz write datetime mocks sucks!
    if start_date is None:
        start_date = dt.datetime.now(tz=timezone)

    return [
        (start_date + dt.timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(7 - start_date.weekday())
    ]

async def verify_this_week_and_get_fish () -> tuple[bool, str]:
    remaining_days = get_dates_until_next_sunday()
    fish_days = []

    for date in remaining_days:
        menu = await get_or_insert_menu_in_cache(date)

        for title, values in menu.items():
            if "peixe" in (protein := values.get("protein", "")).lower() and protein is not None:
                user_friendly_date = dt.datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m")
                food_time = "Almoço" if "almoço" in title.lower() else "Jantar"
                fish_days.append(f"{food_time} {user_friendly_date}: {protein.capitalize()}")

    if len(fish_days) == 0:
        return False, "Ótima noticia! Não tem peixe essa semana."

    output_msg = "Para tristeza geral da nação, teremos peixe nos seguintes dias:\n\n"
    output_msg += "* 🐟"
    output_msg += "\n* ".join(fish_days)

    return True, output_msg
