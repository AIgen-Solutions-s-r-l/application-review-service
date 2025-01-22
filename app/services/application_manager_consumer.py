
from app.services.base_consumer import BaseConsumer
from app.core.config import settings
from app.services.career_docs_publisher import career_docs_publisher

class ApplicationManagerConsumer(BaseConsumer):

    def __init__(self):
        super().__init__()
        self.career_docs_publisher = career_docs_publisher

    def get_queue_name(self):
        return settings.application_manager_queue
    
    async def process_message(self, _):
        await career_docs_publisher.refill_queue()


application_manager_consumer = ApplicationManagerConsumer()