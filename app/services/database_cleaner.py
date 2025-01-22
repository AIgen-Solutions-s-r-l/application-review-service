from app.core.mongo import get_mongo_client

class DatabaseCleaner:

    def __init__(self):
        self.mongo_client = get_mongo_client()

    async def clean_from_db(self, id: str):
        db = self.mongo_client.get_database("resumes")
        collection = db.get_collection("jobs_to_apply_per_user")

        collection.delete_one({"_id": id})
        

database_cleaner = DatabaseCleaner()