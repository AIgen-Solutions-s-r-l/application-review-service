from pymongo import MongoClient

def main():
    client = MongoClient("mongodb://localhost:27017")
    db = client["resumes"]
    collection = db["career_docs_responses"]
    
    # Query
    query = {
        "content.3c916dfc-d0d7-4f8e-b3b0-337cc4b20f00": { "$exists": True }
    }
    projection = {
        "content.3c916dfc-d0d7-4f8e-b3b0-337cc4b20f00": 1
    }

    # Find one document
    result = collection.find_one(query, projection)

    # Print the result
    if result:
        print("Document found:")
        print(result)
    else:
        print("No document matches the query.")

if __name__ == "__main__":
    main()
