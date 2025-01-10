import json
from fastapi import APIRouter, Depends, HTTPException
from typing import Any, List, Dict
from app.core.rabbitmq_client import rabbit_client
from app.core.auth import get_current_user
from app.core.mongo import get_mongo_client
from app.services.applier import send_data_to_microservices, ensure_dict
from app.core.rabbitmq_client import AsyncRabbitMQClient

router = APIRouter()

def get_rabbitmq_client() -> AsyncRabbitMQClient:
    return rabbit_client

@router.get(
    "/apply_content",
    summary="Retrieve career documents for the authenticated user",
    description="Fetch all career document responses associated with the user_id in the JWT, excluding resume_optimized and cover_letter",
    response_model=dict,
)
async def get_career_docs(
    current_user=Depends(get_current_user),
    mongo_client=Depends(get_mongo_client),
):
    """
    Retrieve career document responses for the authenticated user, excluding all 'resume_optimized' and 'cover_letter' fields.

    Args:
        current_user: The authenticated user's ID obtained from the JWT.
        mongo_client: MongoDB client instance.

    Returns:
        dict: A dictionary containing the 'content' field with 'resume_optimized' and 'cover_letter' fields removed.

    Raises:
        HTTPException: If no document is found or a database error occurs.
    """
    user_id = current_user  # Assuming `get_current_user` directly returns the user_id

    try:
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("career_docs_responses")

        # Fetch the entire 'content' field for the user
        document = await collection.find_one({"user_id": user_id}, {"_id": 0, "content": 1})

        if not document:
            raise HTTPException(status_code=404, detail="No career documents found for the user.")

        # Remove 'resume_optimized' and 'cover_letter' dynamically from the content
        content = document.get("content", {})
        for app_id in content.keys():
            content[app_id].pop("resume_optimized", None)
            content[app_id].pop("cover_letter", None)

        return content

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch career documents: {str(e)}")
    
@router.get(
    "/apply_content/{application_id}",
    summary="Retrieve specific application data for the authenticated user",
    description="Fetch the specific career document response associated with the given application ID.",
    response_model=dict,  # Adjust response model to your schema if needed
)
async def get_application_data(
    application_id: str,
    current_user=Depends(get_current_user),
    mongo_client=Depends(get_mongo_client)
):
    """
    Retrieve specific application data for the authenticated user.

    Args:
        application_id: The unique ID of the application to fetch.
        current_user: The authenticated user's ID obtained from the JWT.
        mongo_client: MongoDB client instance.

    Returns:
        dict: The data for the specific application ID.

    Raises:
        HTTPException: If the application ID is not found or a database error occurs.
    """
    user_id = current_user  # Assuming `get_current_user` directly returns the user_id

    try:
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("career_docs_responses")

        # Fetch the document for the user with the specific application ID in the `content`
        document = await collection.find_one(
            {"user_id": user_id, f"content.{application_id}": {"$exists": True}},
            {"_id": 0, f"content.{application_id}": 1}
        )

        if not document:
            raise HTTPException(status_code=404, detail=f"No data found for application ID: {application_id}")

        # Extract and return the specific application data
        return document["content"][application_id]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch application data: {str(e)}")

@router.put(
    "/modify_application/{application_id}",
    summary="Modify specific fields of an application",
    description="Update specific fields of an application within the authenticated user's content",
    response_model=dict,
)
async def modify_application_content(
    application_id: str,  # The ID of the application to be updated
    updates: Dict[str, Any],  # A dictionary of fields to update with new values
    current_user=Depends(get_current_user),
    mongo_client=Depends(get_mongo_client)
):
    """
    Modify specific fields of an application within the user's content.

    Args:
        application_id: The unique ID of the application to modify.
        updates: A dictionary containing the fields to be updated and their new values.
        current_user: The authenticated user's ID obtained from the JWT.
        mongo_client: MongoDB client instance.

    Returns:
        dict: A message indicating the success of the operation.

    Raises:
        HTTPException: If the application ID is not found or an error occurs during the update.
    """
    user_id = current_user  # Assuming `get_current_user` directly returns the user_id

    try:
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("career_docs_responses")

        # Ensure the application exists in the user's content
        existing_document = await collection.find_one(
            {"user_id": user_id, f"content.{application_id}": {"$exists": True}},
            {"_id": 0, f"content.{application_id}": 1}
        )

        if not existing_document:
            raise HTTPException(status_code=404, detail=f"Application ID '{application_id}' not found.")

        for field, value in updates.items():
            updates[field] = ensure_dict(value)

        # Perform the update
        update_query = {f"content.{application_id}.{field}": value for field, value in updates.items()}
        result = await collection.update_one(
            {"user_id": user_id},
            {"$set": update_query}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Failed to update application ID '{application_id}'.")

        return {"message": f"Application ID '{application_id}' updated successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to modify application: {str(e)}")


@router.post("/apply_all")
async def process_career_docs(
    current_user=Depends(get_current_user),
    mongo_client=Depends(get_mongo_client),
    rabbitmq: AsyncRabbitMQClient = Depends(get_rabbitmq_client)
):
    user_id = current_user
    try:
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("career_docs_responses")

        # Fetch the user's document
        document = await collection.find_one({"user_id": user_id}, {"_id": 0})

        if not document:
            raise HTTPException(
                status_code=404,
                detail="No career documents found for the user."
            )

        # Send the entire document to the microservices
        await send_data_to_microservices(document, rabbitmq)

        # Update `sent` field to True for all applications
        for app_id in document.keys():
            if app_id != "user_id":  # Skip user_id
                await collection.update_one(
                    {"user_id": user_id},
                    {"$set": {f"{app_id}.sent": True}}
                )

        return {"message": "Career documents processed successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process career documents: {str(e)}"
        )

@router.post(
    "/apply_selected",
    summary="Process selected applications for the authenticated user",
    description="Send a single document containing only the specified applications to RabbitMQ for processing",
    response_model=dict,
)
async def process_selected_applications(
    application_ids: List[str],  # List of application IDs from the request body
    current_user=Depends(get_current_user),
    mongo_client=Depends(get_mongo_client),
    rabbitmq: AsyncRabbitMQClient = Depends(get_rabbitmq_client)
):
    """
    Process selected applications for the authenticated user.

    Args:
        application_ids: List of application IDs to process.
        current_user: The authenticated user's ID obtained from the JWT.
        mongo_client: MongoDB client instance.
        rabbitmq: RabbitMQ client instance.

    Returns:
        dict: Success message if the specified applications are processed.

    Raises:
        HTTPException: If any error occurs during processing or if IDs are not found.
    """
    user_id = current_user  # Assuming `get_current_user` directly returns the user_id
    
    try:
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("career_docs_responses")

        # Fetch the user's document containing all their applications
        document = await collection.find_one({"user_id": user_id}, {"_id": 0})

        if not document or "content" not in document:
            raise HTTPException(status_code=404, detail="No career documents found for the user.")

        # Extract and filter the `content` field to include only the selected application IDs
        content = document["content"]
        filtered_content = {app_id: content[app_id] for app_id in application_ids if app_id in content}

        if not filtered_content:
            raise HTTPException(status_code=404, detail="None of the specified application IDs were found.")

        # Create the filtered document to send
        filtered_document = {
            "user_id": user_id,
            "content": filtered_content
        }

        # Send the filtered document to RabbitMQ
        await send_data_to_microservices(filtered_document, rabbitmq)

        # Update the "sent" field to True for the selected application IDs
        for app_id in application_ids:
            await collection.update_one(
                {"user_id": user_id, f"content.{app_id}": {"$exists": True}},
                {"$set": {f"content.{app_id}.sent": True}}
            )

        return {"message": "Selected applications processed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process selected applications: {str(e)}")