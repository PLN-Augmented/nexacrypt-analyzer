# analyzer.py
from typing import List, Dict
import os

class NexacryptAnalyzer:
    
    def __init__(self):
        self.rule_based = True        # On peut désactiver facilement
        self.llm_enabled = False      # On activera plus tard

    def rule_based_analysis(self, row: Dict) -> Dict:
        text = row.get("Texte", "").lower()
        
        COMPONENTS = ["soulcrypt", "soulbleed", "serveurs", "sauvegardes", "monitoring", 
                     "dex", "dat", "raid", "openssl"]
        
        RISK_CATEGORIES = {
            "Knowledge Concentration": ["seule", "seul", "dans ma tête", "personne d'autre", "irremplaçable", "spof"],
            "Documentation Gap": ["pas documenté", "incomplet", "obsolète", "readme", "wiki"],
            "Backup Risk": ["sauvegarde", "restauration", "jamais testé"],
            "Security Risk": ["vulnérabilité", "faille", "heartbleed"],
            "Governance Risk": ["pas de budget", "pas de plan"]
        }

        components = [c for c in COMPONENTS if c in text]
        risks = [name for name, patterns in RISK_CATEGORIES.items() 
                if any(p in text for p in patterns)]

        return {
            "components": components,
            "risks_rule": risks,
            "severity_rule": "HIGH" if risks else "MEDIUM"
        }

    def analyze_row(self, row: Dict) -> Dict:
        """Version Hybride actuelle"""
        rule_result = self.rule_based_analysis(row)
        
        return {
            **row,
            **rule_result,
            "analysis_type": "hybrid_rule_based",
            "note": "Analyse hybride (règles + futur LLM)"
        }

    def analyze_batch(self, data: List[Dict]) -> List[Dict]:
        return [self.analyze_row(row) for row in data]
