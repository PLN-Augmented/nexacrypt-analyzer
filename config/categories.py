# config/categories.py
COMPONENTS = ["nexacrypt engine", "nexacrypt core v2", "nexacrypt core v3", "nexatrace", "serveurs", "sauvegardes", "monitoring", "moteur de chiffrement", "clés de chiffrement", "certificats", "dex", "dat", "raid", "openssl"]

RISK_CATEGORIES = {
    "Knowledge Concentration": [
        "seule", "seul", "dans ma tête", "personne d'autre", "irremplaçable", "spof",
        "personne", "connaît", "comprendre", "complexe", "peur de casser", "annuler la mise en prod",
        "touché", "touchée", "évolutions", "toutes les évolutions", "5 ans", "conçu il y a"
    ],
    "Documentation Gap": [
        "pas documenté", "incomplet", "obsolète", "readme", "wiki", "repo partagé",
        "stocké sur son poste local", "pas dans le repo", "scripts de récupération", "poste local"
    ],
    "Backup Risk": [
        "sauvegarde", "restauration", "jamais testé", "backup", "backups", "corrompues",
        "45 minutes", "démarrer", "SLA", "High", "serveurs dédiés", "2 en prod", "1 en backup",
        "matériel vieux", "disques", "fatigue", "si les 2 serveurs prod tombent"
    ],
    "Security Risk": [
        "vulnérabilité", "faille", "heartbleed", "chiffrement", "sécurité", "compromis",
        "sensibles"
    ],
    "Governance Risk": [
        "pas de budget", "pas de plan", "astreintes", "part en retraite", "seul à connaître",
        "Dave", "retraite", "3 mois", "après son départ"
    ],
    "Connaissances Tacites": [
        "connaissances implicites", "mémoire non formalisée", "souvenir d'un incident", "choix techniques non documentés"
    ],
    "Dépendance Humaine": [
        "toujours moi qu'on appelle", "personne ne saurait", "dépend de moi"   
    ] 
}
