import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
from app.core.config import Settings
from app.core.rabbitmq_client import RabbitMQClient

# Initialize settings and RabbitMQ client
settings = Settings()
rabbitmq_client = RabbitMQClient(settings.rabbitmq_url)
rabbitmq_client.connect()

async def notify_career_docs(user_id: str, resume: dict, jobs: list):
    """
    Publishes a message to the career_docs queue with the user's resume and jobs list.

    Args:
        user_id (str): The ID of the user.
        resume (dict): The user's resume data.
        jobs (list): The list of jobs associated with the user.
    """
    message = {
        "user_id": user_id,
        "resume": resume,
        "jobs": jobs,
    }
    try:
        # Use the RabbitMQ client to publish the message
        rabbitmq_client.publish_message(queue=settings.career_docs_queue, message=message)
        print(f"Notification sent to career_docs for user {user_id}")
    except Exception as e:
        print(f"Failed to send notification to career_docs for user {user_id}: {str(e)}")

async def consume_jobs(mongo_client: AsyncIOMotorClient):
    try:
        print("Connecting to MongoDB...")

        db = mongo_client.get_database("resumes")
        collection = db.get_collection("jobs_to_apply_per_user")

        print("Fetching job lists from MongoDB...")
        cursor = collection.find()
        job_lists = await cursor.to_list(length=None)

        for doc in job_lists:
            if "_id" not in doc or "user_id" not in doc or not isinstance(doc.get("jobs"), dict):
                print(f"Skipping invalid document: {doc}")
                continue

            user_id = doc["user_id"]
            resume = doc.get("resume", {})
            jobs_field = doc["jobs"]

            if "jobs" not in jobs_field:
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

            # After processing all jobs for the user, send the triple to career_docs
            await notify_career_docs(user_id, resume, jobs_data)

            # Optionally, delete the document from the collection after processing
            '''try:
                await collection.delete_one({"_id": doc["_id"]})
            except Exception as e:
                print(f"Error removing document {doc['_id']}: {str(e)}")'''

        print("All jobs have been processed.")

    except Exception as e:
        print(f"Error occurred in main processing loop: {e}")
        raise HTTPException(status_code=500, detail="Error while consuming jobs.")

# Simulated job processing function
async def process_job(user_id, job):
    try:
        print(f"Applying to job {job} for user {user_id}")
        await asyncio.sleep(0.5)  # Simulate a lengthy request or processing
        print(f"Job {job} for user {user_id} has been processed.")
    except Exception as e:
        print(f"Error while processing job {job} for user {user_id}: {e}")

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