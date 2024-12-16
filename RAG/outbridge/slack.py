

def post_to_slack(response_url, message):
    message = message
    request_body = {
        "response_type": "in_channel",
        "text": message
    }

    headers = {
        "Content-Type": "application/json",
    }

    intercom_reply_url = response_url
    requests.post(url=intercom_reply_url, data=json.dumps(request_body), headers=headers)