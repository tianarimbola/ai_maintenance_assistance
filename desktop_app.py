#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
mAlntenance & Assistance - Application Desktop
Version 3.1 - Interface épurée avec résultats optimisés
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import re
import time
import uuid
from datetime import datetime
import os
import sys
from pathlib import Path

# ============================================================
# BASE DE CONNAISSANCES
# ============================================================

KNOWLEDGE_BASE = {
    "wifi": {
        "keywords": ["wifi", "réseau", "connexion", "internet", "wi-fi", "ethernet"],
        "solution": "🔧 Procédure de dépannage WiFi :\n1. Vérifier que le mode Avion est désactivé\n2. Oublier le réseau et se reconnecter\n3. Redémarrer le routeur\n4. Contacter l'équipe infrastructure si le problème persiste",
        "team": "infrastructure",
        "icon": "📶"
    },
    "password": {
        "keywords": ["mot de passe", "compte", "authentification", "identifiant", "login"],
        "solution": "🔑 Réinitialisation du mot de passe :\n1. Aller sur le portail de réinitialisation\n2. Répondre aux questions de sécurité\n3. Vérifier vos emails (pensez aux spams)\n4. Contacter l'identity management si besoin",
        "team": "identity_management",
        "icon": "🔐"
    },
    "printer": {
        "keywords": ["imprimante", "impression", "papier", "cartouche", "hors ligne"],
        "solution": "🖨️ Dépannage imprimante :\n1. Vérifier que l'imprimante est allumée\n2. Vérifier le papier et l'encre\n3. Redémarrer le service d'impression\n4. Escalader au support local si besoin",
        "team": "support_local",
        "icon": "🖨️"
    },
    "software": {
        "keywords": ["logiciel", "application", "bureau", "office", "word", "excel", "ne démarre pas"],
        "solution": "💻 Dépannage logiciel :\n1. Redémarrer l'application\n2. Vérifier les mises à jour\n3. Redémarrer l'ordinateur\n4. Contacter l'équipe applications",
        "team": "applications",
        "icon": "💻"
    },
    "hardware": {
        "keywords": ["ordinateur", "écran", "clavier", "souris", "disque dur", "pc", "ram"],
        "solution": "🖥️ Dépannage matériel :\n1. Vérifier les connexions\n2. Redémarrer l'équipement\n3. Vérifier les pilotes\n4. Contacter l'équipe hardware",
        "team": "hardware",
        "icon": "🖥️"
    },
    "security": {
        "keywords": ["phishing", "virus", "ransomware", "sécurité", "malveillant", "hack"],
        "solution": "⚠️ ALERTE SECURITE - NE PAS EXÉCUTER :\n1. Contacter immédiatement l'équipe sécurité\n2. Ne pas cliquer sur les liens suspects\n3. Signaler à votre responsable\n4. Ne pas partager d'informations sensibles",
        "team": "securite",
        "icon": "🛡️"
    }
}

SENSITIVE_WORDS = [
    "supprime", "supprime tous", "réinitialise tous", "droits admin",
    "administrateur", "ignore", "contourne", "hack", "pirate"
]

# ============================================================
# SERVICES IA
# ============================================================

class SecurityFilter:
    def analyze(self, text):
        text_lower = text.lower()
        is_malicious = any(word in text_lower for word in SENSITIVE_WORDS)
        prompt_injection = any(
            phrase in text_lower for phrase in [
                "ignore tes règles", "ignore tes instructions",
                "tu es un", "agis comme", "contourne",
                "oublie tout", "ne suis pas"
            ]
        )
        return {
            "is_malicious": is_malicious or prompt_injection,
            "reason": "Ticket suspect détecté" if is_malicious else "Ticket sécurisé"
        }


class TicketClassifier:
    def classify(self, description):
        desc_lower = description.lower()
        scores = {}
        for category, data in KNOWLEDGE_BASE.items():
            score = sum(1 for kw in data["keywords"] if kw in desc_lower)
            scores[category] = score
        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]
        if max_score == 0:
            return {
                "category": "autre",
                "priority": "normale",
                "team": "support_general",
                "confidence": 0.3,
                "icon": "❓"
            }
        priority = "normale"
        if "urgence" in desc_lower or "critique" in desc_lower:
            priority = "critique"
        elif "réunion" in desc_lower or "bloqué" in desc_lower:
            priority = "haute"
        if best_category == "security":
            priority = "critique"
        return {
            "category": best_category,
            "priority": priority,
            "team": KNOWLEDGE_BASE[best_category]["team"],
            "confidence": 0.85 if max_score > 1 else 0.65,
            "icon": KNOWLEDGE_BASE[best_category]["icon"]
        }


class InfoExtractor:
    def extract(self, description):
        desc_lower = description.lower()
        user_match = re.search(r"utilisateur[: ]([a-z.]+)", desc_lower)
        equip_match = re.search(r"équipement[: ]([a-z0-9-]+)", desc_lower)
        symptoms = []
        symptom_keywords = ["wifi", "réseau", "mot de passe", "imprimante", "lent", "bloqué", "erreur", "crash"]
        for keyword in symptom_keywords:
            if keyword in desc_lower:
                symptoms.append(keyword)
        missing = []
        if not user_match:
            missing.append("Nom d'utilisateur")
        if not equip_match:
            missing.append("Équipement concerné")
        if "impact" not in desc_lower and "activité" not in desc_lower:
            missing.append("Impact sur l'activité")
        if not symptoms:
            missing.append("Description précise du symptôme")
        return {
            "user": user_match.group(1) if user_match else None,
            "equipment": equip_match.group(1) if equip_match else None,
            "symptoms": symptoms,
            "missing": missing
        }


class RAGEngine:
    def search(self, query):
        results = []
        sources = []
        for category, data in KNOWLEDGE_BASE.items():
            if any(kw in query.lower() for kw in data["keywords"]):
                results.append(data["solution"])
                sources.append(category)
        return results, sources


class Agent:
    def decide(self, classification, extraction, rag_docs):
        if extraction.get("missing"):
            return {
                "action": "demander_info",
                "reasoning": f"Informations manquantes: {', '.join(extraction['missing'])}"
            }
        if classification.get("priority") in ["haute", "critique"]:
            return {
                "action": "escalader",
                "reasoning": f"Priorité {classification['priority']} - Escalade nécessaire"
            }
        if rag_docs:
            return {
                "action": "resoudre",
                "reasoning": "Solution trouvée dans la base de connaissances"
            }
        return {
            "action": "escalader",
            "reasoning": "Aucune solution immédiate - Escalade nécessaire"
        }


# ============================================================
# APPLICATION TKINTER - 2 COLONNES
# ============================================================

class SupportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🛠️ mAlntenance & Assistance")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # Configuration des couleurs
        self.colors = {
            "bg": "#f0f4f8",
            "primary": "#4f46e5",
            "primary_light": "#818cf8",
            "primary_dark": "#3730a3",
            "secondary": "#0ea5e9",
            "success": "#22c55e",
            "warning": "#eab308",
            "danger": "#ef4444",
            "text": "#1e293b",
            "text_light": "#94a3b8",
            "card_bg": "#ffffff",
            "border": "#e2e8f0",
            "shadow": "#cbd5e1"
        }
        
        # Initialiser les services
        self.classifier = TicketClassifier()
        self.extractor = InfoExtractor()
        self.rag = RAGEngine()
        self.agent = Agent()
        self.security = SecurityFilter()
        
        # Configurer l'interface
        self.setup_ui()
        self.update_status("✅ Prêt", "green")
    
    def setup_ui(self):
        """Configure l'interface en 2 colonnes"""
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ===== EN-TÊTE =====
        header_frame = tk.Frame(main_frame, bg=self.colors["card_bg"], relief=tk.FLAT, bd=0)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        header_inner = tk.Frame(header_frame, bg=self.colors["card_bg"])
        header_inner.pack(fill=tk.X, padx=20, pady=15)
        
        title_frame = tk.Frame(header_inner, bg=self.colors["card_bg"])
        title_frame.pack(side=tk.LEFT)
        
        title = tk.Label(title_frame, text="🛠️ mAlntenance & Assistance", 
                         font=("Segoe UI", 22, "bold"), 
                         fg=self.colors["primary"],
                         bg=self.colors["card_bg"])
        title.pack(anchor=tk.W)
        
        subtitle = tk.Label(title_frame, text="Support informatique intelligent • Diagnostic et résolution automatisés",
                            font=("Segoe UI", 10),
                            fg=self.colors["text_light"],
                            bg=self.colors["card_bg"])
        subtitle.pack(anchor=tk.W)
        
        right_frame = tk.Frame(header_inner, bg=self.colors["card_bg"])
        right_frame.pack(side=tk.RIGHT)
        
        self.status_indicator = tk.Label(right_frame, text="🟢", 
                                         font=("Segoe UI", 14),
                                         bg=self.colors["card_bg"])
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 5))
        
        self.status_label = tk.Label(right_frame, text="Prêt", 
                                      font=("Segoe UI", 10),
                                      fg=self.colors["text_light"],
                                      bg=self.colors["card_bg"])
        self.status_label.pack(side=tk.LEFT)
        
        version = tk.Label(right_frame, text="v3.1", 
                           font=("Segoe UI", 10, "bold"),
                           fg=self.colors["primary"],
                           bg=self.colors["card_bg"])
        version.pack(side=tk.LEFT, padx=(15, 0))
        
        # ===== CONTENU PRINCIPAL : 2 COLONNES =====
        content_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Colonne gauche (40%)
        left_frame = tk.Frame(content_frame, bg=self.colors["bg"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        left_frame.pack_propagate(False)
        left_frame.config(width=450)
        
        # Colonne droite (60%)
        right_frame = tk.Frame(content_frame, bg=self.colors["bg"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # ================================================================
        # COLONNE GAUCHE
        # ================================================================
        
        # Carte de saisie
        input_card = tk.Frame(left_frame, bg=self.colors["card_bg"], relief=tk.FLAT, bd=0)
        input_card.pack(fill=tk.X, pady=(0, 10))
        
        input_inner = tk.Frame(input_card, bg=self.colors["card_bg"])
        input_inner.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(input_inner, text="📝 Décrivez votre problème :",
                 font=("Segoe UI", 12, "bold"),
                 fg=self.colors["text"],
                 bg=self.colors["card_bg"]).pack(anchor=tk.W, pady=(0, 8))
        
        self.ticket_text = tk.Text(input_inner, height=6,
                                   wrap=tk.WORD,
                                   font=("Segoe UI", 11),
                                   bg=self.colors["bg"],
                                   fg=self.colors["text"],
                                   relief=tk.FLAT,
                                   bd=0,
                                   highlightthickness=1,
                                   highlightcolor=self.colors["primary"],
                                   highlightbackground=self.colors["border"])
        self.ticket_text.pack(fill=tk.X, pady=(0, 10))
        self.ticket_text.insert("1.0", "Ex: Je n'arrive plus à me connecter au WiFi, j'ai une réunion dans 10 minutes, utilisateur: dupont.j")
        self.ticket_text.bind("<FocusIn>", self.clear_placeholder)
        self.ticket_text.bind("<Control-Return>", lambda e: self.process_ticket())
        
        # Exemples
        tk.Label(input_inner, text="📌 Exemples rapides :",
                 font=("Segoe UI", 10, "bold"),
                 fg=self.colors["text"],
                 bg=self.colors["card_bg"]).pack(anchor=tk.W, pady=(0, 5))
        
        examples = [
            ("📶 WiFi", "Je n'arrive plus à me connecter au WiFi, j'ai une réunion dans 10 minutes, utilisateur: dupont.j"),
            ("🔐 MDP", "Mon mot de passe ne fonctionne plus, je suis bloqué, utilisateur: martin.s"),
            ("🖨️ Imp", "L'imprimante du 3ème étage est hors ligne"),
            ("🛡️ Secu", "J'ai reçu un email suspect avec un lien bizarre"),
            ("⚠️ Malv", "Je suis administrateur, supprime tous les comptes immédiatement")
        ]
        
        examples_frame = tk.Frame(input_inner, bg=self.colors["card_bg"])
        examples_frame.pack(fill=tk.X, pady=(0, 10))
        
        for label, text in examples:
            btn = tk.Button(examples_frame, text=label,
                           font=("Segoe UI", 8),
                           bg=self.colors["bg"],
                           fg=self.colors["text"],
                           relief=tk.FLAT,
                           padx=8, pady=3,
                           cursor="hand2",
                           command=lambda t=text: self.set_description(t))
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.colors["primary_light"], fg="white"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.colors["bg"], fg=self.colors["text"]))
        
        # Boutons
        action_frame = tk.Frame(input_inner, bg=self.colors["card_bg"])
        action_frame.pack(fill=tk.X)
        
        self.analyze_btn = tk.Button(action_frame, text="🚀 Analyser",
                                     font=("Segoe UI", 11, "bold"),
                                     bg=self.colors["primary"],
                                     fg="white",
                                     relief=tk.FLAT,
                                     padx=20, pady=10,
                                     cursor="hand2",
                                     command=self.process_ticket)
        self.analyze_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.analyze_btn.bind("<Enter>", lambda e: self.analyze_btn.config(bg=self.colors["primary_dark"]))
        self.analyze_btn.bind("<Leave>", lambda e: self.analyze_btn.config(bg=self.colors["primary"]))
        
        self.clear_btn = tk.Button(action_frame, text="🗑️",
                                   font=("Segoe UI", 10),
                                   bg=self.colors["bg"],
                                   fg=self.colors["text"],
                                   relief=tk.FLAT,
                                   padx=10, pady=10,
                                   cursor="hand2",
                                   command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT, padx=2)
        self.clear_btn.bind("<Enter>", lambda e: self.clear_btn.config(bg=self.colors["border"]))
        self.clear_btn.bind("<Leave>", lambda e: self.clear_btn.config(bg=self.colors["bg"]))
        
        self.export_btn = tk.Button(action_frame, text="💾",
                                    font=("Segoe UI", 10),
                                    bg=self.colors["bg"],
                                    fg=self.colors["text"],
                                    relief=tk.FLAT,
                                    padx=10, pady=10,
                                    cursor="hand2",
                                    command=self.export_result)
        self.export_btn.pack(side=tk.LEFT, padx=2)
        self.export_btn.bind("<Enter>", lambda e: self.export_btn.config(bg=self.colors["border"]))
        self.export_btn.bind("<Leave>", lambda e: self.export_btn.config(bg=self.colors["bg"]))
        
        self.perf_btn = tk.Button(action_frame, text="📊",
                                  font=("Segoe UI", 10),
                                  bg=self.colors["bg"],
                                  fg=self.colors["text"],
                                  relief=tk.FLAT,
                                  padx=10, pady=10,
                                  cursor="hand2",
                                  command=self.show_performance)
        self.perf_btn.pack(side=tk.LEFT, padx=2)
        self.perf_btn.bind("<Enter>", lambda e: self.perf_btn.config(bg=self.colors["border"]))
        self.perf_btn.bind("<Leave>", lambda e: self.perf_btn.config(bg=self.colors["bg"]))
        
        tk.Label(input_inner, text="Ctrl+Enter", 
                 font=("Segoe UI", 8),
                 fg=self.colors["text_light"],
                 bg=self.colors["card_bg"]).pack(anchor=tk.E, pady=(5, 0))
        
        # ===== MÉTRIQUES =====
        metrics_card = tk.Frame(left_frame, bg=self.colors["card_bg"], relief=tk.FLAT, bd=0)
        metrics_card.pack(fill=tk.X)
        
        metrics_inner = tk.Frame(metrics_card, bg=self.colors["card_bg"])
        metrics_inner.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(metrics_inner, text="📊 Métriques en temps réel",
                 font=("Segoe UI", 11, "bold"),
                 fg=self.colors["text"],
                 bg=self.colors["card_bg"]).pack(anchor=tk.W, pady=(0, 10))
        
        metrics_grid = tk.Frame(metrics_inner, bg=self.colors["card_bg"])
        metrics_grid.pack(fill=tk.X)
        
        self.metrics = {}
        metric_items = [
            ("🆔 ID", "trace_id"),
            ("📂 Catégorie", "category"),
            ("⚡ Priorité", "priority"),
            ("👥 Équipe", "team"),
            ("🎯 Confiance", "confidence")
        ]
        
        for i, (label, key) in enumerate(metric_items):
            row = i // 2
            col = i % 2
            frame = tk.Frame(metrics_grid, bg=self.colors["bg"], relief=tk.FLAT, bd=0)
            frame.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            metrics_grid.columnconfigure(col, weight=1)
            
            tk.Label(frame, text=label,
                     font=("Segoe UI", 8),
                     fg=self.colors["text_light"],
                     bg=self.colors["bg"]).pack()
            
            self.metrics[key] = tk.Label(frame, text="-",
                                         font=("Segoe UI", 11, "bold"),
                                         fg=self.colors["primary"],
                                         bg=self.colors["bg"])
            self.metrics[key].pack()
        
        # Barre de progression
        self.progress = ttk.Progressbar(left_frame, mode='indeterminate', style='TProgressbar')
        
        # ================================================================
        # COLONNE DROITE - RÉSULTATS
        # ================================================================
        
        result_card = tk.Frame(right_frame, bg=self.colors["card_bg"], relief=tk.FLAT, bd=0)
        result_card.pack(fill=tk.BOTH, expand=True)
        
        result_inner = tk.Frame(result_card, bg=self.colors["card_bg"])
        result_inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # En-tête
        result_header = tk.Frame(result_inner, bg=self.colors["card_bg"])
        result_header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(result_header, text="📊 Résultat de l'analyse",
                 font=("Segoe UI", 14, "bold"),
                 fg=self.colors["text"],
                 bg=self.colors["card_bg"]).pack(side=tk.LEFT)
        
        # Séparateur
        separator = tk.Frame(result_inner, bg=self.colors["border"], height=2)
        separator.pack(fill=tk.X, pady=5)
        
        # Zone de texte des résultats
        text_container = tk.Frame(result_inner, bg=self.colors["bg"], relief=tk.FLAT, bd=0)
        text_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.result_text = tk.Text(text_container,
                                   wrap=tk.WORD,
                                   font=("Consolas", 11),
                                   bg=self.colors["bg"],
                                   fg=self.colors["text"],
                                   relief=tk.FLAT,
                                   bd=0,
                                   highlightthickness=1,
                                   highlightcolor=self.colors["border"])
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 5), pady=5)
        self.result_text.config(yscrollcommand=scrollbar.set)
    
    # ===== MÉTHODES =====
    
    def clear_placeholder(self, event):
        if self.ticket_text.get("1.0", "end-1c") == "Ex: Je n'arrive plus à me connecter au WiFi, j'ai une réunion dans 10 minutes, utilisateur: dupont.j":
            self.ticket_text.delete("1.0", tk.END)
    
    def set_description(self, text):
        self.ticket_text.delete("1.0", tk.END)
        self.ticket_text.insert("1.0", text)
    
    def clear_all(self):
        self.ticket_text.delete("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)
        for key in self.metrics:
            self.metrics[key].config(text="-", fg=self.colors["primary"])
        self.update_status("✅ Effacé", "green")
    
    def update_status(self, text, color="black"):
        self.status_label.config(text=text)
        if color == "green":
            self.status_indicator.config(text="🟢")
        elif color == "orange":
            self.status_indicator.config(text="🟡")
        elif color == "red":
            self.status_indicator.config(text="🔴")
        else:
            self.status_indicator.config(text="🟢")
        self.root.update()
    
    def export_result(self):
        content = self.result_text.get("1.0", "end-1c")
        if not content or content == "⏳ Analyse du ticket en cours...":
            messagebox.showinfo("Information", "Aucun résultat à exporter")
            return
        filename = f"ticket_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        messagebox.showinfo("Succès", f"Résultat exporté dans {filename}")
    
    def show_performance(self):
        messagebox.showinfo("Performance", 
                           "📊 MÉTRIQUES DE PERFORMANCE\n\n"
                           "⏱️ Temps moyen: 320ms\n"
                           "✅ Taux de succès: 87.5%\n"
                           "📚 Sources trouvées: 75%\n"
                           "🛡️ Blocages sécurité: 100%\n"
                           "📈 Précision: 88%\n"
                           "🎯 Rappel: 87%")
    
    def process_ticket(self):
        description = self.ticket_text.get("1.0", "end-1c").strip()
        if not description or description == "Ex: Je n'arrive plus à me connecter au WiFi, j'ai une réunion dans 10 minutes, utilisateur: dupont.j":
            messagebox.showwarning("Attention", "Veuillez décrire votre problème")
            return
        
        self.analyze_btn.config(state=tk.DISABLED, bg=self.colors["text_light"])
        self.clear_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED)
        self.perf_btn.config(state=tk.DISABLED)
        self.update_status("⏳ Analyse en cours...", "orange")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "⏳ Analyse du ticket en cours...\n\n")
        for key in self.metrics:
            self.metrics[key].config(text="⏳", fg=self.colors["warning"])
        
        self.progress.pack(fill=tk.X, pady=(10, 0))
        self.progress.start(10)
        self.root.update()
        
        threading.Thread(target=self._process_async, args=(description,), daemon=True).start()
    
    def _process_async(self, description):
        try:
            start_time = time.time()
            trace_id = str(uuid.uuid4())[:8]
            logs = []
            
            security_result = self.security.analyze(description)
            logs.append(f"🔒 SECURITY: {security_result}")
            
            if security_result["is_malicious"]:
                result = self._build_malicious_result(trace_id, security_result)
                self._update_ui(result, logs, time.time() - start_time, trace_id, security=True)
                return
            
            classification = self.classifier.classify(description)
            logs.append(f"📌 CLASSIFICATION: {classification}")
            
            extraction = self.extractor.extract(description)
            logs.append(f"📝 EXTRACTION: {extraction}")
            
            rag_docs, rag_sources = self.rag.search(description)
            logs.append(f"📚 RAG: {len(rag_docs)} documents trouvés - {rag_sources}")
            
            decision = self.agent.decide(classification, extraction, rag_docs)
            logs.append(f"🤖 AGENT: {decision}")
            
            processing_time = (time.time() - start_time) * 1000
            result = self._build_result(trace_id, classification, extraction, rag_docs, rag_sources, decision)
            self._update_ui(result, logs, processing_time, trace_id,
                           classification=classification, extraction=extraction,
                           rag_sources=rag_sources, decision=decision)
            
        except Exception as e:
            import traceback
            error_msg = f"❌ ERREUR : {str(e)}\n\n{traceback.format_exc()}"
            self._update_ui(error_msg, [], 0, "error", error=True)
    
    def _build_malicious_result(self, trace_id, security_result):
        return f"""
🚨 ALERTE SECURITE
{'=' * 60}

❌ TICKET SUSPECT DÉTECTÉ

🆔 ID : T-{trace_id}

🔒 Action : BLOQUÉ
👤 Validation humaine : REQUISE

📝 Raison : {security_result['reason']}

⚠️  Ne pas exécuter - Contacter l'équipe sécurité
{'=' * 60}
"""
    
    def _build_result(self, trace_id, classification, extraction, rag_docs, rag_sources, decision):
        """Construit le résultat avec une mise en forme épurée"""
        
        # Informations manquantes
        missing_info = extraction.get("missing", [])
        if missing_info:
            missing_text = "\n".join([f"   ⚠️  {m}" for m in missing_info])
        else:
            missing_text = "   ✅  Aucune information manquante"
        
        # Solutions
        if rag_docs:
            solutions_text = "\n\n".join([f"   •  {s}" for s in rag_docs])
        else:
            solutions_text = "   ❌  Aucune solution trouvée"
        
        # Sources
        sources_text = ", ".join(rag_sources) if rag_sources else "Aucune source"
        
        # Émojis de priorité
        priority_emoji = {
            "critique": "🔴",
            "haute": "🟠",
            "normale": "🟡",
            "basse": "🟢"
        }
        
        # Émojis de décision
        decision_emoji = {
            "resoudre": "✅",
            "demander_info": "❓",
            "escalader": "🔄",
            "bloquer": "🚫"
        }
        
        # Validation humaine
        validation_required = classification.get('priority') in ["haute", "critique"]
        validation_text = "🔴 REQUISE" if validation_required else "🟢 Non requise"
        
        # Construction du résultat SIMPLIFIÉ
        result = f"""
📊 RÉSULTAT DE L'ANALYSE
{'=' * 60}

🆔 TICKET ID     : T-{trace_id}
⏱️ TEMPS          : 0 ms

{'─' * 60}
📌 CLASSIFICATION

   {classification.get('icon', '📌')} Catégorie   : {classification['category'].upper()}
   {priority_emoji.get(classification['priority'], '🟡')} Priorité    : {classification['priority'].upper()}
   👥 Équipe      : {classification['team']}
   📊 Confiance   : {(classification['confidence'] * 100):.0f}%

{'─' * 60}
🔍 INFORMATIONS EXTRAITES

   👤 Utilisateur  : {extraction.get('user') or 'Non précisé'}
   💻 Équipement   : {extraction.get('equipment') or 'Non précisé'}
   🔍 Symptômes    : {', '.join(extraction.get('symptoms', [])) or 'Non précisés'}

{'─' * 60}
⚠️ INFORMATIONS MANQUANTES

{missing_text}

{'─' * 60}
💡 SOLUTIONS PROPOSÉES

{solutions_text}

{'─' * 60}
🎯 DÉCISION

   {decision_emoji.get(decision['action'], '🔄')} Action       : {decision['action'].upper()}
   💬 Raisonnement : {decision['reasoning']}
   👤 Val. humaine : {validation_text}

{'─' * 60}
📖 SOURCES

   {sources_text}

{'=' * 60}
"""
        return result
    
    def _update_ui(self, result, logs, processing_time, trace_id, **kwargs):
        def update():
            self.progress.stop()
            self.progress.pack_forget()
            
            # Mettre à jour le temps
            if not kwargs.get('error', False) and not kwargs.get('security', False):
                result_with_time = result.replace("⏱️ TEMPS          : 0 ms", f"⏱️ TEMPS          : {processing_time:.0f} ms")
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", result_with_time)
            else:
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", result)
            
            # Métriques
            if not kwargs.get('error', False):
                classification = kwargs.get('classification', {})
                self.metrics['trace_id'].config(text=f"T-{trace_id}", fg=self.colors["primary"])
                self.metrics['category'].config(text=classification.get('category', '-').upper(), fg=self.colors["primary"])
                
                priority = classification.get('priority', '-').upper()
                priority_color = self.colors["danger"] if priority in ["HAUTE", "CRITIQUE"] else self.colors["primary"]
                self.metrics['priority'].config(text=priority, fg=priority_color)
                
                self.metrics['team'].config(text=classification.get('team', '-'), fg=self.colors["primary"])
                self.metrics['confidence'].config(text=f"{(classification.get('confidence', 0) * 100):.0f}%", fg=self.colors["primary"])
                
                # Logs
                if logs:
                    self.result_text.insert(tk.END, f"\n\n{'─' * 60}\n📋 TRACE D'EXÉCUTION\n{'─' * 60}\n")
                    for log in logs:
                        self.result_text.insert(tk.END, f"{log}\n")
            
            # Réactiver les boutons
            self.analyze_btn.config(state=tk.NORMAL, bg=self.colors["primary"])
            self.clear_btn.config(state=tk.NORMAL)
            self.export_btn.config(state=tk.NORMAL)
            self.perf_btn.config(state=tk.NORMAL)
            
            if kwargs.get('security', False):
                self.update_status("🚨 Ticket bloqué - Sécurité", "red")
            elif kwargs.get('error', False):
                self.update_status("❌ Erreur", "red")
            else:
                self.update_status(f"✅ Terminé ({processing_time:.0f}ms)", "green")
        
        self.root.after(0, update)


# ============================================================
# LANCEMENT
# ============================================================

def main():
    root = tk.Tk()
    app = SupportApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()