# config/prompts.py
# Définis RISK_PROMPT_TEMPLATE au niveau racine (pas dans une fonction/classe)
RISK_PROMPT_TEMPLATE = """
Tu es un **expert en analyse de risques techniques**. Ta tâche est **UNIQUEMENT** d'analyser le texte suivant et de retourner **UNIQUEMENT** un JSON valide avec les champs suivants :
- `risks` : une **liste** de catégories de risques parmi {risk_categories} (ou une liste vide si aucun risque).
- `confidence` : **UNIQUEMENT** "high", "medium" ou "low".
- `explanation` : **UNIQUEMENT** une phrase courte en français expliquant la détection (ou une chaîne vide si aucun risque).

**Règles absolues** :
✅ Réponds **UNIQUEMENT** en JSON valide, **sans aucun autre texte** avant, après ou autour.
✅ Le JSON doit **obligatoirement** commencer par `{{` et se terminer par `}}`.
✅ Ne **jamais** inclure de texte comme "Je pense que...", "Voici les risques :", etc.
✅ Si aucun risque n'est détecté, retourne `{{"risks": [], "confidence": "high", "explanation": ""}}`.

**Exemples de réponses VALIDES** :
- `{{"risks": ["Knowledge Concentration", "Documentation Gap"], "confidence": "high", "explanation": "Alice est la seule à connaître NexaCrypt Engine et la documentation est obsolète."}}`
- `{{"risks": [], "confidence": "high", "explanation": ""}}`

**Exemples de réponses INVALIDES** (à éviter absolument) :
- "Je détecte les risques suivants : Knowledge Concentration, Documentation Gap" ❌
- "{{risks: ['Knowledge Concentration']}}" ❌ (clés non entre guillemets)
- "{{'risks': ['Knowledge Concentration']}}" ❌ (guillemets simples)
- "Aucun risque détecté." ❌

**Texte à analyser** :
{text}
"""
