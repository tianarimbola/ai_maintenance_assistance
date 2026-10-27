from app.models import ExtractionResult
from app.config import config
import ollama
import json
import re

class InfoExtractor:
    def __init__(self):
        self.model = config.OLLAMA_MODEL
    
    async def extract(self, description: str) -> ExtractionResult:
        """Extrait les informations avec Ollama"""
        
        # 1. D'abord l'extraction par regex (rapide)
        regex_result = self._extract_by_regex(description)
        
        # 2. Si tout est trouvé, on retourne
        if not regex_result.missing_info:
            return regex_result
        
        # 3. Sinon, on utilise Ollama
        return await self._extract_with_ollama(description, regex_result)
    
    def _extract_by_regex(self, description: str) -> ExtractionResult:
        """Extraction rapide par regex"""
        desc_lower = description.lower()
        
        user_match = re.search(r"utilisateur[: ]([a-z.]+)", desc_lower)
        equip_match = re.search(r"équipement[: ]([a-z0-9-]+)", desc_lower)
        
        symptoms = []
        symptom_keywords = ["wifi", "réseau", "mot de passe", "imprimante", "lent", "bloqué", "erreur"]
        for keyword in symptom_keywords:
            if keyword in desc_lower:
                symptoms.append(keyword)
        
        missing_info = []
        if not user_match:
            missing_info.append("Quel est votre nom d'utilisateur ?")
        if not equip_match:
            missing_info.append("Sur quel équipement ?")
        if "impact" not in desc_lower and "activité" not in desc_lower:
            missing_info.append("Quel est l'impact sur votre activité ?")
        if not symptoms:
            missing_info.append("Pouvez-vous décrire plus précisément le symptôme ?")
        
        return ExtractionResult(
            user_id=user_match.group(1) if user_match else None,
            equipment_id=equip_match.group(1) if equip_match else None,
            symptoms=symptoms,
            time_occurred="Non précisé",
            business_impact="Non précisé",
            attempted_fixes=[],
            missing_info=missing_info
        )
    
    async def _extract_with_ollama(self, description: str, regex_result: ExtractionResult) -> ExtractionResult:
        """Extraction fine avec Ollama"""
        
        prompt = f"""Analyse ce ticket de support et extrait les informations structurées.

Ticket: "{description}"

Extrais:
- user_id: nom d'utilisateur (format: prenom.nom)
- equipment_id: identifiant de l'équipement
- symptoms: liste des symptômes
- time_occurred: moment du problème
- business_impact: impact sur l'activité

Réponds UNIQUEMENT avec ce JSON:
{{
    "user_id": "nom.utilisateur",
    "equipment_id": "PC-123",
    "symptoms": ["symptôme1", "symptôme2"],
    "time_occurred": "ce matin",
    "business_impact": "bloque le travail"
}}

Si une information n'est pas présente, mets null."""

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
                
                # Mettre à jour avec les nouvelles infos
                missing_info = regex_result.missing_info.copy()
                
                if data.get("user_id"):
                    missing_info = [m for m in missing_info if "nom d'utilisateur" not in m.lower()]
                if data.get("equipment_id"):
                    missing_info = [m for m in missing_info if "équipement" not in m.lower()]
                if data.get("business_impact"):
                    missing_info = [m for m in missing_info if "impact" not in m.lower()]
                
                return ExtractionResult(
                    user_id=data.get("user_id", regex_result.user_id),
                    equipment_id=data.get("equipment_id", regex_result.equipment_id),
                    symptoms=data.get("symptoms", regex_result.symptoms),
                    time_occurred=data.get("time_occurred", regex_result.time_occurred),
                    business_impact=data.get("business_impact", regex_result.business_impact),
                    attempted_fixes=regex_result.attempted_fixes,
                    missing_info=missing_info
                )
            
            return regex_result
            
        except Exception as e:
            print(f"Erreur Ollama extraction: {e}")
            return regex_result