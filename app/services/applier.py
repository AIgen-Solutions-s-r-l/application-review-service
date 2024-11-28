# app/services/applier.py

import asyncio
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.rabbitmq_client import AsyncRabbitMQClient
import json
from aio_pika import IncomingMessage
from app.core.appliers_config import APPLIERS, process_default

async def notify_career_docs(user_id: str, resume: dict, jobs: list, rabbitmq_client: AsyncRabbitMQClient, settings):
    """
    Publishes a message to the career_docs queue with the user's resume and jobs list.
    """
    message = {
        "user_id": user_id,
        "resume": resume,
        "jobs": jobs,
    }
    try:
        # Use the RabbitMQ client to publish the message
        await rabbitmq_client.publish_message(queue_name=settings.career_docs_queue, message=message)
        print(f"Notification sent to career_docs for user {user_id}")
    except Exception as e:
        print(f"Failed to send notification to career_docs for user {user_id}: {str(e)}")


async def consume_jobs(mongo_client: AsyncIOMotorClient, rabbitmq_client: AsyncRabbitMQClient, settings):
    while True:  # Infinite loop to keep consuming jobs
        try:
            print("Connecting to MongoDB...")
            db = mongo_client.get_database("resumes")
            collection = db.get_collection("jobs_to_apply_per_user")

            print("Fetching job lists from MongoDB...")
            cursor = collection.find({}, {"_id": 0})
            job_lists = await cursor.to_list(length=None)

            for doc in job_lists:
                if "user_id" not in doc:
                    print(f"Skipping invalid document")
                    continue

                user_id = doc["user_id"]
                resume = doc.get("resume", {})
                jobs_field = doc["jobs"]

                # Check if jobs_field is a JSON string and parse it
                if isinstance(jobs_field, str):
                    try:
                        jobs_field = json.loads(jobs_field)
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse 'jobs' JSON: {str(e)}")
                        continue

                if not isinstance(jobs_field, dict) or "jobs" not in jobs_field:
                    print(f"Invalid 'jobs' structure in document: {doc}")
                    continue

                jobs_data = jobs_field["jobs"]

                if not isinstance(jobs_data, list):
                    print(f"'jobs' is not a list in document: {doc}")
                    continue

                for job in jobs_data:
                    job_id = job.get("id")
                    job_title = job.get("title")
                    print(f"Processing job '{job_title}' (Job ID: {job_id}) for user {user_id}")

                    # Process the job
                    await process_job(user_id, job)

                # After processing all jobs for the user, send the data to career_docs
                await notify_career_docs(user_id, resume, jobs_data, rabbitmq_client, settings)

                #TOENABLE then: Remove the processed document from MongoDB
                '''result = await collection.delete_one({"user_id": user_id})
                if result.deleted_count > 0:
                    print(f"Successfully deleted document for user_id: {user_id}")
                else:
                    print(f"Failed to delete document for user_id: {user_id}")'''

            print("All jobs have been processed.")

            # Wait before fetching again to avoid overloading MongoDB
            await asyncio.sleep(10)

        except Exception as e:
            print(f"Error occurred in main processing loop: {str(e)}")
            # Optional: Add a short delay to prevent rapid retries
            await asyncio.sleep(5)

# Simulated job processing function
async def process_job(user_id, job):
    try:
        print(f"Applying to job {job} for user {user_id}")
        await asyncio.sleep(0.5)  # Simulate a lengthy request or processing
        print(f"Job {job} for user {user_id} has been processed.")
    except Exception as e:
        print(f"Error while processing job {job} for user {user_id}: {e}")


async def consume_career_docs_responses(rabbitmq_client: AsyncRabbitMQClient, settings):
    """
    Consumes messages from the career_docs_response_queue.
    """
    async def on_message(message: IncomingMessage):
        body = message.body.decode()
        data = json.loads(body)
        print(f"Received response from career_docs: {data}")

        # Process the received data and send to other appliers (see core/appliers_config.py)
        # TODO: When we'll have other appliers: add them and decomment it!
        # await send_data_to_microservices(data, rabbitmq_client)
        
        # Acknowledge the message
        await message.ack()

    await rabbitmq_client.consume_messages(
        queue_name=settings.career_docs_response_queue,
        callback=on_message,
        auto_ack=False  # We'll manually acknowledge after processing
    )

async def send_data_to_microservices(data, rabbitmq_client: AsyncRabbitMQClient):
    """
    Processes the received data and sends it to different microservices via their queues.
    """
    for microservice_name, microservice_info in APPLIERS.items():
        queue_name = microservice_info['queue_name']
        process_function = microservice_info.get('process_function', process_default)

        # Process data for the microservice
        microservice_data = process_function(data)

        # Send data to the microservice's queue
        await rabbitmq_client.publish_message(queue_name=queue_name, message=microservice_data)
        print(f"Sent data to microservice '{microservice_name}' via queue '{queue_name}'")