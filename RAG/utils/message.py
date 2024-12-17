from RAG import chat_log_dir
import os
import json
import tiktoken
from RAG import intercom_default_response, openai, rewrite_query_prompt
from RAG.utils.db import query_collection
import requests
import chromadb


def rewrite_query_for_vector_search(context, query: str) -> str:
    """
    Function to rewrite a customer query to make it more suitable for vector database search.

    Args:
        query (str): The original customer query.

    Returns:
        str: The rewritten query suitable for vector database search.
        :param query:
        :param context:
    """

    request = [{
        "role": "system", "content": rewrite_query_prompt
    }]
    for each in context:
        if each["role"] == "user":
            request.append(each)
    user_query = {
        "role": "user",
        "content": query
    }
    request.append(user_query)

    try:
        # Use the OpenAI API to generate the rewritten query
        response = get_gpt3_5_16k_response(request)

        return response

    except Exception as e:
        print(f"Error during query rewriting: {e}")
        return query  # If an error occurs, return the original query


def get_conversation(conversation_id: str, initial_system_instruction: str):
    messages = []
    chat_file_path = f"{chat_log_dir}/{conversation_id}.jsonl"

    if os.path.exists(chat_file_path):
        with open(chat_file_path, 'r', encoding='utf-8') as f:
            messages = [json.loads(line) for line in f]
    else:
        messages.append({"role": "system", "content": initial_system_instruction})

    return messages


def search_documentation(collection: chromadb.Collection, query):
    response = query_collection(collection,
                                query_texts=query,
                                n_results=3
                                )
    # print (response)
    # response = ""
    # c = 0
    # for idx, result in results.iterrows():
    #     c = c + 1
    #     print(f"Similarity: {result['similarity']}")
    #     if result["n_tokens"] <= 6000:
    #         response = result["combined"]
    #     elif 8000 > result["n_tokens"] > 6000:
    #         response = get_gpt4_32k_response(messages=[{
    #             "role": "system",
    #             "content": f"Summarize the documentation: {result['combined']}"
    #         }])
    #     else:
    #         response = result["url"]
    #     if c == 1:
    #         break
    # return response
    return response


def num_tokens_from_messages(messages, model="gpt-4o-mini"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-4o-mini":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        print(f"Tokens: {num_tokens}")
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}. See 
        https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to 
        tokens.""")


def write_to_file(conversation_id: str, conversation: dict):
    with open(f"{chat_log_dir}/{conversation_id}.jsonl", "a") as outfile:
        outfile.write(json.dumps(conversation))
        outfile.write("\r\n")


def save_conversation(conversation_id, messages):
    chat_file_path = f"{chat_log_dir}/{conversation_id}.jsonl"
    with open(chat_file_path, 'w', encoding='utf-8') as f:
        for item in messages:
            f.write(json.dumps(item, ensure_ascii=False) + '\r\n')


def feedback_log(feedback):
    feedback_file = "Feedback/feedback_forms.txt"
    with open(feedback_file, 'a+', encoding='utf-8') as f:
        f.write(feedback + '\n')


def get_gpt3_5_16k_response(messages: list, probability=False):
    # Todo: Optimize below hyper-parameters.

    print("Inside get_gpt3_5_16k_response")
    request_body = {
        "model": "gpt-4o-mini",
        "logprobs": probability,
        "messages": messages,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }
    openai_chat_completion_url = "https://api.openai.com/v1/chat/completions"
    text_completion_response = requests.post(url=openai_chat_completion_url, data=json.dumps(request_body),
                                             headers=headers, timeout=60)

    response = text_completion_response.json()
    if text_completion_response.status_code != 200:
        return intercom_default_response
    else:
        # Todo: Parser the message separately
        return response['choices'][0]['message']['content'].strip(), response['choices'][0].get('logprobs')
