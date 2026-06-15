# config/prompts.py
# Définis RISK_PROMPT_TEMPLATE au niveau racine (pas dans une fonction/classe)
RISK_PROMPT_TEMPLATE = """
Tu es un **expert en analyse de risques techniques et humains**. Ta tâche est **UNIQUEMENT** de :
1. Lire le texte ci-dessous.
2. Identifier **UNIQUEMENT** les catégories de risques parmi cette liste : {risk_categories}.
   Voici des **exemples concrets** pour chaque catégorie :
   - **Knowledge Concentration** : "seule", "seul", "personne d'autre", "irremplaçable", "toujours moi qu'on appelle", "je suis la seule à connaître".
   - **Documentation Gap** : "pas documenté", "incomplet", "obsolète", "README de 2021", "notes personnelles", "fiche réflexe jamais testée".
   - **Backup Risk** : "sauvegarde", "rotation des clés", "mise en production reportée", "backup échoué", "3 semaines d'analyse sans succès".
   - **Security Risk** : "vulnérabilité", "faille", "incident de chiffrement", "conséquences importantes", "sécurité".
   - **Governance Risk** : "astreinte permanente", "téléphone allumé tout le temps", "officieusement", "pas de procédure", "pas de plan".
   - **Connaissances Tacites** : "connaissances implicites", "mémoire non formalisée", "souvenir d'un incident", "choix techniques non documentés", "je me souviens d'un incident similaire".
   - **Dépendance Humaine** : "dépend de moi", "c'est toujours moi qu'on appelle", "personne ne saurait", "on m'appelle".

3. Retourner **UNIQUEMENT** un JSON valide avec **EXACTEMENT** cette structure :
   {{
     "risks": ["Categorie1", "Categorie2"],  // Liste des risques détectés (ou liste vide si aucun)
     "confidence": "high",                  // UNIQUEMENT "high", "medium" ou "low"
     "explanation": "Explication en une phrase en français"  // Justification claire
   }}

---
**RÈGLES ABSOLUES** (à respecter **impérativement**) :
✅ Le JSON **doit** commencer par `{{` et se terminer par `}}`.
✅ **Ne jamais** ajouter de texte avant, après ou autour du JSON (pas de "Voici les risques :", pas de commentaires, etc.).
✅ **Ne jamais** utiliser de guillemets simples (`'`), toujours des guillemets doubles (`"`).
✅ **Ne jamais** omettre les deux-points (`:`) ou les virgules (`,`) dans le JSON.
✅ Si aucun risque n'est détecté, retourner **obligatoirement** :
   {{"risks": [], "confidence": "high", "explanation": ""}}

---
**Exemples de réponses VALIDES** :
- {{"risks": ["Knowledge Concentration", "Documentation Gap"], "confidence": "high", "explanation": "Alice est la seule à connaître NexaCrypt Engine et la documentation est obsolète."}}
- {{"risks": ["Governance Risk"], "confidence": "high", "explanation": "Alice est en astreinte permanente (téléphone allumé tout le temps)."}}
- {{"risks": [], "confidence": "high", "explanation": ""}}

**Exemples de réponses INVALIDES** (à éviter **absolument**) :
- "Je détecte les risques suivants : Knowledge Concentration" ❌
- {{'risks': ['Knowledge Concentration']}} ❌ (guillemets simples)
- {{"risks": "Knowledge Concentration"}} ❌ (doit être une liste)
- Aucun risque détecté. ❌

---
**Texte à analyser** :
{text}
"""
