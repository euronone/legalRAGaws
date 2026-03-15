from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.upload import router as upload_router
from backend.routes.chat import router as chat_router

app = FastAPI(
    title="Legal RAG System",
    description="RAG-based legal document search and Q&A system powered by AWS Bedrock and OpenSearch",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(upload_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    return {"message": "Legal RAG System API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
