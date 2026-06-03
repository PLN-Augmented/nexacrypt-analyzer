# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from analyzer import NexacryptAnalyzer
import traceback
import os

# Initialisation de FastAPI
app = FastAPI(title="Nexacrypt Analyzer")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation de l'analyseur
try:
    analyzer = NexacryptAnalyzer()
    print("✅ Analyseur initialisé avec succès.")
except Exception as e:
    print(f"❌ Erreur à l'initialisation de l'analyseur : {e}")
    traceback.print_exc()
    analyzer = None

# Route pour l'analyse
@app.post("/analyze")
async def analyze(request: Request):
    try:
        if analyzer is None:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Analyseur non initialisé. Vérifie MISTRAL_API_KEY."
                }
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
        print(f"❌ Erreur dans /analyze : {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "type": type(e).__name__
            }
        )

# Route racine
@app.get("/")
async def read_root():
    return JSONResponse(content={"message": "Nexacrypt Analyzer API is running!"})

# --- Fonction requise par Vercel ---
# Cette fonction DOIT être au niveau racine du fichier (pas dans une classe ou une fonction)
def handler(request):
    from vercel_python import VercelRequest
    return app(VercelRequest(request))
