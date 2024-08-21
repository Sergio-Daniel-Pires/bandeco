import asyncio
import dataclasses as dc
import logging

import config
import requests
from dataclasses_json import dataclass_json
from initialize_bot import initialize_bot
from redis import Redis
from whatsapp import messages
from whatsapp.bot import WhatsappBot

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

@dataclass_json
@dc.dataclass
class BotPublisher (WhatsappBot):
    bot_number: str = dc.field(kw_only=True)

    @property
    def redis_conn(self) -> Redis:
        return Redis(host=config.REDIS_CONN, password=config.REDIS_PASSWORD)

    def get_update (self) -> messages.Incoming | None:
        return self.redis_conn.lpop(f"whatsapp:updates:{self.bot_number}")

async def main ():
    bot = BotPublisher(
        verify_token=config.WHATSAPP_VERIFY_TOKEN,
        whatsapp_token=config.WHATSAPP_API_TOKEN,
        bot_number=config.WHATSAPP_BOT_NUMBER
    )

    # This request allow bot to send messages
    requests.request(
        "POST", "http://whatsapp-bot-gateway:3579/handle-bot",
        headers={ "Content-Type": "application/json" },
        json = {
            "bot_number": config.WHATSAPP_BOT_NUMBER,
            "status": "1",
            "token": config.WHATSAPP_GATEWAY_TOKEN
        }
    )

    await initialize_bot(bot)

    await bot.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
