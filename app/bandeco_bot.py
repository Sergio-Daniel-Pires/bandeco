import asyncio
import dataclasses as dc
import logging
import multiprocessing
import time

import config
import redis
import requests
from dataclasses_json import dataclass_json
from initialize_bot import initialize_bot
from redis_conn import LOCK_TIMEOUT, redis_lock
from whatsapp import messages
from whatsapp.bot import WhatsappBot
from whatsapp.error import EmptyState

# Lock expiration time in seconds
LOCK_TIMEOUT = 3

# Interval to renew the lock in seconds (MUST be less than LOCK_TIMEOUT)
LOCK_RENEW_INTERVAL = LOCK_TIMEOUT // 3

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
    def redis_conn(self) -> redis.Redis:
        return redis.Redis(host=config.REDIS_CONN, password=config.REDIS_PASSWORD)

    def get_update (self) -> messages.Incoming | None:
        return self.redis_conn.lpop(f"whatsapp:updates:{self.bot_number}")

    async def _process_update (
        self, redis_client: redis.Redis, queue_name: str, max_time: float
    ):
        """
        Continuously retrieves items from the specified Redis queue and processes them
        until the maximum time is reached.

        :param redis_client: The Redis client instance to interact with the Redis server.
        :param queue_name: The name of the Redis queue to process items from.
        :param max_time: The maximum time (in seconds) to process items from the queue.
        """
        start_time = time.time()
        logging.debug(f"Starting processing of queue '{queue_name}' for up to {max_time} seconds.")

        while time.time() - start_time < max_time:
            item = redis_client.lpop(queue_name)

            if item is None:
                break

            try:
                await self.process_update(messages.Incoming.from_json(item))

            except Exception as exc:
                logging.error(exc)

        logging.debug("Max time reached or no tasks in queue")

    async def run_forever(self, interval = 0.1):
        if self._initial_state is None and not self._can_run_empty:
            raise EmptyState("No states are defined for the bot")

        while True:
            # Get all queues with tasks
            customer_with_jobs = self.redis_conn.smembers(config.DEFAULT_QUEUES_WITH_TASKS)

            if not customer_with_jobs:
                time.sleep(0.1)

                continue

            for customer_key in customer_with_jobs:
                customer_key = customer_key.decode("utf-8")
                lock_name = f"whatsapp:lock:{customer_key}"

                # Attempt to acquire the lock for the queue
                with redis_lock(self.redis_conn, lock_name, LOCK_TIMEOUT) as acquired:
                    if not acquired:
                        logging.warning(f"Cannot acquire lock for queue '{customer_key}'.")

                        continue

                    # Remove the queue from the global set
                    removed = self.redis_conn.srem(config.DEFAULT_QUEUES_WITH_TASKS, customer_key)

                    if removed:
                        logging.debug(
                            f"Queue '{customer_key}' removed from '{config.DEFAULT_QUEUES_WITH_TASKS}'."
                        )

                    else:
                        logging.warning(f"Queue '{customer_key}' was removed by another worker.")

                    try:
                        # Process the queue for a limited time
                        queue_name = f"whatsapp:updates:{customer_key}"
                        await self._process_update(self.redis_conn, queue_name, 1)

                        # Check if there are remaining tasks in the queue
                        remaining = self.redis_conn.llen(queue_name)

                        if remaining > 0:
                            self.redis_conn.sadd(config.DEFAULT_QUEUES_WITH_TASKS, queue_name)
                            logging.debug(
                                f"Queue '{queue_name}' added back to global "
                                f"'{config.DEFAULT_QUEUES_WITH_TASKS}' with {remaining} jobs remaining."
                            )

                    except Exception as e:
                        logging.error(f"Error processing queue '{queue_name}': {e}")

            time.sleep(interval)

def create_bot ():
    """
    Target function for each process to run an async bot.
    """
    async def bot_main():
            
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
                "shared_workers": config.DEFAULT_QUEUES_WITH_TASKS, "token": config.WHATSAPP_GATEWAY_TOKEN
            }
        )

        await initialize_bot(bot)

        await bot.run_forever()
    
    asyncio.run(bot_main())

async def main():
    """
    Main entry point to initialize and run multiple bot processes.
    """
    processes = []

    # Create a process for each bot
    for _ in range(3):
        process = multiprocessing.Process(target=create_bot)
        processes.append(process)
        process.start()

    # Wait for all processes to complete
    for process in processes:
        process.join()

if __name__ == "__main__":
    asyncio.run(main())
