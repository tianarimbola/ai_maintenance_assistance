from app.models import AgentDecision
from app.config import config
import ollama
import json
import re

class Agent:
    def __init__(self):
        self.model = config.OLLAMA_MODEL
    
    async def decide(self, classification: dict, extraction: dict, rag_results: dict, description: str) -> AgentDecision:
        """Prend une décision avec Ollama"""
        
        # 1. Vérifier les règles simples
        missing_info = extraction.get('missing_info', [])
        
        if missing_info:
            return AgentDecision(
                action="demander_info",
                reasoning=f"Informations manquantes: {', '.join(missing_info)}",
                tools_called=[],
                requires_human_validation=False,
                confidence=0.8
            )
        
        priority = classification.get('priority')
        if priority in ["critique"]:
            return AgentDecision(
                action="escalader",
                reasoning=f"Priorité {priority} - Escalade nécessaire",
                tools_called=[],
                requires_human_validation=True,
                confidence=0.9
            )
        
        # 2. Utiliser Ollama pour la décision
        return await self._decide_with_ollama(classification, extraction, rag_results, description)
    
    async def _decide_with_ollama(self, classification: dict, extraction: dict, rag_results: dict, description: str) -> AgentDecision:
        """Décision avec Ollama"""
        
        documents = rag_results.get('documents', [])
        sources = rag_results.get('sources', [])
        
        prompt = f"""Tu es un agent de support informatique. Prends une décision.

Ticket: "{description}"

Classification:
- Catégorie: {classification.get('category')}
- Priorité: {classification.get('priority')}
- Équipe: {classification.get('assigned_team')}
- Confiance: {classification.get('confidence')}

Informations extraites:
- Utilisateur: {extraction.get('user_id')}
- Équipement: {extraction.get('equipment_id')}
- Symptômes: {extraction.get('symptoms')}

Solutions trouvées:
{documents if documents else "Aucune"}

Sources: {sources if sources else "Aucune"}

Décide l'action:
- "resoudre": si une solution est trouvée
- "demander_info": si des infos manquent
- "escalader": si besoin d'un technicien
- "bloquer": si c'est dangereux

Réponds UNIQUEMENT avec ce JSON:
{{
    "action": "resoudre|demander_info|escalader|bloquer",
    "reasoning": "raison détaillée",
    "requires_human_validation": true/false,
    "confidence": 0.85
}}"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            
            content = response['message']['content']
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                
                # Si des documents sont trouvés, on favorise la résolution
                if documents and data.get('action') == 'escalader':
                    data['action'] = 'resoudre'
                    data['reasoning'] = "Solution trouvée dans la base de connaissances"
                    data['confidence'] = 0.85
                
                return AgentDecision(
                    action=data.get("action", "escalader"),
                    reasoning=data.get("reasoning", "Décision automatique"),
                    tools_called=[],
                    requires_human_validation=data.get("requires_human_validation", False),
                    confidence=data.get("confidence", 0.7)
                )
            
            # Fallback
            return AgentDecision(
                action="escalader",
                reasoning="Décision par défaut",
                tools_called=[],
                requires_human_validation=True,
                confidence=0.5
            )
            
        except Exception as e:
            print(f"Erreur Ollama agent: {e}")
            return AgentDecision(
                action="escalader",
                reasoning=f"Erreur: {str(e)}",
                tools_called=[],
                requires_human_validation=True,
                confidence=0.3
            )