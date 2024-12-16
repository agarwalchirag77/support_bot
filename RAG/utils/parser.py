import re
import requests

def extract_user_message(data):
    if data.get("topic") == "conversation.user.created":
        return data.get("data").get("item").get("source").get("body")
    else:
        return data.get("data").get("item").get("conversation_parts").get("conversation_parts")[0].get("body")


def parse_user_message(user_message):
    parsed_user_message = BeautifulSoup(user_message, features="html.parser").get_text()
    return {
        "role": "user",
        "content": parsed_user_message
    }


def valid_response(message: str) -> bool:
    # message_url = re.search("(?P<url>https?://[^\s]+)", message)
    pattern = r"(?:(?<=\()|(?<=\[)|(?<=\{))?(https?://(?:[\w\-]+\.)+[a-zA-Z]{2,}(?:/[\w\-./?%&=]*)?)(?:(?=\))|(?=\])|(?=\}))?"
    message_urls = re.findall(pattern, message)
    if len(message_urls) == 0:
        return True
    for url in message_urls:
        test_response = requests.get(url=url)
        if '''page not found!''' in test_response.text.lower():
            return False
    return True
