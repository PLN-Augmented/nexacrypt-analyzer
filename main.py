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
        self.risk_chain = self.risk_prompt | self.llm | StrOutputParser()

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
    # --- Analyse LLM ---
    async def llm_analysis(self, text: str, risk_categories: List[str]) -> List[str]:
        logger.info(f"🔍 Texte à analyser par LLM: {text[:100]}...")
        if not self.llm_enabled:
            logger.warning("⚠️ LLM désactivé, analyse annulée.")
            return []

        try:
            result = await self.risk_chain.ainvoke({
                "risk_categories": ", ".join(risk_categories),
                "text": text
            })
            logger.info(f"🤖 Réponse brute du LLM: {result}")

            # Parsing robuste
            if isinstance(result, dict):
                result_text = (
                    result.get("output", "") or
                    result.get("text", "") or
                    result.get("content", "") or
                    str(result)
                )
            else:
                result_text = str(result)

            result_text = result_text.strip().lower()
            logger.info(f"📝 Texte extrait: {result_text}")

            if result_text in ["aucun", "none", "rien", ""]:
                logger.info("✅ Aucun risque détecté par le LLM.")
                return []

            # Parsing amélioré : cherche chaque catégorie dans la réponse
            detected_risks = []
            for category in risk_categories:
                # Normalise la catégorie pour la comparaison (ex: "Knowledge Concentration" → "knowledgeconcentration")
                normalized_category = self.normalize_text(category)
                # Cherche la catégorie normalisée dans le texte normalisé
                if normalized_category in result_text:
                    detected_risks.append(category)

            if not detected_risks:
                detected_risks = ["Inconnu"]
                logger.warning("⚠️ AUCUN RISQUE DÉTECTÉ PAR LLM !")

            logger.info(f"🎯 Risques détectés par LLM: {detected_risks}")
            return detected_risks

        except Exception as e:
            logger.error(f"❌ Erreur dans llm_analysis: {e}")
            import traceback
            traceback.print_exc()
            return ["Erreur LLM"]
            
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
        if use_llm:
            llm_risks = await self.llm_analysis(text, list(self.RISK_CATEGORIES.keys()))
            logger.info(f"🎯 Risques (LLM): {llm_risks}")

        all_risks = list(set(rule_risks + llm_risks))  # Combinaison hybride
        method = "hybrid" if use_llm else "rule-based"

        if not all_risks:
            all_risks = ["Inconnu"]
            logger.warning("⚠️ Aucun risque détecté, valeur par défaut appliquée.")

        # Calcul de la sévérité (basée sur tous les risques)
        severity = "HIGH" if "Security Risk" in all_risks else "MEDIUM" if "Backup Risk" in all_risks else "LOW"

        return {
            **row,
            "components": rule_result["components"],
            "risks": all_risks,  # ← Tous les risques combinés
            "risks_rule": rule_risks,  # ←  Risques détectés par les règles
            "risks_llm": llm_risks,  # ←  Risques détectés par le LLM
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
