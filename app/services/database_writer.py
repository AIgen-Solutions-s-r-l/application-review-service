from app.core.mongo import get_mongo_client
from bson import ObjectId

class DatabaseWriter:

    def __init__(self):
        self.mongo_client = get_mongo_client()
        

    async def clean_from_db(self, id: str):
        db = self.mongo_client.get_database("resumes")
        collection = db.get_collection("jobs_to_apply_per_user")

        await collection.delete_one({"_id": ObjectId(id)})


    async def restore_sent(self, mongo_id: str):
        db = self.mongo_client.get_database("resumes")
        collection = db.get_collection("jobs_to_apply_per_user")

        await collection.update_one(
            {"_id": mongo_id},
            {"$set": {"sent": False}}
        )


database_writer = DatabaseWriter()