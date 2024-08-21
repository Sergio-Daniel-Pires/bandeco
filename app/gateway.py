import logging

import config
import flask
from redis import Redis
from whatsapp.bot import WhatsappBot
from whatsapp.error import VerificationFailed
from whatsapp.messages import Incoming
from whatsapp.utils import middleware

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

class WhatsappBotGateway(WhatsappBot):
    @property
    def redis_conn(self):
        return Redis(host=config.REDIS_CONN, password=config.REDIS_PASSWORD)

    def enqueue_update(self, update: Incoming):
        bot_number = update.metadata.display_phone_number

        bot_allowed = self.redis_conn.get(f"whatsapp:registered:bots:{bot_number}")

        if not bot_allowed:
            logger.error(f"Bot {bot_number} is not allowed to send/receive messages")
        
        self.redis_conn.lpush(f"whatsapp:updates:{bot_number}", update.to_json())

    def create_app(self, flask_config: object = None) -> flask.Flask:
        app = super().create_app(flask_config)

        @app.route("/handle-bot", methods=["POST"])
        @middleware
        def register_bot ():
            data = flask.request.json

            bot_number = data.get("bot_number")
            bot_status = data.get("status")
            token = data.get("token")

            if token != config.WHATSAPP_GATEWAY_TOKEN:
                raise VerificationFailed("Invalid token")

            if bot_status == "1":
                self.redis_conn.set(f"whatsapp:registered:bots:{bot_number}", "1")
                message = f"Bot {bot_number} allowed successfully!"

            else:
                self.redis_conn.set(f"whatsapp:registered:bots:{bot_number}", "0")
                message = f"Bot {bot_number} disallowed successfully!"

            logger.info(message)
            return { "message": message }
        
        return app

gateway = WhatsappBotGateway(
    whatsapp_token=config.WHATSAPP_API_TOKEN,
    verify_token=config.WHATSAPP_VERIFY_TOKEN,
    _can_run_empty=True
)

# Create flask app (gunicorn will use)
app = gateway.create_app()

if __name__ == "__main__":
    app.run()
