from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import TicketRequest, TicketResponse
from app.core.classifier import TicketClassifier
from app.core.extractor import InfoExtractor
from app.core.rag_engine import RAGEngine
from app.core.agent import Agent
from app.core.security import SecurityFilter
import time
import uuid
from datetime import datetime

# Initialisation des composants
classifier = TicketClassifier()
extractor = InfoExtractor()
rag_engine = RAGEngine()
agent = Agent()
security_filter = SecurityFilter()

app = FastAPI(title="mAlntenance & Assistance API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/api/process", response_model=TicketResponse)
async def process_ticket(request: TicketRequest):
    start_time = time.time()
    trace_id = str(uuid.uuid4())[:8]
    logs = []
    description = request.description
    
    try:
        # 1. Sécurité
        security_result = security_filter.analyze(description)
        logs.append({"step": "security", "result": security_result})
        
        if security_result["is_malicious"]:
            return TicketResponse(
                ticket_id=f"T-{trace_id}",
                category="cybersecurite",
                priority="critique",
                assigned_team="securite",
                confidence=1.0,
                extracted_info=await extractor.extract(description),
                rag_sources=[],
                suggested_actions=["⚠️ Validation humaine requise - Ticket suspect"],
                decision={
                    "action": "bloquer",
                    "reasoning": security_result["reason"],
                    "requires_human_validation": True,
                    "confidence": 1.0
                },
                security_flagged=True,
                human_validation_required=True,
                trace_id=trace_id,
                processing_time_ms=(time.time() - start_time) * 1000,
                logs=logs
            )
        
        # 2. Classification
        classification = await classifier.classify(description)
        logs.append({"step": "classification", "result": classification.dict()})
        
        # 3. Extraction
        extraction = await extractor.extract(description)
        logs.append({"step": "extraction", "result": extraction.dict()})
        
        # 4. RAG
        rag_docs, rag_sources = await rag_engine.search(description)
        logs.append({"step": "rag", "documents_found": len(rag_docs), "sources": rag_sources})
        
        # 5. Agent
        decision = await agent.decide(
            classification=classification.dict(),
            extraction=extraction.dict(),
            rag_results={"documents": rag_docs, "sources": rag_sources},
            description=description
        )
        logs.append({"step": "agent", "decision": decision.dict()})
        
        # 6. Réponse
        processing_time = (time.time() - start_time) * 1000
        
        return TicketResponse(
            ticket_id=f"T-{trace_id}",
            category=classification.category,
            priority=classification.priority,
            assigned_team=classification.assigned_team,
            confidence=classification.confidence,
            extracted_info=extraction,
            rag_sources=rag_sources,
            suggested_actions=rag_docs if rag_docs else ["Aucune solution trouvée - Contactez le support"],
            decision=decision,
            security_flagged=security_result["is_malicious"],
            human_validation_required=decision.requires_human_validation,
            trace_id=trace_id,
            processing_time_ms=processing_time,
            logs=logs
        )
        
    except Exception as e:
        logs.append({"step": "error", "result": str(e)})
        raise HTTPException(status_code=500, detail=str(e))