import uvicorn
from fastapi import FastAPI
from RAG.routes import health, intercom
from RAG.utils.openai_utils import generate_response

app = FastAPI()

# app.include_router(slack.router)
app.include_router(intercom.router)
app.include_router(health.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
