import asyncio
from app.services.career_docs_publisher import career_docs_publisher

class TimedQueueRefiller:

    WAIT_TIME: int = 10 * 60     # wait 10 minutes between each check

    def __init__(self):
        self.career_docs_publisher = career_docs_publisher

    async def start(self):
        """
        Continuously refills the career_docs queue at constant intervals (right now it's every 10 minutes)
        
        """
        self.running = True
        while self.running:
            await self.career_docs_publisher.refill_queue()
            await asyncio.sleep(TimedQueueRefiller.WAIT_TIME)

    def stop(self):
        self.running = False

timed_queue_refiller = TimedQueueRefiller()