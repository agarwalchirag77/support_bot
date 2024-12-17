import math

from RAG import support_bot_prompt, intercom_default_response, db_path, db_collection_name
from RAG.utils.message import get_conversation
from RAG.utils.message import num_tokens_from_messages
from RAG.utils.message import search_documentation
from RAG.utils.message import rewrite_query_for_vector_search
from RAG.utils.message import get_gpt3_5_16k_response
from RAG.utils.parser import valid_response
from RAG.outbridge.intercom import default_reply_update
from RAG.utils.message import save_conversation
from RAG.outbridge.intercom import post_to_intercom
from RAG.outbridge.slack import post_to_slack
from RAG.utils import db
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_response(conversation_id, user_message, mode, response_url):
    messages = get_conversation(conversation_id=conversation_id, initial_system_instruction=support_bot_prompt)
    # user_message = rewrite_query_for_vector_search(messages, user_message)
    # print("Re-written query: " + user_message)
    related_docs = search_documentation(db.get_collection(db.get_client(db_path), db_collection_name), user_message)

    if num_tokens_from_messages(messages=messages) > 54000:
        print("Summarize convo start")
        messages.append({
            "role": "system",
            "content": "Summarize the conversation in third person"
        })
        messages = [{
            "role": "system",
            "content": f"{support_bot_prompt}. "
                       f"Summary of conversation till now: {get_gpt3_5_16k_response(messages=messages)[0]}"
        }]
        print("Summarized convo success")
    messages.append({
        "role": "user",
        "content": user_message
    })

    messages.append(
        {
            "role": "system",
            "content": "Related Documentation to answer user query: "
                       + "1. URL: " + related_docs['ids'][0][0] + " Title:'" + related_docs['metadatas'][0][0]['Title'] + "' Document content: '" + str(related_docs['documents'][0][0]) + "'" + " \n"
                       + "2. URL: " + related_docs['ids'][0][1] + " Title:'" + related_docs['metadatas'][0][1]['Title'] + "' Document content: '" + str(related_docs['documents'][0][1]) + "'" + " \n"
                       + "3. URL: " + related_docs['ids'][0][2] + " Title:'" + related_docs['metadatas'][0][2]['Title'] + "' Document content: '" + str(related_docs['documents'][0][2]) + "'" + " \n"

        }
    )
    content, logprob = get_gpt3_5_16k_response(messages=messages, probability=True)
    confidence = 0
    for each in logprob['content']:
        confidence = confidence + math.exp(each['logprob'])
    messages.append(
        {
            "role": "assistant",
            "content": content
        }
    )
    # print("Final response:" + messages[-1].get("content") + '\n'+ 'Response Confidence:'+str(int((confidence*100) / len(logprob['content'])))+'%')
    messages.pop(-2)
    if valid_response(messages[-1].get("content")) and messages[-1].get("content") != "Incomplete Data":
        pass
    else:
        messages[-1]["content"] = intercom_default_response
        default_reply_update(conversation_id=conversation_id)
    print("final GPT response")
    save_conversation(conversation_id=conversation_id, messages=messages)
    print("Save Convo")
    print("Post to intercom/slack start")

    if mode == 'intercom':
        # feedback = f"[Feedback](https://docs.google.com/forms/d/e/1FAIpQLSeHC4kjcI8wZvquGUeEJE_Xny7mTOJ5x10owMjgD8MBZgu52Q/viewform?usp=pp_url&entry.1057886803={conversation_id}&entry.87765696=https://app.intercom.com/a/inbox/t7inwklp/inbox/conversation/{conversation_id}%23part_id%3Dcomment-{conversation_id}-{conversation_part_id})"
        # message = messages[-1].get(
        #     "content") + '\n' + feedback
        # print(messages[-1].get("content"))

        # feedback_log(feedback)
        if post_to_intercom(conversation_id=conversation_id, message=messages[-1].get("content")+ '\n'+ 'Response Confidence:'+str(int((confidence*100) / len(logprob['content'])))+'%'):
            print("Post to intercom success")
    elif mode == 'slack':
        feedback_response = "\n\nPlease Add your feedback for the response in the form " \
                            "https://forms.gle/oBK7EbEUmUY8tFkT6"
        post_to_slack(response_url, message=messages[-1].get("content") + feedback_response)


def generate_response_test():
    return 0
