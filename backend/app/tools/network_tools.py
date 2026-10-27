import json
import random
from datetime import datetime

# Données simulées
INCIDENTS_ACTIFS = {
    "wifi": {
        "incident": "INC-2026-015",
        "description": "Panne partielle du WiFi au 3ème étage",
        "statut": "en_cours",
        "impact": "moyen"
    },
    "vpn": {
        "incident": "INC-2026-018",
        "description": "VPN lent pour les utilisateurs distants",
        "statut": "investigation",
        "impact": "eleve"
    }
}

SERVICES_STATUT = {
    "wifi": {"statut": "operationnel", "uptime": "99.8%", "derniere_panne": "2026-08-12"},
    "vpn": {"statut": "degrade", "uptime": "95.2%", "derniere_panne": "2026-08-13"},
    "imprimante": {"statut": "hors_ligne", "uptime": "0%", "derniere_panne": "2026-08-13"},
    "email": {"statut": "operationnel", "uptime": "99.9%", "derniere_panne": "2026-08-10"}
}

def verifier_etat_service(service: str) -> dict:
    """Vérifie l'état d'un service"""
    service = service.lower()
    if service in SERVICES_STATUT:
        return {
            "service": service,
            "statut": SERVICES_STATUT[service]["statut"],
            "uptime": SERVICES_STATUT[service]["uptime"],
            "derniere_panne": SERVICES_STATUT[service]["derniere_panne"],
            "timestamp": datetime.now().isoformat()
        }
    return {
        "service": service,
        "statut": "inconnu",
        "erreur": "Service non reconnu"
    }

def rechercher_incidents_actifs(service: str) -> dict:
    """Recherche des incidents en cours pour un service"""
    service = service.lower()
    if service in INCIDENTS_ACTIFS:
        incident = INCIDENTS_ACTIFS[service]
        return {
            "has_active_incident": True,
            "incident": incident,
            "timestamp": datetime.now().isoformat()
        }
    return {
        "has_active_incident": False,
        "message": f"Aucun incident actif pour {service}",
        "timestamp": datetime.now().isoformat()
    }

def verifier_droits(utilisateur: str, action: str) -> dict:
    """Vérifie si un utilisateur a les droits pour une action"""
    # Simulé - en vrai on irait chercher dans un AD/LDAP
    admin_users = ["martin.s", "admin"]
    
    return {
        "utilisateur": utilisateur,
        "action": action,
        "autorise": utilisateur in admin_users,
        "niveau_droits": "admin" if utilisateur in admin_users else "utilisateur",
        "timestamp": datetime.now().isoformat()
    }

def reinitialiser_compte(utilisateur: str, type: str = "mot_de_passe") -> dict:
    """Réinitialise un compte - action sensible"""
    return {
        "action": "reinitialisation",
        "utilisateur": utilisateur,
        "type": type,
        "statut": "validation_humaine_requise",
        "message": "Cette action nécessite une validation humaine",
        "validation_requise": True,
        "timestamp": datetime.now().isoformat()
    }