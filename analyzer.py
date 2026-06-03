from typing import List, Dict
import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import asyncio

from config.categories import COMPONENTS, RISK_CATEGORIES
from config.prompts import RISK_PROMPT


class NexacryptAnalyzer:
    def __init__(self):
        load_dotenv()

        self.rule_based = True
        self.llm_enabled = True

        # Utilisation des constantes importées
        self.COMPONENTS = COMPONENTS
        self.RISK_CATEGORIES = RISK_CATEGORIES

        # Initialisation LLM
        if self.llm_enabled:
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise ValueError("❌ Clé API Mistral non trouvée dans .env")

            self.llm = ChatMistralAI(api_key=api_key, model="mistral-tiny")
            self._setup_prompts()

    # -----------------------------
    # RULE-BASED ANALYSIS
    # -----------------------------
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

    # -----------------------------
    # PROMPTS LLM
    # -----------------------------
    def _setup_prompts(self):
        self.risk_prompt = ChatPromptTemplate.from_template(RISK_PROMPT)
        self.risk_chain = self.risk_prompt | self.llm | StrOutputParser()

    # -----------------------------
    # LLM ANALYSIS
    # -----------------------------
    async def llm_analysis(self, text: str, risk_categories: List[str]) -> List[str]:
        if not self.llm_enabled:
            return []

        try:
            result = await self.risk_chain.ainvoke({
                "risk_categories": ", ".join(risk_categories),
                "text": text
            })

            # Normalisation
            if isinstance(result, dict):
                result_text = result.get("text") or result.get("output") or ""
            else:
                result_text = str(result)

            result_text = result_text.strip()

            if result_text.lower() == "aucun":
                return []

            risks = [r.strip() for r in result_text.split(",")]

            normalized_categories = {
                c.lower().replace(" ", "").replace("-", "")
                for c in risk_categories
            }

            detected = []
            for r in risks:
                key = r.lower().replace(" ", "").replace("-", "")
                if key in normalized_categories:
                    detected.append(r)

            return detected

        except Exception as e:
            print(f"⚠️ Erreur LLM : {e}")
            return []

    # -----------------------------
    # HYBRID ANALYSIS
    # -----------------------------
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

    # -----------------------------
    # BATCH ANALYSIS
    # -----------------------------
    async def analyze_batch(self, data: List[Dict]) -> List[Dict]:
        return await asyncio.gather(*(self.analyze_row(row) for row in data))
