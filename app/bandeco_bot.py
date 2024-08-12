import asyncio
import logging

from whatsapp.bot import WhatsappBot

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

START = range(1)


async def main ():
    from init import initialize_bot

    bot = WhatsappBot(verify_token="", whatsapp_token="")
    await initialize_bot(bot)

    bot.start_webhook(port=3000)

    await bot.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
