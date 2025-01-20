from loguru import logger
from app.core.rabbitmq_client import rabbit_client
from app.core.appliers_config import APPLIERS, process_default

class GenericPublisher:
    
    def __init__(self):
        self.rabbitmq_client = rabbit_client

    async def publish_data_to_microservices(self, data) -> None:
        """
        Processes the received data and sends it to different microservices via their queues.

        Args:
            data (dict): Data to send.
            rabbitmq_client (AsyncRabbitMQClient): RabbitMQ client instance.
        """

        for microservice_name, microservice_info in APPLIERS.items():
            queue_name = microservice_info['queue_name']
            process_function = microservice_info.get('process_function', process_default)

            microservice_data = process_function(data)
            logger.info(microservice_data)
            await self.rabbitmq_client.connect()
            await self.rabbitmq_client.publish_message(queue_name, microservice_data)
            logger.info(f"Sent data to microservice '{microservice_name}' via queue '{queue_name}'")


generic_publisher = GenericPublisher()