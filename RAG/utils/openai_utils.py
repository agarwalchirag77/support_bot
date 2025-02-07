import math

from RAG import support_bot_prompt, intercom_default_response, db_path, db_collection_name, feedback_dir, chat_log_dir
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
from datetime import datetime, timezone
import json
import os, re
import pandas as pd
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def bot_main(conversation_id, user_message, mode, response_url):
    messages = generate_response(conversation_id, user_message)
    if mode == 'intercom':
        # feedback = f"[Feedback](https://docs.google.com/forms/d/e/1FAIpQLSeHC4kjcI8wZvquGUeEJE_Xny7mTOJ5x10owMjgD8MBZgu52Q/viewform?usp=pp_url&entry.1057886803={conversation_id}&entry.87765696=https://app.intercom.com/a/inbox/t7inwklp/inbox/conversation/{conversation_id}%23part_id%3Dcomment-{conversation_id}-{conversation_part_id})"
        # message = messages[-1].get(
        #     "content") + '\n' + feedback
        # print(messages[-1].get("content"))

        # feedback_log(feedback)
        if post_to_intercom(conversation_id=conversation_id, message=messages[-1].get("content") + '\n' + 'Response Confidence:' + str(int((confidence * 100) / len(logprob['content']))) + '%'):
            print("Post to intercom success")
    # elif mode == 'slack':
    #     feedback_response = "\n\nPlease Add your feedback for the response in the form " \
    #                         "https://forms.gle/oBK7EbEUmUY8tFkT6"
    #     post_to_slack(response_url, message=messages[-1].get("content") + feedback_response)


def generate_response(conversation_id, user_message):
    messages = get_conversation(conversation_id=conversation_id, initial_system_instruction=support_bot_prompt)
    logger.info("Post to intercom/slack start")
    # user_message = rewrite_query_for_vector_search(messages, user_message)
    related_docs = search_documentation(db.get_collection(db.get_client(db_path), db_collection_name), user_message)

    if num_tokens_from_messages(messages=messages) > 54000:
        logger.info("Summarize convo start")
        messages.append({
            "role": "system",
            "content": "Summarize the conversation in third person"
        })
        messages = [{
            "role": "system",
            "content": f"{support_bot_prompt}. "
                       f"Summary of conversation till now: {get_gpt3_5_16k_response(messages=messages)[0]}"
        }]
        logger.info("Summarized convo success")
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
    messages.pop(-2)
    if valid_response(messages[-1].get("content")) and messages[-1].get("content") != "Incomplete Data":
        pass
    else:
        messages[-1]["content"] = intercom_default_response
        default_reply_update(conversation_id=conversation_id)
    logger.info("GPT response processed successfully")

    save_conversation(conversation_id=conversation_id, messages=messages)
    logger.info("Saved conversation to chat_log")
    return messages


def compare_response(bot_response: str, actual_response: str) -> dict:
    test_prompt = """
    You are tasked with comparing a bot's response to an actual response and evaluating it based on specific metrics. Here are the responses you need to analyze:

<bot_response>
%s
</bot_response>

<actual_response>
%s
</actual_response>

Your task is to evaluate the bot's response based on the following metrics:

1. Correctness: Determine if the bot's response is correct, incorrect, or if the bot responded that it did not find the answer in the documentation.
2. Completeness: Assess if the bot's response is complete, incomplete, or if the bot responded that it did not find the answer in the documentation.
3. Reference doc: Check if the bot provided a reference document than say provided doc or if did not provide a reference document than say dod not provide doc, or if the bot responded that it did not find the answer in the documentation.

Carefully analyze both responses and compare them. Consider the following:
- Does the bot's response contain all the relevant information present in the actual response?
- Is the information provided by the bot accurate when compared to the actual response?
- Did the bot provide any reference to a document or source of information?

After your analysis, provide your evaluation for each metric. For each metric, first provide a brief justification for your rating, then give the rating itself.

Output your results in the following json format:

{"evaluation":
{
    "correctness": {
    "reasoning": "Your reasoning here",
    "score": "The appropriate score"
  },
  "completeness": {
    "reasoning": "Your reasoning here",
    "score": "The appropriate score"
  },
  "reference_doc": {
    "reasoning": "Your reasoning here",
    "score": "The appropriate score"
  }
}
}

Here are two examples of how your output might look:

Example 1:
{
    "evaluation": {
    "correctness": {
    "reasoning": "The bot's response accurately reflects the information provided in the actual response, including the correct figures and key points.",
      "score": "correct"
    },
    "completeness": {
    "reasoning": "The bot's response covers all the main points from the actual response, providing a comprehensive answer.",
      "score": "complete"
    },
    "reference_doc": {
    "reasoning": "The bot mentions 'According to the quarterly report' but does not provide a specific document reference.",
      "score": "Did not provide Doc"
    }
  }
}


Example 2:
{
    "evaluation": {
    "correctness": {
    "reasoning": "The bot explicitly stated that it does not have the information to answer the question in the Hevo documentation .",
      "score": "Bot responded that it did not know answer"
    },
    "completeness": {
    "reasoning": "As the bot did not provide an answer as it did not found the relevant data in documents",
      "score": "Bot responded that it did not know answer"
    },
    "reference_doc": {
    "reasoning": "The bot did not provide any reference document as it stated it did not have the information.",
      "score": "Bot responded that it did not know answer"
    }
  }
}


Please provide your evaluation based on the given bot response and actual response.

    """ % (bot_response, actual_response)
    messages = [{'role': 'system', 'content': test_prompt}]
    content = get_gpt3_5_16k_response(messages=messages)
    return content


def analyze_test_result(file_path):
    # Lists to store data
    indices = []
    correctness_scores = []
    completeness_scores = []
    documentation_scores = []

    # Read JSONL file
    with open(file_path, 'r') as file:
        for line in file:
            data = json.loads(line)

            # Extract required fields
            indices.append(data['test_case']['index'])
            correctness_scores.append(data['evaluation']['correctness']['score'])
            completeness_scores.append(data['evaluation']['completeness']['score'])
            documentation_scores.append(data['evaluation']['reference_doc']['score'])

    # Create DataFrame
    df = pd.DataFrame({
        'index': indices,
        'correctness': correctness_scores,
        'completeness': completeness_scores,
        'documentation': documentation_scores
    })

    # Calculate statistics for each metric
    total_cases = len(df)
    metrics = ['correctness', 'completeness', 'documentation']

    print("Analysis Report\n")
    print(f"Total number of test cases: {total_cases}\n")

    for metric in metrics:
        counts = Counter(df[metric])
        print(f"\n{metric.title()} Scores Distribution:")
        print("-" * 40)
        for score, count in counts.items():
            percentage = (count / total_cases) * 100
            print(f"{score}: {count} cases ({percentage:.2f}%)")

    return None


def generate_response_test(test_messages: list):
    current_datetime = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    test_output = f"{feedback_dir}/test_output_{current_datetime}.jsonl"
    try:

        with open(test_output, 'w', encoding='utf-8') as f:
            for case in test_messages:
                logger.info(f"Evaluating Test case:{case['index']}")
                conversation_id = f"test_case_{current_datetime}_{case['index']}"
                messages = generate_response(conversation_id, case['query'])
                # print (json.loads(messages[-1].get("content")))
                messages = json.loads(messages[-1].get("content"))
                metrics_str = compare_response(messages.get('response'), case['response'])
                metrics = json.loads(metrics_str)
                metrics = {'test_case': case, 'bot_response': messages.get('response'), 'evaluation': metrics['evaluation']}
                f.write(json.dumps(metrics) + '\r\n')
    except:
        print(metrics_str)
    finally:
        for filename in os.listdir(chat_log_dir):
            if filename.startswith('test_case_'):
                file_path = os.path.join(chat_log_dir, filename)
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted {file_path}")
                except OSError as e:
                    logger.info(f"Error deleting {file_path}: {e}")

        analyze_test_result(test_output)

    return 0


if __name__ == "__main__":
    test_messages = []
    with open(f"{feedback_dir}/test_use_case.jsonl", 'r', encoding="utf-8") as f:
        for line in f:
            test_messages.append(json.loads(line))
    # analyze_test_result(f"{feedback_dir}/test_output_20250204_0841.jsonl")
    # conversation_id=123123
    # user_message="How can I rename a destination table while ensuring Hevo still recognizes it?"
    # print (generate_response(conversation_id, user_message))
    generate_response_test(test_messages)

# 2025-02-03 17:57:06,820 - INFO - Evaluating Test case:1
