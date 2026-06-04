# config/categories.py

# Composants techniques
COMPONENTS = [
    "soulcrypt", "soulbleed", "serveurs", "sauvegardes", "monitoring",
    "dex", "dat", "raid", "openssl"
]

# Catégories de risques et leurs mots-clés
RISK_CATEGORIES = {
    "Knowledge Concentration": ["seule", "seul", "dans ma tête", "personne d'autre", "irremplaçable", "spof"],
    "Documentation Gap": ["pas documenté", "incomplet", "obsolète", "readme", "wiki"],
    "Backup Risk": ["sauvegarde", "restauration", "jamais testé"],
    "Security Risk": ["vulnérabilité", "faille", "heartbleed"],
    "Governance Risk": ["pas de budget", "pas de plan"]
}
