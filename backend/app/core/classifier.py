from app.models import ClassificationResult, TicketCategory, TicketPriority
from app.config import config
import ollama
import json
import re

class TicketClassifier:
    def __init__(self):
        self.model = config.OLLAMA_MODEL
        
        self.team_mapping = {
            TicketCategory.RESEAU: "infrastructure",
            TicketCategory.COMPTES: "identity_management",
            TicketCategory.IMPRIMANTES: "support_local",
            TicketCategory.LOGICIELS: "applications",
            TicketCategory.MATERIEL: "hardware",
            TicketCategory.CYBERSECURITE: "securite",
            TicketCategory.AUTRE: "support_general"
        }
    
    async def classify(self, description: str) -> ClassificationResult:
        """Classifie le ticket avec Ollama"""
        
        # 1. D'abord avec des règles simples (rapide)
        rule_result = self._classify_by_rules(description)
        
        # 2. Si confiance > 0.8, on retourne directement
        if rule_result.confidence > 0.8:
            return rule_result
        
        # 3. Sinon, on utilise Ollama pour affiner
        return await self._classify_with_ollama(description, rule_result)
    
    def _classify_by_rules(self, description: str) -> ClassificationResult:
        """Classification rapide par règles"""
        desc_lower = description.lower()
        
        keywords = {
            TicketCategory.RESEAU: ["wifi", "réseau", "connexion", "internet", "vpn", "dns"],
            TicketCategory.COMPTES: ["mot de passe", "compte", "authentification", "identifiant", "login"],
            TicketCategory.IMPRIMANTES: ["imprimante", "impression", "cartouche", "papier"],
            TicketCategory.LOGICIELS: ["application", "logiciel", "bureau", "office"],
            TicketCategory.MATERIEL: ["ordinateur", "écran", "clavier", "souris", "disque dur", "pc"],
            TicketCategory.CYBERSECURITE: ["phishing", "virus", "ransomware", "sécurité", "malveillant"]
        }
        
        scores = {}
        for category, words in keywords.items():
            score = sum(1 for w in words if w in desc_lower)
            scores[category] = score
        
        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]
        
        if max_score == 0:
            return ClassificationResult(
                category=TicketCategory.AUTRE,
                priority=TicketPriority.NORMALE,
                assigned_team="support_general",
                confidence=0.3
            )
        
        priority = TicketPriority.NORMALE
        if "urgence" in desc_lower or "critique" in desc_lower:
            priority = TicketPriority.CRITIQUE
        elif "réunion" in desc_lower or "bloqué" in desc_lower:
            priority = TicketPriority.HAUTE
        
        if best_category == TicketCategory.CYBERSECURITE:
            priority = TicketPriority.CRITIQUE
        
        return ClassificationResult(
            category=best_category,
            priority=priority,
            assigned_team=self.team_mapping[best_category],
            confidence=0.7 if max_score > 1 else 0.5
        )
    
    async def _classify_with_ollama(self, description: str, rule_result: ClassificationResult) -> ClassificationResult:
        """Classification fine avec Ollama"""
        
        prompt = f"""Tu es un expert en support informatique. Analyse ce ticket et classifie-le.

Ticket: "{description}"

Règles automatiques:
- Catégorie estimée: {rule_result.category.value}
- Priorité estimée: {rule_result.priority.value}
- Équipe estimée: {rule_result.assigned_team}

Réponds UNIQUEMENT avec ce JSON:
{{
    "category": "reseau|comptes|imprimantes|logiciels|materiel|cybersecurite|autre",
    "priority": "basse|normale|haute|critique",
    "assigned_team": "nom_de_l_equipe",
    "confidence": 0.85
}}

La confiance doit être entre 0 et 1."""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            
            # Extraire le JSON de la réponse
            content = response['message']['content']
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                return ClassificationResult(
                    category=TicketCategory(data.get("category", rule_result.category.value)),
                    priority=TicketPriority(data.get("priority", rule_result.priority.value)),
                    assigned_team=data.get("assigned_team", rule_result.assigned_team),
                    confidence=data.get("confidence", rule_result.confidence)
                )
            
            return rule_result
            
        except Exception as e:
            print(f"Erreur Ollama: {e}")
            return rule_result