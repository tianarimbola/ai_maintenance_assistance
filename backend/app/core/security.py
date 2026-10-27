from app.config import config

class SecurityFilter:
    def analyze(self, text: str) -> dict:
        text_lower = text.lower()
        
        is_malicious = any(word in text_lower for word in config.SENSITIVE_WORDS)
        
        prompt_injection = any(
            phrase in text_lower for phrase in [
                "ignore tes règles", "ignore tes instructions",
                "tu es un", "agis comme", "contourne",
                "oublie tout", "ne suis pas"
            ]
        )
        
        return {
            "is_malicious": is_malicious or prompt_injection,
            "reason": "Ticket suspect détecté" if is_malicious else "Ticket sécurisé",
            "prompt_injection_detected": prompt_injection
        }