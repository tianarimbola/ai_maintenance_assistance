from typing import List, Tuple
from app.config import config
import os
import ollama
import re

class RAGEngine:
    def __init__(self):
        self.knowledge_base = {}
        self.model = config.OLLAMA_MODEL
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Charge les documents depuis le dossier knowledge_base"""
        kb_path = config.KNOWLEDGE_BASE_PATH
        
        os.makedirs(kb_path, exist_ok=True)
        
        # Documents par défaut
        default_docs = {
            "wifi.txt": """Titre: Procédure de dépannage WiFi (KB-NET-04)
Catégorie: Réseau
Description: Problème de connexion WiFi
Étapes:
1. Vérifier que le mode Avion est désactivé
2. Oublier le réseau et se reconnecter
3. Redémarrer le routeur
4. Contacter l'équipe infrastructure si le problème persiste""",
            
            "password.txt": """Titre: Réinitialisation mot de passe (KB-ACC-01)
Catégorie: Comptes
Description: Mot de passe oublié ou bloqué
Étapes:
1. Aller sur le portail de réinitialisation
2. Répondre aux questions de sécurité
3. Vérifier vos emails (pensez aux spams)
4. Contacter l'identity management si besoin""",
            
            "printer.txt": """Titre: Imprimante hors ligne (KB-PRT-02)
Catégorie: Imprimantes
Description: Problème d'impression
Étapes:
1. Vérifier que l'imprimante est allumée
2. Vérifier le papier et l'encre
3. Redémarrer le service d'impression
4. Escalader au support local si besoin""",
            
            "security.txt": """Titre: ALERTE SECURITE (KB-SEC-01)
Catégorie: Cybersécurité
Description: Ticket suspect ou malveillant
Action:
1. Contacter immédiatement l'équipe sécurité
2. Ne pas cliquer sur les liens suspects
3. Signaler à votre responsable
4. Ne pas partager d'informations sensibles"""
        }
        
        # Créer les fichiers par défaut
        for filename, content in default_docs.items():
            filepath = os.path.join(kb_path, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        # Charger tous les documents
        for filename in os.listdir(kb_path):
            if filename.endswith('.txt'):
                filepath = os.path.join(kb_path, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    category = filename.replace('.txt', '')
                    self.knowledge_base[category] = {
                        'content': content,
                        'keywords': self._extract_keywords(content)
                    }
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extrait les mots-clés du contenu"""
        words = content.lower().split()
        important = [w for w in words if len(w) > 4 and w not in ['vérifier', 'redémarrer', 'contacter']]
        return list(set(important))[:5]
    
    async def search(self, query: str, top_k: int = 3) -> Tuple[List[str], List[str]]:
        """Recherche les documents pertinents avec Ollama"""
        query_lower = query.lower()
        results = []
        sources = []
        
        # 1. Recherche par mots-clés
        for category, data in self.knowledge_base.items():
            if any(kw in query_lower for kw in data.get('keywords', [])):
                results.append(data['content'])
                sources.append(category)
        
        # 2. Si pas de résultats, utiliser Ollama pour trouver le meilleur document
        if not results:
            result = await self._search_with_ollama(query)
            if result:
                results.append(result['content'])
                sources.append(result['category'])
        
        return results[:top_k], sources[:top_k]
    
    async def _search_with_ollama(self, query: str) -> dict:
        """Recherche sémantique avec Ollama"""
        
        # Construire le contexte avec tous les documents
        context = "\n\n---\n\n".join([
            f"Document {i+1} ({cat}):\n{data['content']}"
            for i, (cat, data) in enumerate(self.knowledge_base.items())
        ])
        
        prompt = f"""Voici une base de connaissances de support informatique.

{context}

Question de l'utilisateur: "{query}"

Quel document est le plus pertinent pour répondre à cette question ?
Réponds UNIQUEMENT avec le nom de la catégorie du document (wifi, password, printer, security).
Si aucun document n'est pertinent, réponds "aucun"."""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            
            content = response['message']['content'].strip().lower()
            
            if content in self.knowledge_base:
                return {
                    'category': content,
                    'content': self.knowledge_base[content]['content']
                }
            
            return None
            
        except Exception as e:
            print(f"Erreur RAG Ollama: {e}")
            return None