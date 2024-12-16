import os
import logging
from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, status
from bs4 import BeautifulSoup
from RAG.utils.openai_utils import generate_response
from RAG import chat_log_dir

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/slack", status_code=200)
async def slack(background_tasks: BackgroundTasks,
                channel_id: str = Form(..., description="Slack channel ID"),
                user_id: str = Form(..., description="User ID from Slack"),
                text: str = Form(..., description="User message text"),
                response_url: str = Form(..., description="URL to post the response to Slack")
                ):
    """
    Endpoint to handle incoming Slack messages, process them, and generate responses using OpenAI.
    Supports clearing chat history by using the '--fresh' command.
    """
    conversation_id = f"{channel_id}{user_id}"
    user_message = BeautifulSoup(text, features="html.parser").get_text()

    if "--fresh" in user_message:
        # Handle clearing chat context
        chat_file_path = os.path.join(chat_log_dir, f"{conversation_id}.jsonl")
        archived_chat_file_path = os.path.join(chat_log_dir, f"{conversation_id}_archived.jsonl")

        try:
            # Check if chat file exists before renaming
            if os.path.exists(chat_file_path):
                os.renames(chat_file_path, archived_chat_file_path)
                logger.info(f"Chat context cleared for conversation: {conversation_id}")
                return {"response_type": "in_channel", "text": "Old chat context cleared from memory."}
            else:
                logger.warning(f"No chat file found to clear for conversation: {conversation_id}")
                return {"response_type": "in_channel", "text": "No previous chat context found."}
        except OSError as e:
            logger.error(f"Error occurred while renaming the file for {conversation_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error clearing chat context.")

    # Process new message in the background
    try:
        logger.info(f"Generating response for conversation: {conversation_id}")
        background_tasks.add_task(generate_response, conversation_id, user_message, 'slack', response_url)
        return {"response_type": "in_channel", "text": "Thinking of a response..."}
    except Exception as e:
        logger.error(f"Error generating response for {conversation_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing the request.")
