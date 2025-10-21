"""
FastAPI Server - API per Antonio Gemma3 Evo Q4
Endpoints: /chat, /feedback, /stats, /neurons
WebSocket: /ws per chat real-time
"""

import asyncio
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.evomemory import EvoMemoryDB, Neuron, NeuronStore, RAGLite
from core.inference import LlamaInference, ConfidenceScorer


# ============================================================================
# MODELS
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True
    skill_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    confidence: float
    confidence_label: str
    reasoning: str
    neuron_id: int
    tokens_generated: int
    tokens_per_second: float
    rag_used: bool


class FeedbackRequest(BaseModel):
    neuron_id: int
    feedback: int  # -1, 0, +1


class StatsResponse(BaseModel):
    neurons_total: int
    meta_neurons: int
    rules_active: int
    skills_active: int
    avg_confidence: float
    uptime: str


# ============================================================================
# APP
# ============================================================================

app = FastAPI(
    title="Antonio Gemma3 Evo Q4",
    description="Self-learning offline AI for Raspberry Pi",
    version="0.1.0"
)

# CORS (per web UI future)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# GLOBAL STATE
# ============================================================================

class AppState:
    def __init__(self):
        self.db: Optional[EvoMemoryDB] = None
        self.neuron_store: Optional[NeuronStore] = None
        self.rag: Optional[RAGLite] = None
        self.llama: Optional[LlamaInference] = None
        self.scorer: ConfidenceScorer = ConfidenceScorer()
        self.start_time = datetime.now()

        # System prompt
        self.system_prompt = """Tu sei Antonio Gemma3 Evo Q4, un'intelligenza artificiale auto-evolutiva che gira offline.

Caratteristiche:
- Impari da ogni conversazione salvando "neuroni" in memoria locale
- Rilevi automaticamente la lingua (IT/EN) e rispondi nella stessa
- Assegni un livello di confidenza (0-1) ad ogni risposta
- Se non sei sicuro, lo dichiari e chiedi chiarimenti
- Puoi controllare GPIO, file system, e media (con consenso utente)

Comportamento:
- Sii conciso, pratico e amichevole
- Spiega passo per passo
- Chiedi prima di eseguire azioni sensibili
- Mantieni etica e privacy

You are Antonio Gemma3 Evo Q4, a self-learning offline AI.

Features:
- Learn from every conversation by saving "neurons" in local memory
- Auto-detect language (IT/EN) and respond accordingly
- Assign confidence score (0-1) to each response
- If uncertain, declare doubt and ask for clarification
- Can control GPIO, filesystem, media (with user consent)

Behavior:
- Be concise, practical, friendly
- Explain step-by-step
- Ask before executing sensitive actions
- Maintain ethics and privacy
"""

state = AppState()


# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup():
    """Inizializza componenti"""
    print("🚀 Starting Antonio Gemma3 Evo Q4...")

    # Database
    db_path = Path(__file__).parent.parent / "data/evomemory/neurons.db"
    state.db = EvoMemoryDB(str(db_path))
    state.neuron_store = NeuronStore(state.db)

    # RAG
    state.rag = RAGLite(state.neuron_store)
    state.rag.index_neurons(max_neurons=500)

    # LLM
    # Cerca il modello
    model_candidates = [
        Path(__file__).parent.parent.parent / "artifacts/gemma3-1b-q4_0.gguf",
        Path(__file__).parent.parent / "data/models/gemma3-1b-q4_0.gguf",
    ]

    model_path = None
    for candidate in model_candidates:
        if candidate.exists():
            model_path = candidate
            break

    if not model_path:
        print("⚠️  Warning: No model found, running in API-only mode")
    else:
        llama_cli = Path(__file__).parent.parent.parent / "build/bin/llama-cli"
        if llama_cli.exists():
            state.llama = LlamaInference(
                model_path=str(model_path),
                llama_cli_path=str(llama_cli),
            )
            print(f"✓ Loaded model: {model_path.name}")
        else:
            print("⚠️  llama-cli not found, running in API-only mode")

    stats = state.db.get_stats()
    print(f"✓ EvoMemory loaded: {stats['neurons']} neurons, {stats['rules']} rules")
    print(f"✓ Server ready at http://localhost:8000")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup"""
    if state.db:
        state.db.close()
    print("👋 Shutdown complete")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "name": "Antonio Gemma3 Evo Q4",
        "version": "0.1.0",
        "mode": "full" if state.llama else "api-only",
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Statistiche sistema"""
    stats = state.db.get_stats()
    uptime = datetime.now() - state.start_time

    return StatsResponse(
        neurons_total=stats["neurons"],
        meta_neurons=stats["meta_neurons"],
        rules_active=stats["rules"],
        skills_active=stats["skills"],
        avg_confidence=stats["avg_confidence"],
        uptime=str(uptime).split(".")[0],  # HH:MM:SS
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint principale"""

    if not state.llama:
        raise HTTPException(status_code=503, detail="LLM not loaded")

    # RAG context
    rag_context = ""
    if request.use_rag:
        rag_context = state.rag.get_context_for_prompt(request.message)

    # Build prompt
    user_prompt = request.message
    if rag_context:
        user_prompt = f"{rag_context}\n### Domanda attuale:\n{request.message}"

    # Generate
    result = state.llama.generate(
        prompt=user_prompt,
        system_prompt=state.system_prompt,
    )

    # Score confidence
    confidence, reasoning = state.scorer.score(
        result["output"],
        context={
            "tokens_per_second": result["tokens_per_second"],
            "prompt_tokens": result["prompt_tokens"],
        }
    )

    # Salva neurone
    neuron = Neuron(
        input_text=request.message,
        output_text=result["output"],
        idea=f"RAG used: {bool(rag_context)}",
        confidence=confidence,
        skill_id=request.skill_id,
        mood="neutral",
    )

    neuron_id = state.neuron_store.save_neuron(neuron)

    # Re-index RAG periodicamente
    neuron_count = state.db.get_stats()["neurons"]
    if neuron_count % 10 == 0:
        state.rag.index_neurons(max_neurons=500)

    return ChatResponse(
        response=result["output"],
        confidence=confidence,
        confidence_label=state.scorer.get_confidence_label(confidence),
        reasoning=reasoning,
        neuron_id=neuron_id,
        tokens_generated=result["tokens_generated"],
        tokens_per_second=result["tokens_per_second"],
        rag_used=bool(rag_context),
    )


@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Feedback su un neurone"""
    state.neuron_store.update_feedback(request.neuron_id, request.feedback)

    return {"status": "ok", "neuron_id": request.neuron_id, "feedback": request.feedback}


@app.get("/neurons/recent")
async def get_recent_neurons(limit: int = 10):
    """Ultimi neuroni"""
    neurons = state.neuron_store.get_recent_neurons(limit=limit)
    return [n.to_dict() for n in neurons]


@app.get("/neurons/{neuron_id}")
async def get_neuron(neuron_id: int):
    """Recupera un neurone specifico"""
    neuron = state.neuron_store.get_neuron(neuron_id)
    if not neuron:
        raise HTTPException(status_code=404, detail="Neuron not found")
    return neuron.to_dict()


# ============================================================================
# WEBSOCKET
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket per chat real-time"""
    await websocket.accept()

    try:
        while True:
            # Ricevi messaggio
            data = await websocket.receive_json()
            message = data.get("message", "")

            if not message:
                continue

            # Simula streaming (chunked response)
            await websocket.send_json({"type": "thinking", "data": "🤔"})

            # Generate
            request = ChatRequest(message=message, use_rag=data.get("use_rag", True))
            response = await chat(request)

            # Invia risposta
            await websocket.send_json({
                "type": "response",
                "data": response.dict(),
            })

    except WebSocketDisconnect:
        print("WebSocket disconnected")


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Dev only
        log_level="info",
    )
