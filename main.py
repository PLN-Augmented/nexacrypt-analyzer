# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from analyzer import NexacryptAnalyzer
import traceback

app = FastAPI(title="Nexacrypt Analyzer")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation
try:
    analyzer = NexacryptAnalyzer()
except Exception as e:
    # Si l'initialisation échoue (ex: clé API manquante), on crée un analyzer minimal
    print(f"⚠️ Erreur à l'initialisation : {e}")
    analyzer = None

@app.post("/analyze")
async def analyze(request: Request):
    try:
        if analyzer is None:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Analyseur non initialisé (clé API manquante ?)"}
            )

        data = await request.json()
        results = await analyzer.analyze_batch([row for row in data.get("data", [])])
        return JSONResponse(content={
            "status": "success",
            "processed": len(results),
            "results": results,
            "analysis_version": "hybrid_v1"
        })
    except Exception as e:
        # Retourne TOUJOURS du JSON, même en cas d'erreur
        print(f"⚠️ Erreur dans /analyze : {e}")
        traceback.print_exc()  # Affiche la stack trace dans les logs Vercel
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/")
async def read_root():
    return JSONResponse(content={"message": "Nexacrypt Analyzer API is running!"})

# Pour Vercel
def handler(request):
    from vercel_python import VercelRequest
    return app(VercelRequest(request))from fastapi import FastAPI
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
