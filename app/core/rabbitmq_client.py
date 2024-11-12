import logging
import time
from typing import Callable, Any, Optional

import pika
import pika.channel
import pika.frame


class RabbitMQClient:
    """
    RabbitMQ Client to handle asynchronous connections, publishing, and consuming of messages.
    Uses pika.SelectConnection for asynchronous communication with RabbitMQ.
    """

    def __init__(self, rabbitmq_url: str, queue: str,
                 callback: Callable[[Any, pika.spec.Basic.Deliver, pika.spec.BasicProperties, bytes], None]) -> None:
        """
        Initializes the RabbitMQClient with a connection URL, queue name, and message callback function.
        """
        self.rabbitmq_url = rabbitmq_url
        self.queue = queue
        self.callback = callback
        self.connection: Optional[pika.SelectConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self.should_reconnect = False  # Flag to control reconnection

    def connect(self) -> None:
        """
        Establish an asynchronous connection to RabbitMQ and declare the queue.
        """
        logging.info("Connecting to RabbitMQ")
        try:
            self.connection = pika.SelectConnection(
                pika.URLParameters(self.rabbitmq_url),
                on_open_callback=self.on_connection_open,
                on_open_error_callback=self.on_connection_open_error,
                on_close_callback=self.on_connection_closed
            )
        except Exception as e:
            logging.error(f"Connection setup failed: {e}")
            self.schedule_reconnect()

    def on_connection_open(self, connection: pika.SelectConnection) -> None:
        logging.info("RabbitMQ connection opened")
        connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_open_error(self, connection: pika.SelectConnection, error: Exception) -> None:
        logging.error(f"Failed to open connection: {error}")
        self.schedule_reconnect()

    def on_connection_closed(self, connection: pika.SelectConnection, reason: Any) -> None:
        logging.warning(f"Connection closed: {reason}")
        if self.should_reconnect:
            self.schedule_reconnect()

    def on_channel_open(self, channel: pika.channel.Channel) -> None:
        logging.info("RabbitMQ channel opened")
        self.channel = channel
        self.channel.queue_declare(queue=self.queue, callback=self.on_queue_declared)

    def on_queue_declared(self, frame: pika.frame.Method) -> None:
        logging.info(f"Queue '{self.queue}' declared")
        self.channel.basic_consume(queue=self.queue, on_message_callback=self.callback, auto_ack=True)
        logging.info("Started consuming messages")

    def schedule_reconnect(self, delay: int = 5) -> None:
        """
        Schedule reconnection attempt after a delay.
        """
        logging.info(f"Reconnecting to RabbitMQ in {delay} seconds")
        self.should_reconnect = True
        if self.connection and self.connection.is_closing:
            self.connection.ioloop.call_later(delay, self.connect)
        else:
            time.sleep(delay)  # Fallback for manual control if ioloop not started

    def start(self) -> None:
        """
        Start the connection's I/O loop.
        """
        self.connect()
        if self.connection:
            try:
                self.connection.ioloop.start()
            except KeyboardInterrupt:
                self.stop()

    def stop(self) -> None:
        """
        Gracefully stop the connection's I/O loop.
        """
        self.should_reconnect = False
        if self.connection:
            self.connection.close()
            self.connection.ioloop.stop()
            logging.info("RabbitMQ connection closed and I/O loop stopped")
