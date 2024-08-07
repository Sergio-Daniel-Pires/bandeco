import asyncio
from threading import Thread

import config
from init import initialize_bot
from whatsapp.bot import WhatsappBot

# Create bot and add commands
bot = WhatsappBot(
    verify_token=config.WHATSAPP_VERIFY_TOKEN,
    whatsapp_token=config.WHATSAPP_API_TOKEN
)
asyncio.run(initialize_bot(bot))

# Run update processor in background
bot_thread = Thread(target=asyncio.run, args=(bot.run_forever(),))
bot_thread.start()

# Create flask app
app = bot.create_app()
