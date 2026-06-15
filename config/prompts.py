# config/prompts.py
# Définis RISK_PROMPT_TEMPLATE au niveau racine (pas dans une fonction/classe)
RISK_PROMPT_TEMPLATE = """
Tu es un expert en analyse de risques techniques.
Analyse le texte suivant et identifie UNIQUEMENT les catégories de risques parmi : {risk_categories}.
Réponds **UNIQUEMENT** en JSON valide, au format :
{{
  "risks": ["Categorie1", "Categorie2"],
  "confidence": "high|medium|low",
  "explanation": "Brève justification (1 phrase max)"
}}

Exemple de réponse attendue :
{{
  "risks": ["Knowledge Concentration", "Documentation Gap"],
  "confidence": "high",
  "explanation": "Le texte mentionne une dépendance unique à Alice et une documentation obsolète."
}}

Texte à analyser :
{text}
"""
