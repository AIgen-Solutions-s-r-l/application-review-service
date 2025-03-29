from app.log.logging import logger
from app.core.rabbitmq_client import rabbit_client
from app.core.appliers_config import APPLIERS, process_default

class GenericPublisher:
    
    def __init__(self):
        self.rabbitmq_client = rabbit_client

    async def publish_data_to_microservices(self, data) -> None:
        """
        Processes the received data and sends a separate message for each application
        to different microservices via their queues.
        
        Args:
            data (dict): Data containing user_id and a 'content' dict with multiple applications.
        """
        user_id = data.get("user_id")
        content = data.get("content", {})

        # Iterate over each application in the content
        for app_id, app_content in content.items():
            # Create a new document for the single application
            single_app_document = {
                "user_id": user_id,
                "content": {app_id: app_content}
            }
            
            # Send the document for each microservice as before
            for microservice_name, microservice_info in APPLIERS.items():
                queue_name = microservice_info["queue_name"]
                process_function = microservice_info.get("process_function", process_default)
                
                microservice_data = process_function(single_app_document)
                if not microservice_data:
                    continue
                await self.rabbitmq_client.connect()
                await self.rabbitmq_client.publish_message(queue_name, microservice_data)
                logger.info(
                    f"Sent data for application {app_id} to microservice {microservice_name} via queue {queue_name}",
                    event_type="generic_publisher"
                )

generic_publisher = GenericPublisher()