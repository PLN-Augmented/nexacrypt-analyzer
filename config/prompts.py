# config/prompts.py
# Définis RISK_PROMPT_TEMPLATE au niveau racine (pas dans une fonction/classe)
RISK_PROMPT_TEMPLATE = """
Tu es un expert en analyse de risques techniques et humains.
Analyse le texte suivant pour identifier :
1. Les **catégories de risques** parmi : {risk_categories}.
2. Les **risques implicites** (ex : connaissances tacites, mémoire non formalisée, dépendances cachées).

Réponds **UNIQUEMENT** en JSON valide, au format :
{{
  "risks": ["Categorie1", "Categorie2", "RisqueImplicite1"],
  "confidence": "high|medium|low",
  "explanation": "Brève justification (1 phrase max)"
}}

Exemple de réponse attendue :
{{
  "risks": ["Knowledge Concentration", "Documentation Gap", "Connaissances Tacites"],
  "confidence": "high",
  "explanation": "Le texte mentionne une dépendance unique à Alice, une documentation obsolète, et des connaissances non formalisées."
}}

Texte à analyser :
{text}
"""
