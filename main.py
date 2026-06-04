# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from config.categories import COMPONENTS, RISK_CATEGORIES
from config.prompts import RISK_PROMPT_TEMPLATE
import os
import traceback
from typing import List, Dict
from langchain_mistralai import ChatMistralAI  # ✅ Note le underscore (_) entre langchain et mistralai
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Initialisation de FastAPI ---
app = FastAPI(title="Nexacrypt Analyzer")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Classe NexacryptAnalyzer (anciennement dans analyzer.py) ---
class NexacryptAnalyzer:
    def __init__(self):
        self.rule_based = True
        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
        self.llm_enabled = MISTRAL_API_KEY is not None and MISTRAL_API_KEY != ""

        self.COMPONENTS = COMPONENTS
        self.RISK_CATEGORIES = RISK_CATEGORIES

        if self.llm_enabled:
            try:
                self.llm = ChatMistralAI(api_key=MISTRAL_API_KEY, model="mistral-tiny")
                self._setup_prompts()
                print("✅ LLM initialisé avec succès.")
            except Exception as e:
                print(f"❌ Erreur à l'initialisation du LLM : {e}")
                self.llm_enabled = False
        else:
            print("⚠️ LLM désactivé (clé API manquante).")

    def _setup_prompts(self):
        self.risk_prompt = ChatPromptTemplate.from_template(RISK_PROMPT_TEMPLATE)
        self.risk_chain = self.risk_prompt | self.llm | StrOutputParser()

    def rule_based_analysis(self, row: Dict) -> Dict:
        text = row.get("Texte", "").lower()
        components = [c for c in self.COMPONENTS if c in text]
        risks = [
            name for name, patterns in self.RISK_CATEGORIES.items()
            if any(p in text for p in patterns)
        ]
        return {
            "components": components,
            "risks_rule": risks,
            "severity_rule": "HIGH" if risks else "MEDIUM"
        }

    async def llm_analysis(self, text: str, risk_categories: List[str]) -> List[str]:
        if not self.llm_enabled:
            return []

        try:
            result = await self.risk_chain.ainvoke({
                "risk_categories": ", ".join(risk_categories),
                "text": text
            })

            if isinstance(result, dict):
                result_text = (
                    result.get("output", "") or
                    result.get("text", "") or
                    result.get("content", "") or
                    str(result)
                )
            else:
                result_text = str(result)

            result_text = result_text.strip()

            if result_text.lower() in ["aucun", "none", "rien", ""]:
                return []

            risks = [r.strip() for r in result_text.split(",") if r.strip()]

            normalized_categories = {
                c.lower().replace(" ", "").replace("-", ""): c
                for c in risk_categories
            }

            detected = []
            for r in risks:
                key = r.lower().replace(" ", "").replace("-", "")
                if key in normalized_categories:
                    detected.append(normalized_categories[key])

            return detected

        except Exception as e:
            print(f"⚠️ Erreur dans llm_analysis : {e}")
            return []

    async def analyze_row(self, row: Dict) -> Dict:
        text = row.get("Texte", "")
        rule_result = self.rule_based_analysis(row)
        rule_risks = rule_result["risks_rule"]

        use_llm = self.llm_enabled and (not rule_risks or len(text.split()) > 20)

        if use_llm:
            llm_risks = await self.llm_analysis(text, list(self.RISK_CATEGORIES.keys()))
            all_risks = list(set(rule_risks + llm_risks))
            method = "hybrid"
        else:
            all_risks = rule_risks
            method = "rule-based"

        return {
            **row,
            "components": rule_result["components"],
            "risks": all_risks,
            "severity": "HIGH" if all_risks else "MEDIUM",
            "analysis_type": method,
            "note": "Analyse hybride (règles + LLM)" if use_llm else "Analyse par règles"
        }

    async def analyze_batch(self, data: List[Dict]) -> List[Dict]:
        return [await self.analyze_row(row) for row in data]

# --- Initialisation de l'analyseur ---
try:
    analyzer = NexacryptAnalyzer()
    print("✅ Analyseur initialisé avec succès.")
except Exception as e:
    print(f"❌ Erreur à l'initialisation : {e}")
    traceback.print_exc()
    analyzer = None

# --- Routes FastAPI ---
@app.post("/analyze")
async def analyze(request: Request):
    try:
        if analyzer is None:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": "Analyseur non initialisé"}
            )

        data = await request.json()
        results = await analyzer.analyze_batch([row for row in data.get("data", [])])
        return JSONResponse(content={
            "status": "success",
            "processed": len(results),
            "results": results,
            "analysis_version": "hybrid_v1"
        })
    except Exception as e:
        print(f"❌ Erreur dans /analyze : {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/")
async def read_root():
    return JSONResponse(content={"message": "Nexacrypt Analyzer API is running!"})

# --- Fonction handler pour Vercel ---
def handler(request):
    from vercel_python import VercelRequest
    return app(VercelRequest(request))

# Pour Vercel (variable `app` requise)
app = FastAPI(title="Nexacrypt Analyzer")  # Déjà défini plus haut, mais on le réassigne ici pour Vercel
