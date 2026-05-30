from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Nexacrypt Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InterviewRow(BaseModel):
    Interview: str
    Date: str
    Interviewé: str
    Locuteur: str
    Texte: str

class AnalysisRequest(BaseModel):
    data: List[InterviewRow]

# Configuration
COMPONENTS = ["soulcrypt", "soulbleed", "serveurs", "sauvegardes", "monitoring", "dex", "dat", "raid", "openssl"]

RISK_CATEGORIES = {
    "Knowledge Concentration": ["seule", "seul", "dans ma tête", "personne d'autre", "irremplaçable", "spof"],
    "Documentation Gap": ["pas documenté", "incomplet", "obsolète", "readme", "wiki"],
    "Backup Risk": ["sauvegarde", "restauration", "jamais testé"],
    "Security Risk": ["vulnérabilité", "faille", "heartbleed"],
    "Governance Risk": ["pas de budget", "pas de plan"]
}

def analyze_row(row: dict):
    text = row.get("Texte", "").lower()
    components = [c for c in COMPONENTS if c in text]
    risks = [name for name, patterns in RISK_CATEGORIES.items() if any(p in text for p in patterns)]
    
    return {
        **row,
        "components": components,
        "risks": risks,
        "severity": "HIGH" if risks else "MEDIUM"
    }

@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    results = [analyze_row(row.dict()) for row in request.data]
    return {
        "status": "success",
        "processed": len(results),
        "results": results
    }

@app.get("/")
def read_root():
    return {"message": "Nexacrypt Analyzer API is running !"}
