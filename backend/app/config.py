import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

class Config:
    # Ollama
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")
    
    # Base de données
    DATA_PATH = DATA_DIR
    KNOWLEDGE_BASE_PATH = DATA_DIR / "knowledge_base"
    LOGS_PATH = DATA_DIR / "logs"
    
    # Sécurité
    SENSITIVE_WORDS = [
        "supprime", "supprime tous", "réinitialise tous", "droits admin",
        "administrateur", "ignore", "contourne", "phishing", "virus",
        "ransomware", "hack", "pirate"
    ]
    
    # Logging
    LOG_LEVEL = "INFO"
    ENABLE_TRACING = True

config = Config()

# Créer les dossiers nécessaires
os.makedirs(config.KNOWLEDGE_BASE_PATH, exist_ok=True)
os.makedirs(config.LOGS_PATH, exist_ok=True)