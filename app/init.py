import logging

from utils import (REGEX_DATE, get_menu_from_command,
                   verify_this_week_and_get_fish)
from whatsapp.bot import WhatsappBot
from whatsapp.messages import Incoming, TextMessage

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

START = range(1)

async def get_today (bot: WhatsappBot, incoming: Incoming) -> int:
    _, formatted_menu = await get_menu_from_command("today")

    echo_msg = TextMessage.to_send(incoming.message.from_, formatted_menu)
    await bot.send_message(echo_msg, incoming.metadata.phone_number_id)

    return START

async def get_tomorrow (bot: WhatsappBot, incoming: Incoming) -> int:
    _, formatted_menu = await get_menu_from_command("tomorrow")

    message = incoming.message.to_send(incoming.message.from_, formatted_menu)
    await bot.send_message(message, incoming.metadata.phone_number_id)

    return START

async def get_specific_day (bot: WhatsappBot, incoming: Incoming) -> int:
    message = incoming.message.message_value
    success, formatted_menu = await get_menu_from_command(message)

    if not success:
        logger.error(f"Error getting menu: {formatted_menu}")
        logger.error(f"Message: {message}")

    message = incoming.message.to_send(incoming.message.from_, formatted_menu)
    await bot.send_message(message, incoming.metadata.phone_number_id)

    return START

async def verify_fish_in_menu (bot: WhatsappBot, incoming: Incoming) -> int:
    success, fish_menu_msg = await verify_this_week_and_get_fish(message)

    if not success:
        logger.error(f"Error getting menu: {fish_menu_msg}")
        logger.error(f"Message: {message}")

    message = incoming.message.to_send(incoming.message.from_, fish_menu_msg)
    await bot.send_message(message, incoming.metadata.phone_number_id)

    return START

async def initialize_bot (bot: WhatsappBot):
    # More for cache week and less for the fish
    logger.info("Starting scrapper bot")
    await verify_this_week_and_get_fish()

    logger.info("Adding bot states whatsapp bot")
    bot.add_new_state(START, get_today, r"/hoje")
    bot.add_new_state(START, get_tomorrow, r"/(amanha|amanhã)")
    bot.add_new_state(START, get_specific_day, REGEX_DATE)
    bot.add_new_state(START, verify_fish_in_menu, r"/peixe")
