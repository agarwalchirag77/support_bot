from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, status
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError, Field
from typing import Dict, Any
import logging

from RAG.utils.parser import extract_user_message
from RAG.outbridge.intercom import pass_to_person
from RAG import intercom_break_message, intercom_continue_message, tag_id
from RAG.utils.openai_utils import generate_response

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic model to validate incoming data
class IntercomData(BaseModel):
    data: Dict[str, Any] = Field(..., description="Data from Intercom webhook")


# Custom validation function for required fields
def validate_intercom_data(data: Dict[str, Any]):
    try:
        item = data.get('data', {}).get('item', {})
        if not item:
            raise ValueError("Missing 'item' in request data.")
        if 'tags' not in item or 'id' not in item:
            raise ValueError("Missing 'tags' or 'id' in item.")
        return item
    except (AttributeError, ValueError) as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/intercom", status_code=200)
async def intercom(background_tasks: BackgroundTasks, data: IntercomData = Body()):
    """
    Handles incoming webhooks from Intercom and triggers necessary actions.
    """
    try:
        print ("Received intercom webhook")
        # Validate and extract data
        item = validate_intercom_data(data.dict())

        tags = item.get("tags", {}).get("tags", [])
        conversation_id = item.get("id")
        logger.info(f"Processing conversation ID: {conversation_id}")

        # Iterate over tags to find relevant action
        for tag in tags:
            if tag.get("id") == str(tag_id):
                user_message = extract_user_message(data.dict())
                user_message = BeautifulSoup(user_message, features="html.parser").get_text()

                # Break, continue, or process the message
                if user_message in intercom_continue_message:
                    return {"success": True}
                elif user_message in intercom_break_message:
                    pass_to_person(conversation_id)
                    logger.info(f"Conversation {conversation_id} passed to a person.")
                else:
                    background_tasks.add_task(generate_response, conversation_id, user_message, 'intercom', None)
                    logger.info(f"Generating response for conversation ID: {conversation_id}")
                break
        else:
            logger.info(f"No matching tag found for conversation ID: {conversation_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching tag found.")

        return {"success": True}

    except ValidationError as e:
        logger.error(f"Validation error: {e.json()}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")
