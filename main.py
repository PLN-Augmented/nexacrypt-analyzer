from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Activer CORS pour Make.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les origines (à restreindre en production)
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les headers
)

# Modèles de données
class InterviewRow(BaseModel):
    Interview: str
    Date: str
    Interviewé: str
    Locuteur: str
    Texte: str

class AnalysisRequest(BaseModel):
    data: List[InterviewRow]

# Configuration des composants et risques
COMPONENTS = ["nexacrypt", "soulcrypt", "serveurs", "sauvegardes", "monitoring", "dex", "dat", "raid", "openssl"]
RISK_CATEGORIES = {
    "Knowledge Concentration": ["seule", "seul", "dans ma tête", "personne d'autre", "irremplaçable", "spof"],
    "Documentation Gap": ["pas documenté", "incomplet", "obsolète", "readme", "wiki"],
    "Backup Risk": ["sauvegarde", "restauration", "jamais testé"],
    "Security Risk": ["vulnérabilité", "faille", "heartbleed"],
    "Governance Risk": ["pas de budget", "pas de plan"]
}

def analyze_row(row: Dict) -> Dict:
    text = row["Texte"].lower() if row["Texte"] else ""
    components = [c for c in COMPONENTS if c in text]
    risks = [name for name, patterns in RISK_CATEGORIES.items() if any(p in text for p in patterns)]
    bus_factor = 1 if any(p in text for p in ["seule", "seul", "dans ma tête"]) else 2
    criticite = 5 if any(p in text for p in ["critique", "20% du ca", "6h de downtime"]) else 3
    impact = 5 if any(p in text for p in ["20% du ca", "perte de client"]) else 3
    return {
        **row,
        "components": components,
        "risks": risks,
        "bus_factor": bus_factor,
        "criticite": criticite,
        "impact": impact,
        "score_risque": bus_factor * criticite * impact,
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
    return {"message": "NexaCrypt Analyzer API - Ready!"}