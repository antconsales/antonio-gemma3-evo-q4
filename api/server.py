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
from core.question_classifier import classify_question, get_system_prompt, Complexity
from core.metrics_collector import MetricsCollector
from core.inference import LlamaInference, ConfidenceScorer
from core.query_router import QueryRouter, QueryType
from core.voice_prompts import get_prompt_for_mode


# ============================================================================
# MODELS
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True
    skill_id: Optional[str] = None
    voice_mode: bool = False  # Voice mode: fast, concise responses


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

        # Dual model system
        self.llama_fast: Optional[LlamaInference] = None  # Fast model for simple chat
        self.llama_tools: Optional[LlamaInference] = None # Tool-aware model for complex tasks
        self.query_router: QueryRouter = QueryRouter()

        # Legacy support (points to fast model)
        self.llama: Optional[LlamaInference] = None

        self.scorer: ConfidenceScorer = ConfidenceScorer()
        self.start_time = datetime.now()

        # System prompt
        self.system_prompt = """You are Antonio, an AI that thinks step-by-step before answering.

Tu sei Antonio Gemma3 Evo Q4, un'intelligenza artificiale auto-evolutiva.

REASONING RULES:
1. Math subtraction: "X has N, loses M" → Calculate: N - M
2. Math addition: "X has N, adds M" → Calculate: N + M  
3. If uncertain → Admit "Non sono sicuro / I'm not sure"

PROCESS:
1. Understand the question
2. If math/logic: break into steps and show reasoning
3. Give final answer

EXAMPLES:

Q: Se un cane ha 4 zampe e ne perde 1, quante ne ha?
A: Ragioniamo:
   - Zampe iniziali: 4
   - Zampe perse: 1
   - Calcolo: 4 - 1 = 3
   Risposta: 3 zampe.

Q: If I have 10 coins and lose 3, how many left?
A: Step-by-step:
   - Initial: 10
   - Lost: 3
   - Calculation: 10 - 3 = 7
   Answer: 7 coins.

Caratteristiche:
- Impari da ogni conversazione (EvoMemory)
- Rilevi lingua (IT/EN) e rispondi nella stessa
- Assegni confidenza (0-1) ad ogni risposta
- Controlli GPIO/filesystem (con consenso)

Comportamento:
- Sii conciso, pratico e amichevole
- Spiega passo per passo
- Chiedi prima di eseguire azioni sensibili
        # Adaptive reasoning based on complexity
        complexity, _ = classify_question(request.message)
        adaptive_prompt = get_system_prompt(complexity)
        
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
metrics = MetricsCollector()


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

    # LLM - Dual Model System
    # Load both fast model (for simple chat) and tool model (for complex tasks)
    print("🧠 Loading dual model system...")

    try:
        # Fast model for simple conversations
        state.llama_fast = LlamaInference(
            model_path="antconsales/antonio-gemma3-evo-q4"
        )
        print("  ✓ Fast model loaded: antconsales/antonio-gemma3-evo-q4")

        # Tool-aware model for complex tasks
        state.llama_tools = LlamaInference(
            model_path="antonio-tools"
        )
        print("  ✓ Tool model loaded: antonio-tools (fine-tuned)")

        # Legacy support - point to fast model
        state.llama = state.llama_fast

        print("✓ Dual model system ready - automatic routing enabled!")
    except Exception as e:
        print(f"⚠️  Warning: Could not load models: {e}")
        print("⚠️  Running in API-only mode")

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
    mode = "dual-model" if (state.llama_fast and state.llama_tools) else "api-only"
    return {
        "status": "online",
        "name": "Antonio Gemma3 Evo Q4 - Dual Model System",
        "version": "0.2.0",
        "mode": mode,
        "models": {
            "fast": "antconsales/antonio-gemma3-evo-q4" if state.llama_fast else None,
            "tools": "antonio-tools" if state.llama_tools else None,
        },
        "routing": "automatic"
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




@app.get("/metrics")
async def get_metrics():
    """Get adaptive prompting performance metrics"""
    return metrics.get_stats()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint principale con ottimizzazioni voice mode"""

    if not state.llama_fast or not state.llama_tools:
        raise HTTPException(status_code=503, detail="LLM not loaded")

    # 🧠 AUTOMATIC MODEL ROUTING
    # Use query router to select appropriate model
    selected_model_name, routing_reason = state.query_router.get_model_for_query(request.message)
    query_type, _ = state.query_router.classify(request.message)

    # Select the actual model instance
    if "antonio-tools" in selected_model_name:
        selected_model = state.llama_tools
        model_label = "🔧 TOOL"
    else:
        selected_model = state.llama_fast
        model_label = "⚡ FAST"

    mode_emoji = "🎤" if request.voice_mode else "💬"
    print(f"[{model_label}] [{mode_emoji}] {request.message[:40]}... | {routing_reason}")

    # 🚀 VOICE MODE OPTIMIZATIONS
    # Disable RAG for simple queries in voice mode (saves ~200ms)
    use_rag_this_request = request.use_rag
    if request.voice_mode and query_type == QueryType.SIMPLE:
        use_rag_this_request = False

    # RAG context
    rag_context = ""
    if use_rag_this_request:
        rag_context = state.rag.get_context_for_prompt(request.message)

    # Build prompt
    user_prompt = request.message
    if rag_context:
        user_prompt = f"{rag_context}\n### Domanda attuale:\n{request.message}"

    # 🎯 Select prompt based on mode
    if request.voice_mode:
        # Ultra-concise prompt for voice
        system_prompt = get_prompt_for_mode(voice_mode=True)
    else:
        # Normal adaptive prompt for text
        complexity, complexity_reason = classify_question(request.message)
        system_prompt = get_system_prompt(complexity)

    # 🔧 Voice mode generation parameters
    gen_params = {}
    if request.voice_mode:
        gen_params = {
            "num_predict": 50,      # Max 50 tokens = ~2 sentences
            "num_ctx": 512,          # Reduced context for speed
            "temperature": 0.7,
        }
    else:
        gen_params = {
            "num_predict": 256,      # Normal length
            "num_ctx": 1024,         # Full context
        }

    # Generate with selected model
    result = selected_model.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        params=gen_params,
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



    # Log metrics for adaptive prompting analysis
    if not request.voice_mode:
        # Only log metrics in text mode (voice mode uses different prompting)
        import time
        metrics.log_request(
            question=request.message,
            complexity=complexity if not request.voice_mode else Complexity.SIMPLE,
            complexity_reason=complexity_reason if not request.voice_mode else "voice_mode",
            response=result["output"],
            tokens_generated=result["tokens_generated"],
            tokens_per_second=result["tokens_per_second"],
            response_time_ms=result.get("response_time_ms", 0),
            confidence=confidence
        )

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
