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

    bot = WhatsappBot(verify_token="", whatsapp_token="EAAP4fM5pvHEBO9gFfZC0ZBv6bf8pIEZAZC5dlsWVTP5QH2CWZAAlfZCWSClsoxFrpKsrmRmlyFJ0KaTZCpJDVa6B9qskZAbkzBEoi0UB6NMIPmO44xSm2ndMa27ZCRn5NKNx0CXBVjKZBUZCQZClDgdWHwPXgkiEkQP26KN8ju37UEuxvzwONqYtIlrXv5HwW78bJ9vL")
    await initialize_bot(bot)

    bot.start_webhook(port=3000)

    await bot.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
