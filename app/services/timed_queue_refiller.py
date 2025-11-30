import asyncio
from app.log.logging import logger
from app.services.career_docs_publisher import career_docs_publisher


class TimedQueueRefiller:

    WAIT_TIME: int = 10 * 60     # wait 10 minutes between each check

    def __init__(self):
        self.career_docs_publisher = career_docs_publisher
        self.running = False

    async def start(self):
        """
        Continuously refills the career_docs queue at constant intervals (every 10 minutes).
        Includes error handling to prevent silent failures.
        """
        self.running = True
        logger.info("TimedQueueRefiller started", event_type="queue_refiller_start")

        while self.running:
            try:
                await self.career_docs_publisher.refill_queue()
            except asyncio.CancelledError:
                logger.info("TimedQueueRefiller cancelled", event_type="queue_refiller_cancelled")
                raise  # Re-raise to allow proper shutdown
            except Exception as e:
                logger.exception(
                    f"Error in queue refiller: {e}",
                    event_type="queue_refiller_error",
                    error_type=type(e).__name__,
                    error_details=str(e)
                )
                # Continue running despite error

            await asyncio.sleep(TimedQueueRefiller.WAIT_TIME)

    def stop(self):
        """Stop the queue refiller."""
        self.running = False
        logger.info("TimedQueueRefiller stopped", event_type="queue_refiller_stop")


timed_queue_refiller = TimedQueueRefiller()
