#!/usr/bin/env python
import pika
import logging

# create our logger
logger = logging.getLogger(__name__)

# make sure have the logger set to level to 
# accept the logging statements
logger.setLevel(logging.DEBUG)

# create a handler for our logs, so we can see them 
console = logging.StreamHandler()
# add the handler, so logs are shared as stream to STDOUT
logger.addHandler(console)

connection = pika.BlockingConnection(
    pika.URLParameters("amqp://guest:guest@localhost:5672")
)

# we need a channel to sent things to 
channel = connection.channel()
channel.queue_declare(queue="hello")

channel.basic_publish(exchange="", routing_key="hello", body="Hello World!")

logger.info(" [x] Sent 'Hello World!'")
connection.close()
