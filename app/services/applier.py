import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
from bson import ObjectId

async def consume_jobs_interleaved(mongo_client: AsyncIOMotorClient):
    try:
        print("Connecting to MongoDB...")
        
        db = mongo_client['db_name']
        collection = db['jobs_to_apply_per_user']
        
        print("Fetching job lists from MongoDB...")
        cursor = collection.find()
        job_lists = await cursor.to_list(length=None)
        
        print(f"Total job lists retrieved: {len(job_lists)}")
        
        pointers = {
            doc["_id"]: 0
            for doc in job_lists
            if "_id" in doc and "user_id" in doc and "jobs" in doc
        }
        
        missing_keys_docs = [
            doc for doc in job_lists
            if "_id" not in doc or "user_id" not in doc or "jobs" not in doc
        ]
        
        if missing_keys_docs:
            print(f"Skipping {len(missing_keys_docs)} documents with missing keys.")

        while pointers:
            print(f"Current pointers state: {pointers}")
            to_remove = []
            
            for doc in job_lists:
                if "_id" not in doc or "user_id" not in doc or "jobs" not in doc:
                    continue
                
                try:
                    doc_id = doc["_id"]
                    user_id = doc["user_id"]
                    jobs = doc["jobs"]
                    pointer = pointers.get(doc_id, 0)

                    # Ensure doc_id is a valid ObjectId instance
                    if not isinstance(doc_id, ObjectId):
                        raise ValueError(f"Invalid ObjectId: {doc_id}")

                    print(f"Processing document ID: {doc_id}, User ID: {user_id}, Pointer: {pointer}")

                    if pointer < len(jobs):
                        job = jobs[pointer]
                        print(f"Processing job {job.get('job_id', 'unknown')} for user {user_id}")
                        await process_job(user_id, job)
                        pointers[doc_id] += 1
                    else:
                        print(f"All jobs for document {doc_id} have been processed.")
                        to_remove.append(doc_id)

                except KeyError as ke:
                    print(f"KeyError in document {doc_id}: Missing key '{ke.args[0]}'")
                except Exception as e:
                    print(f"Error processing document {doc_id}: {str(e)}")
            
            for doc_id in to_remove:
                try:
                    print(f"Removing completed document ID: {doc_id}")
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