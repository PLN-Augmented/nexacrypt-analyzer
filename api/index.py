# api/index.py
import sys
import os

# Ajoute le dossier racine au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from nexacrypt_analyzer.main import app as fastapi_app

def handler(request):
    from vercel_python import VercelRequest
    return fastapi_app(VercelRequest(request))

app = fastapi_app  # Pour Vercel
