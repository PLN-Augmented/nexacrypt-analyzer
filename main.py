# main.py
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from config.categories import COMPONENTS, RISK_CATEGORIES
from config.prompts import RISK_PROMPT_TEMPLATE
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import logging
import unicodedata
from typing import List, Dict
import json
from typing import Dict, List, Optional

# --- Configuration des logs ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Initialisation de FastAPI ---
app = FastAPI(title="Nexacrypt Analyzer")

# Middleware CORS (obligatoire pour Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Définition des poids pour chaque risque
RISK_WEIGHTS = {
    "Knowledge Concentration": 3,
    "Documentation Gap": 2,
    "Backup Risk": 2,
    "Security Risk": 3,
    "Governance Risk": 2,
}

# --- Classe NexacryptAnalyzer (avec normalize_text) ---
class NexacryptAnalyzer:
    def __init__(self):
        logger.info("🔍 Initialisation de NexacryptAnalyzer...")
        self.rule_based = True
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
        self.llm_enabled = MISTRAL_API_KEY is not None and MISTRAL_API_KEY != ""

        self.COMPONENTS = COMPONENTS
        self.RISK_CATEGORIES = RISK_CATEGORIES

        if self.llm_enabled:
            try:
                self.llm = ChatMistralAI(api_key=MISTRAL_API_KEY, model="mistral-tiny")
                self._setup_prompts()
                logger.info("✅ LLM initialisé avec succès.")
            except Exception as e:
                logger.error(f"❌ Erreur LLM: {e}")
                self.llm_enabled = False
        else:
            logger.warning("⚠️ LLM désactivé (clé API manquante).")

    # --- Méthode normalize_text (ton code original) ---
    def normalize_text(self, text: str) -> str:
        """Nettoie et normalise un texte pour une comparaison robuste."""
        if not text:
            return ""

        # Nettoyage JSON
        text = text.encode('utf-8', 'ignore').decode('unicode_escape')

        # Suppression des caractères invisibles
        invisibles = [
            "\u2028", "\u2029", "\u2026", "\u00A0", "\u200B", "\u200C", "\u200D",
            "\uFEFF", "\uFFFD"
        ]
        for inv in invisibles:
            text = text.replace(inv, " ")

        # Apostrophes typographiques
        text = text.replace("’", "'").replace("‘", "'")

        # Guillemets typographiques
        text = text.replace("“", '"').replace("”", '"')

        # Normalisation Unicode
        text = unicodedata.normalize("NFKD", text)

        # Suppression des accents
        text = "".join(c for c in text if not unicodedata.combining(c))

        return text.lower().strip()

    # --- Setup des prompts LLM ---
    def _setup_prompts(self):
        self.risk_prompt = ChatPromptTemplate.from_template(RISK_PROMPT_TEMPLATE)
        self.risk_chain = self.risk_prompt | self.llm  # On enlève StrOutputParser pour récupérer le JSON brut

    # --- Analyse basée sur des règles ---
    def rule_based_analysis(self, row: Dict) -> Dict:
        raw_text = row.get("Texte", "")
        text = self.normalize_text(raw_text)

        components = [c for c in self.COMPONENTS if c in text]

        # Applique normalize_text à chaque pattern pour une comparaison cohérente
        risks = [
            name for name, patterns in self.RISK_CATEGORIES.items()
            if any(self.normalize_text(p) in text for p in patterns)
        ]

        # Calcul de la sévérité (toujours une valeur)
        severity = "HIGH" if "Security Risk" in risks else "MEDIUM" if "Backup Risk" in risks else "LOW" if risks else "LOW"

        return {
            "components": components,
            "risks_rule": risks,
            "severity_rule": severity
        }
    # --- Analyse LLM ---async
    def llm_analysis(self, text: str, risk_categories: List[str]) -> Dict:
        """Analyse le texte avec le LLM et retourne un dictionnaire structuré."""
        logger.info(f"🔍 Texte à analyser par LLM: {text[:100]}...")
        if not self.llm_enabled:
            logger.warning("⚠️ LLM désactivé, analyse annulée.")
            return {"risks": [], "confidence": "low", "explanation": "LLM désactivé"}

        try:
            result = await self.risk_chain.ainvoke({
                "risk_categories": ", ".join(risk_categories),
                "text": text
            })
            logger.info(f"🤖 Réponse brute du LLM: {result}")

            # Récupérer le contenu de la réponse
            if hasattr(result, 'content'):
                result_text = result.content
            elif isinstance(result, dict):
                result_text = result.get("output", "") or result.get("text", "") or result.get("content", "") or str(result)
            else:
                result_text = str(result)

            logger.info(f"📝 Texte extrait: {result_text}")

            # Essayer de parser le JSON
            try:
                parsed_result = json.loads(result_text)
                # Valider que le JSON contient bien les champs attendus
                if "risks" in parsed_result:
                    return {
                        "risks": parsed_result["risks"],
                        "confidence": parsed_result.get("confidence", "medium"),
                        "explanation": parsed_result.get("explanation", "")
                    }
                else:
                    logger.warning("⚠️ Réponse LLM non conforme (champ 'risks' manquant).")
                    return {"risks": [], "confidence": "low", "explanation": "Réponse LLM non conforme"}
            except json.JSONDecodeError:
                logger.warning("⚠️ Réponse LLM non valide (JSON invalide).")
                # Fallback : essayer de détecter les risques avec du pattern-matching (ancienne méthode)
                detected_risks = []
                normalized_text = self.normalize_text(result_text)
                for category in risk_categories:
                    normalized_category = self.normalize_text(category)
                    if normalized_category in normalized_text:
                        detected_risks.append(category)
                return {
                    "risks": detected_risks,
                    "confidence": "low",
                    "explanation": "Réponse LLM non valide, fallback en pattern-matching"
                }

        except Exception as e:
            logger.error(f"❌ Erreur dans llm_analysis: {e}")
            import traceback
            traceback.print_exc()
            return {"risks": [], "confidence": "low", "explanation": f"Erreur LLM: {str(e)}"}

    def calculate_severity(self, all_risks: List[str]) -> str:
        """Calcule la sévérité en fonction du score cumulatif des risques."""
        score = sum(RISK_WEIGHTS.get(risk, 1) for risk in all_risks)

        if score >= 6:
            return "CRITICAL"
        elif score >= 4:
            return "HIGH"
        elif score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    # --- Analyse hybride (règles + LLM) ---
    async def analyze_row(self, row: Dict) -> Dict:
        text = row.get("Texte", "")
        logger.info(f"📄 Analyse de la ligne: {row.get('Interview', 'N/A')}")

        rule_result = self.rule_based_analysis(row)
        rule_risks = rule_result["risks_rule"]
        logger.info(f"📌 Risques (règles): {rule_risks}")

        use_llm = self.llm_enabled and (not rule_risks or len(text.split()) > 20)
        logger.info(f"USE_LLM ? {use_llm}")

        llm_risks = []
        llm_confidence = "low"
        llm_explanation = ""
        if use_llm:
            llm_result = await self.llm_analysis(text, list(self.RISK_CATEGORIES.keys()))
            llm_risks = llm_result.get("risks", [])
            llm_confidence = llm_result.get("confidence", "low")
            llm_explanation = llm_result.get("explanation", "")
            logger.info(f"🎯 Risques (LLM): {llm_risks}")

        all_risks = list(set(rule_risks + llm_risks))  # Combinaison hybride
        method = "hybrid" if use_llm else "rule-based"

        if not all_risks:
            all_risks = ["Inconnu"]
            logger.warning("⚠️ Aucun risque détecté, valeur par défaut appliquée.")

        # Calcul de la sévérité avec le score cumulatif
        severity = self.calculate_severity(all_risks)

        return {
            **row,
            "components": rule_result["components"],
            "risks": all_risks,
            "risks_rule": rule_risks,
            "risks_llm": llm_risks,
            "llm_confidence": llm_confidence,  # Nouveau champ
            "llm_explanation": llm_explanation,  # Nouveau champ
            "severity": severity,
            "analysis_type": method,
            "note": f"Analyse {method}"
        }
    
    # --- Analyse par lots ---
    async def analyze_batch(self, data: List[Dict]) -> List[Dict]:
        results = []
        for row in data:
            try:
                result = await self.analyze_row(row)
                results.append(result)
            except Exception as e:
                logger.error(f"🔥 ERREUR analyze_row: {e}")
                results.append({
                    **row,
                    "error": str(e),
                    "components": [],
                    "risks": ["Erreur"],
                    "severity": "HIGH",
                    "analysis_type": "error",
                    "note": f"Erreur: {str(e)}"
                })
        return results

# --- Initialisation de l'analyseur ---
try:
    analyzer = NexacryptAnalyzer()
    logger.info("✅ Analyseur initialisé avec succès.")
except Exception as e:
    logger.error(f"❌ Erreur à l'initialisation: {e}")
    analyzer = None

# --- Routes FastAPI ---
@app.post("/analyze")
async def analyze(request: Request):
    start_time = time.time()  # ← Début du chronométrage

    try:
        data = await request.json()
        logger.info(f"📥 Données reçues: {len(data.get('data', []))} lignes")

        if analyzer is None:
            logger.error("❌ Analyseur non initialisé!")
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Analyseur non initialisé"}
            )

        results = await analyzer.analyze_batch(data.get("data", []))
        duration = time.time() - start_time  # ← Calcul de la durée

        logger.info(f"⏱️ Temps d'exécution: {duration:.2f}s pour {len(results)} lignes")

        return JSONResponse(content={
            "status": "success",
            "processed": len(results),
            "results": results,
            "analysis_version": "hybrid_v1",
            "performance": {  # ← Ajoute les métriques ici
                "duration_seconds": duration,
                "lines_processed": len(results),
                "avg_time_per_line": duration / len(results) if results else 0
            }
        })

    except Exception as e:
        logger.error(f"❌ Erreur dans /analyze: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
# --- Fonction handler pour Vercel ---
def handler(request):
    from vercel import VercelRequest
    return app(VercelRequest(request)) 
