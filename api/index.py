# api/index.py
import sys
import os

# Ajoute le dossier racine au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import de l'application FastAPI
from nexacrypt_analyzer.main import app as fastapi_app

# Fonction handler requise par Vercel
def handler(request):
    from vercel_python import VercelRequest
    return fastapi_app(VercelRequest(request))

# --- AJOUT EXPLICITE POUR VERCEL ---
# Vercel cherche parfois une variable `app` ou `application` en plus de `handler`
app = fastapi_app  # Ajoute cette ligne pour que Vercel trouve aussi `app`
