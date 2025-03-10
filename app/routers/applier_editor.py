import json
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Any, List, Dict
from app.core.rabbitmq_client import rabbit_client
from app.core.auth import get_current_user
from app.core.mongo import get_mongo_client
from app.models.resume import Resume
from app.core.rabbitmq_client import AsyncRabbitMQClient
from app.schemas.app_jobs import ApplyContent, DetailedJobData, JobResponse

from app.services.generic_publisher import generic_publisher

router = APIRouter()

def get_rabbitmq_client() -> AsyncRabbitMQClient:
    return rabbit_client


@router.get(
    "/apply_content",
    summary="Retrieve career documents for the authenticated user",
    description="Fetch all career document responses associated with the user_id in the JWT, excluding resume_optimized and cover_letter",
    response_model=ApplyContent,
)
async def get_career_docs(
    current_user=Depends(get_current_user),
    mongo_client=Depends(get_mongo_client),
):
    user_id = current_user

    try:
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("career_docs_responses")

        # Fetch the entire 'content' field for the user
        document = await collection.find_one({"user_id": user_id}, {"_id": 0, "content": 1})

        if not document:
            raise HTTPException(status_code=404, detail="No career documents found for the user.")

        content = document.get("content", {})

        # We'll build a dict of app_id -> job_data
        jobs_dict = {}

        for app_id, app_data in content.items():
            if isinstance(app_data, dict):
                app_data.pop("resume_optimized", None)
                app_data.pop("cover_letter", None)

                jobs_dict[app_id] = JobResponse(**app_data)

        return ApplyContent(jobs=jobs_dict)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch career documents: {str(e)}"
        )
    
@router.get(
    "/apply_content/{application_id}",
    summary="Retrieve specific application data for the authenticated user",
    response_model=DetailedJobData,
)
async def get_application_data(
    application_id: str,
    current_user=Depends(get_current_user),
    mongo_client=Depends(get_mongo_client)
):
    user_id = current_user  # or however get_current_user is returning

    try:
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("career_docs_responses")

        document = await collection.find_one(
            {"user_id": user_id, f"content.{application_id}": {"$exists": True}},
            {"_id": 0, f"content.{application_id}": 1}
        )
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for application ID: {application_id} with user ID: {user_id}"
            )

        application_data = document["content"][application_id]

        transformed_data = {
            "resume_optimized": application_data.get("resume_optimized"),
            "cover_letter": application_data.get("cover_letter"),

            "job_info": {
                "id": application_data.get("id"),
                "portal": application_data.get("portal"),
                "title": application_data.get("title"),
                "workplace_type": application_data.get("workplace_type"),
                "posted_date": application_data.get("posted_date"),
                "job_state": application_data.get("job_state"),
                "description": application_data.get("description"),
                "apply_link": application_data.get("apply_link"),
                "company_name": application_data.get("company_name"),
                "location": application_data.get("location"),
                "short_description": application_data.get("short_description"),
                "company_logo": application_data.get("company_logo"),
                "field": application_data.get("field"),
                "experience": application_data.get("experience"),
                "skills_required": application_data.get("skills_required"),
            },
            "style": application_data.get("style"),
            "sent": application_data.get("sent"),
            "gen_cv": application_data.get("gen_cv"),
        }

        # Now parse into your Pydantic model (will also validate fields):
        return DetailedJobData(**transformed_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch application data: {str(e)}")

# Useful for modifying the style (see README)
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
            raise HTTPException(status_code=404, detail=f"Application ID {application_id} not found.")

        #for field, value in updates.items():
            #updates[field] = ensure_dict(value)

        # Perform the update
        update_query = {f"content.{application_id}.{field}": value for field, value in updates.items()}
        result = await collection.update_one(
            {"user_id": user_id},
            {"$set": update_query}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Failed to update application ID {application_id}.")

        return {"message": f"Application ID {application_id} updated successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to modify application: {str(e)}")

@router.put(
    "/update_application/resume_optimized/{application_id}",
    summary="Replace the entire 'resume_optimized' data for an application",
    description="Overwrite the 'resume_optimized' JSON portion for a specific application with the given JSON object",
    response_model=dict,
)
async def replace_resume_optimized(
    application_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    mongo_client=Depends(get_mongo_client),
):
    """
    Replace the entire 'resume_optimized' section for a specific application.

    Args:
        application_id (str): The unique ID of the application to update.
        request (Request): Raw request to validate input data.
        current_user: The authenticated user ID obtained from get_current_user.
        mongo_client: MongoDB client instance.

    Returns:
        dict: A message confirming the operation’s success.

    Raises:
        HTTPException: If the application doesn't exist or an error occurs during the update.
    """
    user_id = current_user  # If get_current_user returns the user_id directly
    try:
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("career_docs_responses")

        raw_data = await request.json()
        resume_data = raw_data.get("resume")
        if not resume_data:
            raise HTTPException(status_code=422, detail="Missing 'resume' key in the input data.")

        try:
            new_resume_optimized = Resume.model_validate(resume_data)
        except Exception as validation_error:
            print(f"Validation error: {validation_error}")
            raise HTTPException(
                status_code=422,
                detail=f"Invalid resume structure: {validation_error}"
            )

        # Debugging: Log the parsed data
        print(f"Validated resume data: {new_resume_optimized}")

        # Check if this application exists for this user
        existing_document = await collection.find_one(
            {"user_id": user_id, f"content.{application_id}.resume_optimized": {"$exists": True}},
            {"_id": 0, f"content.{application_id}.resume_optimized": 1}
        )

        if not existing_document:
            raise HTTPException(
                status_code=404,
                detail=f"Application ID {application_id} not found or missing 'resume_optimized' section."
            )

        # Serialize the Resume model to a dictionary
        serialized_data = new_resume_optimized.model_dump()

        # Replace the entire 'resume_optimized' content
        result = await collection.update_one(
            {"user_id": user_id},
            {"$set": {f"content.{application_id}.resume_optimized.resume": serialized_data}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Failed to update 'resume_optimized' for application {application_id}.")

        return {"message": f"'resume_optimized' for application ID {application_id} replaced successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put(
    "/update_application/cover_letter/{application_id}",
    summary="Replace the entire 'cover_letter' data for an application",
    description="Overwrite the 'cover_letter' JSON portion for a specific application with the given JSON object",
    response_model=dict,
)
async def replace_cover_letter(
    application_id: str,
    new_cover_letter: Dict[str, Any],
    current_user=Depends(get_current_user),
    mongo_client=Depends(get_mongo_client),
):
    """
    Replace the entire 'cover_letter' section for a specific application.

    Args:
        application_id (str): The unique ID of the application to update.
        new_cover_letter (Dict[str, Any]): The new 'cover_letter' object that will overwrite the existing one.
        current_user: The authenticated user ID obtained from get_current_user.
        mongo_client: MongoDB client instance.

    Returns:
        dict: A message confirming the operation’s success.

    Raises:
        HTTPException: If the application doesn't exist or an error occurs during the update.
    """
    user_id = current_user
    try:
        db = mongo_client.get_database("resumes")
        collection = db.get_collection("career_docs_responses")

        # Check if this application exists for this user
        existing_document = await collection.find_one(
            {"user_id": user_id, f"content.{application_id}.cover_letter.cover_letter": {"$exists": True}},
            {"_id": 0, f"content.{application_id}.cover_letter": 1}
        )

        if not existing_document:
            raise HTTPException(
                status_code=404,
                detail=f"Application ID {application_id} not found or missing 'cover_letter' section."
            )

        # Replace the entire 'cover_letter' content
        result = await collection.update_one(
            {"user_id": user_id},
            {"$set": {f"content.{application_id}.cover_letter": new_cover_letter}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Failed to update 'cover_letter' for application {application_id}.")

        return {"message": f"'cover_letter' for application ID {application_id} replaced successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        await generic_publisher.publish_data_to_microservices(document)

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
        await generic_publisher.publish_data_to_microservices(filtered_document)

        # Update the "sent" field to True for the selected application IDs
        for app_id in application_ids:
            await collection.update_one(
                {"user_id": user_id, f"content.{app_id}": {"$exists": True}},
                {"$set": {f"content.{app_id}.sent": True}}
            )

        return {"message": "Selected applications processed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process selected applications: {str(e)}")