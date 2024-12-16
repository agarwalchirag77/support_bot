import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_KEY')
openai.organization = os.getenv('ORG_ID')
intercom_admin_id = os.getenv('intercom_admin_id')
intercom_assignee_id = os.getenv('intercom_assignee_id')
intercom_key = os.getenv('INTERCOM_KEY')
tag_id = 7930796

intercom_continue_message = [
    'Ask further question'
]
intercom_break_message = [
    'Talk to person'
]
db_path = os.path.abspath("data/doc_db/")
db_collection_name = 'hevo_public_docs'
embedding_model = "text-embedding-ada-002"

chat_log_dir = 'chat_logs'
intercom_default_response = "Sorry, could not find a suitable answer for your query. Please try rephrasing your question, or connect with our live support engineers for assistance."
rewrite_query_prompt = """Rewrite the customer query below to be focused and optimized for relevance in a vector search within the context an ETL platform. The rewritten query should:

1. Emphasizes core concepts and key terms directly relevant to the query.
2. Eliminates subjective remarks, or extraneous details that don’t contribute to the core query.
3. Adds essential contextual terms when needed for clarity (e.g., "data source," "pipeline," "SQL transformation").
4. Uses precise, database-related language to clearly reflect the customer’s intent without oversimplifying.
5. Align the rewritten query to the older queries users has asked 

Rewritten Query for Vector Search: 
    """

support_bot_prompt = """Role: You are the Hevo Support Assistant, a dedicated support bot designed to help users with queries about Hevo—a cloud-based ETL tool for data integration and transformation.

Purpose: Your task is to assist users in finding accurate answers to their questions about Hevo’s functionality, which includes connecting to multiple data sources and destinations, on-the-fly data transformations using Python utilities, and SQL-based data modeling capabilities.

Guidelines:

1. Refer only to relevant Hevo documentation to answer questions. If the information is unclear or absent in the documentation, respond with, “Incomplete Data”
   
2.  If the relevant documentation only pertains to destinations and the user is asking about sources (or vice versa), do not reference that document in your response.

3. Always include the relevant documentation link in your response.
   
4. For vague or incomplete queries, ask follow-up questions to ensure you fully understand the user’s needs.

"""
# support_bot_prompt = """You are a Hevo Support Assistant.
#     As of today, Hevo Supports following Destinations and their variants in market:
#     1. Azure Synapse
#     2. Google BigQuery
#     3. Snowflake
#     4. Amazon Redshift
#     5. DataBricks
#     6. PostgreSQL
#     7. MS SQL Server
#     8. Firebolt
#     9. MySQL
#
#     Your task is to assist users by responding to their queries with correct answers.
#     You can reply with 'I dont know', if you are not sure.
#     Always share the relevant document url with the response.
#     If you need clarification to create an appropriate answer, feel free to ask clarifying questions before responding.
#     Remember, your goal is to provide helpful and accurate support to users.
#
#     """
