import logging

import config
import flask
import redis
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
    def redis_conn(self) -> redis.Redis:
        return redis.Redis(host=config.REDIS_CONN, password=config.REDIS_PASSWORD)

    def enqueue_update (self, update: Incoming):
        if update.message is None:
            return

        business_wa_id = update.metadata.display_phone_number
        customer_wa_id = update.message.from_

        
        multiple_workers_queue = (
            self.redis_conn.get(f"{config.DEFAULT_QUEUES_WITH_TASKS}:{business_wa_id}")
        )

        customer_key = f"{business_wa_id}:{customer_wa_id}"

        if multiple_workers_queue is not None:
            self.redis_conn.sadd(multiple_workers_queue.decode("utf-8"), customer_key)
            queue_name = f"whatsapp:updates:{customer_key}"

        else:
            queue_name = f"whatsapp:updates:{business_wa_id}"

        self.redis_conn.rpush(queue_name, update.to_json())

    def create_app(self, flask_config: object = None) -> flask.Flask:
        app = super().create_app(flask_config)

        @app.route("/handle-bot", methods=["POST"])
        @middleware
        def register_bot ():
            data = flask.request.json

            business_number = data.get("bot_number")
            shared_workers = data.get("shared_workers")
            token = data.get("token")

            if token != config.WHATSAPP_GATEWAY_TOKEN:
                raise VerificationFailed("Invalid token")

            self.redis_conn.set(
                f"{config.DEFAULT_QUEUES_WITH_TASKS}:{business_number}", shared_workers
            )

            message = (
                f"Bot {business_number} registered successfully to "
                f"share workers with {shared_workers}"
            )

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
