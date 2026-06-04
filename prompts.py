# config/prompts.py
RISK_PROMPT = """
Tu es un expert en analyse de risques techniques.
Analyse le texte suivant et identifie UNIQUEMENT les catégories de risques parmi : {risk_categories}.
Réponds avec une liste de catégories séparées par des virgules, ou 'Aucun' si aucun risque.
Texte : {text}
"""
