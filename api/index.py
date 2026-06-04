# api/index.py
import sys
import os

# Ajoute le dossier parent au PYTHONPATH pour que Vercel trouve nexacrypt_analyzer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import de l'application FastAPI depuis nexacrypt_analyzer
from nexacrypt_analyzer.main import app as fastapi_app

# Fonction handler requise par Vercel
def handler(request):
    from vercel_python import VercelRequest
    return fastapi_app(VercelRequest(request))
