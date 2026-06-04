# api/index.py
import sys
import os

# Ajoute le dossier racine au PYTHONPATH
# On remonte de deux niveaux depuis api/index.py pour atteindre la racine
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Maintenant, on peut importer nexacrypt_analyzer
from nexacrypt_analyzer.main import app as fastapi_app

# Fonction handler requise par Vercel
def handler(request):
    from vercel_python import VercelRequest
    return fastapi_app(VercelRequest(request))
