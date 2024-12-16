from fastapi import APIRouter
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


# Define Pydantic models for request body validation
class AddDocuments(BaseModel):
    documents: List[str]
    ids: List[str]


class DeleteDocuments(BaseModel):
    ids: List[str]


class UpdateDocuments(BaseModel):
    ids: List[str]
    new_documents: List[str]


class QueryDocuments(BaseModel):
    query_texts: List[str]
    n_results: Optional[int] = 2


# API Endpoints
@router.post("/db/add")
def add_documents(payload: AddDocuments):
    try:
        collection = get_collection()
        collection.add(documents=payload.documents, ids=payload.ids)
        return {"message": f"Added {len(payload.documents)} documents successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding documents: {str(e)}")


@router.post("/db/delete")
def delete_documents(payload: DeleteDocuments):
    try:
        collection = get_collection()
        collection.delete(ids=payload.ids)
        return {"message": f"Deleted {len(payload.ids)} documents successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting documents: {str(e)}")


@router.post("/db/update")
def update_documents(payload: UpdateDocuments):
    try:
        collection = get_collection()
        # Assuming update means deleting old docs and adding new ones
        collection.delete(ids=payload.ids)
        collection.add(documents=payload.new_documents, ids=payload.ids)
        return {"message": f"Updated {len(payload.new_documents)} documents successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating documents: {str(e)}")


@router.post("/db/query")
def query_documents(payload: QueryDocuments):
    try:
        collection = get_collection()
        results = collection.query(query_texts=payload.query_texts, n_results=payload.n_results)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying documents: {str(e)}")
