from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class TicketPriority(str, Enum):
    BASSE = "basse"
    NORMALE = "normale"
    HAUTE = "haute"
    CRITIQUE = "critique"

class TicketCategory(str, Enum):
    RESEAU = "reseau"
    COMPTES = "comptes"
    IMPRIMANTES = "imprimantes"
    LOGICIELS = "logiciels"
    MATERIEL = "materiel"
    CYBERSECURITE = "cybersecurite"
    AUTRE = "autre"

class TicketStatus(str, Enum):
    NOUVEAU = "nouveau"
    ANALYSE = "analyse"
    EN_COURS = "en_cours"
    RESOLU = "resolu"
    ESCALADE = "escalade"
    BLOQUE = "bloque"

class ToolCall(BaseModel):
    name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    status: str = "pending"
    timestamp: datetime = Field(default_factory=datetime.now)

class TicketRequest(BaseModel):
    description: str
    user_id: Optional[str] = None
    equipment_id: Optional[str] = None

class ClassificationResult(BaseModel):
    category: TicketCategory
    priority: TicketPriority
    assigned_team: str
    confidence: float = Field(ge=0, le=1)

class ExtractionResult(BaseModel):
    user_id: Optional[str] = None
    equipment_id: Optional[str] = None
    symptoms: List[str] = []
    time_occurred: Optional[str] = None
    business_impact: Optional[str] = None
    attempted_fixes: List[str] = []
    missing_info: List[str] = []

class RAGResult(BaseModel):
    documents: List[str]
    sources: List[str]
    relevance_scores: List[float]
    has_sufficient_info: bool

class AgentDecision(BaseModel):
    action: str  # "resoudre", "demander_info", "escalader", "bloquer"
    reasoning: str
    tools_called: List[ToolCall]
    requires_human_validation: bool
    confidence: float

class TicketResponse(BaseModel):
    ticket_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Classification
    category: TicketCategory
    priority: TicketPriority
    assigned_team: str
    confidence: float
    
    # Extraction
    extracted_info: ExtractionResult
    
    # RAG
    rag_sources: List[str]
    suggested_actions: List[str]
    
    # Agent
    decision: AgentDecision
    
    # Security
    security_flagged: bool
    human_validation_required: bool
    
    # Observability
    trace_id: str
    processing_time_ms: float
    logs: List[Dict[str, Any]]