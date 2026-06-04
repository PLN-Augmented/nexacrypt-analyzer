# api/index.py
from fastapi import FastAPI
from nexacrypt_analyzer.main import app as fastapi_app

# Vercel doit voir une variable "app" = handler ASGI
app = fastapi_app
