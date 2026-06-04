# config/categories.py

# Composants techniques
COMPONENTS = [
    "soulcrypt", "soulbleed", "serveurs", "sauvegardes", "monitoring",
    "dex", "dat", "raid", "openssl"
]

# Catégories de risques et leurs mots-clés
RISK_CATEGORIES = {
    "Knowledge Concentration": [
        "seul",
        "seule",
        "personne d'autre",
        "irremplacable",
        "spof"
    ],
    "Documentation Gap": [
        "pas documente",
        "incomplet",
        "obsolete",
        "readme",
        "wiki",
        "pas dans le repo",
        "pas partage"
    ],
    "Backup Risk": [
        "sauvegarde",
        "restauration",
        "jamais teste",
        "jamais ete teste",
        "jamais ete testee"
    ],
    "Security Risk": [
        "vulnerabilite",
        "faille",
        "heartbleed"
    ],
    "Governance Risk": [
        "pas de budget",
        "pas de plan"
    ]
}

