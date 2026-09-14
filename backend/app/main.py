from fastapi import FastAPI

from app.api.cases import router as cases_router
from app.api.evidence import router as evidence_router


app = FastAPI(
    title="Recruitment Scam Investigation Platform",
    description="Backend API for recruitment scam investigation and campaign intelligence.",
    version="0.1.0"
)


app.include_router(cases_router)
app.include_router(evidence_router)


@app.get("/")
def root():
    return {
        "message": "Recruitment Scam Investigation API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }