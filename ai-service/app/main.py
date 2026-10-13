from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.ingestion import router as ingestion_router
from app.api.query import router as query_router

app = FastAPI(
    title="Financial Statement Intelligence Platform - AI Service",
    description="Internal FastAPI service providing document ingestion, vector RAG, and financial analysis.",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health_router)
app.include_router(ingestion_router)
app.include_router(query_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
