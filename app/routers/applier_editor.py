from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.auth import get_current_user
from app.core.mongo import get_mongo_client

router = APIRouter()

@router.get(
    "/apply_content",
    summary="Retrieve career documents for the authenticated user",
    description="Fetch all career document responses associated with the user_id in the JWT",
    response_model=List[dict],  # Adjust response model to your schema if needed
)
async def get_career_docs(
    current_user=Depends(get_current_user),
    mongo_client=Depends(get_mongo_client)
):
    """
    Retrieve career document responses for the authenticated user.

    Args:
        current_user: The authenticated user's ID obtained from the JWT.
        mongo_client: MongoDB client instance.

    Returns:
        List[dict]: A list of career document responses containing the 'content' field.

    Raises:
        HTTPException: If no documents are found or a database error occurs.
    """
    user_id = current_user  # Assuming `get_current_user` directly returns the user_id
    
    try:
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("career_docs_responses")

        documents = await collection.find({"user_id": user_id}, {"_id": 0, "content": 1}).to_list(length=None)

        if not documents:
            raise HTTPException(status_code=404, detail="No career documents found for the user.")

        return documents

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch career documents: {str(e)}")