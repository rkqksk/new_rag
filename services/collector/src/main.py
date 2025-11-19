from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Data Collector Service", version="1.0.0")

class WebCollectRequest(BaseModel):
    url: str
    selectors: dict = {}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "collector"}

@app.post("/collect/web")
def collect_web(request: WebCollectRequest):
    # TODO: Implement web scraping
    return {
        "url": request.url,
        "status": "pending",
        "message": "Collector service scaffold - implementation pending"
    }

@app.get("/jobs")
def list_jobs():
    return {"jobs": [], "total": 0}
