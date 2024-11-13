import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
from bson import ObjectId
from app.core.config import Settings  # Only import Settings
from app.core.rabbitmq_client import RabbitMQClient

# Initialize settings and RabbitMQ client
settings = Settings()
rabbitmq_client = RabbitMQClient(settings.rabbitmq_url, settings.career_docs_queue, callback=None)
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
        # Connect to RabbitMQ if the channel isn't open
        if not rabbitmq_client.channel or not rabbitmq_client.channel.is_open:
            print("Connecting to RabbitMQ...")
            rabbitmq_client.connect()
            await asyncio.sleep(1)  # Brief sleep to allow connection establishment
        
        # Wait until the RabbitMQ channel is open, up to a maximum wait time
        max_wait_time = 100  # Adjust timeout as needed
        wait_time = 0
        while not rabbitmq_client.channel or not rabbitmq_client.channel.is_open:
            if wait_time >= max_wait_time:
                raise RuntimeError("RabbitMQ channel did not open in time.")
            print("Waiting for RabbitMQ channel to open...")
            await asyncio.sleep(1)
            wait_time += 1

        # Publish the message once the channel is open
        rabbitmq_client.publish_message(message)
        print(f"Notification sent for user {user_id}, job {job_id}")
    except Exception as e:
        print(f"Failed to send notification for user {user_id}, job {job_id}: {str(e)}")

async def consume_jobs_interleaved(mongo_client: AsyncIOMotorClient):
    try:
        print("Connecting to MongoDB...")
        
        db = mongo_client['db_name']
        collection = db['jobs_to_apply_per_user']
        
        print("Fetching job lists from MongoDB...")
        cursor = collection.find()
        job_lists = await cursor.to_list(length=None)
        
        pointers = {
            doc["_id"]: 0
            for doc in job_lists
            if "_id" in doc and "user_id" in doc and "jobs" in doc
        }

        while pointers:
            to_remove = []
            
            for doc in job_lists:
                if "_id" not in doc or "user_id" not in doc or "jobs" not in doc:
                    continue
                
                try:
                    doc_id = doc["_id"]
                    user_id = doc["user_id"]
                    jobs = doc["jobs"]
                    pointer = pointers.get(doc_id, 0)

                    if pointer < len(jobs):
                        job = jobs[pointer]
                        print(f"Processing job {job.get('job_id', 'unknown')} for user {user_id}")
                        
                        # Process the job
                        await process_job(user_id, job)

                        # Notify the career_docs service
                        await notify_career_docs(user_id, job.get('job_id', 'unknown'))
                        
                        pointers[doc_id] += 1
                    else:
                        to_remove.append(doc_id)

                except KeyError as ke:
                    print(f"KeyError in document {doc_id}: Missing key '{ke.args[0]}'")
                except Exception as e:
                    print(f"Error processing document {doc_id}: {str(e)}")
            
            for doc_id in to_remove:
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