from fastapi import FastAPI

from app.api.cases import router as cases_router
from app.api.evidence import router as evidence_router
from app.api.campaigns import router as campaigns_router
from app.api.entities import router as entities_router
from app.api.verdicts import router as verdicts_router
from app.api.reports import router as reports_router
from app.api.auth import router as auth_router


app = FastAPI(
    title="Recruitment Scam Investigation Platform",
    description="Backend API for recruitment scam investigation and campaign intelligence.",
    version="0.1.0"
)


app.include_router(cases_router)
app.include_router(evidence_router)
app.include_router(campaigns_router)
app.include_router(entities_router)
app.include_router(verdicts_router)
app.include_router(reports_router)
app.include_router(auth_router)


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