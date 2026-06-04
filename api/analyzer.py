from typing import List, Dict
import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import asyncio
import unicodedata

from .config.categories import COMPONENTS, RISK_CATEGORIES
from .config.prompts import RISK_PROMPT


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



    def normalize_text(self, text: str) -> str:
        # 1. Nettoyage des échappements JSON
        text = text.replace('\\"', '"').replace("\\'", "'").replace("\\", "")

         # 2. Suppression des caractères parasites (soulignés, séparateurs, unicode invisibles)
        text = text.replace("________________________________________", "")
        text = text.replace("\u2028", " ").replace("\u2029", " ").replace("\u2026", " ")
        text = text.replace("\u2018", "'").replace("\u2019", "'")

        # 3. Normalisation Unicode
        text = unicodedata.normalize("NFKD", text)

        # 4. Apostrophes typographiques
        text = text.replace("’", "'").replace("‘", "'")

        # 5. Suppression des accents
        text = "".join(c for c in text if not unicodedata.combining(c))

        # 6. Mise en minuscules
        return text.lower().strip()



    # -----------------------------
    # RULE-BASED ANALYSIS
    # -----------------------------
    def rule_based_analysis(self, row: Dict) -> Dict:
        raw_text = row.get("Texte", "")
        text = self.normalize_text(raw_text)

        components = [c for c in self.COMPONENTS if c in text]


        risks = [
            name for name, patterns in self.RISK_CATEGORIES.items()
            if any(self.normalize_text(p) in text for p in patterns)
        ]


        # Calcul de la sévérité en fonction des risques détectés
        severity = ""
        if risks:
            if "Security Risk" in risks:
                severity = "high"
            elif "Backup Risk" in risks:
                severity = "medium"
            else:
                severity = "low"

        return {
            "components": components,
            "risks_rule": risks,
            "severity_rule": severity
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
        """
        Analyse un texte avec Mistral pour détecter des catégories de risques.
        Args:
            text: Texte à analyser.
            risk_categories: Liste des catégories de risques valides.
        Returns:
            Liste des risques détectés (vide si erreur ou aucun risque).
        """
        if not self.llm_enabled:
            return []

        try:
            # 1. Appel au LLM avec le prompt configuré
            result = await self.risk_chain.ainvoke({
                "risk_categories": ", ".join(risk_categories),
                "text": text
            })

            # 2. Normalisation de la réponse du LLM
            #    - Si result est un dict (ex: {"output": "..."}), extrait la valeur.
            #    - Sinon, convertit en chaîne de caractères.
            if isinstance(result, dict):
                # Essaye plusieurs clés possibles (selon le format de réponse de Mistral)
                result_text = (
                    result.get("output", "") or
                    result.get("text", "") or
                    result.get("content", "") or
                    str(result)
                )
            else:
                result_text = str(result)

            # Nettoyage du texte (supprime les espaces et sauts de ligne)
            result_text = result_text.strip()

            # 3. Si le LLM répond "Aucun" ou une variante, retourne une liste vide
            if result_text.lower() in ["aucun", "none", "rien", ""]:
                return []

            # 4. Séparation des risques (ex: "Risque1, Risque2" → ["Risque1", "Risque2"])
            risks = [r.strip() for r in result_text.split(",") if r.strip()]

            # 5. Normalisation des catégories pour une comparaison insensible à la casse/espaces
            #    Ex: "Knowledge Concentration" → "knowledgeconcentration"
            normalized_categories = {
                c.lower().replace(" ", "").replace("-", ""): c  # Conserve la catégorie originale
                for c in risk_categories
            }

            # 6. Détection des risques valides
            detected = []
            for r in risks:
                # Normalise le risque détecté (ex: "Knowledge Concentration" → "knowledgeconcentration")
                key = r.lower().replace(" ", "").replace("-", "")
                # Si le risque normalisé correspond à une catégorie valide, ajoute-le à la liste
                if key in normalized_categories:
                    detected.append(normalized_categories[key])  # Utilise le nom original de la catégorie

            return detected

        except Exception as e:
            # Log l'erreur pour le débogage (visible dans les logs Vercel)
            print(f"⚠️ Erreur dans llm_analysis : {e}")
            # Retourne une liste vide pour éviter de casser l'API
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
    async def analyze_batch(self, data):
        results = []
        for row in data:
            try:
                result = await self.analyze_row(row)
                results.append(result)
            except Exception as e:
                print("🔥 ERREUR analyze_row :", e)
                import traceback
                traceback.print_exc()
                results.append({
                    "error": str(e),
                    "row": row
                })
        return results
