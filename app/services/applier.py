import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
from bson import ObjectId

# Function to consume job lists in an interleaved manner with enhanced error handling and ObjectId support
async def consume_jobs_interleaved(mongo_client: AsyncIOMotorClient):
    try:
        print("Connecting to MongoDB...")
        
        # Retrieve all job lists from MongoDB
        db = mongo_client['db_name']
        collection = db['jobs_to_apply_per_user']
        
        print("Fetching job lists from MongoDB...")
        cursor = collection.find()
        job_lists = await cursor.to_list(length=None)
        
        print(f"Total job lists retrieved: {len(job_lists)}")
        
        # Initialize reading pointers for each list
        pointers = {doc["_id"]: 0 for doc in job_lists if "_id" in doc and "jobs" in doc and "user_id" in doc}
        print(f"Initialized pointers for job lists: {pointers}")
        
        while pointers:
            print(f"Current pointers state: {pointers}")
            to_remove = []
            
            for doc in job_lists:
                try:
                    # Validate and extract document fields
                    doc_id = doc["_id"]
                    user_id = doc["user_id"]
                    jobs = doc["jobs"]
                    pointer = pointers.get(doc_id, 0)

                    # Ensure doc_id is a valid ObjectId instance
                    if not isinstance(doc_id, ObjectId):
                        raise ValueError(f"Invalid ObjectId: {doc_id}")

                    print(f"Processing document ID: {doc_id}, User ID: {user_id}, Pointer: {pointer}")

                    if pointer < len(jobs):
                        # Process the next job
                        job = jobs[pointer]
                        print(f"Processing job {job['job_id']} for user {user_id}")

                        # Simulate job application process
                        await process_job(user_id, job)

                        # Increment the pointer
                        pointers[doc_id] += 1
                    else:
                        print(f"All jobs for document {doc_id} have been processed.")
                        # All jobs for this document have been consumed
                        to_remove.append(doc_id)

                except KeyError as ke:
                    print(f"KeyError in document {doc.get('_id')}: {ke}")
                except Exception as e:
                    print(f"Error processing document {doc.get('_id')}: {str(e)}")
            
            # Remove fully processed documents
            for doc_id in to_remove:
                try:
                    print(f"Removing completed document ID: {doc_id}")
                    await collection.delete_one({"_id": doc_id})
                    del pointers[doc_id]
                except Exception as e:
                    print(f"Error removing document {doc_id}: {str(e)}")
            
            # Pause to avoid infinite loop in case of long operations
            await asyncio.sleep(0.1)
        
        print("All jobs have been processed.")
    
    except Exception as e:
        print(f"Error occurred in main processing loop: {e}")
        raise HTTPException(status_code=500, detail="Error while consuming jobs.")

# Simulated job processing function with additional logging
async def process_job(user_id, job):
    try:
        print(f"Applying to job {job['title']} (Job ID: {job['job_id']}) for user {user_id}")
        await asyncio.sleep(0.5)  # Simulate a lengthy request or processing
        print(f"Job {job['job_id']} for user {user_id} has been processed.")
    except Exception as e:
        print(f"Error while processing job {job['job_id']} for user {user_id}: {e}")