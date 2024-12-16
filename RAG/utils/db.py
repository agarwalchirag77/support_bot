import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from RAG import openai, db_path, embedding_model, db_collection_name
import logging
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Initialize ChromaDB Client
def get_client(path: str) -> chromadb.PersistentClient:
    """Initialize the ChromaDB Persistent Client."""
    try:
        client = chromadb.PersistentClient(path=path)
        logger.info(f"ChromaDB Client initialized with document path: {db_path}")
        return client
    except Exception as e:
        logger.error(f"Error initializing ChromaDB Client: {e}")
        raise


def get_embedding_function(key: openai.api_key, model: str) -> embedding_functions:
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=key,
        model_name=model
    )


def get_collection(client: chromadb.PersistentClient, name: str) -> chromadb.Collection:
    """Retrieve or create a ChromaDB collection with metadata and embedding function."""
    try:

        collection = client.get_collection(
            name=name,
            embedding_function=get_embedding_function(openai.api_key, embedding_model)
        )
        logger.info(f"Collection '{name}' retrieved or created.")
        return collection
    except Exception as e:
        logger.error(f"Error retrieving or creating collection: {e}")
        raise


# Create or retrieve collection
def get_or_create_collection(client: chromadb.PersistentClient, name: str, metadata: dict) -> chromadb.Collection:
    """Retrieve or create a ChromaDB collection with metadata and embedding function."""
    try:
        collection = client.get_or_create_collection(
            name=name,
            metadata=metadata,
            embedding_function=get_embedding_function(openai.api_key, embedding_model)
        )
        logger.info(f"Collection '{name}' retrieved or created.")
        return collection
    except Exception as e:
        logger.error(f"Error retrieving or creating collection: {e}")
        raise


# Add documents to the collection
def add_documents_to_collection(collection: chromadb.Collection, documents: List[str], ids: List[str], metadata: List[str]):
    """Add documents to the ChromaDB collection."""
    try:
        collection.upsert(documents=documents, ids=ids, metadatas=metadata)
        logger.info(f"Added {len(documents)} documents to the collection.")
    except Exception as e:
        logger.error(f"Error adding documents to collection: {e}")
        raise


# Query the collection
def query_collection(collection: chromadb.Collection, query_texts: List[str], n_results: int = 1):
    """Query the ChromaDB collection."""
    try:
        results = collection.query(query_texts=query_texts, n_results=n_results)
        logger.info(f"Search Query executed successfully. Results: {results}")
        return results
    except Exception as e:
        logger.error(f"Error querying the collection: {e}")
        raise
