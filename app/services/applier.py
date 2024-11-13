# /app/services/applier.py

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException

# Funzione per consumare le liste in modo interlacciato
async def consume_jobs_interleaved(mongo_client: AsyncIOMotorClient):
    try:
        print("Connecting to MongoDB...")
        
        # Recupera tutte le liste di lavoro da MongoDB
        db = mongo_client['db_name']
        collection = db['jobs_to_apply_per_user']
        
        print("Fetching job lists from MongoDB...")
        cursor = collection.find()
        job_lists = await cursor.to_list(length=None)
        
        print(f"Total job lists retrieved: {len(job_lists)}")
        
        # Inizializza gli indici di lettura per ogni lista
        pointers = {doc["_id"]: 0 for doc in job_lists}
        print(f"Initialized pointers for job lists: {pointers}")
        
        while pointers:
            print(f"Current pointers state: {pointers}")
            to_remove = []
            
            for doc in job_lists:
                doc_id = doc["_id"]
                user_id = doc["user_id"]
                jobs = doc["jobs"]
                pointer = pointers.get(doc_id, 0)
                
                print(f"Processing document ID: {doc_id}, User ID: {user_id}, Pointer: {pointer}")
                
                if pointer < len(jobs):
                    # Consuma il prossimo lavoro
                    job = jobs[pointer]
                    print(f"Processing job {job['job_id']} for user {user_id}")
                    
                    # Simula il processo di applicazione al lavoro
                    await process_job(user_id, job)
                    
                    # Incrementa il puntatore
                    pointers[doc_id] += 1
                else:
                    print(f"All jobs for document {doc_id} have been processed.")
                    # Tutti i lavori per questo documento sono stati consumati
                    to_remove.append(doc_id)
            
            # Rimuovi documenti consumati completamente
            for doc_id in to_remove:
                print(f"Removing completed document ID: {doc_id}")
                await collection.delete_one({"_id": doc_id})
                del pointers[doc_id]
            
            # Fai una pausa per evitare loop infinito in caso di operazioni lunghe
            await asyncio.sleep(0.1)
        
        print("All jobs have been processed.")
    
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Error while consuming jobs.")

# Simulazione della funzione di elaborazione del lavoro
async def process_job(user_id, job):
    print(f"Applying to job {job['title']} (Job ID: {job['job_id']}) for user {user_id}")
    await asyncio.sleep(0.5)  # Simula una richiesta o elaborazione lunga
    print(f"Job {job['job_id']} for user {user_id} has been processed.")
