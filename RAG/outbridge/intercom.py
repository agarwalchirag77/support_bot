import time

import math
import requests
import json
from RAG import intercom_key, intercom_admin_id, tag_id


def pass_to_person(conversation_id):
    print(conversation_id)
    delete_tag(conversation_id=conversation_id)


def delete_tag(conversation_id):
    request_body = {
        "admin_id": intercom_admin_id
    }

    headers = {
        "Intercom-Version": "2.8",
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {intercom_key}"
    }

    intercom_delete_tag_url = f"https://api.intercom.io/conversations/{conversation_id}/tags/{tag_id}"
    requests.delete(url=intercom_delete_tag_url, data=json.dumps(request_body), headers=headers)


def post_to_intercom(conversation_id, message):
    request_body = {
        "message_type": "comment",
        "type": "admin",
        "admin_id": intercom_admin_id,
        "body": message.replace('\n', '<br>')
    }

    headers = {
        "Intercom-Version": "2.8",
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {intercom_key}"
    }

    intercom_reply_url = f"https://api.intercom.io/conversations/{conversation_id}/reply"

    try:
        response = requests.post(url=intercom_reply_url, data=json.dumps(request_body), headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # Handle HTTP error
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")  # Handle connection error
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")  # Handle timeout error
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred: {req_err}")  # Handle any request exception
    except Exception as e:
        print(f"An unexpected error occurred: {e}")  # Handle any other unexpected errors
    else:
        print(f"Message posted successfully: {response.status_code}")

    request_body = {
        "message_type": "snoozed",
        "admin_id": 6500280,
        "snoozed_until": str(math.ceil(time.time()) + 5 * 60)
    }
    intercom_parts_url = f"https://api.intercom.io/conversations/{conversation_id}/parts"
    response = requests.post(url=intercom_parts_url, data=json.dumps(request_body), headers=headers)
    # print(response.json())
    return 1


def assign_to_team(conversation_id):
    request_body = {
        "message_type": "assignment",
        "type": "team",
        "admin_id": intercom_admin_id,
        "assignee_id": intercom_assignee_id
    }

    headers = {
        "Intercom-Version": "2.8",
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {intercom_key}"
    }

    intercom_assign_url = f"https://api.intercom.io/conversations/{conversation_id}/parts"
    requests.post(url=intercom_assign_url, data=json.dumps(request_body), headers=headers)


def default_reply_update(conversation_id):
    request_body = {
        "custom_attributes": {
            "First_Feedback": "Yes"
        },
        "read": True
    }
    headers = {
        "Intercom-Version": "2.8",
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {intercom_key}"
    }
    intercom_reply_url = f"https://api.intercom.io/conversations/{conversation_id}"
    requests.put(url=intercom_reply_url, data=json.dumps(request_body), headers=headers)
