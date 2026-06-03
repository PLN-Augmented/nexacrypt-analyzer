from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from analyzer import NexacryptAnalyzer

app = FastAPI(title="Nexacrypt Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation
analyzer = NexacryptAnalyzer()

class InterviewRow(BaseModel):
    Interview: str
    Date: str
    Interviewé: str
    Locuteur: str
    Texte: str

class AnalysisRequest(BaseModel):
    data: List[InterviewRow]

@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    # Utilise await car analyze_batch est asynchrone
    results = await analyzer.analyze_batch([row.dict() for row in request.data])

    return {
        "status": "success",
        "processed": len(results),
        "results": results,
        "analysis_version": "hybrid_v1"
    }

@app.get("/")
def read_root():
    return {"message": "Nexacrypt Analyzer API is running !"}
