import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
from app.core.config import Settings
from app.core.rabbitmq_client import RabbitMQClient

# Initialize settings and RabbitMQ client
settings = Settings()
rabbitmq_client = RabbitMQClient(settings.rabbitmq_url)
rabbitmq_client.connect()

async def notify_career_docs(user_id: str, job_id: str):
    """
    Publishes a message to the career_docs queue after a job is processed.

    Args:
        user_id (str): The ID of the user associated with the job.
        job_id (str): The ID of the processed job.
    """
    message = {
        "user_id": user_id,
        "job_id": job_id,
        "status": "processed"
    }
    try:
        # Use the existing rabbitmq_client to publish the message
        rabbitmq_client.publish_message(queue=settings.career_docs_queue, message=message)
        print(f"Notification sent for user {user_id}, job {job_id}")
    except Exception as e:
        print(f"Failed to send notification for user {user_id}, job {job_id}: {str(e)}")

async def consume_jobs_interleaved(mongo_client: AsyncIOMotorClient):
    try:
        print("Connecting to MongoDB...")

        db = mongo_client.get_database("db_name")
        collection = db.get_collection("jobs_to_apply_per_user")

        print("Fetching job lists from MongoDB...")
        cursor = collection.find()
        job_lists = await cursor.to_list(length=None)

        # Initialize pointers with a guard clause for non-empty jobs
        pointers = {
            doc["_id"]: 0
            for doc in job_lists
            if "_id" in doc and "user_id" in doc and "jobs" in doc and len(doc["jobs"]) > 0
        }

        while pointers:
            to_remove = []

            for doc in job_lists:
                if "_id" not in doc or "user_id" not in doc or "jobs" not in doc:
                    continue

                doc_id = doc["_id"]
                user_id = doc["user_id"]
                jobs = doc["jobs"]

                if doc_id not in pointers:
                    continue

                pointer = pointers[doc_id]

                if pointer < len(jobs):
                    job = jobs[pointer]
                    print(f"Processing job {job.get('job_id', 'unknown')} for user {user_id}")

                    # Process the job
                    await process_job(user_id, job)

                    # Notify the career_docs service
                    await notify_career_docs(user_id, job.get('job_id', 'unknown'))

                    # Increment pointer after processing
                    pointers[doc_id] += 1

                    # If pointer exceeds job length, mark for removal
                    if pointers[doc_id] >= len(jobs):
                        to_remove.append(doc_id)
                else:
                    to_remove.append(doc_id)

            # Remove documents that have been fully processed
            for doc_id in to_remove:
                if doc_id in pointers:
                    try:
                        await collection.delete_one({"_id": doc_id})
                        del pointers[doc_id]
                    except Exception as e:
                        print(f"Error removing document {doc_id}: {str(e)}")

            await asyncio.sleep(0.1)

        print("All jobs have been processed.")

    except Exception as e:
        print(f"Error occurred in main processing loop: {e}")
        raise HTTPException(status_code=500, detail="Error while consuming jobs.")

# Simulated job processing function
async def process_job(user_id, job):
    try:
        print(f"Applying to job {job.get('title', 'Unknown Title')} (Job ID: {job.get('job_id', 'unknown')}) for user {user_id}")
        await asyncio.sleep(0.5)  # Simulate a lengthy request or processing
        print(f"Job {job.get('job_id', 'unknown')} for user {user_id} has been processed.")
    except Exception as e:
        print(f"Error while processing job {job.get('job_id', 'unknown')} for user {user_id}: {e}")

async def handle_career_docs_response(body: dict):
    """
    Handle the response from the career_docs service.
    Args:
        body (dict): The message containing the CV, cover letter, and interview responses.
    """
    try:
        print(f"Received response from career_docs: {body}")
        # Example of processing the received response
        cv = body.get("cv")
        cover_letter = body.get("cover_letter")
        interview_responses = body.get("interview_responses")
        
        # Process or save to MongoDB as required
        print(f"Processing: CV={cv}, Cover Letter={cover_letter}, Interview Responses={interview_responses}")
    except Exception as e:
        print(f"Error handling career_docs response: {e}")