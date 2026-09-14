from fastapi import FastAPI

from app.api.cases import router as cases_router


app = FastAPI(
    title="Recruitment Scam Investigation Platform",
    description="Backend API for recruitment scam investigation and campaign intelligence.",
    version="0.1.0"
)


app.include_router(cases_router)


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