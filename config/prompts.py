# config/prompts.py
# Définis RISK_PROMPT_TEMPLATE au niveau racine (pas dans une fonction/classe)
RISK_PROMPT_TEMPLATE = """
Tu es un expert en analyse de risques techniques.
Analyse le texte suivant et identifie UNIQUEMENT les catégories de risques parmi : {risk_categories}.
Réponds avec une liste de catégories séparées par des virgules, ou 'Aucun' si aucun risque.
Texte : {text}
"""
